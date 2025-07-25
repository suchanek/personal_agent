"""
Memory management CLI commands for the Personal AI Agent.

This module contains all CLI functions related to memory operations,
extracted from the main agno_main.py file for better organization.

DUAL STORAGE ARCHITECTURE:
--------------------------
The Personal Agent uses a dual storage approach for memories:
1. Local SQLite memory system via agent.agno_memory.memory_manager
2. LightRAG graph memory system via HTTP requests to LightRAG server

These CLI commands have been updated to ensure that memory operations are
consistently applied to both storage systems by using the agent's tool functions
that handle the dual storage logic. Each command attempts to find and use the
appropriate agent tool function, with a fallback to direct memory manager calls
if the tool function is not available.

The following operations are supported:
- Storing memories (store_immediate_memory)
- Retrieving memories (show_all_memories, show_memories_by_topic_cli)
- Analyzing memories (show_memory_analysis, show_memory_stats)
- Deleting memories (delete_memory_by_id_cli, delete_memories_by_topic_cli, clear_all_memories)

Each function includes proper error handling and logging to track operations
across both storage systems.
"""

import logging
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console
    from ..core.agno_agent import AgnoPersonalAgent

# Configure logging
logger = logging.getLogger(__name__)


def find_tool_by_name(agent: "AgnoPersonalAgent", tool_name: str) -> Optional[Callable]:
    """
    Find a tool function by name from the agent's tools, including nested toolkits.
    
    Args:
        agent: The AgnoPersonalAgent instance
        tool_name: The name of the tool to find
        
    Returns:
        The tool function if found, None otherwise
    """
    if not agent.agent or not hasattr(agent.agent, "tools"):
        return None
        
    for toolkit in agent.agent.tools:
        # Check if the toolkit itself is a callable tool (for standalone functions)
        if getattr(toolkit, "__name__", "") == tool_name:
            return toolkit

        # Check for tools within the toolkit if it has a 'tools' attribute
        if hasattr(toolkit, "tools") and isinstance(toolkit.tools, list):
            for tool in toolkit.tools:
                if hasattr(tool, "__name__") and tool.__name__ == tool_name:
                    return tool
    
    return None


async def show_all_memories(agent: "AgnoPersonalAgent", console: "Console"):
    """Show all memories for the user, using the agent's memory tools when available."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Find the get_all_memories tool function
        get_all_memories_func = find_tool_by_name(agent, "get_all_memories")
        
        if get_all_memories_func:
            # Use the tool function that provides consistent results
            result = await get_all_memories_func()
            console.print(result)
            logger.info("Retrieved all memories using agent tool function")
        else:
            # Fallback to direct memory manager call
            results = agent.agno_memory.memory_manager.get_memories_by_topic(
                db=agent.agno_memory.db,
                user_id=agent.user_id,
                topics=None,
                limit=None,
            )

            if not results:
                console.print("📝 No memories found")
                return

            console.print(f"📝 All memories ({len(results)}):")
            for i, memory in enumerate(results, 1):
                console.print(f"  {i}. {memory.memory}")
                if memory.topics:
                    console.print(f"     Topics: {', '.join(memory.topics)}")
            
            logger.info(f"Retrieved {len(results)} memories using direct memory manager")

    except Exception as e:
        console.print(f"❌ Error retrieving memories: {e}")
        logger.exception(f"Exception while retrieving all memories: {e}")


async def show_memories_by_topic_cli(agent: "AgnoPersonalAgent", topic: str, console: "Console"):
    """Show memories by topic via the CLI, using the agent's memory tools when available."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Find the get_memories_by_topic tool function
        get_memories_by_topic_func = find_tool_by_name(agent, "get_memories_by_topic")
        
        if get_memories_by_topic_func:
            # Use the tool function that provides consistent results
            result = await get_memories_by_topic_func(topic)
            console.print(result)
            logger.info(f"Retrieved memories for topic '{topic}' using agent tool function")
        else:
            # Fallback to direct memory manager call
            topics = [t.strip() for t in topic.split(",")]
            results = agent.agno_memory.memory_manager.get_memories_by_topic(
                db=agent.agno_memory.db,
                user_id=agent.user_id,
                topics=topics,
                limit=None,
            )

            if not results:
                console.print(f"📝 No memories found for topic(s): {topic}")
                return

            console.print(f"📝 Memories for topic(s) '{topic}' ({len(results)}):")
            for i, memory in enumerate(results, 1):
                console.print(f"  {i}. {memory.memory}")
                if memory.topics:
                    console.print(f"     Topics: {', '.join(memory.topics)}")
            
            logger.info(f"Retrieved {len(results)} memories for topic '{topic}' using direct memory manager")

    except Exception as e:
        console.print(f"❌ Error retrieving memories by topic: {e}")
        logger.exception(f"Exception while retrieving memories for topic '{topic}': {e}")


async def show_memory_analysis(agent: "AgnoPersonalAgent", console: "Console"):
    """Show detailed memory analysis, using the agent's memory tools when available."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Find the get_memory_stats tool function
        get_memory_stats_func = find_tool_by_name(agent, "get_memory_stats")
        
        if get_memory_stats_func:
            # Use the tool function that provides comprehensive stats
            result = await get_memory_stats_func()
            console.print(result)
            logger.info("Retrieved memory analysis using agent tool function")
        else:
            # Fallback to direct memory manager call
            stats = agent.agno_memory.memory_manager.get_memory_stats(
                db=agent.agno_memory.db, user_id=agent.user_id
            )

            if "error" in stats:
                console.print(f"❌ Error getting memory analysis: {stats['error']}")
                return

            console.print("📊 Memory Analysis:")
            console.print(f"Total memories: {stats.get('total_memories', 0)}")
            console.print(
                f"Average memory length: {stats.get('average_memory_length', 0):.1f} characters"
            )
            console.print(f"Recent memories (24h): {stats.get('recent_memories_24h', 0)}")

            if stats.get("most_common_topic"):
                console.print(f"Most common topic: {stats['most_common_topic']}")

            if stats.get("topic_distribution"):
                console.print("\nTopic distribution:")
                for topic, count in stats["topic_distribution"].items():
                    console.print(f"  - {topic}: {count}")
            
            logger.info("Retrieved memory analysis using direct memory manager")

    except Exception as e:
        console.print(f"❌ Error getting memory analysis: {e}")
        logger.exception(f"Exception while retrieving memory analysis: {e}")


async def show_memory_stats(agent: "AgnoPersonalAgent", console: "Console"):
    """Show memory statistics, using the agent's memory tools when available."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Find the get_memory_stats tool function
        get_memory_stats_func = find_tool_by_name(agent, "get_memory_stats")
        
        if get_memory_stats_func:
            # Use the tool function that provides comprehensive stats
            result = await get_memory_stats_func()
            console.print(result)
            logger.info("Retrieved memory stats using agent tool function")
        else:
            # Fallback to direct memory manager call
            stats = agent.agno_memory.memory_manager.get_memory_stats(
                db=agent.agno_memory.db, user_id=agent.user_id
            )

            if "error" in stats:
                console.print(f"❌ Error getting memory stats: {stats['error']}")
                return

            console.print(f"📊 Memory Stats: {stats}")
            logger.info("Retrieved memory stats using direct memory manager")

    except Exception as e:
        console.print(f"❌ Error getting memory stats: {e}")
        logger.exception(f"Exception while retrieving memory stats: {e}")


async def clear_all_memories(agent: "AgnoPersonalAgent", console: "Console"):
    """Clear all memories for the user from both SQLite and LightRAG storage."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Find the clear_memories tool function that handles both storage systems
        clear_memories_func = find_tool_by_name(agent, "clear_memories")
        
        if clear_memories_func:
            # Use the tool function that handles both storage systems
            result = await clear_memories_func()
            console.print(result)
            logger.info("Cleared all memories using dual storage tool function")
        else:
            # Fallback to direct memory manager call (SQLite only)
            success, message = agent.agno_memory.memory_manager.clear_memories(
                db=agent.agno_memory.db, user_id=agent.user_id
            )
            
            if success:
                console.print(f"✅ {message} (SQLite only)")
                console.print("⚠️ Warning: Could not clear graph memory (tool not found)")
                logger.warning("Cleared memories from SQLite only - graph memory tool not found")
            else:
                console.print(f"❌ Error clearing memories: {message}")
                logger.error(f"Failed to clear memories: {message}")

    except Exception as e:
        console.print(f"❌ Error clearing memories: {e}")
        logger.exception(f"Exception while clearing memories: {e}")


async def store_immediate_memory(agent: "AgnoPersonalAgent", content: str, console: "Console"):
    """
    Store content immediately as a memory in both SQLite and LightRAG storage.
    
    This function uses the agent's store_user_memory method which already handles
    dual storage in both SQLite and LightRAG graph memory systems.
    """
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # agent.store_user_memory already handles dual storage
        result = await agent.store_user_memory(content=content)
        console.print(f"✅ Stored memory: {result}")
        logger.info(f"Stored memory using dual storage: {content[:50]}...")

    except Exception as e:
        console.print(f"❌ Error storing memory: {e}")
        logger.exception(f"Exception while storing memory: {e}")


async def delete_memory_by_id_cli(agent: "AgnoPersonalAgent", memory_id: str, console: "Console"):
    """Delete a single memory by its ID from both SQLite and LightRAG storage."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Find the delete_memory tool function that handles both storage systems
        delete_memory_func = find_tool_by_name(agent, "delete_memory")
        
        if delete_memory_func:
            # Use the tool function that handles both storage systems
            result = await delete_memory_func(memory_id)
            console.print(result)
            logger.info(f"Deleted memory {memory_id} using dual storage tool function")
        else:
            # Fallback to direct memory manager call (SQLite only)
            success, message = agent.agno_memory.memory_manager.delete_memory(
                memory_id=memory_id, db=agent.agno_memory.db, user_id=agent.user_id
            )
            
            if success:
                console.print(f"✅ Successfully deleted memory from SQLite: {memory_id}")
                console.print("⚠️ Warning: Could not delete from graph memory (tool not found)")
                logger.warning(f"Deleted memory {memory_id} from SQLite only - graph memory tool not found")
            else:
                console.print(f"❌ Error deleting memory: {message}")
                logger.error(f"Failed to delete memory {memory_id}: {message}")

    except Exception as e:
        console.print(f"❌ Error deleting memory: {e}")
        logger.exception(f"Exception while deleting memory {memory_id}: {e}")


async def delete_memories_by_topic_cli(agent: "AgnoPersonalAgent", topic: str, console: "Console"):
    """Delete memories by topic from both SQLite and LightRAG storage."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Find the delete_memories_by_topic tool function that handles both storage systems
        delete_topic_func = find_tool_by_name(agent, "delete_memories_by_topic")
        
        if delete_topic_func:
            # Use the tool function that handles both storage systems
            result = await delete_topic_func(topic)
            console.print(result)
            logger.info(f"Deleted memories for topic '{topic}' using dual storage tool function")
        else:
            # Fallback to direct memory manager call (SQLite only)
            topics = [t.strip() for t in topic.split(",")]
            success, message = agent.agno_memory.memory_manager.delete_memories_by_topic(
                topics=topics, db=agent.agno_memory.db, user_id=agent.user_id
            )
            
            if success:
                console.print(f"✅ {message} (SQLite only)")
                console.print("⚠️ Warning: Could not delete from graph memory (tool not found)")
                logger.warning(f"Deleted memories for topic '{topic}' from SQLite only - graph memory tool not found")
            else:
                console.print(f"❌ Error deleting memories by topic: {message}")
                logger.error(f"Failed to delete memories for topic '{topic}': {message}")

    except Exception as e:
        console.print(f"❌ Error deleting memories by topic: {e}")
        logger.exception(f"Exception while deleting memories for topic '{topic}': {e}")
