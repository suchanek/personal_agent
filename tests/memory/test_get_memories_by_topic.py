#!/usr/bin/env python3
"""
Test script for the get_memories_by_topic function in Semantic Memory Manager.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.semantic_memory_manager import create_semantic_memory_manager


@pytest.fixture
def db_path():
    """Fixture for test database path."""
    path = Path(AGNO_STORAGE_DIR) / "test_topic_search.db"
    # Remove existing test database
    if path.exists():
        path.unlink()
    yield path
    # Cleanup after test
    if path.exists():
        path.unlink()


@pytest.fixture
def memory_db(db_path):
    """Fixture for memory database."""
    return SqliteMemoryDb(
        table_name="test_topic_search",
        db_file=str(db_path),
    )


@pytest.fixture
def manager():
    """Fixture for SemanticMemoryManager."""
    return create_semantic_memory_manager(
        similarity_threshold=0.95,  # High threshold to avoid false positives
        debug_mode=True,
    )


@pytest.fixture
def test_memories():
    """Fixture for test memory data."""
    return [
        ("I work as a software engineer at a large tech company.", ["work", "career"]),
        ("My favorite hobby is playing the guitar.", ["personal", "hobbies"]),
        ("I studied computer science at Stanford University.", ["education", "university"]),
        ("I am proficient in Python, Java, and C++.", ["work", "skills"]),
        ("I enjoy hiking in the mountains on weekends.", ["hobbies", "personal"]),
        ("I'm learning to speak Spanish.", ["personal", "learning"]),
        ("My first job was as a web developer.", ["work", "career"]),
        ("I have a degree in electrical engineering.", ["education", "degree"]),
    ]


def test_get_memories_by_single_topic(manager, memory_db, test_memories):
    """Test getting memories for a single topic."""
    print("\n🧠 Testing get_memories_by_topic - Single Topic")
    print("=" * 60)

    # Add test memories
    print("--- Adding test memories ---")
    for memory_text, topics in test_memories:
        result = manager.add_memory(
            memory_text, memory_db, USER_ID, topics=topics
        )
        if result.is_success:
            print(f"✅ Added: '{memory_text[:40]}...' (Topics: {topics})")
        else:
            print(f"❌ Failed to add memory: {result.message}")
            # If adding fails, we should stop the test
            assert result.is_success, f"Failed to add memory: {result.message}"
    # Get memories for a single topic
    print("\n--- Get memories for topic 'work' ---")
    work_memories = manager.get_memories_by_topic(memory_db, USER_ID, topics=["work"])
    assert len(work_memories) == 3
    assert all(mem.topics and "work" in mem.topics for mem in work_memories)
    print(f"✅ Found {len(work_memories)} memories for topic 'work'.")
    for mem in work_memories:
        print(f"   - '{mem.memory}'")

def test_get_memories_by_multiple_topics(manager, memory_db, test_memories):
    """Test getting memories for multiple topics."""
    print("\n🧠 Testing get_memories_by_topic - Multiple Topics")
    print("=" * 60)
    
    # Add test memories
    print("--- Adding test memories ---")
    for memory_text, topics in test_memories:
        result = manager.add_memory(
            memory_text, memory_db, USER_ID, topics=topics
        )
        assert result.is_success, f"Failed to add memory: {result.message}"
    
    # Get memories for multiple topics
    print("\n--- Get memories for topics 'hobbies' and 'education' ---")
    hobby_edu_memories = manager.get_memories_by_topic(
        memory_db, USER_ID, topics=["hobbies", "education"]
    )
    assert len(hobby_edu_memories) == 4
    print(f"✅ Found {len(hobby_edu_memories)} memories for topics 'hobbies' or 'education'.")
    for mem in hobby_edu_memories:
        print(f"   - '{mem.memory}' (Topics: {mem.topics})")

def test_get_all_memories(manager, memory_db, test_memories):
    """Test getting all memories when topics is None."""
    print("\n🧠 Testing get_memories_by_topic - All Memories")
    print("=" * 60)
    
    # Add test memories
    print("--- Adding test memories ---")
    for memory_text, topics in test_memories:
        result = manager.add_memory(
            memory_text, memory_db, USER_ID, topics=topics
        )
        assert result.is_success, f"Failed to add memory: {result.message}"
    
    # Get all memories
    print("\n--- Get all memories (topics=None) ---")
    all_memories = manager.get_memories_by_topic(memory_db, USER_ID, topics=None)
    assert len(all_memories) == len(test_memories)
    print(f"✅ Found all {len(all_memories)} memories.")

def test_get_memories_with_limit(manager, memory_db, test_memories):
    """Test getting memories with a limit."""
    print("\n🧠 Testing get_memories_by_topic - With Limit")
    print("=" * 60)
    
    # Add test memories
    print("--- Adding test memories ---")
    for memory_text, topics in test_memories:
        result = manager.add_memory(
            memory_text, memory_db, USER_ID, topics=topics
        )
        assert result.is_success, f"Failed to add memory: {result.message}"
    
    # Get memories with limit
    print("\n--- Get all memories with limit=3 ---")
    limited_memories = manager.get_memories_by_topic(
        memory_db, USER_ID, topics=None, limit=3
    )
    assert len(limited_memories) == 3
    print(f"✅ Correctly found {len(limited_memories)} memories with limit=3.")

def test_get_memories_nonexistent_topic(manager, memory_db, test_memories):
    """Test getting memories for a non-existent topic."""
    print("\n🧠 Testing get_memories_by_topic - Non-existent Topic")
    print("=" * 60)
    
    # Add test memories
    print("--- Adding test memories ---")
    for memory_text, topics in test_memories:
        result = manager.add_memory(
            memory_text, memory_db, USER_ID, topics=topics
        )
        assert result.is_success, f"Failed to add memory: {result.message}"
    
    # Get memories for non-existent topic
    print("\n--- Get memories for topic 'finance' ---")
    finance_memories = manager.get_memories_by_topic(
        memory_db, USER_ID, topics=["finance"]
    )
    assert len(finance_memories) == 0
    print("✅ Correctly found 0 memories for topic 'finance'.")
    
def test_case_insensitive_topic_search(manager, memory_db, test_memories):
    """Test case-insensitive topic search."""
    print("\n🧠 Testing get_memories_by_topic - Case Insensitive")
    print("=" * 60)
    
    # Add test memories
    print("--- Adding test memories ---")
    for memory_text, topics in test_memories:
        result = manager.add_memory(
            memory_text, memory_db, USER_ID, topics=topics
        )
        assert result.is_success, f"Failed to add memory: {result.message}"
    
    # Case-insensitive search
    print("\n--- Get memories for topic 'WORK' (uppercase) ---")
    work_memories_upper = manager.get_memories_by_topic(memory_db, USER_ID, topics=["WORK"])
    assert len(work_memories_upper) == 3
    print(f"✅ Found {len(work_memories_upper)} memories for topic 'WORK' (case-insensitive).")


def test_auto_topic_generation(manager, test_memories):
    """Test auto-topic generation and question presentation."""
    print("\n🧠 Testing Auto-Topic Generation")
    print("=" * 60)
    
    # Create fresh database for this test
    db_path_auto = Path(AGNO_STORAGE_DIR) / "test_topic_search_auto.db"
    if db_path_auto.exists():
        db_path_auto.unlink()
    
    memory_db_auto = SqliteMemoryDb(
        table_name="test_topic_search_auto",
        db_file=str(db_path_auto),
    )
    
    print("--- Adding memories and generating topics automatically ---")
    all_generated_topics = set()
    test_facts = [memory[0] for memory in test_memories]

    for memory_text in test_facts:
        result = manager.add_memory(
            memory_text, memory_db_auto, USER_ID, topics=None
        )
        if result.is_success:
            print(f"✅ Added: '{memory_text[:40]}...' -> Topics: {result.topics}")
            if result.topics:
                all_generated_topics.update(result.topics)
        else:
            print(f"❌ Failed to add memory: {result.message}")
            assert result.is_success, f"Failed to add memory: {result.message}"
    print("\n--- Questions Based on Generated Topics ---")
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
    
    # Cleanup
    if db_path_auto.exists():
        db_path_auto.unlink()