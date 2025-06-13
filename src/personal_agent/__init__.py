"""Personal AI Agent package initialization.

This module serves as the main entry point for the Personal AI Agent package,
providing a comprehensive suite of AI-powered tools and capabilities including:

- Multi-agent framework powered by HuggingFace smolagents
- Model Context Protocol (MCP) integration with 6 servers
- Weaviate vector database for persistent memory
- 13 integrated tools spanning memory management, file operations, and web research
- Flask web interface for easy interaction
- Modular architecture with organized code structure

The package supports both LangChain ReAct and smolagents frameworks, with the
smolagents implementation being the primary interface for production use.

Author: Personal Agent Development Team
Last modified: June 2, 2025
"""

import logging

# Import core components
from .config import USE_MCP, USE_WEAVIATE, get_mcp_servers
from .core import SimpleMCPClient, create_agent_executor, setup_weaviate
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
__version__ = "0.3.0"

# Setup package and module-level logging
# Configure logging for the package

# Disable master logger to avoid duplicate logs
configure_master_logger(disabled=False)

# Disable annoying warnings
setup_logging_filters()

# Package-level logger
_logger = setup_logging()
_logger.info("Initializing Personal AI Agent package...")


# Main entry points
from .agno_main import cli_main
from .smol_main import run_smolagents_web


def print_configuration() -> str:
    """Print comprehensive configuration information for the Personal AI Agent.

    :return: Configuration information as formatted string
    """
    import os

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

    except Exception as e:
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
    # Main entry points
    "main",
    "create_web_app",
    "initialize_system",
    "run_smolagents_web",
    "print_configuration",
    # Package info
    "__version__",
]
