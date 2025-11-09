"""Core package for Personal Agent."""

from .agent import create_agent_executor
from .agent_knowledge_manager import AgentKnowledgeManager
from .agent_memory_manager import AgentMemoryManager
from .agent_model_manager import AgentModelManager
from .agno_agent import create_simple_personal_agent, load_agent_knowledge
from .agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
    load_lightrag_knowledge_base,
)
from .anti_duplicate_memory import AntiDuplicateMemory, create_anti_duplicate_memory
from .docker_integration import (
    DockerIntegrationManager,
    check_docker_user_consistency,
    ensure_docker_user_consistency,
)
from .knowledge_coordinator import KnowledgeCoordinator, create_knowledge_coordinator
from .lightrag_manager import LightRAGManager
from .mcp_client import SimpleMCPClient
from .memory import (
    is_agno_storage_connected,
    is_memory_connected,
    is_weaviate_connected,
    reset_weaviate_if_corrupted,
    setup_weaviate,
)
from .nlp_extractor import extract_entities, extract_relationships
from .semantic_memory_manager import (
    SemanticDuplicateDetector,
    SemanticMemoryManager,
    SemanticMemoryManagerConfig,
    create_semantic_memory_manager,
)
# Legacy smolagents import removed - no longer used
# from .smol_agent import create_smolagents_executor, create_smolagents_model
from .smollm2_parser import (
    extract_content_from_smollm2_response,
    format_smollm2_system_prompt,
    is_smollm2_model,
    parse_smollm2_response,
    prepare_smollm2_messages,
)
from .structured_response import (
    ResponseError,
    ResponseMetadata,
    StructuredResponse,
    StructuredResponseParser,
    ToolCall,
    create_structured_instructions,
    get_ollama_format_schema,
)
from .topic_classifier import RuleSet, TopicClassifier
from .user_manager import UserManager
from .user_registry import UserRegistry

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
    # Agent managers
    "AgentKnowledgeManager",
    "AgentMemoryManager", 
    "AgentModelManager",
    # Legacy smolagents exports removed - no longer used
    # "create_smolagents_executor",
    # "create_smolagents_model",
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
    # User management
    "UserManager",
    "UserRegistry",
    # LightRAG management
    "LightRAGManager",
    # Docker integration
    "DockerIntegrationManager",
    "check_docker_user_consistency",
    "ensure_docker_user_consistency",
    # SmolLM2 parsing utilities
    "extract_content_from_smollm2_response",
    "format_smollm2_system_prompt",
    "is_smollm2_model",
    "parse_smollm2_response",
    "prepare_smollm2_messages",
]
