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
            logger.warning(
                "Attempted to show memories but memory system is not available"
            )
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

        logger.info("Retrieved %d memories", len(results))

    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error("Memory system attribute error: %s", str(e), exc_info=True)
    except Exception:
        console.print("❌ Unexpected error retrieving memories. Please check the logs.")
        logger.exception("Unexpected exception while retrieving all memories")


async def show_all_memories_brief(agent: "AgnoPersonalAgent", console: "Console"):
    """Show a brief list of all memories for the user."""
    try:
        result = await agent.list_all_memories()
        console.print(result)
        logger.debug("Retrieved brief memory list")
    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error("Memory system attribute error: %s", str(e), exc_info=True)
    except Exception:
        console.print(
            "❌ Unexpected error retrieving memory list. Please check the logs."
        )
        logger.exception("Unexpected exception while retrieving brief memory list")


async def show_memories_by_topic_cli(
    agent: "AgnoPersonalAgent", topic: str, console: "Console"
):
    """Show memories by topic via the CLI."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            logger.warning(
                "Attempted to show memories by topic but memory system is not available"
            )
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

        logger.info("Retrieved %d memories for topic '%s'", len(results), topic)

    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error(
            "Memory system attribute error for topic '%s': %s",
            topic,
            str(e),
            exc_info=True,
        )
    except Exception:
        console.print(
            f"❌ Unexpected error retrieving memories for topic '{topic}'. Please check the logs."
        )
        logger.exception(
            "Unexpected exception while retrieving memories for topic '%s'", topic
        )


async def show_memory_analysis(agent: "AgnoPersonalAgent", console: "Console"):
    """Show detailed memory analysis."""
    try:
        result = await agent.get_memory_stats()
        console.print(result)
        logger.info("Retrieved memory analysis")
    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error("Memory system attribute error: %s", str(e), exc_info=True)
    except Exception:
        console.print(
            "❌ Unexpected error getting memory analysis. Please check the logs."
        )
        logger.exception("Unexpected exception while retrieving memory analysis")


async def show_memory_stats(agent: "AgnoPersonalAgent", console: "Console"):
    """Show memory statistics."""
    try:
        result = await agent.get_memory_stats()
        console.print(result)
        logger.info("Retrieved memory stats")
    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error("Memory system attribute error: %s", str(e), exc_info=True)
    except Exception:
        console.print(
            "❌ Unexpected error getting memory stats. Please check the logs."
        )
        logger.exception("Unexpected exception while retrieving memory stats")


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
                logger.info("User cancelled memory deletion")
                return
        except (EOFError, KeyboardInterrupt):
            console.print("\n❌ Memory deletion cancelled.")
            logger.info("User interrupted memory deletion prompt")
            return

        console.print("🗑️  Proceeding with memory deletion...")
        result = await agent.clear_all_memories()
        console.print(result)
        logger.info("Cleared all memories")

    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error("Memory system attribute error: %s", str(e), exc_info=True)
    except Exception:
        console.print("❌ Unexpected error clearing memories. Please check the logs.")
        logger.exception("Unexpected exception while clearing memories")


async def store_immediate_memory(
    agent: "AgnoPersonalAgent", content: str, console: "Console"
):
    """Store content immediately as a memory."""
    try:
        if not content or not content.strip():
            console.print("❌ Cannot store empty memory")
            logger.warning("Attempted to store empty memory")
            return

        result = await agent.store_user_memory(content=content)
        console.print(f"✅ Stored memory: {result}")
        logger.info("Stored memory: %s...", content[:50])
    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error("Memory system attribute error: %s", str(e), exc_info=True)
    except ValueError as e:
        console.print(f"❌ Invalid memory content: {e}")
        logger.error("Invalid memory content: %s", str(e))
    except Exception:
        console.print("❌ Unexpected error storing memory. Please check the logs.")
        logger.exception("Unexpected exception while storing memory")


async def delete_memory_by_id_cli(
    agent: "AgnoPersonalAgent", memory_id: str, console: "Console"
):
    """Delete a single memory by its ID."""
    try:
        if not memory_id or not memory_id.strip():
            console.print("❌ Memory ID is required")
            logger.warning("Attempted to delete memory without ID")
            return

        result = await agent.delete_memory(memory_id)
        console.print(result)
        logger.info("Deleted memory %s", memory_id)
    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error("Memory system attribute error: %s", str(e), exc_info=True)
    except ValueError as e:
        console.print(f"❌ Invalid memory ID: {e}")
        logger.error("Invalid memory ID '%s': %s", memory_id, str(e))
    except KeyError:
        console.print(f"❌ Memory with ID '{memory_id}' not found")
        logger.warning("Memory ID '%s' not found", memory_id)
    except Exception:
        console.print(
            f"❌ Unexpected error deleting memory '{memory_id}'. Please check the logs."
        )
        logger.exception("Unexpected exception while deleting memory %s", memory_id)


async def delete_memories_by_topic_cli(
    agent: "AgnoPersonalAgent", topic: str, console: "Console"
):
    """Delete memories by topic."""
    try:
        if not topic or not topic.strip():
            console.print("❌ Topic is required")
            logger.warning("Attempted to delete memories without topic")
            return

        result = await agent.delete_memories_by_topic(topic)
        console.print(result)
        logger.info("Deleted memories for topic '%s'", topic)
    except AttributeError as e:
        console.print("❌ Memory system not properly initialized")
        logger.error("Memory system attribute error: %s", str(e), exc_info=True)
    except ValueError as e:
        console.print(f"❌ Invalid topic: {e}")
        logger.error("Invalid topic '%s': %s", topic, str(e))
    except Exception:
        console.print(
            f"❌ Unexpected error deleting memories for topic '{topic}'. Please check the logs."
        )
        logger.exception(
            "Unexpected exception while deleting memories for topic '%s'", topic
        )
