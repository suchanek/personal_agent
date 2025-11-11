#!/usr/bin/env python3
"""
Simple test to verify enhanced memory fields are preserved through retrieval.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import tempfile

from agno.memory.v2 import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb

from personal_agent.core.enhanced_memory import EnhancedUserMemory
from personal_agent.core.semantic_memory_manager import SemanticMemoryManager
from personal_agent.core.user_model import User


def test_enhanced_memory_retrieval():
    """Test that enhanced fields are preserved through all retrieval methods."""

    print("🧪 Testing Enhanced Memory Retrieval")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = f"{tmpdir}/test_memory.db"
        print(f"📂 Using temporary database: {db_file}")

        # Create memory database
        db = SqliteMemoryDb(table_name="user_memories", db_file=db_file)

        # Create semantic memory manager
        memory_manager = SemanticMemoryManager()

        print("\n1️⃣ Storing memories with different confidence values...")

        # Store memory with default confidence
        result1 = memory_manager.add_memory(
            memory_text="User loves morning coffee",
            db=db,
            user_id="test_user",
            topics=["preferences", "habits"],
            confidence=0.75,  # User cognitive state
            is_proxy=False,
        )
        print(f"   ✅ Memory 1: confidence=0.75, is_proxy=False")

        # Store proxy memory
        result2 = memory_manager.add_memory(
            memory_text="User has appointment at 3pm",
            db=db,
            user_id="test_user",
            topics=["schedule"],
            confidence=1.0,  # Proxy always 1.0
            is_proxy=True,
            proxy_agent="SchedulerBot",
        )
        print(
            f"   ✅ Memory 2: confidence=1.0, is_proxy=True, proxy_agent=SchedulerBot"
        )

        # Store memory with low confidence
        result3 = memory_manager.add_memory(
            memory_text="User might prefer tea instead",
            db=db,
            user_id="test_user",
            topics=["preferences"],
            confidence=0.5,
            is_proxy=False,
        )
        print(f"   ✅ Memory 3: confidence=0.5, is_proxy=False")

        print("\n" + "=" * 60)
        print("🔍 TESTING RETRIEVAL METHODS")
        print("=" * 60)

        # Test 1: search_memories
        print("\n2️⃣ Testing search_memories()...")
        search_results = memory_manager.search_memories(
            query="coffee",
            db=db,
            user_id="test_user",
            limit=10,
            similarity_threshold=0.1,
        )

        print(f"   Found {len(search_results)} results")
        for memory, score in search_results:
            print(f"\n   📝 Memory: {memory.memory[:50]}...")
            print(f"      Similarity: {score:.3f}")
            print(f"      Confidence: {memory.confidence}")
            print(f"      Is Proxy: {memory.is_proxy}")
            print(f"      Proxy Agent: {memory.proxy_agent}")

            # Verify this is EnhancedUserMemory
            assert isinstance(
                memory, EnhancedUserMemory
            ), f"Expected EnhancedUserMemory, got {type(memory)}"
            assert hasattr(memory, "confidence"), "Missing confidence field!"
            assert hasattr(memory, "is_proxy"), "Missing is_proxy field!"
            assert hasattr(memory, "proxy_agent"), "Missing proxy_agent field!"

        # Test 2: get_all_memories
        print("\n3️⃣ Testing get_all_memories()...")
        all_memories = memory_manager.get_all_memories(
            db=db,
            user_id="test_user",
        )

        print(f"   Found {len(all_memories)} memories")
        for memory in all_memories:
            print(f"\n   📝 Memory: {memory.memory[:50]}...")
            print(f"      Confidence: {memory.confidence}")
            print(f"      Is Proxy: {memory.is_proxy}")
            print(f"      Proxy Agent: {memory.proxy_agent}")

            # Verify this is EnhancedUserMemory
            assert isinstance(
                memory, EnhancedUserMemory
            ), f"Expected EnhancedUserMemory, got {type(memory)}"
            assert hasattr(memory, "confidence"), "Missing confidence field!"
            assert hasattr(memory, "is_proxy"), "Missing is_proxy field!"
            assert hasattr(memory, "proxy_agent"), "Missing proxy_agent field!"

        # Test 3: get_memories_by_topic
        print("\n4️⃣ Testing get_memories_by_topic()...")
        topic_memories = memory_manager.get_memories_by_topic(
            db=db,
            user_id="test_user",
            topics=["preferences"],
        )

        print(f"   Found {len(topic_memories)} memories for topic 'preferences'")
        for memory in topic_memories:
            print(f"\n   📝 Memory: {memory.memory[:50]}...")
            print(f"      Confidence: {memory.confidence}")
            print(f"      Is Proxy: {memory.is_proxy}")
            print(f"      Proxy Agent: {memory.proxy_agent}")

            # Verify this is EnhancedUserMemory
            assert isinstance(
                memory, EnhancedUserMemory
            ), f"Expected EnhancedUserMemory, got {type(memory)}"
            assert hasattr(memory, "confidence"), "Missing confidence field!"
            assert hasattr(memory, "is_proxy"), "Missing is_proxy field!"
            assert hasattr(memory, "proxy_agent"), "Missing proxy_agent field!"

        # Verify specific values
        print("\n" + "=" * 60)
        print("✅ VERIFYING SPECIFIC VALUES")
        print("=" * 60)

        proxy_memory = [m for m in all_memories if m.is_proxy]
        assert (
            len(proxy_memory) == 1
        ), f"Expected 1 proxy memory, found {len(proxy_memory)}"
        assert (
            proxy_memory[0].confidence == 1.0
        ), "Proxy memory should have confidence=1.0"
        assert (
            proxy_memory[0].proxy_agent == "SchedulerBot"
        ), "Proxy agent name not preserved"
        print("   ✓ Proxy memory: confidence=1.0, proxy_agent=SchedulerBot")

        low_conf_memory = [m for m in all_memories if m.confidence == 0.5]
        assert (
            len(low_conf_memory) == 1
        ), f"Expected 1 low-confidence memory, found {len(low_conf_memory)}"
        assert not low_conf_memory[
            0
        ].is_proxy, "Low-confidence memory should not be proxy"
        print("   ✓ Low-confidence memory: confidence=0.5, is_proxy=False")

        mid_conf_memory = [m for m in all_memories if m.confidence == 0.75]
        assert (
            len(mid_conf_memory) == 1
        ), f"Expected 1 mid-confidence memory, found {len(mid_conf_memory)}"
        assert not mid_conf_memory[
            0
        ].is_proxy, "Mid-confidence memory should not be proxy"
        print("   ✓ Mid-confidence memory: confidence=0.75, is_proxy=False")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nVerified:")
        print("  ✓ search_memories() returns EnhancedUserMemory objects")
        print("  ✓ get_all_memories() returns EnhancedUserMemory objects")
        print("  ✓ get_memories_by_topic() returns EnhancedUserMemory objects")
        print("  ✓ All enhanced fields preserved (confidence, is_proxy, proxy_agent)")
        print("  ✓ Confidence values correctly stored and retrieved")
        print("  ✓ Proxy flag correctly stored and retrieved")
        print("  ✓ Proxy agent name correctly stored and retrieved")


if __name__ == "__main__":
    test_enhanced_memory_retrieval()
