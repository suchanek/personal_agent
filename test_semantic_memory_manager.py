#!/usr/bin/env python3
"""
Test script for the Semantic Memory Manager.

This script demonstrates the capabilities of the new semantic memory manager
that provides LLM-free memory management with semantic search and duplicate detection.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.memory.v2.db.sqlite import SqliteMemoryDb

from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.semantic_memory_manager import create_semantic_memory_manager


def test_semantic_memory_manager():
    """Test the semantic memory manager functionality."""
    print("🧠 Testing Semantic Memory Manager")
    print("=" * 60)

    # Create database connection
    db_path = Path(AGNO_STORAGE_DIR) / "test_semantic_memory.db"
    print(f"📂 Database: {db_path}")

    # Remove existing test database
    if db_path.exists():
        db_path.unlink()
        print("🗑️  Removed existing test database")

    memory_db = SqliteMemoryDb(
        table_name="test_semantic_memory",
        db_file=str(db_path),
    )

    # Create SemanticMemoryManager instance
    manager = create_semantic_memory_manager(
        similarity_threshold=0.8,
        debug_mode=True,
    )

    print(f"\n✅ Created SemanticMemoryManager with config:")
    print(f"   - Similarity threshold: {manager.config.similarity_threshold}")
    print(f"   - Semantic dedup: {manager.config.enable_semantic_dedup}")
    print(f"   - Exact dedup: {manager.config.enable_exact_dedup}")
    print(f"   - Topic classification: {manager.config.enable_topic_classification}")

    # Test 1: Basic memory addition
    print(f"\n" + "=" * 60)
    print("TEST 1: Basic Memory Addition")
    print("=" * 60)

    test_memories = [
        "My name is Alice Johnson",
        "I work as a data scientist at TechCorp",
        "I live in Seattle, Washington",
        "I love hiking and mountain biking",
        "My favorite programming language is Python",
        "I have a cat named Whiskers",
    ]

    for i, memory_text in enumerate(test_memories, 1):
        print(f"\n--- Adding memory {i}: {memory_text}")
        success, message, memory_id = manager.add_memory(
            memory_text, memory_db, USER_ID
        )

        if success:
            print(f"✅ Added successfully (ID: {memory_id})")
        else:
            print(f"❌ Failed: {message}")

    # Test 2: Duplicate detection
    print(f"\n" + "=" * 60)
    print("TEST 2: Duplicate Detection")
    print("=" * 60)

    duplicate_tests = [
        "My name is Alice Johnson",  # Exact duplicate
        "I work as a data scientist at TechCorp",  # Exact duplicate
        "I'm a data scientist working at TechCorp",  # Semantic duplicate
        "I live in Seattle, WA",  # Semantic duplicate
        "I enjoy hiking and biking in the mountains",  # Semantic duplicate
        "I have a dog named Rex",  # Different but similar structure
    ]

    for i, memory_text in enumerate(duplicate_tests, 1):
        print(f"\n--- Testing duplicate {i}: {memory_text}")
        success, message, memory_id = manager.add_memory(
            memory_text, memory_db, USER_ID
        )

        if success:
            print(f"✅ Added successfully (ID: {memory_id})")
        else:
            print(f"🚫 Rejected: {message}")

    # Test 3: Topic classification
    print(f"\n" + "=" * 60)
    print("TEST 3: Topic Classification")
    print("=" * 60)

    topic_test_inputs = [
        "I graduated from Stanford University with a computer science degree",
        "I'm married to John and we have two kids",
        "I prefer tea over coffee in the morning",
        "I go to the gym three times a week",
        "My goal is to become a machine learning engineer",
    ]

    for i, input_text in enumerate(topic_test_inputs, 1):
        print(f"\n--- Topic test {i}: {input_text}")
        topics = manager.topic_classifier.classify_topic(input_text)
        print(f"    Classified topics: {topics}")

        success, message, memory_id = manager.add_memory(input_text, memory_db, USER_ID)
        if success:
            print(f"✅ Added with topics: {topics}")
        else:
            print(f"🚫 Rejected: {message}")

    # Test 4: Input processing
    print(f"\n" + "=" * 60)
    print("TEST 4: Input Processing")
    print("=" * 60)

    complex_inputs = [
        "Hi there! My name is Bob Smith and I work as a software engineer. I live in Portland and I love playing guitar.",
        "I have been working at Microsoft for 5 years. I really enjoy my job and my colleagues are great.",
        "Yesterday I went hiking with my friends. We had a great time exploring the trails.",
    ]

    for i, input_text in enumerate(complex_inputs, 1):
        print(f"\n--- Processing input {i}: {input_text}")
        result = manager.process_input(input_text, memory_db, USER_ID)

        print(f"✅ Processing result:")
        print(f"   Success: {result['success']}")
        print(f"   Total processed: {result['total_processed']}")
        print(f"   Added: {len(result['memories_added'])}")
        print(f"   Rejected: {len(result['memories_rejected'])}")

        for memory in result["memories_added"]:
            print(f"   📝 Added: '{memory['memory']}' (topics: {memory['topics']})")

        for rejection in result["memories_rejected"]:
            print(f"   🚫 Rejected: '{rejection['memory']}' - {rejection['reason']}")

    # Test 5: Memory search
    print(f"\n" + "=" * 60)
    print("TEST 5: Memory Search")
    print("=" * 60)

    search_queries = [
        "software engineer",
        "Seattle",
        "Python programming",
        "hiking",
        "university degree",
    ]

    for query in search_queries:
        print(f"\n--- Searching for: '{query}'")
        results = manager.search_memories(query, memory_db, USER_ID, limit=3)

        if results:
            print(f"   Found {len(results)} results:")
            for memory, similarity in results:
                print(
                    f"   📋 {similarity:.3f}: '{memory.memory}' (topics: {memory.topics})"
                )
        else:
            print("   No results found")

    # Test 6: Memory statistics
    print(f"\n" + "=" * 60)
    print("TEST 6: Memory Statistics")
    print("=" * 60)

    stats = manager.get_memory_stats(memory_db, USER_ID)

    print(f"📊 Memory Statistics:")
    for key, value in stats.items():
        if key == "topic_distribution" and isinstance(value, dict):
            print(f"   {key}:")
            for topic, count in sorted(value.items(), key=lambda x: x[1], reverse=True):
                print(f"     - {topic}: {count}")
        else:
            print(f"   {key}: {value}")

    # Test 7: Semantic similarity demonstration
    print(f"\n" + "=" * 60)
    print("TEST 7: Semantic Similarity Demonstration")
    print("=" * 60)

    similarity_tests = [
        ("I work as a software engineer", "I'm a software developer"),
        ("I live in San Francisco", "I reside in SF"),
        ("I love hiking", "I enjoy mountain climbing"),
        ("My favorite color is blue", "I prefer the color red"),
    ]

    for text1, text2 in similarity_tests:
        similarity = manager.duplicate_detector._calculate_semantic_similarity(
            text1, text2
        )
        print(f"   '{text1}' vs '{text2}': {similarity:.3f}")

    print(f"\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

    # Cleanup
    print(f"\n🧹 Cleaning up test database...")
    if db_path.exists():
        db_path.unlink()
        print("✅ Test database removed")


if __name__ == "__main__":
    test_semantic_memory_manager()
