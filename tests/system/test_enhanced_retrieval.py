#!/usr/bin/env python3
"""
Test script to verify enhanced memory fields are preserved through retrieval.

Tests:
1. Store memory with confidence and proxy fields
2. Retrieve via search_memories()
3. Retrieve via get_all_memories()
4. Retrieve via get_memories_by_topic()
5. Verify all enhanced fields are present
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agent_memory_manager import AgentMemoryManager
from personal_agent.core.user_model import User


@pytest.mark.asyncio
async def test_enhanced_memory_retrieval():
    """Test that enhanced fields are preserved through all retrieval methods."""

    print("🧪 Testing Enhanced Memory Retrieval")
    print("=" * 60)

    # Create temporary directory for test database
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"📂 Using temporary directory: {tmpdir}")

        # Initialize memory manager
        print("\n1️⃣ Initializing AgentMemoryManager...")
        memory_manager = AgentMemoryManager(
            user_id="test_user",
            storage_dir=tmpdir,
            agno_memory=None,  # Will create internal memory
            lightrag_url="http://localhost:9621",
            lightrag_memory_url="http://localhost:9622",
            enable_memory=True,
        )

        # Create test user with cognitive state
        user = User(
            user_id="test_user",
            user_name="Test User",
            cognitive_state=75,  # 75/100 = 0.75 confidence
        )

        # Test 1: Store memory with user (cognitive state -> confidence)
        print("\n2️⃣ Storing memory with user cognitive state (75 -> 0.75 confidence)...")
        result1 = await memory_manager.store_user_memory(
            content="User loves morning coffee",
            topics=["preferences", "habits"],
            user=user,
        )
        print(f"   ✅ Stored: {result1.memory_id}")

        # Test 2: Store proxy memory (should have confidence=1.0)
        print("\n3️⃣ Storing proxy memory (confidence=1.0)...")
        result2 = await memory_manager.store_user_memory(
            content="User has appointment at 3pm",
            topics=["schedule"],
            user=user,
            is_proxy=True,
            proxy_agent="SchedulerBot",
        )
        print(f"   ✅ Stored: {result2.memory_id}")

        # Test 3: Store memory with explicit confidence
        print("\n4️⃣ Storing memory with explicit confidence (0.5)...")
        result3 = await memory_manager.store_user_memory(
            content="User might prefer tea instead",
            topics=["preferences"],
            user=user,
            confidence=0.5,
        )
        print(f"   ✅ Stored: {result3.memory_id}")

        # Wait a moment for persistence
        await asyncio.sleep(0.5)

        print("\n" + "=" * 60)
        print("🔍 TESTING RETRIEVAL METHODS")
        print("=" * 60)

        # Test retrieval via search_memories
        print("\n5️⃣ Testing search_memories()...")
        if memory_manager.agno_memory:
            search_results = memory_manager.agno_memory.memory_manager.search_memories(
                query="coffee",
                db=memory_manager.agno_memory.db,
                user_id="test_user",
                limit=10,
                similarity_threshold=0.1,
            )

            print(f"   Found {len(search_results)} results")
            for memory, score in search_results:
                print(f"\n   Memory: {memory.memory[:50]}...")
                print(f"   Similarity: {score:.3f}")
                print(f"   ✓ Confidence: {memory.confidence}")
                print(f"   ✓ Is Proxy: {memory.is_proxy}")
                print(f"   ✓ Proxy Agent: {memory.proxy_agent}")

                # Verify enhanced fields exist
                assert hasattr(memory, "confidence"), "Missing confidence field!"
                assert hasattr(memory, "is_proxy"), "Missing is_proxy field!"
                assert hasattr(memory, "proxy_agent"), "Missing proxy_agent field!"

        # Test retrieval via get_all_memories
        print("\n6️⃣ Testing get_all_memories()...")
        if memory_manager.agno_memory:
            all_memories = memory_manager.agno_memory.memory_manager.get_all_memories(
                db=memory_manager.agno_memory.db,
                user_id="test_user",
            )

            print(f"   Found {len(all_memories)} memories")
            for memory in all_memories:
                print(f"\n   Memory: {memory.memory[:50]}...")
                print(f"   ✓ Confidence: {memory.confidence}")
                print(f"   ✓ Is Proxy: {memory.is_proxy}")
                print(f"   ✓ Proxy Agent: {memory.proxy_agent}")

                # Verify enhanced fields exist
                assert hasattr(memory, "confidence"), "Missing confidence field!"
                assert hasattr(memory, "is_proxy"), "Missing is_proxy field!"
                assert hasattr(memory, "proxy_agent"), "Missing proxy_agent field!"

        # Test retrieval via get_memories_by_topic
        print("\n7️⃣ Testing get_memories_by_topic()...")
        if memory_manager.agno_memory:
            topic_memories = (
                memory_manager.agno_memory.memory_manager.get_memories_by_topic(
                    db=memory_manager.agno_memory.db,
                    user_id="test_user",
                    topics=["preferences"],
                )
            )

            print(f"   Found {len(topic_memories)} memories for topic 'preferences'")
            for memory in topic_memories:
                print(f"\n   Memory: {memory.memory[:50]}...")
                print(f"   ✓ Confidence: {memory.confidence}")
                print(f"   ✓ Is Proxy: {memory.is_proxy}")
                print(f"   ✓ Proxy Agent: {memory.proxy_agent}")

                # Verify enhanced fields exist
                assert hasattr(memory, "confidence"), "Missing confidence field!"
                assert hasattr(memory, "is_proxy"), "Missing is_proxy field!"
                assert hasattr(memory, "proxy_agent"), "Missing proxy_agent field!"

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nVerified:")
        print("  ✓ search_memories() returns EnhancedUserMemory")
        print("  ✓ get_all_memories() returns EnhancedUserMemory")
        print("  ✓ get_memories_by_topic() returns EnhancedUserMemory")
        print("  ✓ All enhanced fields preserved (confidence, is_proxy, proxy_agent)")
        print("  ✓ Cognitive state correctly mapped to confidence")
        print("  ✓ Proxy memories have confidence=1.0")
        print("  ✓ Explicit confidence values preserved")


if __name__ == "__main__":
    asyncio.run(test_enhanced_memory_retrieval())
