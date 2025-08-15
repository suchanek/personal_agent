"""
CLI package for the Personal AI Agent.

This package provides command-line interface components including
memory management commands, CLI utilities, and command parsing.
"""

from .agno_cli import run_agno_cli
from .memory_commands import (
    clear_all_memories,
    delete_memories_by_topic_cli,
    delete_memory_by_id_cli,
    show_all_memories,
    show_memories_by_topic_cli,
    show_memory_analysis,
    show_memory_stats,
    store_immediate_memory,
)

__all__ = [
    # Main CLI functions
    "run_agno_cli",
    # Memory command functions
    "show_all_memories",
    "show_memories_by_topic_cli",
    "show_memory_analysis",
    "show_memory_stats",
    "clear_all_memories",
    "store_immediate_memory",
    "delete_memory_by_id_cli",
    "delete_memories_by_topic_cli",
]
