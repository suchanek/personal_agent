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
# Default: ~/.persag, overridable via environment variable PERSAG_HOME
PERSAG_HOME = os.getenv("PERSAG_HOME", str(Path.home() / ".persag"))


# Handle imports differently when run as a script vs imported as a module
def _get_logger():
    """Initialize logging system with import path handling and circular import protection.
    
    Attempts to import the custom logging setup from the utils module, handling both
    direct script execution and module import scenarios. Falls back to basic logging
    if circular imports occur.
    
    Returns:
        logging.Logger: Configured logger instance
    """
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

# Load environment variables from .env file
dotenv_loaded = load_dotenv(dotenv_path=dotenv_path)

logger = _get_logger()


# Import user management functions from the dedicated module
from .user_id_mgr import load_user_from_file

# Initialize ~/.persag and load user ID
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
PERSAG_ROOT = get_env_var(
    "PERSAG_ROOT", "/Users/Shared/personal_agent_data"
)  # Root directory for MCP filesystem server
HOME_DIR = get_env_var("HOME_DIR", os.path.expanduser("~"))  # User's home directory
DATA_DIR = get_env_var("DATA_DIR", "./data")  # Data directory for vector database
REPO_DIR = get_env_var("REPO_DIR", "./repos")  # Repository directory

# Storage backend configuration
STORAGE_BACKEND = get_env_var("STORAGE_BACKEND", "agno")  # "weaviate" or "agno"


# Import user-specific functions from the dedicated module
from .user_id_mgr import get_userid, get_user_storage_paths


# Get initial storage paths (these will be dynamic)
_storage_paths = get_user_storage_paths()
AGNO_STORAGE_DIR = _storage_paths["AGNO_STORAGE_DIR"]
AGNO_KNOWLEDGE_DIR = _storage_paths["AGNO_KNOWLEDGE_DIR"]
LIGHTRAG_STORAGE_DIR = _storage_paths["LIGHTRAG_STORAGE_DIR"]
LIGHTRAG_INPUTS_DIR = _storage_paths["LIGHTRAG_INPUTS_DIR"]
LIGHTRAG_MEMORY_STORAGE_DIR = _storage_paths["LIGHTRAG_MEMORY_STORAGE_DIR"]
LIGHTRAG_MEMORY_INPUTS_DIR = _storage_paths["LIGHTRAG_MEMORY_INPUTS_DIR"]
DATA_DIR = _storage_paths["DATA_DIR"]

# Logging configuration
LOG_LEVEL_STR = get_env_var("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

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


# Import remaining user-specific functions from the dedicated module
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


def print_config():
    """Display comprehensive configuration status with ANSI color formatting.
    
    Renders a detailed, visually formatted configuration report including:
    - Environment file loading status
    - All loaded environment variables (with sensitive value masking)
    - Organized configuration sections (servers, features, directories, etc.)
    - Current user settings and storage paths
    - Docker and timeout configurations
    
    Uses ANSI color codes for enhanced readability and visual organization.
    Automatically masks sensitive values containing 'password', 'secret', 'key', or 'token'.
    """
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
                ("Persag Env Home", PERSAG_HOME),
                ("Persag Data Directory", PERSAG_ROOT),
                ("User Data Directory", DATA_DIR),
                ("Repository Directory", REPO_DIR),
                ("LightRAG Server Dir", LIGHTRAG_SERVER_DIR),
                ("LightRAG Memory Dir", LIGHTRAG_MEMORY_DIR),
                ("Agno Storage Directory", AGNO_STORAGE_DIR),
                ("Agno Knowledge Directory", AGNO_KNOWLEDGE_DIR),
            ],
        },
        {
            "title": "🤖 AI & Storage Configuration",
            "items": [
                ("Storage Backend", STORAGE_BACKEND),
                ("LLM Model", LLM_MODEL),
                ("User ID", get_userid()),
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


def print_configuration() -> str:
    """Display comprehensive configuration with multiple fallback strategies.
    
    Attempts to use the enhanced configuration display from the tools module,
    with graceful fallbacks to simpler display methods if imports fail.
    Provides a robust configuration viewing experience regardless of module state.
    
    Fallback Strategy:
        1. Try enhanced tools.show_config() method (preferred)
        2. Fall back to settings.print_config() with ANSI colors
        3. Final fallback to basic text-based configuration display
    
    Returns:
        str: Status message indicating which display method was used
    """
    try:
        # Import and use the enhanced display function from the module's tools
        from ..tools.show_config import show_config

        # Call the show_config function with default colored output
        show_config()

        return "Configuration displayed successfully using module tools.show_config method."

    except Exception as e:
        # Fallback to the settings.print_config() method if enhanced method fails
        logger.warning("Could not use module tools.show_config display: %s", e)

        try:
            print_config()
            return "Configuration displayed successfully using settings.print_config() fallback."
        except Exception as fallback_error:
            logger.warning("Could not use settings.print_config: %s", fallback_error)

            # Final fallback to basic configuration display

            config_lines = [
                "=" * 80,
                "🤖 PERSONAL AI AGENT CONFIGURATION",
                "=" * 80,
                "",
                "📊 CORE SETTINGS:",
                f"  • Package Version: {get_package_version()}",
                f"  • LLM Model: {LLM_MODEL}",
                f"  • Storage Backend: {STORAGE_BACKEND}",
                f"  • Log Level: {LOG_LEVEL_STR}",
                "",
                "🌐 SERVICE ENDPOINTS:",
                f"  • Ollama URL: {OLLAMA_URL}",
                f"  • Weaviate URL: {WEAVIATE_URL}",
                "",
                "🔧 FEATURE FLAGS:",
                f"  • Weaviate Enabled: {'✅' if USE_WEAVIATE else '❌'} ({USE_WEAVIATE})",
                f"  • MCP Enabled: {'✅' if USE_MCP else '❌'} ({USE_MCP})",
                "",
                "📁 DIRECTORY CONFIGURATION:",
                f"  • Root Directory: {ROOT_DIR}",
                f"  • Home Directory: {HOME_DIR}",
                f"  • User Data Directory: {DATA_DIR}",
                f"  • Personal Agent Data Directory: {PERSAG_ROOT}"
                f"  • Repository Directory: {REPO_DIR}",
                f"  • Agno Storage Directory: {AGNO_STORAGE_DIR}",
                f"  • Agno Knowledge Directory: {AGNO_KNOWLEDGE_DIR}",
                "",
                "=" * 80,
                "🚀 Configuration loaded successfully!",
                "=" * 80,
            ]

            # Join and print
            config_text = "\n".join(config_lines)
            print(config_text)
            return config_text


if __name__ == "__main__":
    print_config()

    # end of file
