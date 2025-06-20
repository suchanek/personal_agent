"""Core package for Personal Agent."""

from .agent import create_agent_executor
from .agno_agent import create_simple_personal_agent, load_agent_knowledge
from .agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
)
from .anti_duplicate_memory import AntiDuplicateMemory, create_anti_duplicate_memory
from .mcp_client import SimpleMCPClient
from .memory import (
    is_weaviate_connected,
    reset_weaviate_if_corrupted,
    setup_weaviate,
    vector_store,
    weaviate_client,
)
from .multi_agent_system import MultiAgentSystem, create_multi_agent_system
from .semantic_memory_manager import (
    SemanticDuplicateDetector,
    SemanticMemoryManager,
    SemanticMemoryManagerConfig,
    create_semantic_memory_manager,
)
from .smol_agent import create_smolagents_executor, create_smolagents_model
from .topic_classifier import RuleSet, TopicClassifier

__all__ = [
    # MCP Client
    "SimpleMCPClient",
    # Memory/Weaviate
    "setup_weaviate",
    "vector_store",
    "weaviate_client",
    "is_weaviate_connected",
    "reset_weaviate_if_corrupted",
    # Agent creation
    "create_agent_executor",
    "create_simple_personal_agent",
    "load_agent_knowledge",
    # Multi-agent system
    "MultiAgentSystem",
    "create_multi_agent_system",
    # Smolagents
    "create_smolagents_executor",
    "create_smolagents_model",
    # Agno storage
    "create_agno_storage",
    "create_agno_memory",
    "create_combined_knowledge_base",
    "load_combined_knowledge_base",
    # Anti-duplicate memory
    "AntiDuplicateMemory",
    "create_anti_duplicate_memory",
    # Semantic memory manager
    "SemanticMemoryManager",
    "SemanticMemoryManagerConfig",
    "SemanticDuplicateDetector",
    "create_semantic_memory_manager",
    # Topic classifier
    "TopicClassifier",
    "RuleSet",
]
