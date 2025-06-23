import os
import psycopg2
from psycopg2.extras import execute_values
import hashlib
import re
from tqdm import tqdm # For progress bar
import sys 

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv # To load environment variables from .env
import logging

# --- Configure Logging (Copy this block) ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
# --- END Configure Logging ---

# --- Configuration ---
# Load environment variables from .env file (if not already loaded by Docker Compose)
load_dotenv()

# Database connection details for vector_db
DB_HOST = os.environ.get("VECTOR_DB_HOST", "vector_db")
DB_NAME = os.environ.get("VECTOR_DB_NAME", "palantir_vector_db")
DB_USER = os.environ.get("VECTOR_DB_USER", "palantir_vector_user")
DB_PASSWORD = os.environ.get("VECTOR_DB_PASSWORD")

# Google API Key for Embeddings
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_api_key_here":
    print("ERROR: GOOGLE_API_KEY not set or is placeholder. Embedding generation will fail.")
    exit(1) # Exit if API key is not valid

# Path to the mounted QAD code repository inside the Docker container
CODE_REPO_PATH = os.environ.get("CODE_REPO_PATH", "/qad-code-repo") # Default mount point

# Initialize the Google Embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

# --- Database Setup and Connection ---
def get_db_connection():
    """Establishes and returns a database connection to vector_db."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Successfully connected to vector_db.")
        return conn
    except Exception as e:
        print(f"Error connecting to vector_db: {e}")
        return None

def create_embeddings_table(cursor):
    """
    Creates the 'code_embeddings' table if it doesn't exist.
    This table will store our code chunks, metadata, and their embeddings.
    """
    try:
        cursor.execute("""
            CREATE EXTENSION IF NOT EXISTS vector;
            CREATE TABLE IF NOT EXISTS code_embeddings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                file_path TEXT NOT NULL,
                procedure_name TEXT,
                chunk_text TEXT NOT NULL,
                chunk_hash TEXT NOT NULL UNIQUE, -- To prevent duplicate ingestion
                embedding VECTOR(768), -- text-embedding-004 produces 768-dimensional embeddings
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("Ensured 'code_embeddings' table and 'vector' extension exist.")
    except Exception as e:
        print(f"Error creating table/extension: {e}")
        raise # Re-raise to stop if table creation fails

def clear_embeddings_table(cursor):
    """Deletes all data from the code_embeddings table."""
    try:
        cursor.execute("TRUNCATE TABLE code_embeddings RESTART IDENTITY;")
        print("Cleared existing data from 'code_embeddings' table.")
    except Exception as e:
        print(f"Error truncating table: {e}")
        raise

# --- OpenEdge Code Chunking Logic ---
def chunk_openedge_code(file_content, file_path):
    """
    Splits OpenEdge ABL code into meaningful chunks (procedures/functions)
    and extracts relevant metadata.
    """
    chunks = []
    # Regex to find PROCEDURE or FUNCTION definitions (case-insensitive)
    # It captures the name after PROCEDURE/FUNCTION
    # It also handles variations like 'PROCEDURE PRIVATE', 'FUNCTION PUBLIC', etc.
    # We use re.DOTALL to allow '.' to match newlines
    procedure_regex = re.compile(
        r'(?:PROCEDURE|FUNCTION)\s+(?:PRIVATE|PUBLIC|INTERNAL)?\s*([\w\-.]+)\s*(\(.*?\))?\s*:',
        re.IGNORECASE | re.DOTALL
    )

    last_end = 0
    for match in procedure_regex.finditer(file_content):
        # Add the text before this procedure/function as a chunk if it exists
        pre_code = file_content[last_end:match.start()].strip()
        if pre_code:
            chunks.append({
                "file_path": file_path,
                "procedure_name": "FILE_HEADER" if last_end == 0 else "INTER_PROCEDURE_CODE",
                "chunk_text": pre_code
            })

        procedure_start = match.start()
        procedure_name = match.group(1).strip()
        # Find the end of the procedure/function
        # This is a heuristic: look for 'END PROCEDURE' or 'END FUNCTION'
        end_match = re.search(
            r'(?:END\s+PROCEDURE|END\s+FUNCTION)\s*(\.|,|$)', # Capture . or , or end of string
            file_content[procedure_start:],
            re.IGNORECASE | re.DOTALL
        )

        chunk_end = len(file_content) # Default to end of file
        if end_match:
            # Add match.start() to convert relative index to absolute index in file_content
            chunk_end = procedure_start + end_match.end()

        chunk_text = file_content[procedure_start:chunk_end].strip()
        if chunk_text:
            chunks.append({
                "file_path": file_path,
                "procedure_name": procedure_name,
                "chunk_text": chunk_text
            })
        last_end = chunk_end

    # Add any remaining code after the last procedure/function
    remaining_code = file_content[last_end:].strip()
    if remaining_code:
        chunks.append({
            "file_path": file_path,
            "procedure_name": "FILE_FOOTER",
            "chunk_text": remaining_code
        })

    return chunks

# --- Main Ingestion Logic ---
def ingest_codebase():
    """
    Main function to orchestrate the code ingestion process.
    Scans the mounted code repository, chunks OpenEdge files,
    generates embeddings, and stores them in the vector database.
    """
    conn = get_db_connection()
    if conn is None:
        print("Cannot proceed without a database connection.")
        return

    try:
        with conn.cursor() as cur:
            create_embeddings_table(cur) # Ensure table exists first
            clear_embeddings_table(cur)  # Clear existing data for a full re-ingestion

            print(f"Starting code scanning in: {CODE_REPO_PATH}")
            all_chunks_to_ingest = []
            # Define explicitly allowed extensions like .p, .w, .t
            explicit_extensions = ('.p', '.w', '.t')

            for root, _, files in os.walk(CODE_REPO_PATH):
                for file in files:
                    file_lower = file.lower()
                    # Get the file extension
                    _, ext = os.path.splitext(file_lower)

                    # Check if the extension is explicitly allowed OR if it starts with '.i'
                    if ext in explicit_extensions or ext.startswith('.i'):
                        file_path = os.path.join(root, file)
                        relative_file_path = os.path.relpath(file_path, CODE_REPO_PATH)
                        print(f"Processing file: {relative_file_path}")

                        try:
                            with open(file_path, 'r', encoding='latin-1') as f: # OpenEdge often uses latin-1
                                file_content = f.read()

                            chunks = chunk_openedge_code(file_content, relative_file_path)
                            for chunk in chunks:
                                # Generate a unique hash for the chunk content
                                chunk_hash = hashlib.sha256(chunk["chunk_text"].encode('utf-8')).hexdigest()
                                chunk["chunk_hash"] = chunk_hash
                                all_chunks_to_ingest.append(chunk)

                        except Exception as e:
                            print(f"Error processing {relative_file_path}: {e}")
                            continue

            print(f"Generated {len(all_chunks_to_ingest)} chunks. Generating embeddings and inserting into DB...")

            # Batching embeddings and insertions to optimize API calls and DB writes
            batch_size = 50 # Adjust based on API limits and performance
            for i in tqdm(range(0, len(all_chunks_to_ingest), batch_size), desc="Ingesting batches"):
                batch_chunks = all_chunks_to_ingest[i:i + batch_size]
                texts_to_embed = [chunk["chunk_text"] for chunk in batch_chunks]

                try:
                    # Generate embeddings for the batch
                    embeddings_list = embeddings.embed_documents(texts_to_embed)

                    # Prepare data for batch insertion
                    values_to_insert = []
                    for j, chunk in enumerate(batch_chunks):
                        values_to_insert.append((
                            chunk["file_path"],
                            chunk.get("procedure_name"), # procedure_name might be None
                            chunk["chunk_text"],
                            chunk["chunk_hash"],
                            embeddings_list[j] # Assign the corresponding embedding from the list
                        ))

                    # Batch insert into the database
                    query = """
                        INSERT INTO code_embeddings (file_path, procedure_name, chunk_text, chunk_hash, embedding)
                        VALUES %s
                        ON CONFLICT (chunk_hash) DO NOTHING; -- Prevents re-inserting identical chunks
                    """
                    execute_values(cur, query, values_to_insert, page_size=batch_size)
                    conn.commit() # Commit after each batch
                except Exception as e:
                    print(f"\nError during batch ingestion (batch {i}-{i+batch_size}): {e}")
                    conn.rollback() # Rollback the current batch on error
                    # Consider more robust error handling: retry, log and continue, etc.

            print("Ingestion process completed.")

    except Exception as e:
        conn.rollback() # Rollback any changes on error if main process fails
        print(f"An error occurred during ingestion: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

# --- Script Execution ---
if __name__ == '__main__':
    print("Starting code ingestion script...")
    ingest_codebase()
    print("Ingestion script finished.")
