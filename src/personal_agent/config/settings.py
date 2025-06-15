"""Environment variables and application settings."""

import logging
import os

import dotenv
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_loaded = load_dotenv()

# Store loaded environment variables if dotenv succeeded
_env_vars = {}
if dotenv_loaded:
    # Load all variables from .env file into a cache
    _env_vars = dotenv.dotenv_values()


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

# API Keys configuration
GITHUB_PERSONAL_ACCESS_TOKEN = get_env_var("GITHUB_PERSONAL_ACCESS_TOKEN", "")
BRAVE_API_KEY = get_env_var("BRAVE_API_KEY", "")
MODELS_LAB_API_KEY = get_env_var("MODELS_LAB_API_KEY", "")
ELEVEN_LABS_API_KEY = get_env_var("ELEVEN_LABS_API_KEY", "")
GIPHY_API_KEY = get_env_var("GIPHY_API_KEY", "")

# User configuration
USER_ID = get_env_var("USER_ID", "default_user")  # Default user ID for agent

# Rate Limiting Configuration
# DuckDuckGo Search Rate Limiting
DUCKDUCKGO_SEARCH_DELAY = float(get_env_var("DUCKDUCKGO_SEARCH_DELAY", "3.0"))
DUCKDUCKGO_MAX_RETRIES = int(get_env_var("DUCKDUCKGO_MAX_RETRIES", "3"))
DUCKDUCKGO_RETRY_DELAY = float(get_env_var("DUCKDUCKGO_RETRY_DELAY", "10.0"))

# Default API Rate Limiting (for other tools)
DEFAULT_API_DELAY = float(get_env_var("DEFAULT_API_DELAY", "1.0"))
DEFAULT_MAX_RETRIES = int(get_env_var("DEFAULT_MAX_RETRIES", "3"))
DEFAULT_RETRY_DELAY = float(get_env_var("DEFAULT_RETRY_DELAY", "5.0"))
