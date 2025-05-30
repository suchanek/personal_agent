"""
Utilities package for the Personal AI Agent.

This package provides logging, cleanup, and other utility functions.
"""

from .cleanup import (
    cleanup,
    inject_dependencies,
    register_cleanup_handlers,
    setup_logging,
)

__all__ = [
    "setup_logging",
    "cleanup",
    "register_cleanup_handlers",
    "inject_dependencies",
]
