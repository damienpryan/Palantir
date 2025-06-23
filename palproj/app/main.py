# app/main.py

import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

import uuid # For unique filenames for uploaded files
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

load_dotenv() # Load environment variables from .env

app = Flask(__name__)

# --- Configure Logging ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper() # Get LOG_LEVEL from .env
log_level = getattr(logging, log_level_str, logging.INFO)

# Remove any default Flask/Gunicorn handlers to ensure only our handler is active
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure basic logging to stdout/stderr (which Docker captures)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Directs logs to console (stdout/stderr)
    ]
)
app.logger.setLevel(log_level) # Set Flask's internal logger level
# --- END Configure Logging -


# Configure your PostgreSQL database for app data (from your proj_dump)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('APP_DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Google API Key for LLM ---
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key or google_api_key == "your_google_api_key_here":
    app.logger.error("GOOGLE_API_KEY is not configured. LLM calls will fail.")
    # For production, you might want to stop the app or raise an error here.
    # For development, we'll let it proceed and return an error from the chat endpoint.

# Initialize your LLM (from your proj_dump)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=google_api_key)

# This is where your vector store is configured, from proj_dump.txt
COLLECTION_NAME = "qad_code_embeddings"
PG_EMBEDDING_CONNECTION_STRING = os.getenv("PG_EMBEDDING_CONNECTION_STRING")

# --- New: File Upload Configuration ---
UPLOAD_FOLDER = 'uploads' # Folder inside the app container
# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Global variable to store content of the last uploaded file for temporary context
# NOTE: This is a *very simple* in-memory solution and will not scale or persist across requests/users.
# For a real application, you'd integrate this with sessions, a temporary DB, or direct RAG processing.
last_uploaded_file_content = ""


@app.route('/')
def home():
    return "Hello from Flask App! The frontend should be at /."

# Placeholder for a database test route (from your dump)
@app.route('/db_test')
def db_test():
    try:
        # Example: Replace with an actual DB query to test connection
        # from sqlalchemy import text
        # db.session.execute(text("SELECT 1"))
        return jsonify({"status": "Database connection seems OK (placeholder for actual test)"})
    except Exception as e:
        return jsonify({"status": "Database connection error", "error": str(e)}), 500

# Your COMBINED RAG chat endpoint
@app.route('/chat/<path:query>', methods=['GET', 'POST']) 
def chat(query):
    global last_uploaded_file_content # Access the global variable

    if not google_api_key or google_api_key == "your_google_api_key_here":
        return jsonify({"response": "Error: Google API Key not configured in .env"}), 500

    try:
        # --- ORIGINAL LANGCHAIN RAG LOGIC RE-INTEGRATED ---
        # Add the context from the last uploaded file to the query
        effective_query = query
        if last_uploaded_file_content:
            effective_query = f"Here is some relevant context:\n{last_uploaded_file_content}\n\nBased on this context and the following question: {query}"
            app.logger.info(f"Using uploaded file content as context for query: {query}")
        
        messages = [
            SystemMessage(content="You are a helpful AI assistant for OpenEdge code. Provide concise and relevant information based on the user's query and any provided context."),
            HumanMessage(content=effective_query),
        ]
        
        llm_response_object = llm.invoke(messages)
        llm_response_content = llm_response_object.content # Extract content from the LangChain response object
        # --- END ORIGINAL LANGCHAIN RAG LOGIC ---

        return jsonify({"query": query, "response": llm_response_content})

    except Exception as e:
        app.logger.error(f"Error communicating with LLM: {e}")
        return jsonify({"response": f"Error communicating with LLM: {str(e)}"}), 500


@app.route('/upload_context', methods=['POST']) 
def upload_context():
    global last_uploaded_file_content # Declare intent to modify global

    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if file:
        # Generate a unique filename to prevent conflicts
        unique_filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)

        file_content = ""
        try:
            # Attempt to read content for text-based files
            with open(filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            app.logger.info(f"File '{unique_filename}' uploaded and content read. Length: {len(file_content)}")
            
            # Store content in the global variable for temporary context
            last_uploaded_file_content = file_content

        except Exception as e:
            app.logger.error(f"Error reading uploaded file {unique_filename}: {e}")
            last_uploaded_file_content = "" # Clear if error reading
            return jsonify({"message": "File uploaded but failed to read content", "filename": unique_filename, "error": str(e)}), 500

        return jsonify({
            "message": "File uploaded successfully",
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_size": file.content_length,
        }), 200

    return jsonify({"message": "File upload failed"}), 500

@app.route('/download/<filename>', methods=['GET']) 
def download_file(filename):
    try:
        # This will serve files from the UPLOAD_FOLDER
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"message": "File not found"}), 404
    except Exception as e:
        return jsonify({"message": f"Error serving file: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
