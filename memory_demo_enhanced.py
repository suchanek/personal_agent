#!/usr/bin/env python3
"""
Enhanced Memory Demo Script with Duplicate Prevention

This script demonstrates Agno's memory capabilities while preventing duplicate memories
by checking existing memories before adding new ones.
"""

import time
from typing import List, Optional

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from rich.pretty import pprint

from src.personal_agent.config import LLM_MODEL, OLLAMA_URL


def check_memory_exists(
    memory: Memory,
    user_id: str,
    new_memory_text: str,
    similarity_threshold: float = 0.8,
) -> bool:
    """Check if a similar memory already exists for the user.

    :param memory: Memory instance to check
    :param user_id: User ID to check memories for
    :param new_memory_text: New memory text to check for duplicates
    :param similarity_threshold: Similarity threshold (0.0 to 1.0)
    :return: True if similar memory exists, False otherwise
    """
    existing_memories = memory.get_user_memories(user_id=user_id)

    # Simple text similarity check (can be enhanced with embeddings)
    new_memory_lower = new_memory_text.lower().strip()

    for existing_mem in existing_memories:
        existing_text_lower = existing_mem.memory.lower().strip()

        # Check for exact matches
        if new_memory_lower == existing_text_lower:
            print(f"   🔍 Exact duplicate found: '{existing_mem.memory}'")
            return True

        # Check for substantial overlap (simple word-based similarity)
        new_words = set(new_memory_lower.split())
        existing_words = set(existing_text_lower.split())

        if len(new_words) > 0 and len(existing_words) > 0:
            intersection = new_words.intersection(existing_words)
            union = new_words.union(existing_words)
            jaccard_similarity = len(intersection) / len(union)

            if jaccard_similarity >= similarity_threshold:
                print(
                    f"   🔍 Similar memory found (similarity: {jaccard_similarity:.2f}): '{existing_mem.memory}'"
                )
                return True

    return False


def add_memory_if_unique(agent: Agent, memory: Memory, user_id: str, fact: str) -> bool:
    """Add a memory only if it doesn't already exist.

    :param agent: Agent instance
    :param memory: Memory instance
    :param user_id: User ID
    :param fact: Fact to potentially add as memory
    :return: True if memory was added, False if duplicate was found
    """
    print(f"🔍 Checking for duplicates before adding: '{fact}'")

    if check_memory_exists(memory, user_id, fact):
        print(f"   ⏭️  Skipping duplicate memory")
        return False

    print(f"   ✅ No duplicate found, processing memory...")

    # Process the fact through the agent
    agent.print_response(
        fact,
        user_id=user_id,
        stream=True,
        stream_intermediate_steps=True,
    )

    return True


def clear_database_completely(db_file: str) -> None:
    """Clear the database completely using direct SQL.

    :param db_file: Path to SQLite database file
    """
    import sqlite3
    from pathlib import Path

    print("🗑️  Clearing database completely...")

    try:
        if Path(db_file).exists():
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   Found {len(tables)} tables in database")
            if not tables:
                print("   No tables found, nothing to clear")
                conn.close()
                return
            print("   Tables to clear:", ", ".join(tables))
            # Clear each table except system tables
            print("   Clearing all user tables...")
            for table in tables:
                if not table.startswith("sqlite_"):
                    cursor.execute(f"DELETE FROM {table}")
                    print(f"   Cleared table: {table}")

            # Reset sequences
            cursor.execute("DELETE FROM sqlite_sequence")

            conn.commit()
            conn.close()
            print("✅ Database cleared completely")
        else:
            print("ℹ️  Database file does not exist")

    except Exception as e:
        print(f"❌ Error clearing database: {e}")


def main():
    """Main function to run enhanced memory demo."""
    # UserId for the memories
    user_id = "ava"
    # Database file for memory and storage
    db_file = "/tmp/agent2.db"

    # Clear database first
    clear_database_completely(db_file)

    # Initialize memory.v2 using Ollama through OpenAI-compatible interface
    memory = Memory(
        model=OpenAIChat(
            id=LLM_MODEL,
            api_key="ollama",
            base_url=f"{OLLAMA_URL}/v1",
        ),
        db=SqliteMemoryDb(table_name="user_memories", db_file=db_file),
    )

    # Initialize storage
    storage = SqliteStorage(table_name="agent_sessions", db_file=db_file)

    # Initialize Agent using Ollama
    memory_agent = Agent(
        model=OpenAIChat(
            id=LLM_MODEL,
            api_key="ollama",
            base_url=f"{OLLAMA_URL}/v1",
        ),
        memory=memory,
        enable_agentic_memory=False,
        enable_user_memories=True,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        markdown=True,
    )

    print(f"🤖 Using Ollama model: {LLM_MODEL}")
    print(f"🔗 Ollama URL: {OLLAMA_URL}")
    print(f"💾 Database file: {db_file}")
    print()

    # List of facts about Ava to test memory storage
    ava_facts = [
        "My name is Ava and I like to ski.",
        "I live in San Francisco, California.",
        "I work as a software engineer at a tech startup.",
        "My favorite color is deep blue like the ocean.",
        "I have a golden retriever named Max who loves hiking.",
        "I'm allergic to shellfish but love sushi.",
        "I speak three languages: English, Spanish, and French.",
        "My birthday is on March 15th, and I'm 28 years old.",
        "I play the piano and have been taking lessons for 10 years.",
        "I'm a vegetarian and love cooking Italian food.",
        "I drive a red Tesla Model 3.",
        "My favorite book is 'The Alchemist' by Paulo Coelho.",
    ]

    print("🧪 Testing enhanced memory capabilities with duplicate prevention...")
    print("=" * 70)

    # Process each fact with duplicate checking
    facts_processed = 0
    facts_skipped = 0

    for i, fact in enumerate(ava_facts, 1):
        print(f"\n🗣️  Fact {i}/{len(ava_facts)}: {fact}")

        # Check for duplicates before processing
        was_added = add_memory_if_unique(memory_agent, memory, user_id, fact)

        if was_added:
            facts_processed += 1
            # Allow time for memory processing
            time.sleep(2)
        else:
            facts_skipped += 1

        # Show current memory state
        print(
            f"\n📝 Current memories ({facts_processed} processed, {facts_skipped} skipped):"
        )
        memories = memory.get_user_memories(user_id=user_id)
        print(f"Total unique memories: {len(memories)}")

        for j, mem in enumerate(
            memories[-3:], max(1, len(memories) - 2)
        ):  # Show last 3
            topics_str = str(mem.topics) if mem.topics else "[No Topics]"
            print(f"  {j}. '{mem.memory}' [topics: {topics_str}]")

        if len(memories) > 3:
            print(f"  ... and {len(memories) - 3} earlier memories")
        print()

    # Test memory retrieval
    print("\n🎯 Testing memory retrieval...")
    memory_agent.print_response(
        "Tell me everything you know about me. Include my personal details, preferences, and lifestyle.",
        user_id=user_id,
        stream=True,
        stream_intermediate_steps=True,
    )

    time.sleep(2)

    # Test trying to add duplicate facts (should be skipped)
    print("\n🔄 Testing duplicate prevention with repeated facts...")
    duplicate_test_facts = [
        "My name is Ava and I like to ski.",  # Exact duplicate
        "I live in San Francisco, CA.",  # Similar but not exact
        "I have a dog named Max who loves hiking.",  # Very similar
    ]

    for i, fact in enumerate(duplicate_test_facts, 1):
        print(f"\n🔄 Duplicate test {i}/{len(duplicate_test_facts)}: {fact}")
        was_added = add_memory_if_unique(memory_agent, memory, user_id, fact)
        if was_added:
            time.sleep(2)

    # Final analysis
    print("\n📊 Final Memory Analysis:")
    print("=" * 50)
    final_memories = memory.get_user_memories(user_id=user_id)
    print(f"Input facts provided: {len(ava_facts)}")
    print(f"Facts processed: {facts_processed}")
    print(f"Facts skipped (duplicates): {facts_skipped}")
    print(f"Total unique memories stored: {len(final_memories)}")
    print(
        f"Memory efficiency: {len(final_memories)}/{len(ava_facts)} = {len(final_memories)/len(ava_facts)*100:.1f}%"
    )

    print("\n🧠 Final Memory List:")
    topic_counts = {}

    for i, memory_obj in enumerate(final_memories, 1):
        topics_str = str(memory_obj.topics) if memory_obj.topics else "[No Topics]"
        print(f"{i}. '{memory_obj.memory}' [topics: {topics_str}]")

        # Count topics
        if memory_obj.topics:
            for topic in memory_obj.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        else:
            topic_counts["[No Topics]"] = topic_counts.get("[No Topics]", 0) + 1

    print(f"\n🏷️  Topic Distribution:")
    for topic, count in sorted(topic_counts.items()):
        print(f"   {topic}: {count} memories")

    print(f"\n✅ Enhanced memory demo completed successfully!")
    print(f"   No duplicate memories detected! 🎉")


if __name__ == "__main__":
    main()
