#!/usr/bin/env python3
"""
Test script based on the Agno memory example to understand memory behavior.

This reproduces the official Agno memory example using Ollama instead of OpenAI.
"""

import asyncio
import logging
import sys
from pathlib import Path
from uuid import uuid4

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_chat_history(session_runs):
    """Print the chat history for a session."""
    print("\n📋 Chat History:")
    print("=" * 50)
    for run in session_runs:
        for message in run.messages:
            role = message.role
            content = message.content
            print(f"{role.upper()}: {content}")
        print("-" * 30)


async def test_memory_example():
    """Test memory using the official Agno example pattern."""
    print("🧠 Testing Agno Memory Example")
    print("=" * 50)

    try:
        from agno.agent.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.ollama import Ollama
        from agno.storage.sqlite import SqliteStorage
        from rich.pretty import pprint

        print("✅ Successfully imported Agno components")

        # Create memory system exactly like the example
        memory_db = SqliteMemoryDb(table_name="memory", db_file="tmp/memory.db")
        memory = Memory(db=memory_db)

        # Reset the memory for this example
        memory.clear()
        print("✅ Memory system created and cleared")

        # Create IDs
        session_id = str(uuid4())
        user_id = "eric@example.com"

        print(f"📋 Session ID: {session_id}")
        print(f"👤 User ID: {user_id}")

        # Create agent exactly like the example but with Ollama
        agent = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            memory=memory,
            storage=SqliteStorage(
                table_name="agent_sessions", db_file="tmp/persistent_memory.db"
            ),
            enable_user_memories=True,
        )
        print("✅ Agent created with memory enabled")

        # Test 1: Initial information storage
        print("\n🧪 Test 1: Storing initial information")
        agent.print_response(
            "My name is Eric and I am a software engineer who loves building AI agents.",
            user_id=user_id,
            session_id=session_id,
        )

        # Test 2: Query stored information
        print("\n🧪 Test 2: Querying stored information")
        response2 = await agent.arun(
            "What do you know about me?", user_id=user_id, session_id=session_id
        )
        print(f"Response: {response2.content}")

        # Check memories after first interaction
        print("\n🔍 Checking memories after first interaction:")
        memories = memory.get_user_memories(user_id=user_id)
        print(f"Found {len(memories)} memories:")
        for i, mem in enumerate(memories, 1):
            print(f"  {i}. {mem.memory}")
            print(f"     Topics: {mem.topics}")
            print(f"     Last updated: {mem.last_updated}")

        # Test 3: Update information
        print("\n🧪 Test 3: Updating information")
        response3 = await agent.arun(
            "Actually, I'm not just a software engineer - I'm a senior software engineer with 10 years of experience.",
            user_id=user_id,
            session_id=session_id,
        )
        print(f"Response: {response3.content}")

        # Test 4: Query updated information
        print("\n🧪 Test 4: Querying updated information")
        response4 = await agent.arun(
            "What is my job title and experience level?",
            user_id=user_id,
            session_id=session_id,
        )
        print(f"Response: {response4.content}")

        # Check final memories
        print("\n🔍 Final memory state:")
        memories = agent.get_user_memories(user_id=user_id)
        print(f"Found {len(memories)} memories:")
        for i, mem in enumerate(memories, 1):
            print(f"  {i}. {mem.memory}")
            print(f"     Topics: {mem.topics}")
            print(f"     Last updated: {mem.last_updated}")

        # Print chat history
        if session_id in memory.runs:
            session_runs = memory.runs[session_id]
            print_chat_history(session_runs)
        else:
            print("No session runs found")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Memory example test failed: %s", e, exc_info=True)
        return False


async def test_memory_duplication_issue():
    """Test specifically for the memory duplication issue we observed."""
    print("\n🔍 Testing Memory Duplication Issue")
    print("=" * 50)

    try:
        from agno.agent.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.ollama import Ollama

        # Create fresh memory system
        memory_db = SqliteMemoryDb(
            table_name="duplication_test", db_file="tmp/duplication_test.db"
        )
        memory = Memory(db=memory_db)
        memory.clear()

        session_id = str(uuid4())
        user_id = "duplication_test_user"

        agent = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            memory=memory,
            enable_user_memories=True,
        )

        # Store the same information multiple times
        print("📝 Storing the same information 3 times...")
        for i in range(3):
            print(
                f"  Attempt {i+1}: Storing 'My name is Eric and I am a software engineer'"
            )
            response = await agent.arun(
                "My name is Eric and I am a software engineer",
                user_id=user_id,
                session_id=session_id,
            )
            print(f"    Response length: {len(response.content)} chars")

            # Check memory count after each attempt
            memories = memory.get_user_memories(user_id=user_id)
            print(f"    Memory count: {len(memories)}")

        # Final memory inspection
        print("\n🔍 Final memory inspection:")
        memories = memory.get_user_memories(user_id=user_id)
        print(f"Total memories: {len(memories)}")

        for i, mem in enumerate(memories, 1):
            print(f"  {i}. {mem.memory}")

        # Check for duplicates
        memory_texts = [mem.memory for mem in memories]
        unique_memories = set(memory_texts)
        print(f"\nUnique memories: {len(unique_memories)}")
        print(f"Duplicate count: {len(memory_texts) - len(unique_memories)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Duplication test failed: %s", e, exc_info=True)
        return False


async def main():
    """Run memory tests based on official example."""
    print("🚀 Starting Memory Example Tests")
    print("=" * 60)

    # Ensure tmp directory exists
    Path("./tmp").mkdir(exist_ok=True)

    test_results = []

    # Test 1: Official example pattern
    result1 = await test_memory_example()
    test_results.append(("Memory Example Test", result1))

    # Test 2: Duplication issue investigation
    result2 = await test_memory_duplication_issue()
    test_results.append(("Duplication Issue Test", result2))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")

    total_passed = sum(result[1] for result in test_results)
    print(f"\nTotal: {total_passed}/{len(test_results)} tests passed")

    return 0 if total_passed == len(test_results) else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
