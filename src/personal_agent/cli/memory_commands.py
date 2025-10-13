"""
Memory management CLI commands for the Personal AI Agent.

This module provides a thin CLI presentation layer for memory operations.
All CLI commands delegate directly to the agent's memory methods, which handle
the dual storage architecture (SQLite + LightRAG) transparently.

Supported operations:
- Storing memories (store_immediate_memory)
- Retrieving memories (show_all_memories, show_all_memories_brief, show_memories_by_topic_cli)
- Analyzing memories (show_memory_analysis, show_memory_stats)
- Deleting memories (delete_memory_by_id_cli, delete_memories_by_topic_cli, clear_all_memories)

Each function provides Rich console formatting, error handling, and logging.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

    from ..core.agno_agent import AgnoPersonalAgent

# Configure logging
logger = logging.getLogger(__name__)




async def show_all_memories(agent: "AgnoPersonalAgent", console: "Console"):
    """Show all memories for the user."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Get raw memory objects directly from memory manager
        results = agent.agno_memory.memory_manager.get_all_memories(
            db=agent.agno_memory.db,
            user_id=agent.user_id,
        )

        if not results:
            console.print("📝 No memories found")
            return

        console.print(f"📝 All memories ({len(results)}):")
        for i, memory in enumerate(results, 1):
            console.print(f"  {i}. {memory.memory}")
            if memory.topics:
                console.print(f"     Topics: {', '.join(memory.topics)}")

        logger.info(f"Retrieved {len(results)} memories")

    except Exception as e:
        console.print(f"❌ Error retrieving memories: {e}")
        logger.exception(f"Exception while retrieving all memories: {e}")


async def show_all_memories_brief(agent: "AgnoPersonalAgent", console: "Console"):
    """Show a brief list of all memories for the user."""
    try:
        result = await agent.list_all_memories()
        console.print(result)
        logger.debug("Retrieved brief memory list")
    except Exception as e:
        console.print(f"❌ Error retrieving brief memory list: {e}")
        logger.exception(f"Exception while retrieving brief memory list: {e}")


async def show_memories_by_topic_cli(
    agent: "AgnoPersonalAgent", topic: str, console: "Console"
):
    """Show memories by topic via the CLI."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        # Get raw memory objects directly from memory manager
        topics = [t.strip() for t in topic.split(",")]
        results = agent.agno_memory.memory_manager.get_memories_by_topic(
            db=agent.agno_memory.db,
            user_id=agent.user_id,
            topics=topics,
        )

        if not results:
            console.print(f"📝 No memories found for topic(s): {topic}")
            return

        console.print(f"📝 Memories for topic(s) '{topic}' ({len(results)}):")
        for i, memory in enumerate(results, 1):
            console.print(f"  {i}. {memory.memory}")
            if memory.topics:
                console.print(f"     Topics: {', '.join(memory.topics)}")

        logger.info(f"Retrieved {len(results)} memories for topic '{topic}'")

    except Exception as e:
        console.print(f"❌ Error retrieving memories by topic: {e}")
        logger.exception(f"Exception while retrieving memories for topic '{topic}': {e}")


async def show_memory_analysis(agent: "AgnoPersonalAgent", console: "Console"):
    """Show detailed memory analysis."""
    try:
        result = await agent.get_memory_stats()
        console.print(result)
        logger.info("Retrieved memory analysis")
    except Exception as e:
        console.print(f"❌ Error getting memory analysis: {e}")
        logger.exception(f"Exception while retrieving memory analysis: {e}")


async def show_memory_stats(agent: "AgnoPersonalAgent", console: "Console"):
    """Show memory statistics."""
    try:
        result = await agent.get_memory_stats()
        console.print(result)
        logger.info("Retrieved memory stats")
    except Exception as e:
        console.print(f"❌ Error getting memory stats: {e}")
        logger.exception(f"Exception while retrieving memory stats: {e}")


async def clear_all_memories(agent: "AgnoPersonalAgent", console: "Console"):
    """Clear all memories for the user."""
    try:
        # Show confirmation prompt for destructive operation
        console.print(
            "⚠️  [bold red]WARNING: This will permanently delete ALL memories![/bold red]"
        )
        console.print("This action cannot be undone.")

        # Get user confirmation
        try:
            confirmation = input("Type 'YES' to confirm deletion: ").strip()
            if confirmation != "YES":
                console.print("❌ Memory deletion cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            console.print("\n❌ Memory deletion cancelled.")
            return

        console.print("🗑️  Proceeding with memory deletion...")
        result = await agent.clear_all_memories()
        console.print(result)
        logger.info("Cleared all memories")

    except Exception as e:
        console.print(f"❌ Error clearing memories: {e}")
        logger.exception(f"Exception while clearing memories: {e}")


async def store_immediate_memory(
    agent: "AgnoPersonalAgent", content: str, console: "Console"
):
    """Store content immediately as a memory."""
    try:
        result = await agent.store_user_memory(content=content)
        console.print(f"✅ Stored memory: {result}")
        logger.info(f"Stored memory: {content[:50]}...")
    except Exception as e:
        console.print(f"❌ Error storing memory: {e}")
        logger.exception(f"Exception while storing memory: {e}")


async def delete_memory_by_id_cli(
    agent: "AgnoPersonalAgent", memory_id: str, console: "Console"
):
    """Delete a single memory by its ID."""
    try:
        result = await agent.delete_memory(memory_id)
        console.print(result)
        logger.info(f"Deleted memory {memory_id}")
    except Exception as e:
        console.print(f"❌ Error deleting memory: {e}")
        logger.exception(f"Exception while deleting memory {memory_id}: {e}")


async def delete_memories_by_topic_cli(
    agent: "AgnoPersonalAgent", topic: str, console: "Console"
):
    """Delete memories by topic."""
    try:
        result = await agent.delete_memories_by_topic(topic)
        console.print(result)
        logger.info(f"Deleted memories for topic '{topic}'")
    except Exception as e:
        console.print(f"❌ Error deleting memories by topic: {e}")
        logger.exception(f"Exception while deleting memories for topic '{topic}': {e}")
