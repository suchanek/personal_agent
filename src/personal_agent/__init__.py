"""Personal AI Agent package initialization.

This module serves as the main entry point for the Personal AI Agent package,
providing a comprehensive suite of AI-powered tools and capabilities including:

- **Primary System**: Agno framework with native async operations and SQLite storage
- **Knowledge Base**: LanceDB-powered vector search with automatic text indexing
- **Model Context Protocol (MCP)**: Integration with 6+ servers for external tool access
- **Multiple LLM Support**: Ollama (local) and OpenAI with model-agnostic design
- **Web Interface**: Flask-based UI with real-time thoughts and tool call streaming
- **Memory Management**: Persistent conversations and automatic knowledge retention
- **Legacy Support**: Maintains compatibility with LangChain and smolagents frameworks

**Current Architecture**:
- **Agno Framework**: Primary system with enhanced performance and native MCP support (Port 5003)
- **Legacy Systems**: LangChain ReAct (Port 5001) and smolagents (Port 5001) for compatibility
- **Unified Entry**: Single `personal_agent.py` script with `--web`, `--cli`, `--query` modes

**Key Features**:
- 🔄 Real-time agent reasoning display with live streaming
- 🧠 Automatic knowledge base with search and memory capabilities
- ⚡ Modern async/await architecture for improved performance
- 🔧 Native MCP integration for seamless external tool access
- 💭 Session-based conversations with persistent memory
- 🛠️ 13+ integrated tools for GitHub, filesystem, web search, and more

Author: Eric Suchanek
Last modified: December 10, 2024
"""

import logging

# Import core components
from .config import USE_MCP, USE_WEAVIATE, get_mcp_servers
from .core import SimpleMCPClient, create_agent_executor, setup_weaviate

# Import agno components (primary system)
from .core.agno_agent import (
    AgnoPersonalAgent,
    create_agno_agent,
    create_agno_agent_sync,
    create_simple_personal_agent,
)
from .core.memory import is_weaviate_connected, vector_store, weaviate_client

# Import tools
from .tools import get_all_tools

# Import utilities
from .utils import cleanup, inject_dependencies, register_cleanup_handlers
from .utils.logging import (
    configure_master_logger,
    disable_stream_handlers_for_namespace,
    list_all_loggers,
    list_handlers,
    set_logger_level,
    set_logger_level_for_module,
    set_logging_level_for_all_handlers,
    setup_logging,
    setup_logging_filters,
    toggle_stream_handler,
)

# Import web interface
from .web import create_app, register_routes

# Package version
__version__ = "0.5.2"

# Setup package and module-level logging
# Configure logging for the package

# Disable master logger to avoid duplicate logs
configure_master_logger(disabled=False)

# Disable annoying warnings
setup_logging_filters()

# Package-level logger
_logger = setup_logging()
_logger.info("Initializing Personal AI Agent package...")


# Agno entry points (primary system)
from .agno_main import cli_main as agno_cli_main
from .agno_main import (
    create_agno_web_app,
    initialize_agno_system,
    run_agno_cli,
    run_agno_web,
)

# Main entry points (legacy systems)
from .main import cli_main, create_web_app, initialize_system, main
from .smol_main import cli_main as smol_cli_main
from .smol_main import run_smolagents_cli, run_smolagents_web


def print_configuration() -> str:
    """Print comprehensive configuration information for the Personal AI Agent.

    :return: Configuration information as formatted string
    """
    import os

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
        f"  • Data Directory: {DATA_DIR}",
        f"  • Repository Directory: {REPO_DIR}",
        "",
        "💾 AGNO STORAGE PATHS:",
        f"  • Agent Sessions: {AGNO_STORAGE_DIR}/agent_sessions.db",
        f"  • Knowledge Database: {AGNO_STORAGE_DIR}/lancedb/",
        f"  • Knowledge Files: {AGNO_KNOWLEDGE_DIR}/",
        "",
    ]

    # MCP Servers configuration
    if USE_MCP:
        mcp_servers = get_mcp_servers()
        config_lines.extend(
            [
                "🔌 MCP SERVERS:",
                f"  • Total Servers: {len(mcp_servers)}",
            ]
        )

        for server_name, config in mcp_servers.items():
            status = "✅" if config.get("enabled", True) else "❌"
            command = config.get("command", "unknown")
            config_lines.append(f"  • {server_name}: {status} ({command})")

        config_lines.append("")
    else:
        config_lines.extend(
            [
                "🔌 MCP SERVERS:",
                "  • MCP is disabled",
                "",
            ]
        )

    # Environment status
    config_lines.extend(
        [
            "🌍 ENVIRONMENT STATUS:",
            f"  • Python Path: {os.sys.executable}",
            f"  • Working Directory: {os.getcwd()}",
            f"  • Environment Variables Loaded: {'✅' if os.getenv('DATA_DIR') else '❌'}",
            "",
        ]
    )

    # Storage status checks
    storage_status = []
    try:
        from pathlib import Path

        # Check if directories exist
        data_exists = Path(DATA_DIR).exists()
        agno_storage_exists = Path(AGNO_STORAGE_DIR).exists()
        knowledge_exists = Path(AGNO_KNOWLEDGE_DIR).exists()

        storage_status.extend(
            [
                "💿 STORAGE STATUS:",
                f"  • Data Directory: {'✅' if data_exists else '❌'} ({DATA_DIR})",
                f"  • Agno Storage: {'✅' if agno_storage_exists else '❌'} ({AGNO_STORAGE_DIR})",
                f"  • Knowledge Directory: {'✅' if knowledge_exists else '❌'} ({AGNO_KNOWLEDGE_DIR})",
            ]
        )

        # Count knowledge files if directory exists
        if knowledge_exists:
            knowledge_path = Path(AGNO_KNOWLEDGE_DIR)
            txt_files = len(list(knowledge_path.glob("*.txt")))
            md_files = len(list(knowledge_path.glob("*.md")))
            pdf_files = len(list(knowledge_path.glob("*.pdf")))
            storage_status.append(
                f"  • Knowledge Files: {txt_files} txt, {md_files} md, {pdf_files} pdf"
            )

    except OSError as e:
        storage_status.extend(
            [
                "💿 STORAGE STATUS:",
                f"  • Error checking storage: {e}",
            ]
        )

    config_lines.extend(storage_status)
    config_lines.extend(
        [
            "",
            "=" * 80,
            "🚀 Configuration loaded successfully!",
            "=" * 80,
        ]
    )

    # Join and print
    config_text = "\n".join(config_lines)
    print(config_text)
    return config_text


# Export public API
__all__ = [
    # Core components
    "SimpleMCPClient",
    "create_agent_executor",
    "setup_weaviate",
    "is_weaviate_connected",
    "vector_store",
    "weaviate_client",
    # Agno components (primary system)
    "AgnoPersonalAgent",
    "create_agno_agent",
    "create_agno_agent_sync",
    "create_simple_personal_agent",
    # Configuration
    "USE_MCP",
    "USE_WEAVIATE",
    "get_mcp_servers",
    # Tools
    "get_all_tools",
    # Utilities
    "cleanup",
    "inject_dependencies",
    "register_cleanup_handlers",
    "configure_master_logger",
    "disable_stream_handlers_for_namespace",
    "list_all_loggers",
    "list_handlers",
    "set_logger_level",
    "set_logger_level_for_module",
    "set_logging_level_for_all_handlers",
    "setup_logging",
    "toggle_stream_handler",
    "setup_logging_filters",
    # Web interface
    "create_app",
    "register_routes",
    # Legacy entry points
    "main",
    "cli_main",
    "create_web_app",
    "initialize_system",
    "run_smolagents_web",
    "run_smolagents_cli",
    "smol_cli_main",
    # Agno entry points (primary system)
    "initialize_agno_system",
    "create_agno_web_app",
    "run_agno_web",
    "run_agno_cli",
    "agno_cli_main",
    "print_configuration",
    # Package info
    "__version__",
]
