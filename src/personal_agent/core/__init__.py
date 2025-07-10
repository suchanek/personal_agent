"""Core package for Personal Agent."""

from .agent import create_agent_executor
from .agno_agent import create_simple_personal_agent, load_agent_knowledge
from .agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
    load_lightrag_knowledge_base,
)
from .anti_duplicate_memory import AntiDuplicateMemory, create_anti_duplicate_memory
from .knowledge_coordinator import KnowledgeCoordinator, create_knowledge_coordinator
from .mcp_client import SimpleMCPClient
from .nlp_extractor import extract_entities, extract_relationships
from .memory import (
    is_weaviate_connected,
    reset_weaviate_if_corrupted,
    setup_weaviate,
    is_agno_storage_connected,
    is_memory_connected,
)
from .multi_agent_system import MultiAgentSystem, create_multi_agent_system
from .semantic_memory_manager import (
    SemanticDuplicateDetector,
    SemanticMemoryManager,
    SemanticMemoryManagerConfig,
    create_semantic_memory_manager,
)
from .smol_agent import create_smolagents_executor, create_smolagents_model
from .structured_response import (
    StructuredResponse,
    StructuredResponseParser,
    ToolCall,
    ResponseMetadata,
    ResponseError,
    get_ollama_format_schema,
    create_structured_instructions,
)
from .topic_classifier import RuleSet, TopicClassifier

__all__ = [
    # MCP Client
    "SimpleMCPClient",
    # Memory/Weaviate
    "setup_weaviate",
    "is_weaviate_connected",
    "reset_weaviate_if_corrupted",
    "is_agno_storage_connected",
    "is_memory_connected",
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
    "load_lightrag_knowledge_base",
    # Anti-duplicate memory
    "AntiDuplicateMemory",
    "create_anti_duplicate_memory",
    # Semantic memory manager
    "SemanticMemoryManager",
    "SemanticMemoryManagerConfig",
    "SemanticDuplicateDetector",
    "create_semantic_memory_manager",
    # Knowledge coordinator
    "KnowledgeCoordinator",
    "create_knowledge_coordinator",
    # NLP extractor
    "extract_entities",
    "extract_relationships",
    # Structured response
    "StructuredResponse",
    "StructuredResponseParser",
    "ToolCall",
    "ResponseMetadata",
    "ResponseError",
    "get_ollama_format_schema",
    "create_structured_instructions",
    # Topic classifier
    "TopicClassifier",
    "RuleSet",
]
