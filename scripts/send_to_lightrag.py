import argparse
import os
import sys
import requests

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from personal_agent.config import settings
except ImportError:
    print("Error: Could not import settings. Make sure you are running from the project root or have configured your Python path correctly.")
    sys.exit(1)

def send_file_to_lightrag(file_path: str):
    """Sends a file to the LightRAG server's /documents/file endpoint."""
    lightrag_server_url = settings.LIGHTRAG_SERVER.rstrip('/')
    upload_url = f"{lightrag_server_url}/documents/file"

    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
            print(f"Sending '{file_path}' to LightRAG server at {upload_url}...")
            response = requests.post(upload_url, files=files, timeout=60)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        print(f"Successfully sent '{file_path}' to LightRAG server.")
        print("Server response:")
        print(response.json())

    except requests.exceptions.RequestException as e:
        print(f"Error sending file to LightRAG server: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Server responded with status {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="Send a file to the LightRAG server.")
    parser.add_argument("file_path", help="The path to the file to send.")
    args = parser.parse_args()

    send_file_to_lightrag(args.file_path)

if __name__ == "__main__":
    main()
