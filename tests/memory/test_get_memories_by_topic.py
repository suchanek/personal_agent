#!/usr/bin/env python3
"""
Test script for the get_memories_by_topic function in Semantic Memory Manager.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.semantic_memory_manager import create_semantic_memory_manager

def test_get_memories_by_topic():
    """Test the get_memories_by_topic functionality."""
    print("🧠 Testing get_memories_by_topic")
    print("=" * 60)

    # Create database connection
    db_path = Path(AGNO_STORAGE_DIR) / "test_topic_search.db"
    print(f"📂 Database: {db_path}")

    # Remove existing test database
    if db_path.exists():
        db_path.unlink()
        print("🗑️  Removed existing test database")

    memory_db = SqliteMemoryDb(
        table_name="test_topic_search",
        db_file=str(db_path),
    )

    # Create SemanticMemoryManager instance
    manager = create_semantic_memory_manager(
        similarity_threshold=0.95,  # High threshold to avoid false positives
        debug_mode=True,
    )

    # Test Data
    test_memories = [
        ("I work as a software engineer at a large tech company.", ["work", "career"]),
        ("My favorite hobby is playing the guitar.", ["personal", "hobbies"]),
        ("I studied computer science at Stanford University.", ["education", "university"]),
        ("I am proficient in Python, Java, and C++.", ["work", "skills"]),
        ("I enjoy hiking in the mountains on weekends.", ["hobbies", "personal"]),
        ("I'm learning to speak Spanish.", ["personal", "learning"]),
        ("My first job was as a web developer.", ["work", "career"]),
        ("I have a degree in electrical engineering.", ["education", "degree"]),
    ]

    print("\n--- Adding test memories ---")
    for memory_text, topics in test_memories:
        success, message, memory_id, _ = manager.add_memory(
            memory_text, memory_db, USER_ID, topics=topics
        )
        if success:
            print(f"✅ Added: '{memory_text[:40]}...' (Topics: {topics})")
        else:
            print(f"❌ Failed to add memory: {message}")
            # If adding fails, we should stop the test
            assert success, f"Failed to add memory: {message}"
    print("-" * 30)

    # Test 1: Get memories for a single topic
    print("\nTEST 1: Get memories for a single topic ('work')")
    work_memories = manager.get_memories_by_topic(memory_db, USER_ID, topics=["work"])
    assert len(work_memories) == 3
    assert all("work" in mem.topics for mem in work_memories)
    print(f"✅ Found {len(work_memories)} memories for topic 'work'.")
    for mem in work_memories:
        print(f"   - '{mem.memory}'")

    # Test 2: Get memories for multiple topics
    print("\nTEST 2: Get memories for multiple topics (['hobbies', 'education'])")
    hobby_edu_memories = manager.get_memories_by_topic(
        memory_db, USER_ID, topics=["hobbies", "education"]
    )
    assert len(hobby_edu_memories) == 4
    print(f"✅ Found {len(hobby_edu_memories)} memories for topics 'hobbies' or 'education'.")
    for mem in hobby_edu_memories:
        print(f"   - '{mem.memory}' (Topics: {mem.topics})")

    # Test 3: Get all memories when topics is None
    print("\nTEST 3: Get all memories (topics=None)")
    all_memories = manager.get_memories_by_topic(memory_db, USER_ID, topics=None)
    assert len(all_memories) == len(test_memories)
    print(f"✅ Found all {len(all_memories)} memories.")

    # Test 4: Get memories with a limit
    print("\nTEST 4: Get all memories with a limit of 3")
    limited_memories = manager.get_memories_by_topic(
        memory_db, USER_ID, topics=None, limit=3
    )
    assert len(limited_memories) == 3
    print(f"✅ Correctly found {len(limited_memories)} memories with limit=3.")

    # Test 5: Get memories for a topic with no entries
    print("\nTEST 5: Get memories for a non-existent topic ('finance')")
    finance_memories = manager.get_memories_by_topic(
        memory_db, USER_ID, topics=["finance"]
    )
    assert len(finance_memories) == 0
    print("✅ Correctly found 0 memories for topic 'finance'.")
    
    # Test 6: Case-insensitivity of topic search
    print("\nTEST 6: Case-insensitive topic search ('WORK')")
    work_memories_upper = manager.get_memories_by_topic(memory_db, USER_ID, topics=["WORK"])
    assert len(work_memories_upper) == 3
    print(f"✅ Found {len(work_memories_upper)} memories for topic 'WORK' (case-insensitive).")


    # Test 7: Auto-topic generation and question presentation
    print("\n" + "=" * 60)
    print("🧠 TEST 7: Auto-Topic Generation and Question Presentation")
    print("=" * 60)

    # Clear the database for a fresh start
    print("\n--- Clearing database for auto-topic test leg ---")
    # we need to close the previous connection before deleting the file
    del memory_db
    if db_path.exists():
        db_path.unlink()
        print("🗑️  Removed existing test database")

    memory_db_auto = SqliteMemoryDb(
        table_name="test_topic_search_auto",
        db_file=str(db_path),
    )
    print("✅ Database cleared and re-initialized.")

    print("\n--- Adding memories and generating topics automatically ---")
    all_generated_topics = set()
    test_facts = [memory[0] for memory in test_memories]

    for memory_text in test_facts:
        success, message, _, generated_topics = manager.add_memory(
            memory_text, memory_db_auto, USER_ID, topics=None
        )
        if success:
            print(f"✅ Added: '{memory_text[:40]}...' -> Topics: {generated_topics}")
            if generated_topics:
                all_generated_topics.update(generated_topics)
        else:
            print(f"❌ Failed to add memory: {message}")
            assert success, f"Failed to add memory: {message}"
    print("-" * 30)

    print("\n--- List of Questions Based on Generated Topics ---")
    if all_generated_topics:
        sorted_topics = sorted(list(all_generated_topics))
        for topic in sorted_topics:
            print(f"❓ What do you know about '{topic}'?")
            retrieved_mems = manager.get_memories_by_topic(
                memory_db_auto, USER_ID, topics=[topic]
            )
            if retrieved_mems:
                for mem in retrieved_mems:
                    print(f"   - '{mem.memory}' (Topics: {mem.topics})")
            else:
                print(f"   - No memories found for topic '{topic}'.")
    else:
        print("No topics were generated.")
    print("-" * 30)


    print(f"\n" + "=" * 60)
    print("✅ All tests for get_memories_by_topic completed successfully!")
    print("=" * 60)

    # Cleanup
    print(f"\n🧹 Cleaning up test database...")
    if db_path.exists():
        db_path.unlink()
        print("✅ Test database removed")


if __name__ == "__main__":
    test_get_memories_by_topic()