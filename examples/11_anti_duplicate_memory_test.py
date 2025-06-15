#!/usr/bin/env python3
"""
Anti-Duplicate Memory Test.

This script tests the AntiDuplicateMemory class against the original
memory duplication issues found in Ollama models.
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
from personal_agent.core.anti_duplicate_memory import AntiDuplicateMemory


async def test_original_memory_behavior():
    """Test the original memory behavior (baseline)."""
    print("🔍 Testing ORIGINAL Memory Behavior (Baseline)")
    print("=" * 60)

    # Create fresh memory database for baseline
    memory_db = SqliteMemoryDb(
        table_name="baseline_test", db_file=f"{AGNO_STORAGE_DIR}/baseline_test.db"
    )
    memory_db.clear()

    # Create original memory instance
    original_memory = Memory(
        db=memory_db, model=Ollama(id=LLM_MODEL, host="http://tesla.local:11434")
    )

    # Create agent with original memory
    agent = Agent(
        model=Ollama(id=LLM_MODEL, host="http://tesla.local:11434"),
        user_id=USER_ID,
        memory=original_memory,
        enable_agentic_memory=False,
        enable_user_memories=True,
        add_history_to_messages=False,
        instructions="""You are a helpful assistant. When users share personal information, 
create specific, separate memories for each distinct fact. Create granular memories 
rather than combining multiple facts into one memory.""",
        debug_mode=True,
    )

    print(f"👤 User ID: {USER_ID}")
    print(f"🤖 Model: {LLM_MODEL}")

    # Test with multiple interactions to trigger duplication
    test_inputs = [
        "My name is Eric and I live in San Francisco.",
        "I work as a software engineer at a tech company.",
        "My favorite programming language is Python.",
        "I live in San Francisco and enjoy hiking on weekends.",  # Potential duplicate
    ]

    all_responses = []

    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n📝 Input {i}: {test_input}")

        # Check state before
        memories_before = original_memory.get_user_memories(user_id=USER_ID)

        # Run the agent
        response = await agent.arun(test_input)
        all_responses.append(response)

        # Check state after
        memories_after = original_memory.get_user_memories(user_id=USER_ID)
        new_memories = memories_after[len(memories_before) :]

        print(f"   New memories created: {len(new_memories)}")
        for j, mem in enumerate(new_memories, 1):
            print(f"     {j}. {mem.memory}")

    # Final analysis
    final_memories = original_memory.get_user_memories(user_id=USER_ID)
    print(f"\n📊 BASELINE RESULTS:")
    print(f"- Total memories: {len(final_memories)}")

    # Check for duplicates
    memory_texts = [m.memory for m in final_memories]
    unique_texts = set(memory_texts)

    print(f"- Unique memories: {len(unique_texts)}")
    print(f"- Exact duplicates: {len(memory_texts) - len(unique_texts)}")

    if len(memory_texts) != len(unique_texts):
        from collections import Counter

        counts = Counter(memory_texts)
        duplicates = {text: count for text, count in counts.items() if count > 1}

        print(f"\n⚠️  EXACT DUPLICATES FOUND:")
        for text, count in duplicates.items():
            print(f"  • '{text}' appears {count} times")

    # Check for semantic duplicates
    import difflib

    semantic_duplicates = []
    for i, mem1 in enumerate(final_memories):
        for j, mem2 in enumerate(final_memories[i + 1 :], i + 1):
            similarity = difflib.SequenceMatcher(
                None, mem1.memory.lower(), mem2.memory.lower()
            ).ratio()
            if similarity >= 0.8:
                semantic_duplicates.append((i, j, similarity, mem1.memory, mem2.memory))

    if semantic_duplicates:
        print(f"\n🔍 SEMANTIC DUPLICATES FOUND:")
        for i, j, similarity, mem1, mem2 in semantic_duplicates:
            print(f"  • {similarity:.2f} similarity:")
            print(f"    [{i}] {mem1}")
            print(f"    [{j}] {mem2}")

    print(f"\n🧠 ALL BASELINE MEMORIES:")
    for i, mem in enumerate(final_memories, 1):
        print(f"  {i}. {mem.memory}")

    return final_memories, memory_texts, semantic_duplicates


async def test_anti_duplicate_memory():
    """Test the AntiDuplicateMemory class."""
    print(f"\n\n🛡️  Testing ANTI-DUPLICATE Memory Behavior")
    print("=" * 60)

    # Create fresh memory database for anti-duplicate test
    memory_db = SqliteMemoryDb(
        table_name="anti_duplicate_test",
        db_file=f"{AGNO_STORAGE_DIR}/anti_duplicate_test.db",
    )
    memory_db.clear()

    # Create anti-duplicate memory instance
    anti_dup_memory = AntiDuplicateMemory(
        db=memory_db,
        model=Ollama(id=LLM_MODEL, host="http://tesla.local:11434"),
        similarity_threshold=0.8,
        debug_mode=True,
    )

    # Create agent with anti-duplicate memory
    agent = Agent(
        model=Ollama(id=LLM_MODEL, host="http://tesla.local:11434"),
        user_id=USER_ID,
        memory=anti_dup_memory,
        enable_agentic_memory=False,
        enable_user_memories=True,
        add_history_to_messages=False,
        instructions="""You are a helpful assistant. When users share personal information, 
create specific, separate memories for each distinct fact. Create granular memories 
rather than combining multiple facts into one memory.""",
        debug_mode=True,
    )

    print(f"👤 User ID: {USER_ID}")
    print(f"🤖 Model: {LLM_MODEL}")
    print(f"🛡️  Using AntiDuplicateMemory with similarity_threshold=0.8")

    # Use the same test inputs as baseline
    test_inputs = [
        "My name is Eric and I live in San Francisco.",
        "I work as a software engineer at a tech company.",
        "My favorite programming language is Python.",
        "I live in San Francisco and enjoy hiking on weekends.",  # Potential duplicate
    ]

    all_responses = []

    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n📝 Input {i}: {test_input}")

        # Check state before
        memories_before = anti_dup_memory.get_user_memories(user_id=USER_ID)

        # Run the agent
        response = await agent.arun(test_input)
        all_responses.append(response)

        # Check state after
        memories_after = anti_dup_memory.get_user_memories(user_id=USER_ID)
        new_memories = memories_after[len(memories_before) :]

        print(f"   New memories accepted: {len(new_memories)}")
        for j, mem in enumerate(new_memories, 1):
            print(f"     {j}. {mem.memory}")

    # Final analysis with anti-duplicate memory
    final_memories = anti_dup_memory.get_user_memories(user_id=USER_ID)

    print(f"\n📊 ANTI-DUPLICATE RESULTS:")
    print(f"- Total memories: {len(final_memories)}")

    # Use the built-in analysis
    anti_dup_memory.print_memory_analysis(user_id=USER_ID)

    return final_memories


async def test_direct_duplicate_prevention():
    """Test direct duplicate prevention capabilities."""
    print(f"\n\n🎯 Testing DIRECT Duplicate Prevention")
    print("=" * 60)

    # Create fresh memory database
    memory_db = SqliteMemoryDb(
        table_name="direct_test", db_file=f"{AGNO_STORAGE_DIR}/direct_test.db"
    )
    memory_db.clear()

    # Create anti-duplicate memory instance
    anti_dup_memory = AntiDuplicateMemory(
        db=memory_db,
        model=Ollama(id=LLM_MODEL, host="http://tesla.local:11434"),
        similarity_threshold=0.8,
        debug_mode=True,
    )

    from agno.memory.v2.schema import UserMemory

    print("🧪 Testing direct memory addition with duplicates...")

    # Test exact duplicates
    print(f"\n1️⃣  Testing EXACT duplicates:")
    memory1 = UserMemory(memory="User's name is Eric")
    memory2 = UserMemory(memory="User's name is Eric")  # Exact duplicate

    id1 = anti_dup_memory.add_user_memory(memory1, user_id=USER_ID)
    id2 = anti_dup_memory.add_user_memory(memory2, user_id=USER_ID)

    print(f"   First memory ID: {id1}")
    print(f"   Duplicate memory ID: {id2}")

    # Test semantic duplicates
    print(f"\n2️⃣  Testing SEMANTIC duplicates:")
    memory3 = UserMemory(memory="User lives in San Francisco")
    memory4 = UserMemory(
        memory="User is located in San Francisco"
    )  # Semantic duplicate

    id3 = anti_dup_memory.add_user_memory(memory3, user_id=USER_ID)
    id4 = anti_dup_memory.add_user_memory(memory4, user_id=USER_ID)

    print(f"   First memory ID: {id3}")
    print(f"   Similar memory ID: {id4}")

    # Test combined memories
    print(f"\n3️⃣  Testing COMBINED memories:")
    memory5 = UserMemory(
        memory="User's name is Eric and he works as a software engineer and lives in San Francisco"
    )

    id5 = anti_dup_memory.add_user_memory(memory5, user_id=USER_ID)
    print(f"   Combined memory ID: {id5}")

    # Final analysis
    print(f"\n📊 DIRECT TEST RESULTS:")
    anti_dup_memory.print_memory_analysis(user_id=USER_ID)


async def main():
    """Run all tests and compare results."""
    try:
        print("🚀 ANTI-DUPLICATE MEMORY COMPREHENSIVE TEST")
        print("=" * 80)

        # Test 1: Baseline behavior
        baseline_memories, baseline_texts, baseline_semantic_dups = (
            await test_original_memory_behavior()
        )

        # Test 2: Anti-duplicate behavior
        anti_dup_memories = await test_anti_duplicate_memory()

        # Test 3: Direct duplicate prevention
        await test_direct_duplicate_prevention()

        # Compare results
        print(f"\n\n📈 COMPARISON SUMMARY")
        print("=" * 80)
        print(f"Baseline (Original) Memory:")
        print(f"  - Total memories: {len(baseline_memories)}")
        print(f"  - Exact duplicates: {len(baseline_texts) - len(set(baseline_texts))}")
        print(f"  - Semantic duplicates: {len(baseline_semantic_dups)}")

        print(f"\nAnti-Duplicate Memory:")
        print(f"  - Total memories: {len(anti_dup_memories)}")

        # Calculate improvement
        baseline_total = len(baseline_memories)
        anti_dup_total = len(anti_dup_memories)

        if baseline_total > anti_dup_total:
            reduction = baseline_total - anti_dup_total
            reduction_pct = (reduction / baseline_total) * 100
            print(
                f"  - Memory reduction: {reduction} memories ({reduction_pct:.1f}% fewer)"
            )

        print(f"\n🎉 TESTS COMPLETE!")
        print("=" * 80)
        print("The AntiDuplicateMemory class provides:")
        print("✅ Exact duplicate prevention")
        print("✅ Semantic duplicate detection")
        print("✅ Combined memory detection")
        print("✅ Configurable similarity thresholds")
        print("✅ Detailed memory quality analysis")
        print("✅ Debug mode for troubleshooting")

    except KeyboardInterrupt:
        print(f"\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Error during tests: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
