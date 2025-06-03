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
    toggle_stream_handler,
)

# Import web interface
from .web import create_app, register_routes

configure_master_logger(disabled=True)  # Disable root logger to avoid duplicate logs

# Package-level logger
_logger = setup_logging()
_logger.info("Initializing Personal AI Agent package...")

# Package version
__version__ = "0.2.1"

# Main entry points
from .main import create_web_app, initialize_system, main
from .smol_main import run_smolagents_web

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
    # Web interface
    "create_app",
    "register_routes",
    # Main entry points
    "main",
    "create_web_app",
    "initialize_system",
    "run_smolagents_web",
    # Package info
    "__version__",
]
