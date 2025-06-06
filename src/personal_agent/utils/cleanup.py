"""
Utilities module for the Personal AI Agent.

This module provides logging setup, cleanup functions, signal handlers,
and other utility functions.
"""

import atexit
import gc
import logging
import signal
import sys
import time


from personal_agent.core.mcp_client import SimpleMCPClient

# These will be injected by the main module
mcp_client: "SimpleMCPClient" = None
logger: logging.Logger = None


def inject_dependencies(mcp_cli, log):
    """Inject dependencies for cleanup functions."""
    global mcp_client, logger
    mcp_client = mcp_cli
    logger = log


def cleanup():
    """Clean up resources on shutdown."""
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
