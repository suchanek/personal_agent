import argparse
import json
import os
import subprocess
import sys

import requests

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from personal_agent.config import settings
except ImportError:
    print(
        "Error: Could not import settings. Make sure you are running from the project root or have configured your Python path correctly."
    )
    sys.exit(1)


def send_file_to_lightrag(
    file_path: str,
    remote_host: str = None,
    remote_user: str = None,
    remote_path: str = None,
    remote_lightrag_url: str = None,
):
    """Sends a file to the LightRAG server's /documents/file endpoint or copies it via SCP."""

    if remote_host and remote_user and remote_path:
        # Handle SCP transfer
        local_filename = os.path.basename(file_path)
        remote_target = f"{remote_user}@{remote_host}:{remote_path}/{local_filename}"
        scp_command = ["scp", file_path, remote_target]

        print(f"Attempting to transfer '{file_path}' to '{remote_target}' via SCP...")
        try:
            subprocess.run(scp_command, check=True, capture_output=True, text=True)
            print(f"Successfully transferred '{file_path}' to remote server.")

            # Trigger remote rescan
            if remote_lightrag_url:
                rescan_url = f"{remote_lightrag_url.rstrip('/')}/documents/scan"  # Corrected endpoint
                print(f"Triggering rescan on remote LightRAG server at {rescan_url}...")
                try:
                    rescan_response = requests.post(rescan_url, timeout=30)
                    rescan_response.raise_for_status()
                    print(f"Remote LightRAG server rescan triggered successfully.")
                    print(json.dumps(rescan_response.json(), indent=2))
                except requests.exceptions.RequestException as e:
                    print(f"Error triggering remote LightRAG rescan: {e}")
                    if hasattr(e, "response") and e.response is not None:
                        print(
                            f"Server responded with status {e.response.status_code}: {e.response.text}"
                        )
            else:
                print("Remote LightRAG URL not provided, skipping remote rescan.")

        except subprocess.CalledProcessError as e:
            print(f"Error during SCP transfer: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
        except FileNotFoundError:
            print(
                f"Error: 'scp' command not found. Make sure OpenSSH client is installed and in your PATH."
            )
        return

    # Original API call logic
    lightrag_server_url = settings.LIGHTRAG_SERVER.rstrip("/")
    upload_url = f"{lightrag_server_url}/documents/file"

    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "application/octet-stream")
            }
            print(f"Sending '{file_path}' to LightRAG server at {upload_url}...")
            response = requests.post(upload_url, files=files, timeout=60)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        print(f"Successfully sent '{file_path}' to LightRAG server.")
        print("\n" + "=" * 40)
        print("  LightRAG Server Response")
        print("=" * 40)
        print(json.dumps(response.json(), indent=2))
        print("=" * 40 + "\n")

    except requests.exceptions.RequestException as e:
        print(f"Error sending file to LightRAG server: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(
                f"Server responded with status {e.response.status_code}: {e.response.text}"
            )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Send a file to the LightRAG server or copy it via SCP."
    )
    parser.add_argument("file_path", help="The path to the file to send.")
    parser.add_argument(
        "--remote-host",
        default="100.100.248.61",
        help="Optional: The hostname or IP address of the remote server for SCP transfer (default: 100.100.248.61).",
    )
    parser.add_argument(
        "--remote-user",
        default="suchanek",
        help="Optional: The SSH username for the remote server (default: suchanek).",
    )
    parser.add_argument(
        "--remote-path",
        default="/Users/Shared/personal_agent_data/knowledge",
        help="Optional: The absolute path on the remote server where the file should be copied (default: /Users/Shared/personal_agent_data/knowledge).",
    )
    parser.add_argument(
        "--remote-lightrag-url",
        default="http://100.100.248.61:9621",
        help="Optional: The URL of the remote LightRAG server API to trigger rescan (default: http://100.100.248.61:9621).",
    )
    args = parser.parse_args()

    send_file_to_lightrag(
        args.file_path,
        args.remote_host,
        args.remote_user,
        args.remote_path,
        args.remote_lightrag_url,
    )


if __name__ == "__main__":
    main()
