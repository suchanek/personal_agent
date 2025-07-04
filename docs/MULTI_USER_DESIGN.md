# Multi-User Support Design

This document outlines the design for implementing multi-user support in the Personal Agent application. The goal is to allow multiple users to use the system with their own isolated data and configurations.

## 1. Strategy

The core of the multi-user design is to make all user-specific data paths dependent on a `user_id`. This `user_id` will be used to create a unique directory for each user, containing their data, knowledge base, and other settings.

The `user_id` will be determined in the following order of precedence:

1.  `--user-id` command-line argument.
2.  `USER_ID` environment variable.
3.  A default value of `default_user` if neither is provided.

## 2. Implementation Steps

### Step 1: Modify `src/personal_agent/config/settings.py`

The `settings.py` file will be updated to incorporate the `user_id` into the path definitions.

```python
# src/personal_agent/config/settings.py

import logging
import os
from pathlib import Path
import argparse

import dotenv
from dotenv import load_dotenv

# Define the project's base directory.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
dotenv_path = BASE_DIR / ".env"

# Load environment variables from .env file
dotenv_loaded = load_dotenv(dotenv_path=dotenv_path)

# --- User ID Configuration ---
def get_user_id():
    """
    Get user ID from command-line arguments first, then environment variables.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--user-id", type=str, help="User ID for the agent")
    args, _ = parser.parse_known_args()

    if args.user_id:
        return args.user_id
    return os.getenv("USER_ID", "eric")

USER_ID = get_user_id()

# Store loaded environment variables if dotenv succeeded
_env_vars = {}
if dotenv_loaded:
    _env_vars = dotenv.dotenv_values(dotenv_path=dotenv_path)

def get_env_var(key: str, fallback: str = "") -> str:
    """Get environment variable from dotenv cache first, then os.environ as fallback."""
    if dotenv_loaded and key in _env_vars:
        return _env_vars[key] or fallback
    else:
        return os.getenv(key, fallback)

# ... (rest of the get_env_var and get_env_bool functions)

# Directory configurations
DATA_DIR = get_env_var("DATA_DIR", f"./data/{USER_ID}")
REPO_DIR = get_env_var("REPO_DIR", f"./repos/{USER_ID}")

# Storage backend configuration
STORAGE_BACKEND = get_env_var("STORAGE_BACKEND", "agno")

# Agno Storage Configuration
AGNO_STORAGE_DIR = os.path.expandvars(
    get_env_var("AGNO_STORAGE_DIR", f"{DATA_DIR}/storage/{STORAGE_BACKEND}")
)
AGNO_KNOWLEDGE_DIR = os.path.expandvars(
    get_env_var("AGNO_KNOWLEDGE_DIR", f"{DATA_DIR}/knowledge")
)

# Create user-specific directories if they don't exist
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(REPO_DIR).mkdir(parents=True, exist_ok=True)
Path(AGNO_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(AGNO_KNOWLEDGE_DIR).mkdir(parents=True, exist_ok=True)

# ... (rest of the settings.py file)
```

### Step 2: Modify `src/personal_agent/agno_main.py`

The `agno_main.py` file will be updated to properly handle the `--user-id` argument.

```python
# src/personal_agent/agno_main.py

import argparse
# ... (other imports)

from .config.settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    USER_ID,  # USER_ID is now correctly set
)

# ... (rest of the file)

def cli_main():
    """
    Main entry point for CLI mode (used by poetry scripts).
    """
    from .utils import configure_all_rich_logging, setup_logging

    configure_all_rich_logging()
    logger = setup_logging()

    parser = argparse.ArgumentParser(
        description="Run the Personal AI Agent with Agno Framework"
    )
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama server"
    )
    parser.add_argument(
        "--recreate", action="store_true", help="Recreate the knowledge base"
    )
    # The --user-id argument is now parsed in settings.py, but we keep it here for help text
    parser.add_argument("--user-id", type=str, help="User ID for the agent (overrides USER_ID env var)")

    args = parser.parse_args()

    logger.info(f"Starting Personal AI Agent for user: {USER_ID}")

    # Run in CLI mode
    asyncio.run(run_agno_cli(use_remote_ollama=args.remote, recreate=args.recreate))


if __name__ == "__main__":
    cli_main()
```

## 3. Mermaid Diagram

Here is a diagram illustrating the new workflow:

```mermaid
graph TD
    A[Start Application] --> B{Get user_id};
    B -- --user-id arg --> C[Use arg value];
    B -- USER_ID env var --> D[Use env var value];
    B -- a default value --> E[Use 'eric'];
    C --> F[USER_ID is set];
    D --> F;
    E --> F;
    F --> G{Construct Paths};
    G -- ./data/{USER_ID} --> H[DATA_DIR];
    G -- ./repos/{USER_ID} --> I[REPO_DIR];
    G -- {DATA_DIR}/storage/agno --> J[AGNO_STORAGE_DIR];
    G -- {DATA_DIR}/knowledge --> K[AGNO_KNOWLEDGE_DIR];
    H & I & J & K --> L[Initialize Agent];
```

## 4. Conclusion

This design provides a robust and scalable way to handle multiple users. By isolating user data, we ensure privacy and prevent data corruption. The use of a command-line argument provides flexibility for launching the agent for different users.