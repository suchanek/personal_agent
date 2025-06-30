#!/usr/bin/env python3
"""
Test script to verify the memory query hesitation fix.

This script tests that the agent immediately calls memory tools when asked
about personal information, without the overthinking behavior observed in
the original interaction.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_memory_query_behavior():
    """Test that the agent immediately queries memory when asked about personal info."""
    print("🧪 Testing Memory Query Fix")
    print("=" * 50)

    # Create agent with debug mode to see tool calls
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="qwen3:1.7b",  # Use a smaller model for testing
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for simpler testing
        debug=True,  # Enable debug to see tool calls
        user_id="test_user",
        storage_dir="./data/test_memory_fix",
    )

    print("🔄 Initializing agent...")
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return False

    print("✅ Agent initialized successfully")
    print()

    # Test 1: Store some test memories first
    print("📝 Test 1: Storing test memories...")
    test_memories = [
        "Eric likes pizza and Italian food",
        "Eric works as a software engineer",
        "Eric enjoys hiking and outdoor activities",
    ]

    for memory in test_memories:
        print(f"Storing: {memory}")
        response = await agent.run(f"Remember this about me: {memory}")
        print(f"Response: {response[:100]}...")
        print()

    # Test 2: The critical test - ask "What do you remember about me?"
    print("🎯 Test 2: Critical Memory Query Test")
    print("Query: 'What do you remember about me?'")
    print(
        "Expected: Agent should IMMEDIATELY call get_recent_memories() without hesitation"
    )
    print()

    response = await agent.run("What do you remember about me?")
    print("Response:")
    print(response)
    print()

    # Test 3: Test specific preference query
    print("🎯 Test 3: Specific Preference Query")
    print("Query: 'What do you know about my food preferences?'")
    print("Expected: Agent should IMMEDIATELY call query_memory('food') or similar")
    print()

    response = await agent.run("What do you know about my food preferences?")
    print("Response:")
    print(response)
    print()

    # Test 4: Test general personal info query
    print("🎯 Test 4: General Personal Info Query")
    print("Query: 'Do you know anything about me?'")
    print("Expected: Agent should IMMEDIATELY call get_recent_memories()")
    print()

    response = await agent.run("Do you know anything about me?")
    print("Response:")
    print(response)
    print()

    print("✅ Memory query fix test completed!")
    print()
    print("🔍 Analysis:")
    print("- Look for immediate tool calls in the debug output above")
    print("- The agent should NOT show any hesitation or internal debate")
    print("- Tool calls should happen BEFORE any response text")
    print("- Responses should be warm and personal, referencing stored memories")

    await agent.cleanup()
    return True


async def main():
    """Main test function."""
    try:
        await test_memory_query_behavior()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
