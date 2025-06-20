from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

app = Flask(__name__)

# Initialize Google Gemini LLM
google_api_key = os.environ.get("GOOGLE_API_KEY")
if not google_api_key or google_api_key == "your_google_api_key_here":
    print("WARNING: GOOGLE_API_KEY not set or is placeholder. LLM calls will fail.")
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=google_api_key)


# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.environ.get('APP_DB_USER')}:{os.environ.get('APP_DB_PASSWORD')}@{os.environ.get('APP_DB_HOST')}/{os.environ.get('APP_DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress a warning

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define a Database Model (Example: ChatHistory)
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<ChatHistory(user_message={self.user_message[:50]}, bot_response={self.bot_response[:50]})>'


@app.route('/')
def hello_world():
    return 'Hello, Palantir Project Flask App! (with SQLAlchemy)'

@app.route('/db_test')
def db_test():
    try:
        # Note: db.create_all() is typically used for initial setup or in development,
        # but in production, you primarily rely on Flask-Migrate's 'upgrade' command.
        # Keeping it here for quick testing, it won't recreate if tables exist.
        db.create_all()

        # Example: Add a chat history entry
        new_entry = ChatHistory(session_id='test_session_sql_alchemy', user_message='Hello from SQLAlchemy!', bot_response='Hi there from SQLAlchemy!')
        db.session.add(new_entry)
        db.session.commit()

        # Query to verify the addition
        all_chats = ChatHistory.query.all()
        return f'Successfully connected to PostgreSQL with SQLAlchemy! Added {len(all_chats)} entries. Last entry: {all_chats[-1].user_message}'
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        return f'Error: {e}', 500

@app.route('/chat/<query>')
def chat_with_llm(query):
    if not google_api_key or google_api_key == "your_google_api_key_here":
        return "Error: Google API Key not configured.", 500

    try:
        messages = [
            SystemMessage(content="You are a helpful AI assistant."),
            HumanMessage(content=query),
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Error communicating with LLM: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
