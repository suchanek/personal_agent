"""Configuration package for Personal Agent."""

from .mcp_servers import MCP_SERVERS, get_mcp_servers
from .settings import (
    DATA_DIR,
    LLM_MODEL,
    LOG_LEVEL,
    OLLAMA_URL,
    ROOT_DIR,
    USE_MCP,
    USE_WEAVIATE,
    WEAVIATE_URL,
    get_env_var,
)


# Create a simple get_settings function for compatibility
def get_settings():
    """Get configuration settings as a dictionary."""
    return {
        "ROOT_DIR": ROOT_DIR,
        "DATA_DIR": DATA_DIR,
        "WEAVIATE_URL": WEAVIATE_URL,
        "OLLAMA_URL": OLLAMA_URL,
        "LLM_MODEL": LLM_MODEL,
        "USE_WEAVIATE": USE_WEAVIATE,
        "USE_MCP": USE_MCP,
        "LOG_LEVEL": LOG_LEVEL,
        "MCP_SERVERS": MCP_SERVERS,
        "get_env_var": get_env_var,
        "get_settings": get_settings,
    }


__all__ = [
    "ROOT_DIR",
    "DATA_DIR",
    "WEAVIATE_URL",
    "OLLAMA_URL",
    "LLM_MODEL",
    "USE_WEAVIATE",
    "USE_MCP",
    "get_env_var",
    "MCP_SERVERS",
    "get_mcp_servers",
    "get_settings",
    "LOG_LEVEL",
]
