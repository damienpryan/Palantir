# app/main.py

import logging
from flask import Flask, request, jsonify, send_from_directory, session
from flask_session import Session  # Import Flask-Session
import os
from dotenv import load_dotenv
import uuid

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

load_dotenv()

app = Flask(__name__)

# --- Session Configuration ---
# Secret key for signing the session cookie
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'super-secret-key-for-dev')
# Configure session to use the filesystem (server-side)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'  # Directory to store session files
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)
# --- END Session Configuration ---

# --- Configure Logging ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO);

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
app.logger.setLevel(log_level)
# --- END Configure Logging ---

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('APP_DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key or google_api_key == "your_google_api_key_here":
    app.logger.error("GOOGLE_API_KEY is not configured. LLM calls will fail.")

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=google_api_key)

COLLECTION_NAME = "qad_code_embeddings"

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return "Hello from Flask App! The frontend should be at /."

@app.route('/db_test')
def db_test():
    try:
        import psycopg2
        DB_HOST = os.environ.get("APP_DB_HOST", "app_db")
        DB_NAME = os.environ.get("APP_DB_NAME", "palantir_app_db")
        DB_USER = os.environ.get("APP_DB_USER", "palantir_user")
        DB_PASSWORD = os.environ.get("APP_DB_PASSWORD")

        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        app.logger.info("Successfully connected to app_db from /db_test.")
        return jsonify({"status": "Database connection successful", "test_query_result": result[0]})
    except Exception as e:
        app.logger.error(f"Error connecting to app_db from /db_test: {e}")
        return jsonify({"status": "Database connection error", "error": str(e)}), 500

@app.route('/chat/<path:query>', methods=['GET', 'POST'])
def chat(query):
    if not google_api_key or google_api_key == "your_google_api_key_here":
        return jsonify({"response": "Error: Google API Key not configured in .env"}), 500

    context_filepath = session.get('context_filepath')
    file_content = ""

    if context_filepath and os.path.exists(context_filepath):
        try:
            with open(context_filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            app.logger.info(f"Using context from session file: {context_filepath}")
            # Clean up the file after reading
            os.remove(context_filepath)
            session.pop('context_filepath', None)
        except Exception as e:
            app.logger.error(f"Error reading or deleting context file {context_filepath}: {e}")
            file_content = "" # Ensure content is clear on error

    try:
        effective_query = query
        if file_content:
            effective_query = f"Here is some relevant context:\n{file_content}\n\nBased on this context and the following question: {query}"
    
        messages = [
            SystemMessage(content="You are a helpful AI assistant for OpenEdge code. Provide concise and relevant information based on the user's query and any provided context."),
            HumanMessage(content=effective_query),
        ]
    
        llm_response_object = llm.invoke(messages)
        llm_response_content = llm_response_object.content

        return jsonify({"query": query, "response": llm_response_content})

    except Exception as e:
        app.logger.error(f"Error communicating with LLM: {e}")
        return jsonify({"response": f"Error communicating with LLM: {str(e)}"}), 500

@app.route('/upload_context', methods=['POST'])
def upload_context():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if file:
        unique_filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Clean up any old file path in session before saving new one
        old_filepath = session.get('context_filepath')
        if old_filepath and os.path.exists(old_filepath):
            os.remove(old_filepath)
            
        file.save(filepath)
        session['context_filepath'] = filepath # Store file path in session
        app.logger.info(f"File '{unique_filename}' uploaded and path stored in session.")

        return jsonify({
            "message": "File uploaded successfully and is ready for context.",
            "filename": unique_filename
        }), 200

    return jsonify({"message": "File upload failed"}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"message": "File not found"}), 404
    except Exception as e:
        return jsonify({"message": f"Error serving file: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
