#!/usr/bin/env python3
"""
Test script to test Agno memory system with OpenAI instead of Ollama.

This reproduces the official Agno memory example using OpenAI to see if the
memory manager initialization issue is specific to Ollama.
"""

import asyncio
import logging
import os
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


async def test_memory_with_openai():
    """Test memory using OpenAI instead of Ollama."""
    print("🧠 Testing Agno Memory with OpenAI")
    print("=" * 50)

    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set it with: export OPENAI_API_KEY=your_key_here")
        return False

    print(f"✅ OpenAI API key found (ends with: ...{openai_api_key[-8:]})")

    try:
        from agno.agent.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.openai import OpenAIChat
        from agno.storage.sqlite import SqliteStorage
        from rich.pretty import pprint

        print("✅ Successfully imported Agno components")

        # Create memory system exactly like the example
        memory_db = SqliteMemoryDb(
            table_name="openai_memory", db_file="tmp/openai_memory.db"
        )
        memory = Memory(db=memory_db)

        # Reset the memory for this example
        memory.clear()
        print("✅ Memory system created and cleared")

        # Create IDs
        session_id = str(uuid4())
        user_id = "eric_openai_test@example.com"

        print(f"📋 Session ID: {session_id}")
        print(f"👤 User ID: {user_id}")

        # Create agent with OpenAI model
        agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),  # Using GPT-4o-mini for cost efficiency
            memory=memory,
            storage=SqliteStorage(
                table_name="openai_agent_sessions",
                db_file="tmp/openai_persistent_memory.db",
            ),
            enable_user_memories=True,
            debug_mode=True,
        )
        print("✅ Agent created with OpenAI model and memory enabled")

        # Test 1: Initial information storage
        print("\n🧪 Test 1: Storing initial information")
        response1 = await agent.arun(
            "My name is Eric and I am a software engineer who loves building AI agents.",
            user_id=user_id,
            session_id=session_id,
        )
        print(f"Response: {response1.content}")

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

        # Test the aupdate_user_memory function specifically
        print("\n🧪 Test 5: Testing aupdate_user_memory function")
        aupdate_memory_func = agent.get_update_user_memory_function(
            user_id=user_id, async_mode=True
        )
        print("✅ aupdate_user_memory function obtained")

        # Test adding a new memory
        result = await aupdate_memory_func(
            task="Add a memory: Eric's favorite programming language is Python"
        )
        print(f"Memory update result: {result}")

        # Check memories after aupdate
        memories = memory.get_user_memories(user_id=user_id)
        print(f"Memories after aupdate: {len(memories)}")
        for i, mem in enumerate(memories, 1):
            print(f"  {i}. {mem.memory}")

        print("\n✅ OpenAI memory test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("OpenAI memory test failed: %s", e, exc_info=True)
        return False


async def test_memory_manager_initialization():
    """Test if memory manager gets properly initialized with OpenAI."""
    print("\n🔧 Testing Memory Manager Initialization with OpenAI")
    print("=" * 50)

    try:
        from agno.agent.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.openai import OpenAIChat

        # Create minimal setup
        memory_db = SqliteMemoryDb(table_name="init_test", db_file="tmp/init_test.db")
        memory = Memory(db=memory_db)
        memory.clear()

        user_id = "init_test_user"

        agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            memory=memory,
            enable_agentic_memory=True,  # Enable agentic memory
            enable_user_memories=True,
            debug_mode=True,
        )

        print("✅ Agent created with agentic memory enabled")

        # Check if memory manager is initialized
        print(f"Memory manager: {getattr(memory, 'manager', 'Not found')}")
        print(f"Memory model: {getattr(memory, 'model', 'Not found')}")

        # Try to use aupdate_user_memory directly
        aupdate_func = agent.get_update_user_memory_function(
            user_id=user_id, async_mode=True
        )

        print("Testing direct aupdate_user_memory call...")
        result = await aupdate_func(task="Add a memory: This is a test memory")
        print(f"Result: {result}")

        print("✅ Memory manager initialization test passed!")
        return True

    except Exception as e:
        print(f"❌ Memory manager initialization failed: {e}")
        logger.error("Memory manager test failed: %s", e, exc_info=True)
        return False


async def main():
    """Run OpenAI memory tests."""
    print("🚀 Starting OpenAI Memory Tests")
    print("=" * 60)

    # Ensure tmp directory exists
    Path("./tmp").mkdir(exist_ok=True)

    test_results = []

    # Test 1: Memory manager initialization
    result1 = await test_memory_manager_initialization()
    test_results.append(("Memory Manager Initialization", result1))

    # Test 2: Full memory example with OpenAI
    result2 = await test_memory_with_openai()
    test_results.append(("OpenAI Memory Example", result2))

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
        print("\n🎉 All tests passed! Memory system works properly with OpenAI.")
    else:
        print(
            "\n💥 Some tests failed. This suggests the issue may not be Ollama-specific."
        )

    return 0 if total_passed == len(test_results) else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
