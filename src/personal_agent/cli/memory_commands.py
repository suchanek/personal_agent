"""
Memory management CLI commands for the Personal AI Agent.

This module contains all CLI functions related to memory operations,
extracted from the main agno_main.py file for better organization.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console
    from ..core.agno_agent import AgnoPersonalAgent


async def show_all_memories(agent: "AgnoPersonalAgent", console: "Console"):
    """Show all memories for the user."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

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

    except Exception as e:
        console.print(f"❌ Error retrieving memories: {e}")


async def show_memories_by_topic_cli(agent: "AgnoPersonalAgent", topic: str, console: "Console"):
    """Show memories by topic via the CLI."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

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

    except Exception as e:
        console.print(f"❌ Error retrieving memories by topic: {e}")


async def show_memory_analysis(agent: "AgnoPersonalAgent", console: "Console"):
    """Show detailed memory analysis."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

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

    except Exception as e:
        console.print(f"❌ Error getting memory analysis: {e}")


async def show_memory_stats(agent: "AgnoPersonalAgent", console: "Console"):
    """Show memory statistics."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        stats = agent.agno_memory.memory_manager.get_memory_stats(
            db=agent.agno_memory.db, user_id=agent.user_id
        )

        if "error" in stats:
            console.print(f"❌ Error getting memory stats: {stats['error']}")
            return

        console.print(f"📊 Memory Stats: {stats}")

    except Exception as e:
        console.print(f"❌ Error getting memory stats: {e}")


async def clear_all_memories(agent: "AgnoPersonalAgent", console: "Console"):
    """Clear all memories for the user."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        success, message = agent.agno_memory.memory_manager.clear_memories(
            db=agent.agno_memory.db, user_id=agent.user_id
        )

        if success:
            console.print(f"✅ {message}")
        else:
            console.print(f"❌ Error clearing memories: {message}")

    except Exception as e:
        console.print(f"❌ Error clearing memories: {e}")


async def store_immediate_memory(agent: "AgnoPersonalAgent", content: str, console: "Console"):
    """Store content immediately as a memory."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        result = await agent.store_user_memory(content=content)
        console.print(f"✅ Stored memory: {result}")

    except Exception as e:
        console.print(f"❌ Error storing memory: {e}")


async def delete_memory_by_id_cli(agent: "AgnoPersonalAgent", memory_id: str, console: "Console"):
    """Delete a single memory by its ID via the CLI."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        success, message = agent.agno_memory.memory_manager.delete_memory(
            memory_id=memory_id, db=agent.agno_memory.db, user_id=agent.user_id
        )

        if success:
            console.print(f"✅ Successfully deleted memory: {memory_id}")
        else:
            console.print(f"❌ Error deleting memory: {message}")

    except Exception as e:
        console.print(f"❌ Error deleting memory: {e}")


async def delete_memories_by_topic_cli(agent: "AgnoPersonalAgent", topic: str, console: "Console"):
    """Delete memories by topic via the CLI."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        topics = [t.strip() for t in topic.split(",")]
        (
            success,
            message,
        ) = agent.agno_memory.memory_manager.delete_memories_by_topic(
            topics=topics, db=agent.agno_memory.db, user_id=agent.user_id
        )

        if success:
            console.print(f"✅ {message}")
        else:
            console.print(f"❌ Error deleting memories by topic: {message}")

    except Exception as e:
        console.print(f"❌ Error deleting memories by topic: {e}")
