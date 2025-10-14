"""Environment variables and application settings."""

import logging
import os
import sys
from pathlib import Path

import dotenv
from dotenv import load_dotenv

from .user_id_mgr import get_user_storage_paths, load_user_from_file

# Define the project's base directory.
# This file is at src/personal_agent/config/settings.py, so we go up 4 levels for the root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
# Default: ~/.persag, overridable via environment variable PERSAG_HOME
PERSAG_HOME = os.getenv("PERSAG_HOME", str(Path.home() / ".persag"))
PERSAG_ROOT = os.getenv("PERSAG_ROOT", str(Path("/Users/Shared/personal_agent_data")))

INSTRUCTION_LEVEL = "STANDARD"

# see below for the ollama server urls

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


# LighRAG server
LIGHTRAG_SERVER = get_env_var("LIGHTRAG_SERVER", "http://localhost:9621")  # DEPRECATED
LIGHTRAG_URL = get_env_var("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_MEMORY_URL = get_env_var("LIGHTRAG_MEMORY_URL", "http://localhost:9622")


# Docker port configurations
PORT = get_env_var("PORT", "9621")  # Default port for lightrag_server (internal)
LIGHTRAG_PORT = get_env_var(
    "LIGHTRAG_PORT", "9621"
)  # Explicit port for lightrag_server (host port)
LIGHTRAG_MEMORY_PORT = get_env_var(
    "LIGHTRAG_MEMORY_PORT", "9622"
)  # Explicit port for lightrag_memory_server

# Configuration constants - All configurable via environment variables
PROVIDER = get_env_var("PROVIDER", "ollama")
WEAVIATE_URL = get_env_var("WEAVIATE_URL", "http://localhost:8080")
USE_WEAVIATE = get_env_bool("USE_WEAVIATE", False)

INSTRUCTION_LEVEL = get_env_var("INSTRUCTION_LEVEL", "CONCISE")
OLLAMA_URL = get_env_var("OLLAMA_URL", "http://localhost:11434")
REMOTE_OLLAMA_URL = get_env_var("REMOTE_OLLAMA_URL", "http://100.100.248.61:11434")
REMOTE_LMSTUDIO_URL = get_env_var("REMOTE_LMSTUDIO_URL", "http://100.100.248.61:1234")

# LMStudio URL configuration - defaults to localhost LMStudio, can be overridden in .env
LMSTUDIO_URL = get_env_var("LMSTUDIO_URL", "http://localhost:1234/v1")
# LMStudio base URL for dedicated lm-studio provider - defaults to user's remote endpoint
LMSTUDIO_BASE_URL = get_env_var("LMSTUDIO_BASE_URL", "http://localhost:1234")
# FIX: Corrected OpenAI API URL - was using chat.openai.com instead of api.openai.com
OPENAI_URL = "https://api.openai.com/v1"

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

ALLOWED_DIRS = [HOME_DIR, DATA_DIR, "/tmp", ".", "/"]

# Logging configuration
LOG_LEVEL_STR = get_env_var("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# Update logger level to use the configured level
logger.setLevel(LOG_LEVEL)

# Provider-specific default models
PROVIDER_DEFAULT_MODELS = {
    "ollama": "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K",
    "lm-studio": "qwen3-4b-instruct-2507-mlx",
    "openai": "gpt-4.1-mini",
}

# LLM Model configuration
LLM_MODEL = get_env_var("LLM_MODEL", "qwen3:4b")

# Qwen Model Settings - Instruct Model Parameters
QWEN_INSTRUCT_TEMPERATURE = get_env_var("QWEN_INSTRUCT_TEMPERATURE", "0.6")
QWEN_INSTRUCT_MIN_P = get_env_var("QWEN_INSTRUCT_MIN_P", "0.00")
QWEN_INSTRUCT_TOP_P = get_env_var("QWEN_INSTRUCT_TOP_P", "0.90")
QWEN_INSTRUCT_TOP_K = get_env_var("QWEN_INSTRUCT_TOP_K", "20")

# Qwen Model Settings - Thinking Model Parameters
QWEN_THINKING_TEMPERATURE = get_env_var("QWEN_THINKING_TEMPERATURE", "0.6")
QWEN_THINKING_MIN_P = get_env_var("QWEN_THINKING_MIN_P", "0.00")
QWEN_THINKING_TOP_P = get_env_var("QWEN_THINKING_TOP_P", "0.95")


def get_qwen_instruct_settings() -> dict:
    """Get Qwen instruct model settings as a dictionary.

    Returns:
        dict: Dictionary containing instruct model parameters
    """
    return {
        "temperature": float(QWEN_INSTRUCT_TEMPERATURE),
        "min_p": float(QWEN_INSTRUCT_MIN_P),
        "top_p": float(QWEN_INSTRUCT_TOP_P),
        "top_k": int(QWEN_INSTRUCT_TOP_K),
    }


def get_qwen_thinking_settings() -> dict:
    """Get Qwen thinking model settings as a dictionary.

    Returns:
        dict: Dictionary containing thinking model parameters
    """
    return {
        "temperature": float(QWEN_THINKING_TEMPERATURE),
        "min_p": float(QWEN_THINKING_MIN_P),
        "top_p": float(QWEN_THINKING_TOP_P),
    }


def get_provider_default_model(provider: str) -> str:
    """Get the default model for a specific provider.

    Args:
        provider: The provider name ('ollama', 'lm-studio', 'openai')

    Returns:
        str: The default model name for the provider
    """
    return PROVIDER_DEFAULT_MODELS.get(provider, "qwen3:1.7b")


def get_effective_model_name(provider: str, specified_model: str = None) -> str:
    """Get the effective model name to use, with provider-specific defaults.

    If no model is specified or the specified model appears incompatible with the provider,
    returns the provider's default model. Otherwise returns the specified model.

    Args:
        provider: The provider name ('ollama', 'lm-studio', 'openai')
        specified_model: The model name specified by user (can be None)

    Returns:
        str: The effective model name to use
    """
    if not specified_model or specified_model.strip() == "":
        logger.info(
            f"No model specified for provider '{provider}', using default: {get_provider_default_model(provider)}"
        )
        return get_provider_default_model(provider)

    # Basic compatibility checks - if model seems incompatible with provider, use default
    specified_model_lower = specified_model.lower()

    if provider == "openai":
        # OpenAI models should not contain colons (Ollama-style) or end with -mlx (MLX-style)
        if ":" in specified_model or specified_model.endswith("-mlx"):
            logger.warning(
                f"Model '{specified_model}' appears incompatible with OpenAI provider, using default"
            )
            return get_provider_default_model(provider)
    elif provider == "lm-studio":
        # LM Studio models typically end with -mlx or are specific LM Studio models
        # Allow some flexibility but warn about obvious mismatches
        if specified_model.startswith("gpt-") and not any(
            term in specified_model_lower for term in ["mlx", "lm", "studio"]
        ):
            logger.warning(
                f"Model '{specified_model}' appears to be an OpenAI model used with LM Studio provider, using default"
            )
            return get_provider_default_model(provider)
    elif provider == "ollama":
        # Ollama models typically contain colons or are specific Ollama model names
        # Allow some flexibility but warn about obvious OpenAI models
        if specified_model.startswith("gpt-") and ":" not in specified_model:
            logger.warning(
                f"Model '{specified_model}' appears to be an OpenAI model used with Ollama provider, using default"
            )
            return get_provider_default_model(provider)

    return specified_model


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
OLLAMA_TEMPERATURE = get_env_var("OLLAMA_TEMPERATURE", "0.4")
OLLAMA_MAX_LOADED_MODELS = 2
OLLAMA_NUM_PARALLEL = 2

# Processing configurations
PDF_CHUNK_SIZE = get_env_var("PDF_CHUNK_SIZE", "1024")
LLM_TIMEOUT = get_env_var("LLM_TIMEOUT", "7200")
EMBEDDING_TIMEOUT = get_env_var("EMBEDDING_TIMEOUT", "3600")

# Display configuration
SHOW_SPLASH_SCREEN = get_env_bool("SHOW_SPLASH_SCREEN", False)


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
