#!/usr/bin/env python3
"""
Test script to verify the memory tools validation fix works correctly.
"""

import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_memory_tools():
    """Test that memory tools work without validation errors."""
    print("🧪 Testing memory tools validation fix...")

    # Create agent using new pattern
    agent = AgnoPersonalAgent(
        model_name="llama3.2:3b", enable_memory=True, user_id="charlie", debug=True
    )

    print(f"✅ Agent created: {agent.model_name}")

    # Test memory operations that previously caused validation errors
    print("🚀 Testing get_recent_memories (this previously failed)...")
    response = await agent.run("What do you remember about me recently?")
    print(f"📝 Response: {response[:100]}...")

    print("🚀 Testing store_user_memory...")
    response2 = await agent.run("Remember that I love testing software and fixing bugs")
    print(f"📝 Response: {response2[:100]}...")

    print("🚀 Testing query_memory...")
    response3 = await agent.run("What do you know about my interests?")
    print(f"📝 Response: {response3[:100]}...")

    return agent


async def main():
    """Run memory tools test."""
    print("🎯 Testing Memory Tools Validation Fix")
    print("=" * 50)

    try:
        agent = await test_memory_tools()

        print("\n" + "=" * 50)
        print("🎉 Memory tools test completed successfully!")
        print(f"✅ Agent: {agent.user_id} (initialized: {agent._initialized})")

        # Check agent info
        info = agent.get_agent_info()
        print(f"📊 Knowledge enabled: {info['knowledge_enabled']}")
        print(f"📊 Memory enabled: {info['memory_enabled']}")
        print(f"📊 Total tools: {info['tool_counts']['total']}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
