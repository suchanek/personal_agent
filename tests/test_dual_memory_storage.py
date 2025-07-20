#!/usr/bin/env python3
"""
Test the dual memory storage functionality
"""

import asyncio
import sys

sys.path.append("src")
from personal_agent.core.agno_agent import create_agno_agent


async def test_dual_storage():
    print("🧪 Testing Dual Memory Storage")
    print("=" * 50)

    # Create agent
    agent = await create_agno_agent(
        model_name="qwen3:1.7B", debug=True, user_id="Eric_test"  # Use correct model
    )

    # Find the store_user_memory tool
    store_memory_tool = None
    for tool in agent.agent.tools:
        if hasattr(tool, "__name__") and tool.__name__ == "store_user_memory":
            store_memory_tool = tool
            break

    if not store_memory_tool:
        print("❌ Could not find store_user_memory tool")
        return

    print("✅ Found store_user_memory tool")

    # Test dual storage with correct function call
    print("\n📝 Testing dual storage...")
    result = await store_memory_tool(
        content="Charlie is my neighbor who plays guitar and teaches music lessons",
        topics=["personal", "music"],
    )
    print("Dual storage result:", result)

    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_dual_storage())
