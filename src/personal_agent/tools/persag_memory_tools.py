# src/personal_agent/tools/persag_memory_tools.py

"""
DEPRECATED: This file is kept for backward compatibility only.

The PersagMemoryTools class has been replaced by standalone memory functions
in memory_functions.py. All memory operations now use these standalone functions
which eliminate duplication and provide a cleaner architecture.

For new code, use:
    from personal_agent.tools.memory_functions import store_user_memory, query_memory, etc.

This file will be removed in a future version.
"""

# Import the standalone functions for backward compatibility
from .memory_functions import (
    clear_all_memories,
    delete_memories_by_topic,
    delete_memory,
    get_all_memories,
    get_graph_entity_count,
    get_memories_by_topic,
    get_memory_graph_labels,
    get_memory_stats,
    get_recent_memories,
    list_all_memories,
    query_memory,
    store_user_memory,
    update_memory,
)

# Re-export for backward compatibility
__all__ = [
    "store_user_memory",
    "query_memory",
    "list_all_memories",
    "get_all_memories",
    "update_memory",
    "delete_memory",
    "get_recent_memories",
    "get_memory_stats",
    "get_memories_by_topic",
    "delete_memories_by_topic",
    "get_memory_graph_labels",
    "clear_all_memories",
    "get_graph_entity_count",
]
