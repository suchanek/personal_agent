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


# Configuration constants
WEAVIATE_URL = "http://localhost:8080"
OLLAMA_URL = "http://localhost:11434"
USE_WEAVIATE = True  # Set to False to bypass Weaviate for testing
USE_MCP = True  # Set to False to bypass MCP for testing

ROOT_DIR = get_env_var("ROOT_DIR", ".")  # Root directory for MCP filesystem server
DATA_DIR = get_env_var("DATA_DIR", "./data")  # Data directory for vector database

LOG_LEVEL = logging.INFO

# LLM_MODEL = "qwen2.5:7b-instruct"  # Ollama model to use for LLM
LLM_MODEL = "qwen3:1.7B"
