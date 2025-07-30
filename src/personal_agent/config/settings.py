"""Environment variables and application settings."""

import logging
import os
import sys
from pathlib import Path

import dotenv
from dotenv import load_dotenv

# Define the project's base directory.
# This file is at src/personal_agent/config/settings.py, so we go up 4 levels for the root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


# Handle imports differently when run as a script vs imported as a module
def _get_logger():
    """Get logger with fallback for circular import issues."""
    try:
        if __name__ == "__main__":
            # When run directly, use absolute imports
            sys.path.insert(0, str(BASE_DIR))
            from personal_agent.utils.pag_logging import setup_logging
        else:
            # When imported as a module, use relative imports
            from ..utils.pag_logging import setup_logging
        return setup_logging()
    except ImportError:
        # Fallback to basic logging if circular import occurs
        import logging

        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)


# Set up paths for environment files
dotenv_path = BASE_DIR / ".env"
userid_path = BASE_DIR / "env.userid"

# Load environment variables from .env file
dotenv_loaded = load_dotenv(dotenv_path=dotenv_path)


logger = _get_logger()


def load_user_from_file():
    """Load the USER_ID from env.userid and set it in the environment."""
    if userid_path.exists():
        with open(userid_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith("USER_ID="):
                user_id = content.split("=", 1)[1].strip().strip("'\"")
                os.environ["USER_ID"] = user_id
                return user_id
    else:
        logger.warning(
            f"Warning: {userid_path} does not exist. Creating new env.user_id file with default USER_ID."
        )
        with open(userid_path, "w") as f:
            f.write('USER_ID="default_user"\n')
        os.environ["USER_ID"] = "default_user"
        return "default_user"


# Load the user ID from the file first to ensure it's set. This is the first point of truth for
# USER_ID!.
load_user_from_file()


# Store loaded environment variables if dotenv succeeded
_env_vars = {}
if dotenv_loaded:
    # Load all variables from .env file into a cache
    _env_vars = dotenv.dotenv_values(dotenv_path=dotenv_path)
else:
    print("Unable to load .env!")


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


# LighRAG server
LIGHTRAG_SERVER = get_env_var("LIGHTRAG_SERVER", "http://localhost:9621")  # DEPRECATED
LIGHTRAG_URL = get_env_var("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_MEMORY_URL = get_env_var("LIGHTRAG_MEMORY_URL", "http://localhost:9622")

LMSTUDIO_URL = get_env_var("LMSTUDIO_URL", "http://localhost:1234/v1")
REMOTE_LMSTUDIO_URL = get_env_var("REMOTE_LMSTUDIO_URL", "http://tesla.local:1234/v1")

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

# User configuration
USER_ID = get_env_var("USER_ID", "default_user")  # Default user ID for agent


# Agno Storage Configuration (expand DATA_DIR variable)
AGNO_STORAGE_DIR = os.path.expandvars(
    get_env_var("AGNO_STORAGE_DIR", f"{DATA_DIR}/{STORAGE_BACKEND}/{USER_ID}")
)
AGNO_KNOWLEDGE_DIR = os.path.expandvars(
    get_env_var(
        "AGNO_KNOWLEDGE_DIR", f"{DATA_DIR}/{STORAGE_BACKEND}/{USER_ID}/knowledge"
    )
)

# LightRAG storage directories
LIGHTRAG_STORAGE_DIR = os.path.expandvars(
    get_env_var(
        "LIGHTRAG_STORAGE_DIR", f"{DATA_DIR}/{STORAGE_BACKEND}/{USER_ID}/rag_storage"
    )
)
LIGHTRAG_INPUTS_DIR = os.path.expandvars(
    get_env_var("LIGHTRAG_INPUTS_DIR", f"{DATA_DIR}/{STORAGE_BACKEND}/{USER_ID}/inputs")
)
LIGHTRAG_MEMORY_STORAGE_DIR = os.path.expandvars(
    get_env_var(
        "LIGHTRAG_MEMORY_STORAGE_DIR",
        f"{DATA_DIR}/{STORAGE_BACKEND}/{USER_ID}/memory_rag_storage",
    )
)
LIGHTRAG_MEMORY_INPUTS_DIR = os.path.expandvars(
    get_env_var(
        "LIGHTRAG_MEMORY_INPUTS_DIR",
        f"{DATA_DIR}/{STORAGE_BACKEND}/{USER_ID}/memory_inputs",
    )
)


# Logging configuration
LOG_LEVEL_STR = get_env_var("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# LLM Model configuration
LLM_MODEL = get_env_var("LLM_MODEL", "qwen3-4b-mlx")

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


def get_current_user_id():
    """Get the current USER_ID dynamically from environment.

    This function always reads from os.environ to ensure we get the latest value
    after user switching, rather than the cached value from module import time.

    Returns:
        Current USER_ID from environment or default fallback
    """
    return load_user_from_file()


def refresh_user_dependent_settings(user_id: str = None):
    """Refresh all USER_ID-dependent settings after user switching.

    This function recalculates all storage paths and settings that depend on USER_ID
    to ensure they reflect the current user after switching.

    Args:
        user_id: Optional user_id to refresh settings for. If not provided,
                 the current user_id from the environment will be used.

    Returns:
        Dictionary with updated settings
    """
    current_user_id = user_id or get_current_user_id()

    # Recalculate storage directories with current USER_ID
    agno_storage_dir = f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}"
    agno_knowledge_dir = f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/knowledge"
    lightrag_storage_dir = f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/rag_storage"
    lightrag_inputs_dir = f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/inputs"
    lightrag_memory_storage_dir = (
        f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/memory_rag_storage"
    )
    lightrag_memory_inputs_dir = "LIGHTRAG_MEMORY_INPUTS_DIR"

    return {
        "USER_ID": current_user_id,
        "AGNO_STORAGE_DIR": agno_storage_dir,
        "AGNO_KNOWLEDGE_DIR": agno_knowledge_dir,
        "LIGHTRAG_STORAGE_DIR": lightrag_storage_dir,
        "LIGHTRAG_INPUTS_DIR": lightrag_inputs_dir,
        "LIGHTRAG_MEMORY_STORAGE_DIR": lightrag_memory_storage_dir,
        "LIGHTRAG_MEMORY_INPUTS_DIR": lightrag_memory_inputs_dir,
    }


def get_package_version():
    """Get package version from the package __init__.py."""
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


def print_config():
    """Pretty print configuration and environment variables."""
    # ANSI color codes
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # Get version for header
    version = get_package_version()

    # Header
    print(f"{BOLD}{HEADER}{'='*60}{ENDC}")
    print(f"{BOLD}{HEADER}  Personal Agent Configuration Status{ENDC}")
    print(f"{BOLD}{HEADER}  Version: {version}{ENDC}")
    print(f"{BOLD}{HEADER}{'='*60}{ENDC}")

    # Environment file status
    print(f"\n{BOLD}{BLUE}📁 Environment File Status:{ENDC}")
    if dotenv_loaded:
        print(f"  {GREEN}✓ Successfully loaded .env from: {dotenv_path}{ENDC}")
    else:
        print(f"  {RED}✗ Failed to load .env file{ENDC}")

    # Environment variables section
    if _env_vars:
        print(f"\n{BOLD}{CYAN}🔧 Environment Variables:{ENDC}")
        print(f"  {UNDERLINE}Variable{' '*20}Value{ENDC}")
        for key, value in sorted(_env_vars.items()):
            # Mask sensitive values
            display_value = value
            if any(
                sensitive in key.lower()
                for sensitive in ["password", "secret", "key", "token"]
            ):
                display_value = "*" * len(value) if value else ""
            print(f"  {YELLOW}{key:<28}{ENDC} {display_value}")

    # Configuration sections
    sections = [
        {
            "title": "🌐 Server Configuration",
            "items": [
                ("LightRAG URL", LIGHTRAG_URL),
                ("LightRAG Memory URL", LIGHTRAG_MEMORY_URL),
                ("LightRAG Port", LIGHTRAG_PORT),
                ("LightRAG Memory Port", LIGHTRAG_MEMORY_PORT),
                ("Weaviate URL", WEAVIATE_URL),
                ("Ollama URL", OLLAMA_URL),
                ("Remote Ollama URL", REMOTE_OLLAMA_URL),
                ("LMSTUDIO URL", LMSTUDIO_URL),
            ],
        },
        {
            "title": "⚙️  Feature Flags",
            "items": [
                (
                    "Use Weaviate",
                    f"{GREEN}✓{ENDC}" if USE_WEAVIATE else f"{RED}✗{ENDC}",
                ),
                ("Use MCP", f"{GREEN}✓{ENDC}" if USE_MCP else f"{RED}✗{ENDC}"),
                (
                    "Show Splash Screen",
                    f"{GREEN}✓{ENDC}" if SHOW_SPLASH_SCREEN else f"{RED}✗{ENDC}",
                ),
            ],
        },
        {
            "title": "📂 Directory Configuration",
            "items": [
                ("Root Directory", ROOT_DIR),
                ("Home Directory", HOME_DIR),
                ("Data Directory", DATA_DIR),
                ("Repository Directory", REPO_DIR),
                ("Agno Storage Directory", AGNO_STORAGE_DIR),
                ("Agno Knowledge Directory", AGNO_KNOWLEDGE_DIR),
            ],
        },
        {
            "title": "🤖 AI & Storage Configuration",
            "items": [
                ("Storage Backend", STORAGE_BACKEND),
                ("LLM Model", LLM_MODEL),
                ("User ID", USER_ID),
                ("Log Level", LOG_LEVEL_STR),
            ],
        },
        {
            "title": "🐳 Docker Configuration",
            "items": [
                ("HTTPX Timeout", f"{HTTPX_TIMEOUT}s"),
                ("HTTPX Connect Timeout", f"{HTTPX_CONNECT_TIMEOUT}s"),
                ("HTTPX Read Timeout", f"{HTTPX_READ_TIMEOUT}s"),
                ("HTTPX Write Timeout", f"{HTTPX_WRITE_TIMEOUT}s"),
                ("HTTPX Pool Timeout", f"{HTTPX_POOL_TIMEOUT}s"),
                ("Ollama Timeout", f"{OLLAMA_TIMEOUT}s"),
                ("Ollama Keep Alive", f"{OLLAMA_KEEP_ALIVE}s"),
                ("Ollama Num Predict", OLLAMA_NUM_PREDICT),
                ("Ollama Temperature", OLLAMA_TEMPERATURE),
                ("PDF Chunk Size", PDF_CHUNK_SIZE),
                ("LLM Timeout", f"{LLM_TIMEOUT}s"),
                ("Embedding Timeout", f"{EMBEDDING_TIMEOUT}s"),
            ],
        },
    ]

    for section in sections:
        print(f"\n{BOLD}{BLUE}{section['title']}:{ENDC}")
        print(f"  {UNDERLINE}Setting{' '*22}Value{ENDC}")
        for name, value in section["items"]:
            print(f"  {CYAN}{name:<30}{ENDC} {value}")

    # Footer
    print(f"\n{BOLD}{HEADER}{'='*60}{ENDC}")
    print(f"{BOLD}{GREEN}Configuration loaded successfully!{ENDC}")
    print(f"{BOLD}{HEADER}{'='*60}{ENDC}")


if __name__ == "__main__":
    print_config()

    # end of file
