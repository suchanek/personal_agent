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


# Logging configuration
LOG_LEVEL_STR = get_env_var("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# LLM Model configuration
LLM_MODEL = get_env_var("LLM_MODEL", "qwen3:8b")


# Display configuration
SHOW_SPLASH_SCREEN = get_env_bool("SHOW_SPLASH_SCREEN", False)


def get_package_version():
    """Get package version from the package __init__.py."""
    try:
        # Import the version from the package
        from personal_agent import __version__
        return __version__
    except ImportError:
        return 'unknown'


def print_config():
    """Pretty print configuration and environment variables."""
    # ANSI color codes
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
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
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                display_value = '*' * len(value) if value else ''
            print(f"  {YELLOW}{key:<28}{ENDC} {display_value}")
    
    # Configuration sections
    sections = [
        {
            'title': '🌐 Server Configuration',
            'items': [
                ('LightRAG URL', LIGHTRAG_URL),
                ('LightRAG Memory URL', LIGHTRAG_MEMORY_URL),
                ('Weaviate URL', WEAVIATE_URL),
                ('Ollama URL', OLLAMA_URL),
                ('Remote Ollama URL', REMOTE_OLLAMA_URL),
            ]
        },
        {
            'title': '⚙️  Feature Flags',
            'items': [
                ('Use Weaviate', f"{GREEN}✓{ENDC}" if USE_WEAVIATE else f"{RED}✗{ENDC}"),
                ('Use MCP', f"{GREEN}✓{ENDC}" if USE_MCP else f"{RED}✗{ENDC}"),
                ('Show Splash Screen', f"{GREEN}✓{ENDC}" if SHOW_SPLASH_SCREEN else f"{RED}✗{ENDC}"),
            ]
        },
        {
            'title': '📂 Directory Configuration',
            'items': [
                ('Root Directory', ROOT_DIR),
                ('Home Directory', HOME_DIR),
                ('Data Directory', DATA_DIR),
                ('Repository Directory', REPO_DIR),
                ('Agno Storage Directory', AGNO_STORAGE_DIR),
                ('Agno Knowledge Directory', AGNO_KNOWLEDGE_DIR),
            ]
        },
        {
            'title': '🤖 AI & Storage Configuration',
            'items': [
                ('Storage Backend', STORAGE_BACKEND),
                ('LLM Model', LLM_MODEL),
                ('User ID', USER_ID),
                ('Log Level', LOG_LEVEL_STR),
            ]
        }
    ]
    
    for section in sections:
        print(f"\n{BOLD}{BLUE}{section['title']}:{ENDC}")
        print(f"  {UNDERLINE}Setting{' '*22}Value{ENDC}")
        for name, value in section['items']:
            print(f"  {CYAN}{name:<30}{ENDC} {value}")
    
    # Footer
    print(f"\n{BOLD}{HEADER}{'='*60}{ENDC}")
    print(f"{BOLD}{GREEN}Configuration loaded successfully!{ENDC}")
    print(f"{BOLD}{HEADER}{'='*60}{ENDC}")


if __name__ == "__main__":
    print_config()

    # end of file
