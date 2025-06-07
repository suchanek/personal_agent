"""Personal AI Agent package initialization.

This module serves as the main entry point for the Personal AI Agent package,
providing a comprehensive suite of AI-powered tools and capabilities including:

- Agno framework for AI agent orchestration
- Model Context Protocol (MCP) integration with 6 servers
- 13 integrated tools spanning memory management, file operations, and web research
- Flask web interface for easy interaction
- Modular architecture with organized code structure

The package uses the Agno framework for AI agent orchestration, with legacy
LangChain and smolagents implementations archived for reference.

Author: Personal Agent Development Team
Last modified: June 2, 2025
"""

import logging

# Package version
from .__version__ import __version__

# Import core components
from .config import USE_MCP, get_mcp_servers
from .core.mcp_client import SimpleMCPClient

# Import tools
from .tools import get_all_tools
from .tools.web import github_search

# Import utilities
from .utils import cleanup, inject_dependencies, register_cleanup_handlers
from .utils.logging import (
    configure_master_logger,
    disable_stream_handlers_for_namespace,
    set_logger_level,
    setup_logging,
    setup_logging_filters,
)

# Import web interface
from .web import create_app, register_routes

# Setup package and module-level logging
# Configure logging for the package

# Disable master logger to avoid duplicate logs
configure_master_logger(disabled=False)

# Disable annoying warnings
setup_logging_filters()

# Package-level logger
_logger = setup_logging()
_logger.info("Initializing Personal AI Agent package...")

# Export logger for public use
logger = _logger

# Initialize MCP client if enabled
mcp_client = None
# if USE_MCP:
#    mcp_client = SimpleMCPClient(get_mcp_servers())

# Main entry points
# Note: main.py and smol_main.py have been archived to legacy_frameworks/
# Current system uses agno_main.py and agno framework

# Export public API
__all__ = [
    # Core components
    "SimpleMCPClient",
    # Configuration
    "USE_MCP",
    "get_mcp_servers",
    # Tools
    "get_all_tools",
    # Utilities
    "cleanup",
    "inject_dependencies",
    "register_cleanup_handlers",
    "configure_master_logger",
    "disable_stream_handlers_for_namespace",
    "set_logger_level",
    "setup_logging",
    "setup_logging_filters",
    # Web interface
    "create_app",
    "register_routes",
    # Package info
    "__version__",
    # Logger
    "logger",
    # MCP Client
    "mcp_client",
    # GitHub Search Tool
    "github_search",
]
