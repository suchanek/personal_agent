#!/usr/bin/env python3
"""
Simple test to understand Agno Memory behavior with Ollama models.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from rich.pretty import pprint

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, USER_ID


def test_simple_memory():
    """Test basic memory functionality."""
    print("🧠 Testing Simple Memory with Ollama")
    print("=" * 50)

    # Create memory database
    memory_db = SqliteMemoryDb(
        table_name="simple_test", db_file=f"{AGNO_STORAGE_DIR}/simple_test.db"
    )

    # Clear any existing data
    memory_db.clear()

    # Create memory instance
    memory = Memory(db=memory_db, model=Ollama(id=LLM_MODEL))

    user_id = USER_ID

    print(f"👤 User ID: {user_id}")
    print(f"🤖 Model: {LLM_MODEL}")

    # Test 1: Create memories from simple text
    print("\n📝 Test 1: Creating memories from simple text")
    text1 = "My name is Eric and I work as a software engineer."

    print(f"Input: {text1}")

    # Get initial memory count
    initial_memories = memory.get_user_memories(user_id=user_id)
    print(f"Initial memories: {len(initial_memories)}")

    # Create memories
    memory.create_user_memories(message=text1, user_id=user_id)

    # Check results
    after_memories = memory.get_user_memories(user_id=user_id)
    new_count = len(after_memories) - len(initial_memories)

    print(f"Memories created: {new_count}")
    print(f"Total memories: {len(after_memories)}")

    if after_memories:
        print("\n🧠 Created memories:")
        for i, mem in enumerate(after_memories, 1):
            print(f"  {i}. {mem.memory}")
            if mem.topics:
                print(f"     Topics: {', '.join(mem.topics)}")

    # Test 2: Create memories from different text
    print("\n📝 Test 2: Creating memories from different text")
    text2 = "I love hiking and reading books."

    print(f"Input: {text2}")

    before_count = len(memory.get_user_memories(user_id=user_id))
    memory.create_user_memories(message=text2, user_id=user_id)
    after_count = len(memory.get_user_memories(user_id=user_id))

    new_memories_count = after_count - before_count
    print(f"New memories created: {new_memories_count}")

    # Show all memories
    all_memories = memory.get_user_memories(user_id=user_id)
    print(f"\n🧠 All memories ({len(all_memories)}):")
    for i, mem in enumerate(all_memories, 1):
        print(f"  {i}. {mem.memory}")
        if mem.topics:
            print(f"     Topics: {', '.join(mem.topics)}")

    # Test memory search
    print("\n🔍 Test 3: Memory search")
    search_queries = [
        "What is the user's name?",
        "What does the user do for work?",
        "What are the user's hobbies?",
    ]

    for query in search_queries:
        print(f"\nQuery: {query}")
        try:
            results = memory.search_user_memories(user_id=user_id, query=query, limit=3)
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.memory}")
            else:
                print("  No results found")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    test_simple_memory()
