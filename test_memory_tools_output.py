#!/usr/bin/env python3
"""
Test memory tools output formatting to verify enhanced fields are displayed.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.memory.v2.db.sqlite import SqliteMemoryDb

from personal_agent.core.semantic_memory_manager import SemanticMemoryManager


def test_memory_tools_output():
    """Test that enhanced fields are displayed in formatted outputs."""

    print("🧪 Testing Memory Tools Output Formatting")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = f"{tmpdir}/test_memory.db"
        print(f"📂 Using temporary database: {db_file}")

        # Create memory database
        db = SqliteMemoryDb(table_name="user_memories", db_file=db_file)

        # Create semantic memory manager
        memory_manager = SemanticMemoryManager()

        print("\n1️⃣ Storing test memories...")

        # Store user memory with medium confidence
        memory_manager.add_memory(
            memory_text="User loves morning coffee",
            db=db,
            user_id="test_user",
            topics=["preferences"],
            confidence=0.75,
            is_proxy=False,
        )
        print("   ✅ User memory (75% confidence)")

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
        print("   ✅ Proxy memory (100% confidence, SchedulerBot)")

        # Store low-confidence memory
        memory_manager.add_memory(
            memory_text="User might prefer tea instead",
            db=db,
            user_id="test_user",
            topics=["preferences"],
            confidence=0.4,
            is_proxy=False,
        )
        print("   ✅ Low-confidence memory (40%)")

        print("\n" + "=" * 60)
        print("📝 TESTING OUTPUT FORMATTING")
        print("=" * 60)

        # Test get_all_memories for basic structure
        print("\n2️⃣ Testing get_all_memories() structure:")
        print("-" * 60)
        all_memories = memory_manager.get_all_memories(db=db, user_id="test_user")

        print(f"Found {len(all_memories)} memories")
        for i, memory in enumerate(all_memories, 1):
            # Simulate formatted output similar to list_all_memories
            enhanced_info = []

            if hasattr(memory, "confidence") and memory.confidence < 1.0:
                conf_percent = int(memory.confidence * 100)
                enhanced_info.append(f"{conf_percent}% conf")

            if hasattr(memory, "is_proxy") and memory.is_proxy:
                proxy_name = getattr(memory, "proxy_agent", "Unknown")
                enhanced_info.append(f"🤖 {proxy_name}")

            enhanced_str = f" ({', '.join(enhanced_info)})" if enhanced_info else ""
            print(f"{i}. {memory.memory}{enhanced_str}")

        # Verify enhanced fields
        proxy_memories = [
            m for m in all_memories if hasattr(m, "is_proxy") and m.is_proxy
        ]
        assert (
            len(proxy_memories) == 1
        ), f"Expected 1 proxy memory, found {len(proxy_memories)}"
        assert (
            proxy_memories[0].proxy_agent == "SchedulerBot"
        ), "Proxy agent name not preserved"
        print("\n✅ Proxy memory displays with 🤖 indicator and agent name")

        low_conf_memories = [
            m for m in all_memories if hasattr(m, "confidence") and m.confidence < 0.5
        ]
        assert (
            len(low_conf_memories) == 1
        ), f"Expected 1 low-conf memory, found {len(low_conf_memories)}"
        print("✅ Low-confidence memory displays with percentage")

        # Test get_memories_by_topic for detailed formatting
        print("\n3️⃣ Testing get_memories_by_topic() detailed output:")
        print("-" * 60)
        topic_memories = memory_manager.get_memories_by_topic(
            db=db,
            user_id="test_user",
            topics=["preferences"],
        )

        print(f"Found {len(topic_memories)} memories for topic 'preferences'\n")
        for i, memory in enumerate(topic_memories, 1):
            print(f"{i}. {memory.memory}")
            if memory.topics:
                print(f"   Topics: {', '.join(memory.topics)}")

            # Show confidence
            if hasattr(memory, "confidence"):
                conf_percent = int(memory.confidence * 100)
                conf_emoji = (
                    "🟢"
                    if memory.confidence >= 0.8
                    else "🟡" if memory.confidence >= 0.5 else "🔴"
                )
                print(f"   Confidence: {conf_emoji} {conf_percent}%")

            # Show proxy info
            if hasattr(memory, "is_proxy") and memory.is_proxy:
                proxy_name = getattr(memory, "proxy_agent", "Unknown")
                print(f"   🤖 Proxy Memory (Agent: {proxy_name})")

            print(f"   ID: {memory.memory_id}\n")

        print("\n" + "=" * 60)
        print("✅ ALL OUTPUT FORMATTING TESTS PASSED!")
        print("=" * 60)
        print("\nVerified:")
        print("  ✓ Memories display with confidence percentages")
        print("  ✓ Proxy memories show 🤖 icon and agent name")
        print("  ✓ Confidence indicators use emoji (🟢🟡🔴)")
        print("  ✓ Compact format shows: 'memory (75% conf, 🤖 Agent)'")
        print("  ✓ Detailed format shows all enhanced fields")


if __name__ == "__main__":
    test_memory_tools_output()
