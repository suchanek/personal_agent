"""Core package for Personal Agent."""

from .agent import create_agent_executor
from .agno_agent import create_simple_personal_agent, load_agent_knowledge
from .agno_storage import (
    create_agno_knowledge,
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_agno_knowledge,
    load_combined_knowledge_base,
    load_pdf_knowledge,
    load_personal_knowledge,
)
from .mcp_client import SimpleMCPClient
from .memory import (
    is_weaviate_connected,
    reset_weaviate_if_corrupted,
    setup_weaviate,
    vector_store,
    weaviate_client,
)
from .multi_agent_system import MultiAgentSystem, create_multi_agent_system
from .smol_agent import create_smolagents_executor, create_smolagents_model

__all__ = [
    "SimpleMCPClient",
    "setup_weaviate",
    "vector_store",
    "weaviate_client",
    "is_weaviate_connected",
    "reset_weaviate_if_corrupted",
    "create_agent_executor",
    "MultiAgentSystem",
    "create_multi_agent_system",
    "create_smolagents_executor",
    "create_smolagents_model",
    "create_agno_storage",
    "create_agno_knowledge",
    "load_agno_knowledge",
    "create_agno_memory",
    "create_combined_knowledge_base",
    "load_combined_knowledge_base",
    "load_personal_knowledge",
    "load_pdf_knowledge",
    "create_simple_personal_agent",
    "load_agent_knowledge",
]
