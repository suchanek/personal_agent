#!/usr/bin/env python3
"""
Debug script to analyze why duplicate detection isn't working properly.
"""

from src.personal_agent.config import LLM_MODEL, OLLAMA_URL
from src.personal_agent.core.agno_storage import (
    EnhancedMemory,
    clear_agno_database_completely,
    create_agno_memory,
)
from src.personal_agent.utils import setup_logging

logger = setup_logging(__name__)


def test_duplicate_detection():
    """Test duplicate detection logic step by step."""
    print("🔍 Debugging Duplicate Detection")
    print("=" * 50)

    # Clear existing data
    print("\n🗑️  Clearing existing data...")
    clear_agno_database_completely()

    # Create memory
    base_memory = create_agno_memory()
    enhanced_memory = EnhancedMemory(base_memory, similarity_threshold=0.8)

    user_id = "debug_user"

    # Test facts with clear duplicates
    test_facts = [
        "My name is Alice",
        "My name is Alice",  # Exact duplicate
        "My name is Bob",
        "I am called Bob",  # Similar to Bob
        "My favorite color is blue",
        "I like the color blue",  # Similar
    ]

    print(f"\n📝 Testing duplicate detection with {len(test_facts)} facts:")

    for i, fact in enumerate(test_facts, 1):
        print(f"\n--- Fact {i}: '{fact}' ---")

        # Check current memories
        current_memories = enhanced_memory.get_user_memories(user_id=user_id)
        print(f"Current memories in DB: {len(current_memories)}")

        if current_memories:
            print("Existing memories:")
            for j, mem in enumerate(current_memories):
                print(f"  {j+1}. '{mem.memory}'")

        # Test duplicate detection
        is_duplicate = enhanced_memory.check_memory_exists(user_id, fact)
        should_create = enhanced_memory.should_create_memory(user_id, fact)

        print(f"Duplicate check result: {is_duplicate}")
        print(f"Should create memory: {should_create}")

        if not is_duplicate:
            print("✅ Adding as unique memory")
            # Manually add to memory for testing (simulating agent behavior)
            # Note: In real usage, agent creates memories automatically
            try:
                # Try to add memory directly if possible
                if hasattr(enhanced_memory._memory, "_add_memory"):
                    enhanced_memory._memory._add_memory(user_id=user_id, memory=fact)
                else:
                    # Simulate memory creation by adding to the underlying DB
                    print(
                        f"⚠️  Cannot directly add memory - would need agent interaction"
                    )
            except Exception as e:
                print(f"⚠️  Error adding memory: {e}")
        else:
            print("⏭️  Skipping duplicate")
            # Show which memory it's similar to
            for mem in current_memories:
                fact_words = set(fact.lower().split())
                existing_words = set(mem.memory.lower().split())
                if len(fact_words) > 0 and len(existing_words) > 0:
                    intersection = fact_words.intersection(existing_words)
                    union = fact_words.union(existing_words)
                    similarity = len(intersection) / len(union)
                    if similarity >= enhanced_memory.similarity_threshold:
                        print(
                            f"🔗 Similar to: '{mem.memory}' (similarity: {similarity:.2f})"
                        )
                        break

    print(f"\n📊 Final Summary:")
    final_memories = enhanced_memory.get_user_memories(user_id=user_id)
    print(f"Total memories stored: {len(final_memories)}")
    print(f"Expected: {len(set(test_facts))} unique memories")


def test_jaccard_similarity():
    """Test the Jaccard similarity calculation directly."""
    print("\n🧮 Testing Jaccard Similarity Calculation")
    print("=" * 50)

    test_pairs = [
        ("My name is Alice", "My name is Alice"),  # Exact match
        ("My name is Alice", "My name is Bob"),  # Different names
        ("My name is Alice", "I am called Alice"),  # Similar but different words
        ("I live in Seattle", "I live in Seattle, WA"),  # Similar
        ("I have a cat named Whiskers", "I have a pet cat called Whiskers"),  # Similar
    ]

    for text1, text2 in test_pairs:
        print(f"\nComparing:")
        print(f"  Text 1: '{text1}'")
        print(f"  Text 2: '{text2}'")

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        print(f"  Words 1: {words1}")
        print(f"  Words 2: {words2}")

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        print(f"  Intersection: {intersection}")
        print(f"  Union: {union}")

        if len(union) > 0:
            similarity = len(intersection) / len(union)
            print(f"  Jaccard similarity: {similarity:.3f}")

            # Test different thresholds
            for threshold in [0.5, 0.7, 0.8]:
                is_duplicate = similarity >= threshold
                print(
                    f"  Threshold {threshold}: {'DUPLICATE' if is_duplicate else 'UNIQUE'}"
                )
        else:
            print(f"  Jaccard similarity: undefined (empty union)")


if __name__ == "__main__":
    test_jaccard_similarity()
    test_duplicate_detection()
