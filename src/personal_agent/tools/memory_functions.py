"""
Standalone Memory Functions for Personal Agent

This module provides standalone memory functions that can be used by any component
that has access to a personal agent instance. These functions eliminate duplication
between agent methods, toolkit classes, and helper classes.

All functions take an agent instance as the first parameter and delegate to the
agent's memory_manager for the actual operations.

Functions:
    - store_user_memory: Store information as a user memory
    - query_memory: Search user memories using semantic search
    - list_all_memories: List all memories in a simple format
    - get_all_memories: Get all user memories with full details
    - update_memory: Update an existing memory
    - delete_memory: Delete a memory from both SQLite and LightRAG systems
    - get_recent_memories: Get recent memories sorted by date
    - get_memory_stats: Get memory statistics including counts and topics
    - get_memories_by_topic: Get memories filtered by topic
    - delete_memories_by_topic: Delete all memories associated with specific topics
    - get_memory_graph_labels: Get entity and relation labels from the memory graph
    - clear_all_memories: Clear all memories from both SQLite and LightRAG systems

Usage:
    from personal_agent.tools.memory_functions import store_user_memory, query_memory
    
    # Store a memory
    result = await store_user_memory(agent, "I like skiing", ["hobbies"])
    
    # Query memories
    memories = await query_memory(agent, "what do I like?", limit=5)

Author: Eric G. Suchanek, PhD
Last revision: 2025-01-16
"""

from typing import List, Union

from ..core.semantic_memory_manager import MemoryStorageResult
from ..utils import setup_logging

logger = setup_logging(__name__)


async def store_user_memory(
    agent, content: str = "", topics: Union[List[str], str, None] = None
) -> MemoryStorageResult:
    """Store information as a user memory in both local SQLite and LightRAG graph systems.

    Args:
        agent: Personal agent instance with memory capabilities
        content: The information to store as a memory
        topics: Optional list of topics/categories for the memory (None = auto-classify)

    Returns:
        MemoryStorageResult: Structured result with detailed status information
    """
    await agent._ensure_initialized()
    # Pass the user instance for delta_year timestamp adjustment
    return await agent.memory_manager.store_user_memory(content, topics, user=agent.user)


async def query_memory(agent, query: str, limit: Union[int, None] = None) -> str:
    """Search user memories using semantic search.

    Args:
        agent: Personal agent instance with memory capabilities
        query: The query to search for in memories
        limit: Maximum number of memories to return

    Returns:
        str: Found memories or message if none found
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.query_memory(query, limit)


async def list_all_memories(agent) -> str:
    """List all memories in a simple, user-friendly format.

    Args:
        agent: Personal agent instance with memory capabilities

    Returns:
        str: Simplified list of all memories
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.list_all_memories()


async def get_all_memories(agent) -> str:
    """Get all user memories with full details.

    Args:
        agent: Personal agent instance with memory capabilities

    Returns:
        str: Formatted string of all memories
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.get_all_memories()


async def update_memory(
    agent, memory_id: str, content: str, topics: Union[List[str], str, None] = None
) -> str:
    """Update an existing memory.

    Args:
        agent: Personal agent instance with memory capabilities
        memory_id: ID of the memory to update
        content: New memory content
        topics: Optional list of topics/categories for the memory

    Returns:
        str: Success or error message
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.update_memory(memory_id, content, topics)


async def delete_memory(agent, memory_id: str) -> str:
    """Delete a memory from both SQLite and LightRAG systems.

    Args:
        agent: Personal agent instance with memory capabilities
        memory_id: ID of the memory to delete

    Returns:
        str: Success or error message
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.delete_memory(memory_id)


async def get_recent_memories(agent, limit: int = 10) -> str:
    """Get recent memories sorted by date.

    Args:
        agent: Personal agent instance with memory capabilities
        limit: Maximum number of memories to return

    Returns:
        str: Formatted string of recent memories
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.get_recent_memories(limit)


async def get_memory_stats(agent) -> str:
    """Get memory statistics including counts and topics.

    Args:
        agent: Personal agent instance with memory capabilities

    Returns:
        str: Formatted string with memory statistics
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.get_memory_stats()


async def get_memories_by_topic(
    agent, topics: Union[List[str], str, None] = None, limit: Union[int, None] = None
) -> str:
    """Get memories filtered by topic.

    Args:
        agent: Personal agent instance with memory capabilities
        topics: Topic or list of topics to filter memories by
        limit: Maximum number of memories to return

    Returns:
        str: Formatted string of memories matching the topics
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.get_memories_by_topic(topics, limit)


async def delete_memories_by_topic(agent, topics: Union[List[str], str]) -> str:
    """Delete all memories associated with specific topics.

    Args:
        agent: Personal agent instance with memory capabilities
        topics: Topic or list of topics to delete memories for

    Returns:
        str: Success or error message
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.delete_memories_by_topic(topics)


async def get_memory_graph_labels(agent) -> str:
    """Get the list of all entity and relation labels from the memory graph.

    Args:
        agent: Personal agent instance with memory capabilities

    Returns:
        str: Formatted string with entity and relation labels
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.get_memory_graph_labels()


async def clear_all_memories(agent) -> str:
    """Clear all memories from both SQLite and LightRAG systems.

    Args:
        agent: Personal agent instance with memory capabilities

    Returns:
        str: Success or error message
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.clear_all_memories()


async def get_graph_entity_count(agent) -> int:
    """Get the count of entities/documents in the LightRAG memory graph.

    Args:
        agent: Personal agent instance with memory capabilities

    Returns:
        int: Number of entities/documents in the graph
    """
    await agent._ensure_initialized()
    return await agent.memory_manager.get_graph_entity_count()
