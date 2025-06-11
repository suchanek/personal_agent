#!/usr/bin/env python3
"""
Test script to verify that AgnoPersonalAgent properly handles user_id for memory operations.
"""

import asyncio

from src.personal_agent.config import LLM_MODEL, OLLAMA_URL
from src.personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_user_id_memory():
    """Test that the agent properly uses user_id for memory operations."""
    print("🧪 Testing AgnoPersonalAgent with user_id support")
    print("=" * 60)

    # Create agent with specific user_id
    test_user_id = "test_user_123"
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for focused test
        storage_dir="./tmp/test_agno_user_id",
        knowledge_dir="./data/knowledge",
        debug=True,
        ollama_base_url=OLLAMA_URL,
        user_id=test_user_id,
    )

    # Initialize the agent
    print(f"🚀 Initializing agent with user_id: {test_user_id}")
    success = await agent.initialize()

    if not success:
        print("❌ Failed to initialize agent")
        return False

    print("✅ Agent initialized successfully!")

    # Check agent info includes user_id
    agent_info = agent.get_agent_info()
    print(f"📊 Agent Info:")
    for key, value in agent_info.items():
        print(f"  - {key}: {value}")

    # Verify user_id is correctly set
    if agent_info.get("user_id") == test_user_id:
        print(f"✅ User ID correctly set: {test_user_id}")
    else:
        print(
            f"❌ User ID mismatch. Expected: {test_user_id}, Got: {agent_info.get('user_id')}"
        )
        return False

    # Test a simple memory interaction
    print(f"\n💬 Testing memory interaction with user_id: {test_user_id}")
    try:
        response = await agent.run(
            "My name is Test User and I like testing AI agents.",
            add_thought_callback=lambda thought: print(f"💭 {thought}"),
        )
        print(f"🤖 Response: {response}")
        print("✅ Memory interaction successful!")

    except Exception as e:
        print(f"❌ Memory interaction failed: {e}")
        return False

    # Cleanup
    await agent.cleanup()
    print("\n🎉 Test completed successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_user_id_memory())
    if success:
        print("🏆 All tests passed!")
    else:
        print("💥 Some tests failed!")
