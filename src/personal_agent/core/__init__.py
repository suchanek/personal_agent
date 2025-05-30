"""Core package for Personal Agent."""

from .agent import create_agent_executor
from .mcp_client import SimpleMCPClient
from .memory import setup_weaviate, vector_store, weaviate_client

__all__ = [
    "SimpleMCPClient",
    "setup_weaviate",
    "vector_store",
    "weaviate_client",
    "create_agent_executor",
]
