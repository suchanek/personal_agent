"""Personal AI Agent package initialization.

This module serves as the main entry point for the Personal AI Agent package,
providing a comprehensive suite of AI-powered tools and capabilities including:

- Agno framework as the primary modern async agent framework
- Model Context Protocol (MCP) integration with multiple servers
- Agno semantic memory via SQLite and LanceDB storage
- Advanced memory management with semantic deduplication and anti-duplicate features
- Knowledge coordination and multi-agent system support
- Comprehensive tool suite for file operations, web research, and system tasks
- Multiple interface options: Streamlit dashboard, Flask web interface, and CLI
- Modular architecture with organized code structure and structured response handling

Framework Support:
- Agno (modern async agent framework) - **PRIMARY INTERFACE**
- LangChain ReAct (legacy support - deprecated)
- Smolagents (legacy support - deprecated)

Key Features:
- MCP server integration with factory pattern for tool creation
- Agno semantic memory with SQLite and LanceDB backends
- Semantic memory management with duplicate detection
- Topic classification and knowledge coordination
- Multi-agent system support
- Structured response parsing
- Comprehensive logging and configuration management
- LightRAG integration for advanced knowledge management

Storage Architecture:
- Primary: Agno storage with SQLite and LanceDB
- Legacy: Weaviate vector database (deprecated)

Author: Eric G. Suchanek, PhD.
Last modified: 2025-07-18 21:28:13
Version: 0.10.0
"""

# pylint: disable=C0413

import logging
import os

# Import core components
from .config import USE_MCP, USE_WEAVIATE, get_mcp_servers
from .core import SimpleMCPClient, create_agent_executor, setup_weaviate
from .core.agent_instruction_manager import AgentInstructionManager
from .core.agent_knowledge_manager import AgentKnowledgeManager
from .core.agent_memory_manager import AgentMemoryManager
from .core.agent_model_manager import AgentModelManager
from .core.agent_tool_manager import AgentToolManager

# Import key classes for pdoc documentation
from .core.agno_agent import (
    AgnoPersonalAgent,
    create_agno_agent,
    create_simple_personal_agent,
    load_agent_knowledge,
)

# Import additional core components
from .core.agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
    load_lightrag_knowledge_base,
)
from .core.anti_duplicate_memory import (
    AntiDuplicateMemory,
    create_anti_duplicate_memory,
)
from .core.knowledge_coordinator import (
    KnowledgeCoordinator,
    create_knowledge_coordinator,
)
from .core.mcp_manager import mcp_manager
from .core.memory import (
    is_agno_storage_connected,
    is_memory_connected,
    is_weaviate_connected,
    vector_store,
    weaviate_client,
)
from .core.multi_agent_system import MultiAgentSystem, create_multi_agent_system
from .core.semantic_memory_manager import (
    MemoryStorageResult,
    MemoryStorageStatus,
    SemanticDuplicateDetector,
    SemanticMemoryManager,
    create_semantic_memory_manager,
)
from .core.structured_response import (
    ResponseError,
    ResponseMetadata,
    StructuredResponse,
    StructuredResponseParser,
    ToolCall,
    create_structured_instructions,
    get_ollama_format_schema,
)
from .core.topic_classifier import RuleSet, TopicClassifier

# Import tools
from .tools import get_all_tools

# Import utilities
from .utils import cleanup, inject_dependencies, register_cleanup_handlers
from .utils.pag_logging import (
    configure_all_rich_logging,
    configure_master_logger,
    disable_stream_handlers_for_namespace,
    list_all_loggers,
    list_handlers,
    set_logger_level,
    set_logger_level_for_module,
    set_logging_level_for_all_handlers,
    setup_agno_rich_logging,
    setup_logging,
    setup_logging_filters,
    toggle_stream_handler,
)
from .utils.store_fact import store_fact_in_knowledge_base

# Import web interface
from .web import create_app, register_routes

# Package version (matches pyproject.toml)
__version__ = "0.10.0"  # Defined once to avoid duplication

# Setup package and module-level logging
# Configure logging for the package

# Disable master logger to avoid duplicate logs
configure_master_logger(disabled=False)

# Disable annoying warnings
setup_logging_filters()

# Package-level logger
_logger = setup_logging()

# Export public API
__all__ = [
    # === PRIMARY AGNO FRAMEWORK ===
    # Core Agno components
    "AgnoPersonalAgent",
    "create_agno_agent",
    "create_simple_personal_agent",
    "load_agent_knowledge",
    # Agno storage components (SQLite + LanceDB)
    "create_agno_memory",
    "create_agno_storage",
    "create_combined_knowledge_base",
    "load_combined_knowledge_base",
    "load_lightrag_knowledge_base",
    "is_agno_storage_connected",
    "is_memory_connected",
    # Agno semantic memory management
    "SemanticMemoryManager",
    "MemoryStorageStatus",
    "MemoryStorageResult",
    "SemanticDuplicateDetector",
    "create_semantic_memory_manager",
    # Anti-duplicate memory
    "AntiDuplicateMemory",
    "create_anti_duplicate_memory",
    # Knowledge coordination
    "KnowledgeCoordinator",
    "create_knowledge_coordinator",
    # Multi-agent system
    "MultiAgentSystem",
    "create_multi_agent_system",
    # Structured response handling
    "StructuredResponse",
    "StructuredResponseParser",
    "ToolCall",
    "ResponseMetadata",
    "ResponseError",
    "get_ollama_format_schema",
    "create_structured_instructions",
    # Topic classification
    "RuleSet",
    "TopicClassifier",
    # Agent managers
    "AgentMemoryManager",
    "AgentInstructionManager",
    "AgentKnowledgeManager",
    "AgentToolManager",
    "AgentModelManager",
    # Main entry points - Agno (primary)
    "cli_main",
    "run_agno_cli",
    # === MCP INTEGRATION ===
    "SimpleMCPClient",
    "mcp_manager",
    "USE_MCP",
    "get_mcp_servers",
    # === TOOLS ===
    "get_all_tools",
    # === UTILITIES ===
    "cleanup",
    "inject_dependencies",
    "register_cleanup_handlers",
    "store_fact_in_knowledge_base",
    # Logging utilities
    "configure_all_rich_logging",
    "configure_master_logger",
    "disable_stream_handlers_for_namespace",
    "list_all_loggers",
    "list_handlers",
    "set_logger_level",
    "set_logger_level_for_module",
    "set_logging_level_for_all_handlers",
    "setup_agno_rich_logging",
    "setup_logging",
    "toggle_stream_handler",
    "setup_logging_filters",
    # === WEB INTERFACE ===
    "create_app",
    "register_routes",
    # === LEGACY COMPONENTS (DEPRECATED) ===
    # Legacy LangChain components
    "create_agent_executor",
    "langchain_main",
    "langchain_cli_main",
    # Legacy Smolagents components
    "run_smolagents_web",
    "run_smolagents_cli",
    # Legacy Weaviate components
    "setup_weaviate",
    "is_weaviate_connected",
    "vector_store",
    "weaviate_client",
    "USE_WEAVIATE",
    # === UTILITY FUNCTIONS ===
    "print_configuration",
    # === PACKAGE INFO ===
    "__version__",
]

# Only log initialization message if log level allows it AND root logger allows it
# This prevents spam when scripts want to suppress logging
root_logger = logging.getLogger()
if _logger.isEnabledFor(logging.INFO) and root_logger.isEnabledFor(logging.INFO):
    _logger.info("Initializing Personal AI Agent package v%s...", __version__)


# Main entry points
from .agno_main import cli_main, run_agno_cli
from .langchain_main import cli_main as langchain_cli_main
from .langchain_main import main as langchain_main
from .smol_main import run_smolagents_cli, run_smolagents_web


def print_configuration() -> str:
    """Print comprehensive configuration information for the Personal AI Agent.

    Uses the enhanced configuration display method from the module's tools.

    :return: Configuration information as formatted string
    """
    try:
        # Import and use the enhanced display function from the module's tools
        from .tools.show_config import show_config

        # Call the show_config function with default colored output
        show_config()

        return "Configuration displayed successfully using module tools.show_config method."

    except Exception as e:
        # Fallback to the settings.print_config() method if enhanced method fails
        _logger.warning("Could not use module tools.show_config display: %s", e)

        try:
            from .config.settings import print_config

            print_config()
            return "Configuration displayed successfully using settings.print_config() fallback."
        except ImportError as fallback_error:
            _logger.warning(
                "Could not import settings.print_config: %s", fallback_error
            )

            # Final fallback to basic configuration display
            from .config import get_mcp_servers
            from .config.settings import (
                AGNO_KNOWLEDGE_DIR,
                AGNO_STORAGE_DIR,
                DATA_DIR,
                HOME_DIR,
                LLM_MODEL,
                LOG_LEVEL_STR,
                OLLAMA_URL,
                REPO_DIR,
                ROOT_DIR,
                STORAGE_BACKEND,
                USE_MCP,
                USE_WEAVIATE,
                WEAVIATE_URL,
            )

            config_lines = [
                "=" * 80,
                "🤖 PERSONAL AI AGENT CONFIGURATION",
                "=" * 80,
                "",
                "📊 CORE SETTINGS:",
                f"  • Package Version: {__version__}",
                f"  • Primary Framework: Agno (modern async agent framework)",
                f"  • LLM Model: {LLM_MODEL}",
                f"  • Storage Backend: {STORAGE_BACKEND}",
                f"  • Log Level: {LOG_LEVEL_STR}",
                "",
                "🌐 SERVICE ENDPOINTS:",
                f"  • Ollama URL: {OLLAMA_URL}",
                f"  • Weaviate URL: {WEAVIATE_URL} (legacy)",
                "",
                "🔧 FEATURE FLAGS:",
                f"  • MCP Enabled: {'✅' if USE_MCP else '❌'} ({USE_MCP})",
                f"  • Weaviate Enabled: {'⚠️' if USE_WEAVIATE else '❌'} ({USE_WEAVIATE}) - LEGACY",
                "",
                "📁 DIRECTORY CONFIGURATION:",
                f"  • Root Directory: {ROOT_DIR}",
                f"  • Home Directory: {HOME_DIR}",
                f"  • Data Directory: {DATA_DIR}",
                f"  • Repository Directory: {REPO_DIR}",
                f"  • Agno Storage Directory: {AGNO_STORAGE_DIR} (primary)",
                f"  • Agno Knowledge Directory: {AGNO_KNOWLEDGE_DIR} (primary)",
                "",
                "🏗️ ARCHITECTURE:",
                "  • Primary: Agno semantic memory (SQLite + LanceDB)",
                "  • Legacy: Weaviate vector database (deprecated)",
                "  • Legacy: LangChain ReAct (deprecated)",
                "  • Legacy: Smolagents (deprecated)",
                "",
                "=" * 80,
                "🚀 Configuration loaded successfully!",
                "=" * 80,
            ]

            # Join and print
            config_text = "\n".join(config_lines)
            print(config_text)
            return config_text


# The __all__ list has been moved above to fix the "using variable before assignment" issue
