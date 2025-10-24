import argparse
import os
import subprocess
import sys
from pathlib import Path


# --- Configuration ---
# Define colors for terminal output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


# --- Path and URL Constants ---
# The script assumes it is run from the root of the personal_agent repository.
LIGHTRAG_MEMORY_DIR = Path("lightrag_memory_server")
ENV_FILE = LIGHTRAG_MEMORY_DIR / ".env"

# Define the URLs for local and remote configurations
# You can adjust the remote IP if needed
CONFIG = {
    "local": {
        "OLLAMA_URL": "http://localhost:11434",
        "OLLAMA_DOCKER_URL": "http://host.docker.internal:11434",
        "EMBEDDING_BINDING_HOST": "http://host.docker.internal:11434",
    },
    "remote": {
        "OLLAMA_URL": "http://100.100.248.61:11434",
        "OLLAMA_DOCKER_URL": "http://host.docker.internal:11434",
        "EMBEDDING_BINDING_HOST": "http://100.100.248.61:11434",
    },
}


def get_current_config():
    """Reads the .env file and returns the current configuration as a dictionary."""
    if not ENV_FILE.exists():
        return {}

    config = {}
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def update_env_file(target_mode: str):
    """Updates the .env file based on the selected mode's configuration."""
    if target_mode not in CONFIG:
        print(
            f"{Colors.RED}✗ Invalid mode '{target_mode}'. Use 'local' or 'remote'.{Colors.NC}"
        )
        return False

    if not ENV_FILE.exists():
        print(f"{Colors.RED}✗ Environment file not found at: {ENV_FILE}{Colors.NC}")
        return False

    new_settings = CONFIG[target_mode]
    current_lines = ENV_FILE.read_text().splitlines()
    updated_lines = []
    keys_to_update = set(new_settings.keys())

    # Update existing keys
    for line in current_lines:
        key_in_line = line.split("=")[0].strip()
        if key_in_line in keys_to_update:
            updated_lines.append(f"{key_in_line}={new_settings[key_in_line]}")
            keys_to_update.remove(key_in_line)
        else:
            updated_lines.append(line)

    # Add any keys that were not found in the file
    for key in keys_to_update:
        updated_lines.append(f"{key}={new_settings[key]}")

    ENV_FILE.write_text("\n".join(updated_lines) + "\n")

    print(
        f"{Colors.GREEN}✓{Colors.NC} Updated {ENV_FILE} for {Colors.YELLOW}{target_mode.upper()}{Colors.NC} mode."
    )
    for key, value in new_settings.items():
        print(f"  - {key} set to: {Colors.BLUE}{value}{Colors.NC}")
    return True


def restart_service():
    """Restarts the lightrag_memory_server using docker-compose."""
    print(f"\n{Colors.BLUE}Restarting the LightRAG Memory service...{Colors.NC}")

    if not LIGHTRAG_MEMORY_DIR.exists():
        print(f"{Colors.RED}✗ Directory not found: {LIGHTRAG_MEMORY_DIR}{Colors.NC}")
        return False

    try:
        # Run docker-compose down
        print(f"{Colors.YELLOW}Stopping services...{Colors.NC}")
        subprocess.run(
            ["docker-compose", "down"],
            cwd=LIGHTRAG_MEMORY_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"{Colors.GREEN}✓{Colors.NC} Services stopped successfully.")

        # Run docker-compose up
        print(f"{Colors.YELLOW}Starting services...{Colors.NC}")
        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=LIGHTRAG_MEMORY_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        print(
            f"{Colors.GREEN}✓{Colors.NC} Services started successfully in detached mode."
        )

        # Show status
        print(f"\n{Colors.YELLOW}Waiting for services to initialize...{Colors.NC}")
        subprocess.run(["sleep", "5"])
        show_status()

        return True

    except subprocess.CalledProcessError as e:
        print(
            f"{Colors.RED}✗ An error occurred while managing Docker services.{Colors.NC}"
        )
        print(f"  - Command: {' '.join(e.cmd)}")
        print(f"  - Return Code: {e.returncode}")
        print(f"  - STDOUT: {e.stdout.strip()}")
        print(f"  - STDERR: {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print(
            f"{Colors.RED}✗ 'docker-compose' command not found. Is Docker installed and in your PATH?{Colors.NC}"
        )
        return False


def show_status():
    """Displays the current configuration and Docker service status."""
    print(f"{Colors.BLUE}--- LightRAG Memory Server Status ---{Colors.NC}")

    # Check .env file status
    current_config = get_current_config()
    if current_config:
        print(f"Ollama Configuration ({ENV_FILE}):")

        # Determine mode by comparing current config with predefined configs
        mode = "CUSTOM / UNKNOWN"
        mode_color = Colors.RED
        if all(current_config.get(k) == v for k, v in CONFIG["local"].items()):
            mode = "LOCAL"
            mode_color = Colors.YELLOW
        elif all(current_config.get(k) == v for k, v in CONFIG["remote"].items()):
            mode = "REMOTE"
            mode_color = Colors.YELLOW

        print(f"  - Mode: {mode_color}{mode}{Colors.NC}")

        # Print all relevant keys from the config
        for key in CONFIG["local"].keys():
            value = current_config.get(key, "Not Set")
            print(f"  - {key}: {Colors.GREEN}{value}{Colors.NC}")

    else:
        print(
            f"{Colors.RED}✗ Could not determine current configuration from {ENV_FILE}{Colors.NC}"
        )

    # Check Docker status
    print("\nDocker Service Status:")
    try:
        subprocess.run(["docker-compose", "ps"], cwd=LIGHTRAG_MEMORY_DIR, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"{Colors.RED}✗ Could not get Docker status. {e}{Colors.NC}")
    print(f"{Colors.BLUE}------------------------------------{Colors.NC}")


def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(
        description="Manage the Ollama configuration for the LightRAG Memory Server.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "command",
        choices=["local", "remote", "status"],
        help=(
            "local   - Switch to local Ollama server (host.docker.internal)\n"
            "remote  - Switch to remote Ollama server (100.100.248.61)\n"
            "status  - Show the current configuration and service status"
        ),
    )

    args = parser.parse_args()

    if args.command == "status":
        show_status()
    elif args.command in ["local", "remote"]:
        print(f"{Colors.BLUE}Switching to {args.command.upper()} mode...{Colors.NC}")
        current_config = get_current_config()
        target_config = CONFIG[args.command]

        # Check if all target settings are already applied
        if all(current_config.get(k) == v for k, v in target_config.items()):
            print(
                f"{Colors.YELLOW}Already in {args.command.upper()} mode. Verifying and restarting services.{Colors.NC}"
            )

        if update_env_file(args.command):
            restart_service()
        else:
            print(f"{Colors.RED}✗ Failed to update configuration. Aborting.{Colors.NC}")
            sys.exit(1)


if __name__ == "__main__":
    main()
