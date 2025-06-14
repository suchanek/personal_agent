#!/usr/bin/env python3
"""
Simple Memory Duplication Test for Ollama Models.

This script focuses specifically on the duplication issue by testing
memory creation in a controlled way.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from rich import print
from rich.console import Console

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, USER_ID


async def test_memory_duplication():
    """Test memory creation to identify duplication issues."""
    print("🔍 Testing Memory Duplication Issues")
    print("=" * 50)

    # Create fresh memory database
    memory_db = SqliteMemoryDb(
        table_name="duplication_test", db_file=f"{AGNO_STORAGE_DIR}/duplication_test.db"
    )

    # Clear any existing data
    memory_db.clear()

    # Create memory instance
    memory = Memory(db=memory_db, model=Ollama(id=LLM_MODEL))

    # Create agent with minimal configuration
    agent = Agent(
        model=Ollama(id=LLM_MODEL),
        user_id=USER_ID,
        memory=memory,
        enable_agentic_memory=True,
        enable_user_memories=False,
        instructions="""You are a helpful assistant. When users share personal information, 
create specific, separate memories for each distinct fact. Avoid combining multiple 
facts into a single memory.""",
        debug_mode=True,
    )

    print(f"👤 User ID: {USER_ID}")
    print(f"🤖 Model: {LLM_MODEL}")

    # Test simple input
    test_message = "My name is Eric and I work as a software engineer."

    print(f"\n📝 Input: {test_message}")

    # Check initial state
    initial_memories = memory.get_user_memories(user_id=USER_ID)
    print(f"Initial memories: {len(initial_memories)}")

    # Run the agent
    print("\n🤖 Running agent...")
    response = await agent.arun(test_message)
    print(f"Response: {response}")

    # Check final state
    final_memories = memory.get_user_memories(user_id=USER_ID)
    new_memories = final_memories[len(initial_memories) :]

    print(f"\n📊 Results:")
    print(f"- Initial memories: {len(initial_memories)}")
    print(f"- Final memories: {len(final_memories)}")
    print(f"- New memories created: {len(new_memories)}")

    if new_memories:
        print(f"\n🧠 New memories:")
        for i, mem in enumerate(new_memories, 1):
            print(f"  {i}. {mem.memory}")
            if mem.topics:
                print(f"     Topics: {', '.join(mem.topics)}")

    # Check for exact duplicates
    memory_texts = [m.memory for m in final_memories]
    unique_texts = set(memory_texts)

    if len(memory_texts) != len(unique_texts):
        print(f"\n⚠️  DUPLICATION DETECTED!")
        print(f"- Total memories: {len(memory_texts)}")
        print(f"- Unique memories: {len(unique_texts)}")

        # Find duplicates
        from collections import Counter

        counts = Counter(memory_texts)
        duplicates = {text: count for text, count in counts.items() if count > 1}

        print(f"\n🔄 Duplicated memories:")
        for text, count in duplicates.items():
            print(f"  • '{text}' appears {count} times")
    else:
        print(f"\n✅ No exact duplicates found!")

    # Quality assessment
    if len(new_memories) == 0:
        print(f"\n❌ ISSUE: No memories created")
    elif len(new_memories) == 1:
        print(f"\n⚠️  ISSUE: Only one memory created (should be 2: name + job)")
        print(f"   Memory: {new_memories[0].memory}")
        if " and " in new_memories[0].memory:
            print(f"   This appears to be a combined memory")
    elif len(new_memories) == 2:
        print(f"\n✅ GOOD: Two memories created as expected")
        name_memory = any(
            "name" in m.memory.lower() or "eric" in m.memory.lower()
            for m in new_memories
        )
        job_memory = any(
            "engineer" in m.memory.lower() or "work" in m.memory.lower()
            for m in new_memories
        )

        if name_memory and job_memory:
            print(f"   ✅ Properly separated name and job information")
        else:
            print(f"   ⚠️  Memories don't contain expected separation")
    else:
        print(f"\n🤔 UNEXPECTED: {len(new_memories)} memories created")
        print(f"   This might indicate over-creation or other issues")


async def test_memory_update_vs_duplicate():
    """Test whether updates create duplicates or properly update existing memories."""
    print(f"\n\n🔄 Testing Memory Updates vs Duplicates")
    print("=" * 50)

    # Create fresh memory database
    memory_db = SqliteMemoryDb(
        table_name="update_test", db_file=f"{AGNO_STORAGE_DIR}/update_test.db"
    )

    # Clear any existing data
    memory_db.clear()

    # Create memory instance
    memory = Memory(db=memory_db, model=Ollama(id=LLM_MODEL))

    # Create agent
    agent = Agent(
        model=Ollama(id=LLM_MODEL),
        user_id=USER_ID,
        memory=memory,
        enable_agentic_memory=True,
        enable_user_memories=False,
        instructions="""You are a helpful assistant. When users share information:
1. Create separate memories for distinct facts
2. Update existing memories when new information contradicts or extends them
3. Don't create duplicate memories for the same information""",
        debug_mode=True,
    )

    # First interaction
    print(f"\n📝 First message: Creating initial memories")
    msg1 = "I have a cat named Whiskers who is 3 years old."
    response1 = await agent.arun(msg1)

    memories_after_first = memory.get_user_memories(user_id=USER_ID)
    print(f"Memories after first message: {len(memories_after_first)}")
    for i, mem in enumerate(memories_after_first, 1):
        print(f"  {i}. {mem.memory}")

    # Second interaction with update
    print(f"\n📝 Second message: Updating cat's age")
    msg2 = "Actually, Whiskers just turned 4 years old!"
    response2 = await agent.arun(msg2)

    memories_after_second = memory.get_user_memories(user_id=USER_ID)
    new_memories = memories_after_second[len(memories_after_first) :]

    print(f"Memories after second message: {len(memories_after_second)}")
    print(f"New memories created: {len(new_memories)}")

    print(f"\n🧠 All memories:")
    for i, mem in enumerate(memories_after_second, 1):
        print(f"  {i}. {mem.memory}")

    # Check for age-related duplicates
    age_memories = [
        m
        for m in memories_after_second
        if "3" in m.memory or "4" in m.memory or "age" in m.memory.lower()
    ]

    if len(age_memories) > 1:
        print(f"\n⚠️  Multiple age-related memories found:")
        for mem in age_memories:
            print(f"  • {mem.memory}")
        print(f"This suggests the agent created duplicates instead of updating")
    else:
        print(f"\n✅ Good: Only one age-related memory found")


async def main():
    """Run the duplication tests."""
    try:
        await test_memory_duplication()
        await test_memory_update_vs_duplicate()

        print(f"\n🎉 DUPLICATION TESTS COMPLETE!")
        print("=" * 50)
        print("Key findings will help identify:")
        print("• Whether Ollama creates exact duplicates")
        print("• Whether memories are properly separated")
        print("• Whether updates create duplicates")
        print("• Memory quality and granularity issues")

    except KeyboardInterrupt:
        print(f"\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Error during tests: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
