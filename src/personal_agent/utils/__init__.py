"""
Utilities package for the Personal AI Agent.

This package provides logging, cleanup, and other utility functions.
Last update: 2025-06-02 23:17:39
"""

from .cleanup import cleanup, inject_dependencies, register_cleanup_handlers
from .logging import (
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
from .store_fact import store_fact_in_knowledge_base

__all__ = [
    # Cleanup utilities
    "cleanup",
    "inject_dependencies",
    "register_cleanup_handlers",
    # Logging utilities
    "setup_logging",
    "setup_logging_filters",
    "configure_master_logger",
    "disable_stream_handlers_for_namespace",
    "list_all_loggers",
    "list_handlers",
    "set_logger_level",
    "set_logger_level_for_module",
    "set_logging_level_for_all_handlers",
    "toggle_stream_handler",
    # Fact storage utilities
    "store_fact_in_knowledge_base",
]
