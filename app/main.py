import os
from flask import Flask
import psycopg2
from psycopg2 import OperationalError # Import OperationalError for connection issues

app = Flask(__name__)

# Function to get a database connection
def get_db_connection():
    db_host = os.environ.get('DB_HOST')
    db_name = os.environ.get('DB_NAME')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')

    conn = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        print("Database connection successful.")
        return conn
    except OperationalError as e:
        print(f"Error connecting to database: {e}")
        return None

@app.route('/')
def hello_world():
    return 'Hello, Palantir Project Flask App!'

@app.route('/db_test')
def db_test():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT version();') # A simple query to get PostgreSQL version
            db_version = cur.fetchone()[0]
            cur.close()
            return f'Successfully connected to PostgreSQL! Version: {db_version}'
        except Exception as e:
            return f'Error performing database query: {e}'
        finally:
            conn.close() # Close connection after use
    else:
        return 'Could not connect to the database.', 500

if __name__ == '__main__':
    # In a Dockerized Gunicorn setup, app.run() is typically not executed
    # because Gunicorn handles running the Flask app.
    # This block is mainly for local development outside of Docker Compose.
    app.run(debug=True, host='0.0.0.0', port=5000)
