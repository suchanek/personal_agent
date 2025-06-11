#!/usr/bin/env python3
"""
Debug script to test enhanced memory duplicate detection
"""

from src.personal_agent.core.agno_storage import (
    EnhancedMemory,
    clear_agno_database_completely,
    create_agno_memory,
)
from src.personal_agent.utils import setup_logging

logger = setup_logging(__name__)


def debug_enhanced_memory():
    """Debug enhanced memory duplicate detection."""
    print("🔍 Debugging Enhanced Memory Duplicate Detection")
    print("=" * 60)

    # Clear existing data
    clear_agno_database_completely()

    # Create enhanced memory
    base_memory = create_agno_memory()
    enhanced_memory = EnhancedMemory(base_memory, similarity_threshold=0.8)

    user_id = "debug_user"

    # Test facts
    facts = [
        "My name is Alice and I work as a data scientist.",
        "My name is Alice and I am a data scientist.",  # Very similar
        "I have a cat named Whiskers.",
        "I have a pet cat called Whiskers.",  # Very similar
    ]

    print(f"\n📝 Testing with {len(facts)} facts:")
    for i, fact in enumerate(facts):
        print(f"  {i+1}. {fact}")

    print(f"\n🔄 Processing facts one by one:")

    for i, fact in enumerate(facts, 1):
        print(f"\n--- Processing Fact {i}: '{fact}' ---")

        # Check current memories
        current_memories = enhanced_memory.get_user_memories(user_id=user_id)
        print(f"Current memories in database: {len(current_memories)}")
        for j, mem in enumerate(current_memories):
            print(f"  {j+1}. '{mem.memory}'")

        # Check if duplicate
        is_duplicate = enhanced_memory.check_memory_exists(user_id, fact)
        print(f"Is duplicate? {is_duplicate}")

        if not is_duplicate:
            print("  → Adding to memory manually for testing...")
            # Manually create a memory entry to simulate agent behavior
            # This is a simplified version - in real usage, agent creates memories
            try:
                # Try to manually add memory for testing
                # NOTE: This is just for debugging, real agent handles memory creation
                import uuid

                from agno.memory.v2.memory import UserMemory

                memory_obj = UserMemory(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    memory=fact,
                    input=fact,
                    topics=["debug_topic"],
                )

                # This is a hack for testing - normally agent handles this
                if hasattr(base_memory.db, "create_user_memory"):
                    base_memory.db.create_user_memory(memory_obj)
                    print(f"  ✅ Memory added successfully")
                else:
                    print(f"  ❌ Cannot manually add memory - need agent to do it")

            except Exception as e:
                print(f"  ❌ Error adding memory: {e}")
        else:
            print("  → Skipping duplicate")

    print(f"\n📊 Final Summary:")
    final_memories = enhanced_memory.get_user_memories(user_id=user_id)
    print(f"Total memories stored: {len(final_memories)}")
    for i, mem in enumerate(final_memories, 1):
        print(f"  {i}. '{mem.memory}'")


if __name__ == "__main__":
    debug_enhanced_memory()
