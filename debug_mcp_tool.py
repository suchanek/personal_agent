#!/usr/bin/env python3
"""
Test script to debug MCP filesystem tool output
"""
import asyncio
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.agno_main import initialize_agno_system


async def test_mcp_tool():
    """Test the MCP filesystem tool directly"""
    print("🔧 Initializing agent...")
    agent = await initialize_agno_system()

    print("🔍 Testing mcp_filesystem-home tool...")

    # Test the tool directly
    response = await agent.arun(message="list my home directory", stream=False)

    print(f"📄 Response: {response.content}")

    # Also test with streaming to see the tool output
    print("\n🌊 Testing with streaming...")
    response_stream = await agent.arun(
        message="list my home directory",
        stream=True,
        stream_intermediate_steps=True,
    )

    async for chunk in response_stream:
        if chunk.tools and len(chunk.tools) > 0:
            for tool in chunk.tools:
                tool_name = getattr(tool, "tool_name", "Unknown")
                tool_result = getattr(tool, "result", None) or getattr(
                    tool, "content", None
                )
                print(f"🔧 Tool: {tool_name}")
                print(f"📝 Result: {tool_result}")
                print(f"📄 Type: {type(tool_result)}")


if __name__ == "__main__":
    asyncio.run(test_mcp_tool())
