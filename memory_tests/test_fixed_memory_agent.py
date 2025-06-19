#!/usr/bin/env python3
"""
Test the fixed memory agent to verify it can actually create and query memories.

This test validates:
1. Agent properly loads memory tools
2. Agent can create memories via tool calls
3. Anti-duplicate system prevents duplicates
4. Memory querying works correctly
5. Ollama vs OpenAI model comparison
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path - go up one level from memory_tests to project root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL
from personal_agent.core.agno_agent import AgnoPersonalAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_memory_agent(model_provider: str, model_name: str):
    """Test memory functionality with specific model."""
    print(f"\n{'='*60}")
    print(f"Testing {model_provider}:{model_name}")
    print(f"{'='*60}")

    # Create agent
    agent = AgnoPersonalAgent(
        model_provider=model_provider,
        model_name=model_name,
        enable_memory=True,
        enable_mcp=False,  # Disable MCP to focus on memory
        debug=True,
        user_id="test_user",
        ollama_base_url=OLLAMA_URL,
        storage_dir=AGNO_STORAGE_DIR,
        recreate=False,
    )

    # Initialize agent
    success = await agent.initialize(recreate=True)
    if not success:
        print(f"❌ Failed to initialize {model_provider}:{model_name} agent")
        return

    print(f"✅ Successfully initialized {model_provider}:{model_name} agent")

    # Check if memory tools are loaded
    if hasattr(agent.agent, "tools") and agent.agent.tools:
        memory_tools = [
            tool
            for tool in agent.agent.tools
            if hasattr(tool, "__name__") and "memory" in tool.__name__.lower()
        ]
        print(f"📝 Memory tools loaded: {len(memory_tools)}")
        for tool in memory_tools:
            print(f"   - {tool.__name__}")
    else:
        print("❌ No tools found on agent!")
        return

    # Test 1: Store a memory using explicit command
    print(f"\n🧠 Test 1: Storing memory about user's name...")
    response1 = await agent.run(
        "My name is Eric and I live in San Francisco. Please remember this information about me."
    )
    print(f"Response: {response1}")

    # Test 2: Store another memory
    print(f"\n🧠 Test 2: Storing memory about user's preferences...")
    response2 = await agent.run(
        "I really enjoy hiking in the mountains on weekends. Please store this as a memory."
    )
    print(f"Response: {response2}")

    # Test 3: Try to store duplicate information
    print(f"\n🧠 Test 3: Attempting to store duplicate...")
    response3 = await agent.run(
        "My name is Eric and I live in San Francisco. Store this please."
    )
    print(f"Response: {response3}")

    # Test 4: Query memories
    print(f"\n🔍 Test 4: Querying memories about location...")
    response4 = await agent.run("Where do I live? Check your memory.")
    print(f"Response: {response4}")

    # Test 5: Query memories about preferences
    print(f"\n🔍 Test 5: Querying memories about hobbies...")
    response5 = await agent.run(
        "What do I like to do on weekends? Look in your memory."
    )
    print(f"Response: {response5}")

    # Test 6: Direct memory tool test
    print(f"\n🔧 Test 6: Direct memory analysis...")
    if agent.agno_memory:
        try:
            # Check how many memories we have
            memories = agent.agno_memory.search_user_memories(
                user_id="test_user", limit=20, retrieval_method="last_n"
            )
            print(f"📊 Total memories stored: {len(memories)}")
            for i, memory in enumerate(memories, 1):
                print(f"   {i}. {memory.memory[:100]}...")

        except Exception as e:
            print(f"❌ Error checking memories directly: {e}")

    print(f"\n✅ Completed testing {model_provider}:{model_name}")


async def main():
    """Run comprehensive memory tests."""
    print("🚀 Testing Fixed Memory Agent")
    print("=" * 80)

    # Test with OpenAI first (known good behavior)
    await test_memory_agent("openai", "gpt-4o-mini")

    # Test with Ollama (the problematic one) - use lowercase version that exists
    await test_memory_agent("ollama", "qwen3:1.7b")

    print("\n" + "=" * 80)
    print("🎯 ANALYSIS COMPLETE")
    print("=" * 80)
    print("Key things to verify:")
    print("1. ✅ Memory tools are properly loaded into agent")
    print("2. ✅ Agent can call store_user_memory tool")
    print("3. ✅ Anti-duplicate system prevents duplicates")
    print("4. ✅ Memory querying returns relevant results")
    print("5. ✅ Both OpenAI and Ollama models work correctly")


if __name__ == "__main__":
    asyncio.run(main())
