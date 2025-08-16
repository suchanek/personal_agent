"""Personal AI Agent package initialization.

This module serves as the main entry point for the Personal AI Agent package,
providing a comprehensive suite of AI-powered tools and capabilities including:

- Multi-framework support: LangChain, smolagents, and Agno frameworks
- Model Context Protocol (MCP) integration with multiple servers
- Weaviate vector database for persistent memory
- Advanced memory management with semantic deduplication
- Comprehensive tool suite for file operations, web research, and system tasks
- Multiple interface options: Streamlit, Flask, and CLI
- Modular architecture with organized code structure

The package supports three main frameworks:
1. LangChain ReAct (legacy support)
2. Smolagents (multi-agent coordination)
3. Agno (modern async agent framework) - primary interface

Author: Personal Agent Development Team
Last modified: 2025-08-09 14:52:45
Version: 0.11.38
"""

# pylint: disable=C0413

import logging
import os

# Set Rust logging to ERROR level to suppress Lance warnings before any imports
if "RUST_LOG" not in os.environ:
    os.environ["RUST_LOG"] = "error"

# Import submodules as modules (for pdoc discovery)
from . import cli, config, core, readers, streamlit, team, tools, utils, web

# Import core components (only those used directly in this file)
from .config import USE_MCP, get_mcp_servers

# Initialize global MCP client if MCP is enabled
mcp_client = None
if USE_MCP:
    try:
        mcp_servers = get_mcp_servers()
        if mcp_servers:
            from .core import SimpleMCPClient

            mcp_client = SimpleMCPClient(mcp_servers)
    except Exception as e:
        _logger = logging.getLogger(__name__)
        _logger.warning("Failed to initialize MCP client: %s", e)
        mcp_client = None

# Import utilities (only those used directly in this file)
from .utils.pag_logging import (
    configure_master_logger,
    setup_logging,
    setup_logging_filters,
)

# Package version (matches pyproject.toml)
__version__ = "0.2.0"  # Defined once to avoid duplication

# Setup package and module-level logging
# Configure logging for the package

# Disable master logger to avoid duplicate logs
configure_master_logger(disabled=False)

# Disable annoying warnings
setup_logging_filters()

# Package-level logger
_logger = setup_logging()

# Export logger for backward compatibility
logger = _logger

# Only log initialization message if log level allows it AND root logger allows it
# This prevents spam when scripts want to suppress logging
root_logger = logging.getLogger()
if _logger.isEnabledFor(logging.INFO) and root_logger.isEnabledFor(logging.INFO):
    _logger.info("Initializing Personal AI Agent package v%s...", __version__)


# Main entry points
from .agno_main import cli_main, run_agno_cli, run_agno_cli_wrapper

# Export public API
__all__ = [
    # Submodules (for pdoc discovery)
    "config",
    "core",
    "tools",
    "utils",
    "web",
    "cli",
    "streamlit",
    "team",
    "readers",
    # MCP Client
    "mcp_client",
    # Logger
    "logger",
    # Main entry points - Agno (primary)
    "cli_main",
    "run_agno_cli",
    "run_agno_cli_wrapper",
    # Utility functions
    # Package info
    "__version__",
]
