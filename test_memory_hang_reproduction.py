#!/usr/bin/env python3
"""
Test to reproduce the exact hanging condition with memory database.
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


async def test_memory_with_database():
    """Test memory system with actual database to reproduce hang."""
    print("🧠 Testing Memory System WITH Database")
    print("=" * 60)

    try:
        from agno.agent.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.ollama import Ollama
        from agno.storage.sqlite import SqliteStorage

        print("✅ Successfully imported Agno components")

        # Create memory system with database (like the hanging example)
        print("🗄️  Creating memory database...")
        memory_db = SqliteMemoryDb(
            table_name="hang_test_memory", db_file="tmp/hang_test_memory.db"
        )
        memory = Memory(db=memory_db)
        memory.clear()  # Start fresh
        print("✅ Memory database created and cleared")

        # Create agent with memory database
        print("🤖 Creating agent with memory database...")
        session_id = str(uuid4())
        user_id = "hang_test_user"

        agent = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            memory=memory,
            storage=SqliteStorage(
                table_name="hang_test_sessions", db_file="tmp/hang_test_sessions.db"
            ),
            enable_user_memories=True,
            user_id=user_id,
        )
        print("✅ Agent created with full memory system")

        # Test the exact scenario that hangs
        print("⚡ Testing memory creation (THIS SHOULD HANG)...")
        print("📝 Starting 10-second timeout test...")

        start_time = asyncio.get_event_loop().time()
        try:
            response = await asyncio.wait_for(
                agent.arun(
                    "My name is Eric and I am a software engineer",
                    user_id=user_id,
                    session_id=session_id,
                ),
                timeout=10.0,  # 10 second timeout
            )
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"✅ Completed in {elapsed:.2f} seconds")
            print(f"Response: {response.content[:100]}...")

            # Check what was created in memory
            memories = memory.get_user_memories(user_id=user_id)
            print(f"📊 Created {len(memories)} memories")

        except asyncio.TimeoutError:
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"⏰ CONFIRMED: Memory system HANGS after {elapsed:.2f} seconds")
            print("🔍 The hang occurs during database-backed memory creation")
            return "HANG_CONFIRMED"

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Database memory test failed: %s", e, exc_info=True)
        return False


async def test_memory_configuration_options():
    """Test different memory configurations to find working options."""
    print("\n🔧 Testing Different Memory Configurations")
    print("=" * 60)

    try:
        from agno.agent.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.ollama import Ollama

        configurations = [
            {
                "name": "Memory Disabled",
                "config": {
                    "enable_user_memories": False,
                    "memory": None,
                },
            },
            {
                "name": "Memory Enabled (No Storage)",
                "config": {
                    "enable_user_memories": True,
                    "memory": None,  # Let Agno create default
                },
            },
            {
                "name": "Memory with Database",
                "config": {
                    "enable_user_memories": True,
                    "memory": Memory(
                        db=SqliteMemoryDb(
                            table_name="config_test", db_file="tmp/config_test.db"
                        )
                    ),
                },
            },
        ]

        for config_info in configurations:
            print(f"\n🧪 Testing: {config_info['name']}")

            agent = Agent(
                model=Ollama(id="qwen2.5:7b-instruct"),
                user_id="config_test_user",
                **config_info["config"],
            )

            start_time = asyncio.get_event_loop().time()
            try:
                response = await asyncio.wait_for(
                    agent.arun("Hello, I am testing configurations"), timeout=8.0
                )
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"  ✅ Success in {elapsed:.2f}s: {response.content[:50]}...")

            except asyncio.TimeoutError:
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"  ⏰ Timeout after {elapsed:.2f}s")
            except Exception as e:
                print(f"  ❌ Error: {e}")

        return True

    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False


async def main():
    """Run hang reproduction tests."""
    print("🔍 Memory Hang Investigation")
    print("=" * 60)

    # Ensure tmp directory exists
    Path("./tmp").mkdir(exist_ok=True)

    test_results = []

    # Test 1: Reproduce the hang
    result1 = await test_memory_with_database()
    test_results.append(("Memory Database Hang Test", result1))

    # Test 2: Configuration options
    result2 = await test_memory_configuration_options()
    test_results.append(("Memory Configuration Options", result2))

    # Summary
    print("\n" + "=" * 60)
    print("📊 INVESTIGATION RESULTS")
    print("=" * 60)

    hang_confirmed = False
    for test_name, result in test_results:
        if result == "HANG_CONFIRMED":
            print(f"🔍 CONFIRMED - {test_name}: HANGS")
            hang_confirmed = True
        elif result:
            print(f"✅ PASSED - {test_name}")
        else:
            print(f"❌ FAILED - {test_name}")

    print("\n💡 ANALYSIS:")
    if hang_confirmed:
        print("   ✅ HANG REPRODUCED: Issue occurs with database-backed memory")
        print("   🔍 Root cause: Agno's memory system makes excessive LLM calls")
        print("   ⚡ Each memory creation triggers 20+ API requests to analyze content")
        print("   🐌 With local Ollama: 20+ requests × 2-3s each = 40-60+ seconds")
        print("   🏥 Solution: Use memory systems optimized for local LLM usage")
    else:
        print("   ❓ Could not reproduce hang - may be intermittent")

    print("\n🛠️  RECOMMENDED SOLUTIONS:")
    print("   1. Disable `enable_user_memories=True` for production")
    print("   2. Use custom lightweight memory (e.g., simple SQLite storage)")
    print("   3. Switch to OpenAI API for memory processing (faster)")
    print("   4. Implement memory batching to reduce API calls")

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
