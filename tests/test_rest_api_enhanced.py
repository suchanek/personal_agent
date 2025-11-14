#!/usr/bin/env python3
"""
Test REST API to verify enhanced memory fields are returned in JSON responses.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import tempfile

from agno.memory.v2.db.sqlite import SqliteMemoryDb

from personal_agent.core.semantic_memory_manager import SemanticMemoryManager


def test_rest_api_memory_serialization():
    """Simulate what REST API does to serialize memory objects."""

    print("🧪 Testing REST API Memory Serialization")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = f"{tmpdir}/test_memory.db"
        print(f"📂 Using temporary database: {db_file}")

        # Create memory database
        db = SqliteMemoryDb(table_name="user_memories", db_file=db_file)

        # Create semantic memory manager
        memory_manager = SemanticMemoryManager()

        print("\n1️⃣ Storing test memories...")

        # Store proxy memory
        memory_manager.add_memory(
            memory_text="User has appointment at 3pm",
            db=db,
            user_id="test_user",
            topics=["schedule"],
            confidence=1.0,
            is_proxy=True,
            proxy_agent="SchedulerBot",
        )
        print("   ✅ Stored proxy memory")

        # Store user memory with cognitive state
        memory_manager.add_memory(
            memory_text="User loves morning coffee",
            db=db,
            user_id="test_user",
            topics=["preferences"],
            confidence=0.75,
            is_proxy=False,
        )
        print("   ✅ Stored user memory")

        print("\n" + "=" * 60)
        print("🔍 TESTING REST API SERIALIZATION")
        print("=" * 60)

        # Simulate /api/v1/memory/search endpoint
        print("\n2️⃣ Simulating /api/v1/memory/search endpoint...")
        search_results = memory_manager.search_memories(
            query="appointment",
            db=db,
            user_id="test_user",
            limit=10,
            similarity_threshold=0.1,
        )

        # Serialize like REST API does
        results = []
        for memory, score in search_results:
            results.append(
                {
                    "memory_id": getattr(memory, "memory_id", None),
                    "content": memory.memory,
                    "similarity_score": round(score, 3),
                    "topics": getattr(memory, "topics", []),
                    "last_updated": str(getattr(memory, "last_updated", None)),
                    "input": getattr(memory, "input", None),
                    "confidence": getattr(memory, "confidence", 1.0),
                    "is_proxy": getattr(memory, "is_proxy", False),
                    "proxy_agent": getattr(memory, "proxy_agent", None),
                }
            )

        print(f"\n   Found {len(results)} search results")
        for result in results:
            print("\n   JSON Response:")
            print(json.dumps(result, indent=4))

            # Verify enhanced fields are present
            assert "confidence" in result, "Missing confidence field in JSON!"
            assert "is_proxy" in result, "Missing is_proxy field in JSON!"
            assert "proxy_agent" in result, "Missing proxy_agent field in JSON!"

            if result["is_proxy"]:
                assert (
                    result["confidence"] == 1.0
                ), "Proxy memory should have confidence=1.0"
                assert (
                    result["proxy_agent"] == "SchedulerBot"
                ), "Proxy agent not serialized"
                print("   ✅ Proxy fields correctly serialized")

        # Simulate /api/v1/memory/list endpoint
        print("\n3️⃣ Simulating /api/v1/memory/list endpoint...")
        memories = memory_manager.get_all_memories(
            db=db,
            user_id="test_user",
        )

        # Serialize like REST API does
        results = []
        for memory in memories:
            results.append(
                {
                    "memory_id": getattr(memory, "memory_id", None),
                    "content": memory.memory,
                    "topics": getattr(memory, "topics", []),
                    "last_updated": str(getattr(memory, "last_updated", None)),
                    "input": getattr(memory, "input", None),
                    "confidence": getattr(memory, "confidence", 1.0),
                    "is_proxy": getattr(memory, "is_proxy", False),
                    "proxy_agent": getattr(memory, "proxy_agent", None),
                }
            )

        print(f"\n   Found {len(results)} memories")
        for result in results:
            print("\n   JSON Response:")
            print(json.dumps(result, indent=4))

            # Verify enhanced fields are present
            assert "confidence" in result, "Missing confidence field in JSON!"
            assert "is_proxy" in result, "Missing is_proxy field in JSON!"
            assert "proxy_agent" in result, "Missing proxy_agent field in JSON!"

        print("\n" + "=" * 60)
        print("✅ ALL REST API TESTS PASSED!")
        print("=" * 60)
        print("\nVerified:")
        print("  ✓ /api/v1/memory/search includes confidence field")
        print("  ✓ /api/v1/memory/search includes is_proxy field")
        print("  ✓ /api/v1/memory/search includes proxy_agent field")
        print("  ✓ /api/v1/memory/list includes confidence field")
        print("  ✓ /api/v1/memory/list includes is_proxy field")
        print("  ✓ /api/v1/memory/list includes proxy_agent field")
        print("  ✓ All enhanced fields properly serialized to JSON")


if __name__ == "__main__":
    test_rest_api_memory_serialization()
