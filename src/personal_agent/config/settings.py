"""Environment variables and application settings."""

import logging
import os
from pathlib import Path

import dotenv
from dotenv import load_dotenv

# Define the project's base directory.
# This file is at src/personal_agent/config/settings.py, so we go up 4 levels for the root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
dotenv_path = BASE_DIR / ".env"


# Load environment variables from .env file
dotenv_loaded = load_dotenv(dotenv_path=dotenv_path)

# Store loaded environment variables if dotenv succeeded
_env_vars = {}
if dotenv_loaded:
    # Load all variables from .env file into a cache
    _env_vars = dotenv.dotenv_values(dotenv_path=dotenv_path)


def get_env_var(key: str, fallback: str = "") -> str:
    """Get environment variable from dotenv cache first, then os.environ as fallback."""
    if dotenv_loaded and key in _env_vars:
        return _env_vars[key] or fallback
    else:
        # If dotenv failed or key not in .env, try os.getenv as fallback
        return os.getenv(key, fallback)


def get_env_bool(key: str, fallback: bool = True) -> bool:
    """Get boolean environment variable with proper parsing."""
    value = get_env_var(key, str(fallback))
    return value.lower() in ("true", "1", "yes", "on")


# Configuration constants - All configurable via environment variables
WEAVIATE_URL = get_env_var("WEAVIATE_URL", "http://localhost:8080")
OLLAMA_URL = get_env_var("OLLAMA_URL", "http://localhost:11434")
REMOTE_OLLAMA_URL = get_env_var("REMOTE_OLLAMA_URL", "http://tesla.local:11434")

USE_WEAVIATE = get_env_bool("USE_WEAVIATE", False)
USE_MCP = get_env_bool("USE_MCP", True)

# Directory configurations
ROOT_DIR = get_env_var("ROOT_DIR", "/")  # Root directory for MCP filesystem server
HOME_DIR = get_env_var("HOME_DIR", os.path.expanduser("~"))  # User's home directory
DATA_DIR = get_env_var("DATA_DIR", "./data")  # Data directory for vector database
REPO_DIR = get_env_var("REPO_DIR", "./repos")  # Repository directory

# Storage backend configuration
STORAGE_BACKEND = get_env_var("STORAGE_BACKEND", "agno")  # "weaviate" or "agno"

# Agno Storage Configuration (expand DATA_DIR variable)
AGNO_STORAGE_DIR = os.path.expandvars(
    get_env_var("AGNO_STORAGE_DIR", f"{DATA_DIR}/{STORAGE_BACKEND}")
)
AGNO_KNOWLEDGE_DIR = os.path.expandvars(
    get_env_var("AGNO_KNOWLEDGE_DIR", f"{DATA_DIR}/knowledge")
)

# Logging configuration
LOG_LEVEL_STR = get_env_var("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# LLM Model configuration
LLM_MODEL = get_env_var("LLM_MODEL", "qwen3:1.7B")

# User configuration
USER_ID = get_env_var("USER_ID", "default_user")  # Default user ID for agent

if __name__ == "__main__":
    print("Loaded environment variables from .env:")
    for key, value in _env_vars.items():
        print(f"{key}={value}")

    print("\n--- Configuration Constants ---")
    print(f"WEAVIATE_URL: {WEAVIATE_URL}")
    print(f"OLLAMA_URL: {OLLAMA_URL}")
    print(f"REMOTE_OLLAMA_URL: {REMOTE_OLLAMA_URL}")
    print(f"USE_WEAVIATE: {USE_WEAVIATE}")
    print(f"USE_MCP: {USE_MCP}")
    print(f"ROOT_DIR: {ROOT_DIR}")
    print(f"HOME_DIR: {HOME_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"REPO_DIR: {REPO_DIR}")
    print(f"STORAGE_BACKEND: {STORAGE_BACKEND}")
    print(f"AGNO_STORAGE_DIR: {AGNO_STORAGE_DIR}")
    print(f"AGNO_KNOWLEDGE_DIR: {AGNO_KNOWLEDGE_DIR}")
    print(f"LOG_LEVEL: {LOG_LEVEL_STR}")
    print(f"LLM_MODEL: {LLM_MODEL}")
    print(f"USER_ID: {USER_ID}")
