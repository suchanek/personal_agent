"""Environment variables and application settings."""

import logging
import os
import sys
from pathlib import Path

import dotenv
from dotenv import load_dotenv

from .user_id_mgr import load_user_from_file

# Define the project's base directory.
# This file is at src/personal_agent/config/settings.py, so we go up 4 levels for the root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
# Default: ~/.persag, overridable via environment variable PERSAG_HOME
PERSAG_HOME = os.getenv("PERSAG_HOME", str(Path.home() / ".persag"))
PERSAG_ROOT = os.getenv("PERSAG_ROOT", str(Path("/Users/Shared/personal_agent_data")))

PROVIDER="ollama"
LMSTUDIO_URL="https://api.openai.com/v1"
REMOTE_LMSTUDIO_URL="https:api.openai.com/v1"

OLLAMA_URL=http://localhost:11434

# Set up paths for environment files
dotenv_path = BASE_DIR / ".env"

# Load environment variables from .env file
dotenv_loaded = load_dotenv(dotenv_path=dotenv_path)

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize ~/.persag (PERSAG_HOME) and load user ID
load_user_from_file()


# Store loaded environment variables if dotenv succeeded
_env_vars = {}
if dotenv_loaded:
    # Load all variables from .env file into a cache
    _env_vars = dotenv.dotenv_values(dotenv_path=dotenv_path)
else:
    print("Unable to load .env!")


def get_env_var(key: str, fallback: str = "") -> str:
    """Retrieve environment variable with intelligent fallback strategy.

    Prioritizes dotenv cache over os.environ to ensure consistent behavior.
    Uses a two-tier lookup: first checks the cached .env values, then falls
    back to system environment variables if not found or if dotenv loading failed.

    Args:
        key: Environment variable name to retrieve
        fallback: Default value if variable not found (default: empty string)

    Returns:
        str: Environment variable value or fallback if not found
    """
    if dotenv_loaded and key in _env_vars:
        return _env_vars[key] or fallback
    else:
        # If dotenv failed or key not in .env, try os.getenv as fallback
        return os.getenv(key, fallback)


# Per-user configuration base directory for docker configs and user state
LIGHTRAG_SERVER_DIR = os.path.join(PERSAG_HOME, "lightrag_server")
LIGHTRAG_MEMORY_DIR = os.path.join(PERSAG_HOME, "lightrag_memory_server")


def get_env_bool(key: str, fallback: bool = True) -> bool:
    """Parse environment variable as boolean with flexible string interpretation.

    Converts string environment variables to boolean values using common
    boolean representations. Accepts multiple formats for true values:
    'true', '1', 'yes', 'on' (case-insensitive).

    Args:
        key: Environment variable name to retrieve and parse
        fallback: Default boolean value if variable not found (default: True)

    Returns:
        bool: Parsed boolean value or fallback if variable not found
    """
    value = get_env_var(key, str(fallback))
    return value.lower() in ("true", "1", "yes", "on")


PROVIDER = "ollama"
PROVIDER = get_env_var("PROVIDER", "ollama")  # DEPRECATED

# LighRAG server
LIGHTRAG_SERVER = get_env_var("LIGHTRAG_SERVER", "http://localhost:9621")  # DEPRECATED
LIGHTRAG_URL = get_env_var("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_MEMORY_URL = get_env_var("LIGHTRAG_MEMORY_URL", "http://localhost:9622")

# LMSTUDIO_URL = get_env_var("LMSTUDIO_URL", "http://localhost:1234/v1")
LMSTUDIO_URL = "https://api.openai.com/v1"
REMOTE_LMSTUDIO_URL = get_env_var(
    "REMOTE_LMSTUDIO_URL", "http://tesla.tail19187e.ts.net:1234/v1"
)

# Docker port configurations
PORT = get_env_var("PORT", "9621")  # Default port for lightrag_server (internal)
LIGHTRAG_PORT = get_env_var(
    "LIGHTRAG_PORT", "9621"
)  # Explicit port for lightrag_server (host port)
LIGHTRAG_MEMORY_PORT = get_env_var(
    "LIGHTRAG_MEMORY_PORT", "9622"
)  # Explicit port for lightrag_memory_server

# Configuration constants - All configurable via environment variables
WEAVIATE_URL = get_env_var("WEAVIATE_URL", "http://localhost:8080")
OLLAMA_URL = get_env_var("OLLAMA_URL", "http://localhost:11434")
REMOTE_OLLAMA_URL = get_env_var(
    "REMOTE_OLLAMA_URL", "http://tesla.tail19187e.ts.net:11434"
)

USE_WEAVIATE = get_env_bool("USE_WEAVIATE", False)
USE_MCP = get_env_bool("USE_MCP", True)

# Directory configurations
ROOT_DIR = get_env_var("ROOT_DIR", "/")  # Root directory for MCP filesystem server
PERSAG_ROOT = get_env_var(
    "PERSAG_ROOT", "/Users/Shared/personal_agent_data"
)  # Root directory for MCP filesystem server
HOME_DIR = get_env_var("HOME_DIR", os.path.expanduser("~"))  # User's home directory
REPO_DIR = get_env_var("REPO_DIR", "./repos")  # Repository directory

# Storage backend configuration
STORAGE_BACKEND = get_env_var("STORAGE_BACKEND", "agno")  # "weaviate" or "agno"


# Import user-specific functions
from .user_id_mgr import get_user_storage_paths, get_userid

# Get initial storage paths (these will be dynamic)
_storage_paths = get_user_storage_paths()
AGNO_STORAGE_DIR = _storage_paths["AGNO_STORAGE_DIR"]
AGNO_KNOWLEDGE_DIR = _storage_paths["AGNO_KNOWLEDGE_DIR"]
LIGHTRAG_STORAGE_DIR = _storage_paths["LIGHTRAG_STORAGE_DIR"]
LIGHTRAG_INPUTS_DIR = _storage_paths["LIGHTRAG_INPUTS_DIR"]
LIGHTRAG_MEMORY_STORAGE_DIR = _storage_paths["LIGHTRAG_MEMORY_STORAGE_DIR"]
LIGHTRAG_MEMORY_INPUTS_DIR = _storage_paths["LIGHTRAG_MEMORY_INPUTS_DIR"]
DATA_DIR = _storage_paths["DATA_DIR"]
USER_DATA_DIR = _storage_paths["USER_DATA_DIR"]

# Logging configuration
LOG_LEVEL_STR = get_env_var("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# Update logger level to use the configured level
logger.setLevel(LOG_LEVEL)

# LLM Model configuration
LLM_MODEL = get_env_var("LLM_MODEL", "qwen3:8b")

# Docker environment variables for LightRAG containers
# HTTP timeout configurations
HTTPX_TIMEOUT = get_env_var("HTTPX_TIMEOUT", "7200")
HTTPX_CONNECT_TIMEOUT = get_env_var("HTTPX_CONNECT_TIMEOUT", "600")
HTTPX_READ_TIMEOUT = get_env_var("HTTPX_READ_TIMEOUT", "7200")
HTTPX_WRITE_TIMEOUT = get_env_var("HTTPX_WRITE_TIMEOUT", "600")
HTTPX_POOL_TIMEOUT = get_env_var("HTTPX_POOL_TIMEOUT", "600")

# Ollama timeout and configuration
OLLAMA_TIMEOUT = get_env_var("OLLAMA_TIMEOUT", "7200")
OLLAMA_KEEP_ALIVE = get_env_var("OLLAMA_KEEP_ALIVE", "3600")
OLLAMA_NUM_PREDICT = get_env_var("OLLAMA_NUM_PREDICT", "16384")
OLLAMA_TEMPERATURE = get_env_var("OLLAMA_TEMPERATURE", "0.1")

# Processing configurations
PDF_CHUNK_SIZE = get_env_var("PDF_CHUNK_SIZE", "1024")
LLM_TIMEOUT = get_env_var("LLM_TIMEOUT", "7200")
EMBEDDING_TIMEOUT = get_env_var("EMBEDDING_TIMEOUT", "3600")

# Display configuration
SHOW_SPLASH_SCREEN = get_env_bool("SHOW_SPLASH_SCREEN", False)


# Import remaining user-specific functions
from .user_id_mgr import get_current_user_id, refresh_user_dependent_settings


def get_package_version():
    """Retrieve package version with import path handling.

    Attempts to import the version from the package's __init__.py file,
    handling both standalone script execution and module import scenarios.
    Uses different import strategies based on execution context.

    Returns:
        str: Package version string or 'unknown' if import fails
    """
    try:
        if __name__ == "__main__":
            # When run as standalone, try absolute import
            sys.path.insert(0, str(BASE_DIR))
            from personal_agent import __version__
        else:
            # When imported as module, use relative import
            from ... import __version__
        return __version__
    except ImportError:
        return "unknown"


if __name__ == "__main__":
    from personal_agent.tools.show_config import show_config

    show_config()

    # end of file
