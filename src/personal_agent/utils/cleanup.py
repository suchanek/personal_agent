"""
Utilities module for the Personal AI Agent.

This module provides logging setup, cleanup functions, signal handlers,
and other utility functions.
"""

import atexit
import gc
import logging
import os
import signal
import sys
import time
import warnings
from typing import TYPE_CHECKING

from rich.logging import RichHandler

if TYPE_CHECKING:
    from weaviate import WeaviateClient

    from personal_agent.core.mcp_client import SimpleMCPClient

# These will be injected by the main module
weaviate_client: "WeaviateClient" = None
vector_store = None
mcp_client: "SimpleMCPClient" = None
logger: logging.Logger = None


def setup_logging() -> logging.Logger:
    """Set up logging configuration with Rich handler."""
    # Suppress warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="ollama")
    warnings.filterwarnings(
        "ignore", message=".*model_fields.*", category=DeprecationWarning
    )
    warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")
    warnings.filterwarnings(
        "ignore", category=ResourceWarning, message=".*subprocess.*"
    )

    # Setup logging with DEBUG level and RichHandler
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    # Reduce httpx logging verbosity to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)

    # Reduce Flask/Werkzeug logging verbosity to WARNING to reduce noise
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("flask").setLevel(logging.WARNING)
    logging.getLogger("flask.app").setLevel(logging.WARNING)
    logging.getLogger("werkzeug._internal").setLevel(logging.WARNING)

    # Also suppress other common noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return log


def inject_dependencies(weaviate_cli, vec_store, mcp_cli, log):
    """Inject dependencies for cleanup functions."""
    global weaviate_client, vector_store, mcp_client, logger
    weaviate_client = weaviate_cli
    vector_store = vec_store
    mcp_client = mcp_cli
    logger = log


def cleanup():
    """Clean up resources on shutdown."""
    global weaviate_client, vector_store

    # Prevent multiple cleanup calls
    if hasattr(cleanup, "called") and cleanup.called:
        logger.debug("Cleanup already called, skipping...")
        return
    cleanup.called = True

    logger.info("Starting cleanup process...")

    # Clean up MCP servers
    if mcp_client:
        try:
            # Use stop_all_servers method (no need for individual stops)
            mcp_client.stop_all_servers()
            logger.info("MCP servers stopped successfully")

            # Give servers time to shutdown properly
            time.sleep(1)

        except Exception as e:
            logger.error("Error stopping MCP servers: %s", e)

    # Clean up Weaviate vector store and client
    if vector_store:
        try:
            # Clean up the vector store first
            if hasattr(vector_store, "client") and vector_store.client:
                vector_store.client.close()
                logger.debug("Vector store client closed")
            vector_store = None
        except Exception as e:
            logger.error("Error closing vector store: %s", e)

    if weaviate_client:
        try:
            # Ensure the client is properly disconnected
            if (
                hasattr(weaviate_client, "is_connected")
                and weaviate_client.is_connected()
            ):
                weaviate_client.close()
                logger.info("Weaviate client closed successfully")
            elif hasattr(weaviate_client, "close"):
                weaviate_client.close()
                logger.info("Weaviate client closed successfully")
            weaviate_client = None
        except Exception as e:
            logger.error("Error closing Weaviate client: %s", e)

    # Force garbage collection to help with cleanup
    gc.collect()

    logger.info("Cleanup process completed")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received signal %d, shutting down gracefully...", signum)
    cleanup()
    sys.exit(0)


def register_cleanup_handlers():
    """Register cleanup functions and signal handlers."""
    # Register cleanup function for normal exit
    atexit.register(cleanup)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
