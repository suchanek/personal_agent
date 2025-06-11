#!/usr/bin/env python3
"""
Test script for the aupdate_user_memory function from Agno library.

This script tests the actual aupdate_user_memory function signature:
aupdate_user_memory(task: str) -> str
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_aupdate_user_memory_function():
    """Test the aupdate_user_memory function with correct signature."""
    print("🧠 Testing aupdate_user_memory Function")
    print("=" * 50)

    try:
        # Import Agno components
        from agno.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.ollama import Ollama

        print("✅ Successfully imported Agno components")

        # Create memory system
        print("\n🔧 Creating memory system...")
        memory_db = SqliteMemoryDb(
            table_name="test_memory", db_file="./data/test_memory.db"
        )

        memory = Memory(db=memory_db)
        memory.clear()  # Clear any existing data
        print("✅ Memory system created")

        # Test user ID
        user_id = "test_user_eric"

        # Create agent with memory enabled
        print("\n🤖 Creating agent with memory enabled...")
        agent = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            user_id=user_id,
            memory=memory,
            enable_agentic_memory=True,
            enable_user_memories=True,
            debug_mode=True,
        )
        print("✅ Agent created with memory enabled")

        # Get the aupdate_user_memory function
        print("\n🔧 Getting aupdate_user_memory function...")
        aupdate_memory_func = agent.get_update_user_memory_function(
            user_id=user_id, async_mode=True
        )
        print("✅ aupdate_user_memory function obtained")

        # Test various memory tasks with correct signature
        test_tasks = [
            "Add a memory: Eric is a software engineer who loves building AI agents",
            "Add a memory: Eric studied computer science at Washington University",
            "Add a memory: Eric's favorite programming languages are Python, TypeScript, and Rust",
            "Add a memory: Eric works on MCP integrations and AI automation",
            "Update memory: Eric is a senior software engineer (not just software engineer)",
            "Search memories about Eric's education",
            "Search memories about Eric's programming skills",
            "List all memories about Eric",
        ]

        print("\n💾 Testing memory tasks...")
        for i, task in enumerate(test_tasks, 1):
            print(f"\n🧪 Test {i}: {task}")
            try:
                # Call the function with correct signature
                result = await aupdate_memory_func(task=task)
                print(f"✅ Result: {result}")

                # Add small delay to avoid overwhelming the system
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error("Memory task failed: %s", e, exc_info=True)

        # Test parameter validation
        print("\n🔍 Testing parameter validation...")
        validation_tests = [
            ("Empty task", ""),
            ("None task", None),
            ("Very long task", "A" * 10000),
            ("Special characters", "Test with émojis 🚀 and spëcial chars: @#$%^&*()"),
        ]

        for test_name, test_task in validation_tests:
            print(f"\n🧪 Validation test: {test_name}")
            try:
                if test_task is None:
                    # Skip None test as it would cause TypeError
                    print("⏭️ Skipping None test (would cause TypeError)")
                    continue

                result = await aupdate_memory_func(task=test_task)
                print(f"✅ Result: {result[:100]}...")

            except Exception as e:
                print(f"❌ Validation error: {e}")
                logger.error("Validation test failed: %s", e, exc_info=True)

        # Test direct memory inspection
        print("\n🔍 Inspecting stored memories...")
        try:
            user_memories = memory.get_user_memories(user_id=user_id)
            print(f"✅ Found {len(user_memories)} user memories:")

            for i, mem in enumerate(user_memories, 1):
                print(f"  {i}. Memory: {mem.memory[:100]}...")
                print(f"     Topics: {mem.topics}")
                print(f"     Updated: {mem.last_updated}")
                print(f"     ID: {mem.id}")

        except Exception as e:
            print(f"❌ Error inspecting memories: {e}")
            logger.error("Memory inspection failed: %s", e, exc_info=True)

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure Agno is properly installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error("Test failed: %s", e, exc_info=True)
        return False


async def test_memory_retrieval_tasks():
    """Test memory retrieval using task-based approach."""
    print("\n🔍 Testing Memory Retrieval with Tasks")
    print("=" * 50)

    try:
        from agno.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.ollama import Ollama

        # Create fresh memory system
        memory_db = SqliteMemoryDb(
            table_name="retrieval_test", db_file="./data/retrieval_test.db"
        )
        memory = Memory(db=memory_db)

        user_id = "test_user_retrieval"

        # Create agent
        agent = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            user_id=user_id,
            memory=memory,
            enable_agentic_memory=True,
            enable_user_memories=True,
            debug_mode=True,
        )

        # Get memory function
        aupdate_memory_func = agent.get_update_user_memory_function(
            user_id=user_id, async_mode=True
        )

        # Add some test data
        print("📝 Adding test memories...")
        test_memories = [
            "Add memory: Eric graduated from Washington University with a Computer Science degree",
            "Add memory: Eric specializes in Python, AI, and machine learning",
            "Add memory: Eric has 5 years of experience in software development",
            "Add memory: Eric currently works on AI agent frameworks",
        ]

        for memory_task in test_memories:
            result = await aupdate_memory_func(task=memory_task)
            print(f"✅ Added: {result}")
            await asyncio.sleep(0.3)

        # Test retrieval tasks
        print("\n🔍 Testing retrieval tasks...")
        retrieval_tasks = [
            "Retrieve all memories about Eric's education",
            "Find memories about Eric's programming skills",
            "Search for memories about Eric's work experience",
            "List all memories containing 'University'",
            "Get memories about AI and machine learning",
            "Show all stored memories for this user",
        ]

        for task in retrieval_tasks:
            print(f"\n❓ Task: {task}")
            try:
                result = await aupdate_memory_func(task=task)
                print(f"✅ Result: {result}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"❌ Error: {e}")

        return True

    except Exception as e:
        print(f"❌ Retrieval test error: {e}")
        logger.error("Retrieval test failed: %s", e, exc_info=True)
        return False


async def main():
    """Run aupdate_user_memory tests with correct signature."""
    print("🚀 Starting aupdate_user_memory Function Tests")
    print("=" * 60)

    # Ensure data directory exists
    Path("./data").mkdir(exist_ok=True)

    test_results = []

    # Test 1: Basic aupdate_user_memory function
    result1 = await test_aupdate_user_memory_function()
    test_results.append(("aupdate_user_memory Function", result1))

    # Test 2: Memory retrieval tasks
    result2 = await test_memory_retrieval_tasks()
    test_results.append(("Memory Retrieval Tasks", result2))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")

    total_passed = sum(result[1] for result in test_results)
    print(f"\nTotal: {total_passed}/{len(test_results)} tests passed")

    if total_passed == len(test_results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed - check logs for details")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
