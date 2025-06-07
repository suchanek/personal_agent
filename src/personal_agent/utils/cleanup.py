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
from typing import Optional

# Global logger reference
logger: Optional[logging.Logger] = None


def inject_dependencies(log):
    """Inject dependencies for cleanup functions."""
    global logger
    logger = log


def cleanup():
    """Clean up resources on shutdown."""
    # Prevent multiple cleanup calls
    if hasattr(cleanup, "called") and cleanup.called:
        if logger:
            logger.debug("Cleanup already called, skipping...")
        return
    cleanup.called = True

    if logger:
        logger.info("Starting cleanup process...")

    # Force garbage collection to help with cleanup
    gc.collect()

    if logger:
        logger.info("Cleanup process completed")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    if logger:
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
