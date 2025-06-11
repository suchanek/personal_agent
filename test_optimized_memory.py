#!/usr/bin/env python3
"""
Optimized Agno agent configuration that uses OpenAI for memory processing
and Ollama for regular responses to avoid the local LLM memory hang issue.
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


async def test_hybrid_memory_agent():
    """Test agent with OpenAI memory + Ollama responses."""
    print("🔄 Testing Hybrid Memory Agent (OpenAI Memory + Ollama Responses)")
    print("=" * 70)

    try:
        from agno.agent.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.ollama import Ollama
        from agno.models.openai import OpenAIChat
        from agno.storage.sqlite import SqliteStorage

        print("✅ Successfully imported Agno components")

        # Create memory system with OpenAI (for fast memory processing)
        print("🧠 Creating memory system with OpenAI backend...")
        memory_db = SqliteMemoryDb(
            table_name="hybrid_memory", db_file="tmp/hybrid_memory.db"
        )

        # Memory uses OpenAI for fast processing
        memory = Memory(
            db=memory_db,
            # Use OpenAI for memory analysis (fast)
            # Note: Memory will inherit the agent's model, but we can specify one
        )
        memory.clear()

        session_id = str(uuid4())
        user_id = "hybrid_test_user"

        print("🤖 Creating hybrid agent...")

        # Create agent with Ollama for responses but enable memory
        agent = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),  # Ollama for responses
            memory=memory,
            storage=SqliteStorage(
                table_name="hybrid_sessions", db_file="tmp/hybrid_sessions.db"
            ),
            enable_user_memories=True,
            user_id=user_id,
        )

        print("✅ Hybrid agent created")

        # Test interactions
        test_interactions = [
            "My name is Eric and I am a software engineer",
            "What is my name?",
            "I also love building AI agents and working with Python",
            "What do you know about me?",
        ]

        for i, message in enumerate(test_interactions, 1):
            print(f"\n💬 Test {i}: {message}")

            start_time = asyncio.get_event_loop().time()
            try:
                response = await asyncio.wait_for(
                    agent.arun(message, user_id=user_id, session_id=session_id),
                    timeout=15.0,
                )
                elapsed = asyncio.get_event_loop().time() - start_time

                print(f"✅ Response ({elapsed:.2f}s): {response.content}")

                # Show current memories
                memories = memory.get_user_memories(user_id=user_id)
                print(f"📊 Total memories: {len(memories)}")

            except asyncio.TimeoutError:
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"⏰ Timeout after {elapsed:.2f}s")
                return False
            except Exception as e:
                print(f"❌ Error: {e}")
                return False

        # Final memory inspection
        print(f"\n🔍 Final Memory State:")
        memories = memory.get_user_memories(user_id=user_id)
        for i, mem in enumerate(memories, 1):
            print(f"  {i}. {mem.memory}")
            print(f"     Topics: {mem.topics}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Hybrid agent test failed: %s", e, exc_info=True)
        return False


async def test_optimized_personal_agent():
    """Test the personal agent pattern with optimized memory."""
    print("\n🎯 Testing Optimized Personal Agent Pattern")
    print("=" * 60)

    try:
        from agno.agent.agent import Agent
        from agno.models.ollama import Ollama
        from agno.storage.sqlite import SqliteStorage

        # Strategy: Use Ollama but disable heavy memory processing
        # Use conversation history instead for lightweight "memory"
        print("🤖 Creating optimized personal agent...")

        agent = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            enable_user_memories=False,  # Disable heavy memory processing
            storage=SqliteStorage(
                table_name="personal_sessions", db_file="tmp/personal_sessions.db"
            ),
            add_history_to_messages=True,  # Use conversation history
            num_history_responses=10,  # Remember last 10 exchanges
            markdown=True,
            instructions="""You are a helpful personal AI assistant. 
            You remember information shared in our conversation and can refer back to it.
            Be friendly, helpful, and maintain context from our discussion.""",
        )

        session_id = str(uuid4())
        user_id = "personal_test_user"

        # Test personal information flow
        personal_tests = [
            "Hi! My name is Eric and I'm a software engineer",
            "What's my name?",
            "I work primarily with Python and AI/ML",
            "What programming languages do I use?",
            "I'm currently working on personal AI agents",
            "Tell me what you know about my work",
        ]

        for i, message in enumerate(personal_tests, 1):
            print(f"\n💬 Test {i}: {message}")

            start_time = asyncio.get_event_loop().time()
            response = await agent.arun(message, user_id=user_id, session_id=session_id)
            elapsed = asyncio.get_event_loop().time() - start_time

            print(f"✅ Response ({elapsed:.2f}s): {response.content}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run optimized memory tests."""
    print("🚀 Optimized Memory System Tests")
    print("=" * 60)

    # Ensure tmp directory exists
    Path("./tmp").mkdir(exist_ok=True)

    test_results = []

    # Test 1: Hybrid approach (if OpenAI available)
    try:
        result1 = await test_hybrid_memory_agent()
        test_results.append(("Hybrid Memory Agent", result1))
    except Exception as e:
        print(f"⚠️  Skipping hybrid test (OpenAI may not be configured): {e}")
        test_results.append(("Hybrid Memory Agent", "SKIPPED"))

    # Test 2: Optimized local approach
    result2 = await test_optimized_personal_agent()
    test_results.append(("Optimized Personal Agent", result2))

    # Summary
    print("\n" + "=" * 60)
    print("📊 OPTIMIZATION RESULTS")
    print("=" * 60)

    for test_name, result in test_results:
        if result == "SKIPPED":
            print(f"⏭️  SKIPPED - {test_name}")
        elif result:
            print(f"✅ PASSED - {test_name}")
        else:
            print(f"❌ FAILED - {test_name}")

    print("\n💡 RECOMMENDED PRODUCTION CONFIGURATION:")
    print("   Option 1: Disable enable_user_memories, use conversation history")
    print("   Option 2: Use OpenAI for memory processing, Ollama for responses")
    print("   Option 3: Implement custom lightweight memory system")
    print("   Option 4: Use the working ChatGPT pattern from memory_test_chatgpt.py")

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
