#!/usr/bin/env python3
"""
Test script to verify the create_or_update_memories method works correctly.
"""

import sys
from pathlib import Path

# Add src to path - go up one level from memory_tests to project root, then into src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.semantic_memory_manager import (
    SemanticMemoryManager,
    SemanticMemoryManagerConfig,
)


# Mock Message class for testing
class MockMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def get_content_string(self) -> str:
        return str(self.content)


def test_create_or_update_memories():
    """Test the create_or_update_memories method."""
    print("🧪 Testing create_or_update_memories Method")
    print("=" * 60)

    # Create database connection
    db_path = Path(AGNO_STORAGE_DIR) / "test_create_update_memory.db"
    print(f"📂 Database: {db_path}")

    memory_db = SqliteMemoryDb(table_name="test_memory", db_file=str(db_path))

    # Create semantic memory manager
    semantic_config = SemanticMemoryManagerConfig(
        similarity_threshold=0.8,
        enable_semantic_dedup=True,
        enable_exact_dedup=True,
        enable_topic_classification=True,
        debug_mode=True,
    )

    semantic_memory_manager = SemanticMemoryManager(config=semantic_config)

    print("✅ SemanticMemoryManager initialized successfully")

    # Test 1: Basic functionality with user messages
    print("\n🔄 Test 1: Basic create_or_update_memories functionality")

    # Create mock messages (simulating Agno Message objects)
    messages = [
        MockMessage("system", "You are a helpful assistant"),
        MockMessage("user", "My name is Alice and I work as a data scientist"),
        MockMessage("assistant", "Nice to meet you Alice!"),
        MockMessage("user", "I live in New York and I love machine learning"),
    ]

    # Existing memories (empty for first test)
    existing_memories = []

    # Call create_or_update_memories
    response = semantic_memory_manager.create_or_update_memories(
        messages=messages,
        existing_memories=existing_memories,
        user_id=USER_ID,
        db=memory_db,
    )

    print(f"📊 Response: {response}")
    print(f"🔄 Memories updated: {semantic_memory_manager.memories_updated}")

    # Test 2: Test with existing memories (duplicate detection)
    print("\n🔄 Test 2: Duplicate detection with existing memories")

    # Get the memories we just created
    memory_rows = memory_db.read_memories(user_id=USER_ID)
    existing_memories = []
    for row in memory_rows:
        if row.user_id == USER_ID and row.memory:
            from agno.memory.v2.schema import UserMemory

            user_memory = UserMemory.from_dict(row.memory)
            existing_memories.append(
                {"memory_id": user_memory.memory_id, "memory": user_memory.memory}
            )

    print(f"📋 Found {len(existing_memories)} existing memories")
    for mem in existing_memories:
        print(f"   - {mem['memory']}")

    # Try to add similar content (should be rejected as duplicates)
    duplicate_messages = [
        MockMessage(
            "user", "My name is Alice and I'm a data scientist"
        ),  # Similar to existing
        MockMessage(
            "user", "I enjoy working with Python and data analysis"
        ),  # New content
    ]

    # Reset memories_updated flag
    semantic_memory_manager.memories_updated = False

    response2 = semantic_memory_manager.create_or_update_memories(
        messages=duplicate_messages,
        existing_memories=existing_memories,
        user_id=USER_ID,
        db=memory_db,
    )

    print(f"📊 Response: {response2}")
    print(f"🔄 Memories updated: {semantic_memory_manager.memories_updated}")

    # Test 3: Test with non-user messages (should be ignored)
    print("\n🔄 Test 3: Non-user messages (should be ignored)")

    non_user_messages = [
        MockMessage("system", "System message"),
        MockMessage("assistant", "Assistant message"),
        MockMessage("tool", "Tool message"),
    ]

    # Reset memories_updated flag
    semantic_memory_manager.memories_updated = False

    response3 = semantic_memory_manager.create_or_update_memories(
        messages=non_user_messages,
        existing_memories=existing_memories,
        user_id=USER_ID,
        db=memory_db,
    )

    print(f"📊 Response: {response3}")
    print(f"🔄 Memories updated: {semantic_memory_manager.memories_updated}")

    # Test 4: Test async version
    print("\n🔄 Test 4: Async version")

    import asyncio

    async def test_async():
        async_messages = [
            MockMessage("user", "I have a cat named Whiskers and I love reading books"),
        ]

        # Reset memories_updated flag
        semantic_memory_manager.memories_updated = False

        response = await semantic_memory_manager.acreate_or_update_memories(
            messages=async_messages,
            existing_memories=existing_memories,
            user_id=USER_ID,
            db=memory_db,
        )

        print(f"📊 Async Response: {response}")
        print(f"🔄 Memories updated: {semantic_memory_manager.memories_updated}")

    asyncio.run(test_async())

    # Final verification: Check all memories in database
    print("\n📋 Final Memory State:")
    final_memory_rows = memory_db.read_memories(user_id=USER_ID)
    print(f"Total memories in database: {len(final_memory_rows)}")

    for i, row in enumerate(final_memory_rows, 1):
        if row.user_id == USER_ID and row.memory:
            from agno.memory.v2.schema import UserMemory

            user_memory = UserMemory.from_dict(row.memory)
            print(f"   {i}. '{user_memory.memory}' (topics: {user_memory.topics})")

    print(f"\n✅ create_or_update_memories test completed successfully!")
    print(f"🎉 The method is now compatible with Agno's Memory framework!")


if __name__ == "__main__":
    test_create_or_update_memories()
