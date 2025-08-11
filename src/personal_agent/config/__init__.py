"""Configuration package for Personal Agent."""

from .mcp_servers import MCP_SERVERS, get_mcp_servers
from .settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    DATA_DIR,
    HOME_DIR,
    LIGHTRAG_MEMORY_URL,
    LIGHTRAG_SERVER,
    LIGHTRAG_URL,
    LLM_MODEL,
    LOG_LEVEL,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    REPO_DIR,
    ROOT_DIR,
    SHOW_SPLASH_SCREEN,
    STORAGE_BACKEND,
    USE_MCP,
    USE_WEAVIATE,
    WEAVIATE_URL,
    get_env_bool,
    get_env_var,
    
)
from .user_id_mgr import (
    get_current_user_id,
    get_userid,
    get_user_storage_paths,
    refresh_user_dependent_settings,
)


# Create a simple get_settings function for compatibility
def get_settings():
    """Get configuration settings as a dictionary."""
    return {
        "USER_ID": get_userid(),
        "ROOT_DIR": ROOT_DIR,
        "HOME_DIR": HOME_DIR,
        "DATA_DIR": DATA_DIR,
        "REPO_DIR": REPO_DIR,
        "WEAVIATE_URL": WEAVIATE_URL,
        "OLLAMA_URL": OLLAMA_URL,
        "REMOTE_OLLAMA_URL": REMOTE_OLLAMA_URL,
        "LLM_MODEL": LLM_MODEL,
        "USE_WEAVIATE": USE_WEAVIATE,
        "USE_MCP": USE_MCP,
        "LOG_LEVEL": LOG_LEVEL,
        "MCP_SERVERS": MCP_SERVERS,
        "get_env_var": get_env_var,
        "get_settings": get_settings,
        "get_mcp_servers": get_mcp_servers,
        "AGNO_STORAGE_DIR": AGNO_STORAGE_DIR,
        "AGNO_KNOWLEDGE_DIR": AGNO_KNOWLEDGE_DIR,
        "STORAGE_BACKEND": STORAGE_BACKEND,
        "LIGHTRAG_SERVER": LIGHTRAG_SERVER,
        "LIGHTRAG_URL": LIGHTRAG_URL,
        "LIGHTRAG_MEMORY_URL": LIGHTRAG_MEMORY_URL,
    }


__all__ = [
    "AGNO_KNOWLEDGE_DIR",
    "AGNO_STORAGE_DIR",
    "DATA_DIR",
    "HOME_DIR",
    "LIGHTRAG_SERVER",
    "LIGHTRAG_URL",
    "LIGHTRAG_MEMORY_URL",
    "LLM_MODEL",
    "LOG_LEVEL",
    "MCP_SERVERS",
    "OLLAMA_URL",
    "REMOTE_OLLAMA_URL",
    "REPO_DIR",
    "ROOT_DIR",
    "SHOW_SPLASH_SCREEN",
    "STORAGE_BACKEND",
    "USE_MCP",
    "USE_WEAVIATE",
    "get_userid",
    "WEAVIATE_URL",
    "get_env_bool",
    "get_env_var",
    "get_mcp_servers",
    "get_settings",
    "get_current_user_id",
    "get_user_storage_paths",
    "refresh_user_dependent_settings",
    "print_configuration",
]
