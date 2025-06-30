import os
import psycopg2
from psycopg2.extras import execute_values
import hashlib
import re
from tqdm import tqdm
import sys
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# --- Configure Logging ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
# --- END Configure Logging ---

# --- Configuration ---
load_dotenv()

DB_HOST = os.environ.get("VECTOR_DB_HOST", "vector_db")
DB_NAME = os.environ.get("VECTOR_DB_NAME", "palantir_vector_db")
DB_USER = os.environ.get("VECTOR_DB_USER", "palantir_vector_user")
DB_PASSWORD = os.environ.get("VECTOR_DB_PASSWORD")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_api_key_here":
    logger.error("ERROR: GOOGLE_API_KEY not set or is placeholder. Embedding generation will fail.")
    sys.exit(1)

CODE_REPO_PATH = os.environ.get("CODE_REPO_PATH", "/qad-code-repo")

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize GoogleGenerativeAIEmbeddings: {e}")
    sys.exit(1)

def get_db_connection():
    """Establishes and returns a database connection to vector_db."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info("Successfully connected to vector_db.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Error connecting to vector_db: {e}")
        return None

def create_embeddings_table(cursor):
    """Creates the 'code_embeddings' table if it doesn't exist."""
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_embeddings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                file_path TEXT NOT NULL,
                procedure_name TEXT,
                chunk_text TEXT NOT NULL,
                chunk_hash TEXT NOT NULL UNIQUE,
                embedding VECTOR(768),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        logger.info("Ensured 'code_embeddings' table and 'vector' extension exist.")
    except Exception as e:
        logger.error(f"Error creating table/extension: {e}")
        raise

def clear_embeddings_table(cursor):
    """Deletes all data from the code_embeddings table."""
    try:
        cursor.execute("TRUNCATE TABLE code_embeddings RESTART IDENTITY;")
        logger.info("Cleared existing data from 'code_embeddings' table.")
    except Exception as e:
        logger.error(f"Error truncating table: {e}")
        raise

def chunk_openedge_code(file_content, file_path):
    """Splits OpenEdge ABL code into meaningful chunks."""
    chunks = []
    procedure_regex = re.compile(
        r'(?:PROCEDURE|FUNCTION)\s+(?:PRIVATE|PUBLIC|INTERNAL)?\s*([\w\-.]+)\s*(\(.*?\))?\s*:',
        re.IGNORECASE | re.DOTALL
    )
    last_end = 0
    for match in procedure_regex.finditer(file_content):
        pre_code = file_content[last_end:match.start()].strip()
        if pre_code:
            chunks.append({
                "file_path": file_path,
                "procedure_name": "FILE_HEADER" if last_end == 0 else "INTER_PROCEDURE_CODE",
                "chunk_text": pre_code
            })
        procedure_start = match.start()
        procedure_name = match.group(1).strip()
        end_match = re.search(
            r'(?:END\s+PROCEDURE|END\s+FUNCTION)\s*(\.|,|$)',
            file_content[procedure_start:],
            re.IGNORECASE | re.DOTALL
        )
        chunk_end = len(file_content)
        if end_match:
            chunk_end = procedure_start + end_match.end()
        chunk_text = file_content[procedure_start:chunk_end].strip()
        if chunk_text:
            chunks.append({
                "file_path": file_path,
                "procedure_name": procedure_name,
                "chunk_text": chunk_text
            })
        last_end = chunk_end
    remaining_code = file_content[last_end:].strip()
    if remaining_code:
        chunks.append({
            "file_path": file_path,
            "procedure_name": "FILE_FOOTER",
            "chunk_text": remaining_code
        })
    return chunks

def ingest_codebase():
    """Main function to orchestrate the code ingestion process."""
    conn = get_db_connection()
    if conn is None:
        logger.error("Cannot proceed without a database connection.")
        return

    total_files_processed = 0
    total_chunks_generated = 0
    total_chunks_ingested = 0

    try:
        with conn.cursor() as cur:
            create_embeddings_table(cur)
            clear_embeddings_table(cur)
            conn.commit()

            logger.info(f"Starting code scanning in: {CODE_REPO_PATH}")
            all_chunks_to_ingest = []
            explicit_extensions = ('.p', '.w', '.t')

            for root, _, files in os.walk(CODE_REPO_PATH):
                for file in files:
                    _, ext = os.path.splitext(file.lower())
                    if ext in explicit_extensions or ext.startswith('.i'):
                        file_path = os.path.join(root, file)
                        relative_file_path = os.path.relpath(file_path, CODE_REPO_PATH)
                        logger.debug(f"Processing file: {relative_file_path}")
                        total_files_processed += 1
                        try:
                            with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                                file_content = f.read()
                            chunks = chunk_openedge_code(file_content, relative_file_path)
                            for chunk in chunks:
                                chunk_hash = hashlib.sha256(chunk["chunk_text"].encode('utf-8')).hexdigest()
                                chunk["chunk_hash"] = chunk_hash
                                all_chunks_to_ingest.append(chunk)
                        except Exception as e:
                            logger.error(f"Error processing {relative_file_path}: {e}")
                            continue
            
            total_chunks_generated = len(all_chunks_to_ingest)
            logger.info(f"Generated {total_chunks_generated} chunks. Generating embeddings and inserting into DB...")

            batch_size = 50
            for i in tqdm(range(0, len(all_chunks_to_ingest), batch_size), desc="Ingesting batches"):
                batch_chunks = all_chunks_to_ingest[i:i + batch_size]
                texts_to_embed = [chunk["chunk_text"] for chunk in batch_chunks]
                try:
                    embeddings_list = embeddings.embed_documents(texts_to_embed)
                    values_to_insert = [
                        (
                            chunk["file_path"],
                            chunk.get("procedure_name"),
                            chunk["chunk_text"],
                            chunk["chunk_hash"],
                            embedding
                        ) for chunk, embedding in zip(batch_chunks, embeddings_list)
                    ]
                    query = """
                        INSERT INTO code_embeddings (file_path, procedure_name, chunk_text, chunk_hash, embedding)
                        VALUES %s
                        ON CONFLICT (chunk_hash) DO NOTHING;
                    """
                    execute_values(cur, query, values_to_insert, page_size=batch_size)
                    conn.commit()
                    total_chunks_ingested += len(values_to_insert)
                except Exception as e:
                    logger.error(f"\nError during batch ingestion (batch {i}-{i+batch_size}): {e}")
                    conn.rollback()

    except Exception as e:
        logger.error(f"An error occurred during ingestion: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

    logger.info("--- Ingestion Process Summary ---")
    logger.info(f"Total files processed: {total_files_processed}")
    logger.info(f"Total chunks generated: {total_chunks_generated}")
    logger.info(f"Total chunks successfully ingested: {total_chunks_ingested}")
    logger.info("--- End of Summary ---")

if __name__ == '__main__':
    logger.info("Starting code ingestion script...")
    ingest_codebase()
    logger.info("Ingestion script finished.")
