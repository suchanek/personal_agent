#!/usr/bin/env python3
"""
Test script to verify the Agno agent migration is working correctly.
"""

import asyncio
import sys
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.core.agno_agent import create_agno_agent


async def test_agno_agent():
    """Test basic Agno agent functionality."""
    print("🧪 Testing Agno Agent Migration")
    print("=" * 40)

    try:
        # Create agent with native storage
        print("✅ Creating Agno agent with native storage...")
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="qwen2.5:7b-instruct",
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for simple test
            storage_dir="./data/test_agno",
            knowledge_dir="./data/knowledge",
            debug=True,
        )

        print("✅ Agent created successfully!")

        # Get agent info
        info = agent.get_agent_info()
        print(f"📊 Agent Info: {info}")

        # Test simple query
        print("\n🔍 Testing simple query...")
        response = await agent.run("Hello! What can you help me with?")
        print(f"🤖 Response: {response[:200]}...")

        # Cleanup
        await agent.cleanup()
        print("✅ Cleanup completed")

        print("\n🎉 Agno agent migration test PASSED!")
        return True

    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_agno_agent())
    sys.exit(0 if success else 1)
