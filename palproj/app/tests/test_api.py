# palproj/tests/test_api.py
import requests
import os

# The base URL for the Flask app, accessible from within the Docker network
BASE_URL = "http://app:5000"

def test_db_connection():
    """
    Tests the /db_test endpoint to ensure the Flask app can connect to the database.
    """
    print("--- Running test: test_db_connection ---")
    try:
        response = requests.get(f"{BASE_URL}/db_test", timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        assert data["status"] == "Database connection successful"
        assert data["test_query_result"] == 1
        
        print("SUCCESS: /db_test endpoint returned a successful connection.")
        
    except requests.exceptions.RequestException as e:
        print(f"FAILURE: An error occurred while calling the /db_test endpoint: {e}")
        exit(1) # Exit with a non-zero code to fail the test
    except AssertionError as e:
        print(f"FAILURE: The response from /db_test was not as expected: {e}")
        exit(1)

if __name__ == "__main__":
    test_db_connection()
    print("\nAll backend API tests passed!")
