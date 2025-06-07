#!/usr/bin/env python3
"""
Test script to directly call the agent with tool execution and see streaming output.
This will help us understand what's happening with tool execution results.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import PersonalAgentConfig
from personal_agent.main import PersonalAgent


async def test_tool_streaming():
    """Test tool execution with streaming to see actual output."""
    print("🔧 Starting tool streaming test...")

    # Initialize the agent
    try:
        config = PersonalAgentConfig()
        agent = PersonalAgent(config=config)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return

    # Test query that should trigger tool usage
    test_query = "What files are in the current directory? List them for me."
    print(f"\n📝 Test query: {test_query}")

    try:
        print("\n🚀 Starting streaming response...")
        print("=" * 60)

        # Stream the response
        response_stream = await agent.arun(
            message=test_query,
            stream=True,
            stream_intermediate_steps=True,
        )

        response_text = ""
        chunk_count = 0

        async for response_chunk in response_stream:
            chunk_count += 1
            print(f"\n--- Chunk {chunk_count} ---")

            # Show event type
            if hasattr(response_chunk, "event") and response_chunk.event:
                print(f"Event: {response_chunk.event}")

            # Show content if available
            if (
                hasattr(response_chunk, "content")
                and response_chunk.content is not None
            ):
                print(f"Content: {repr(response_chunk.content)}")
                if response_chunk.event == "RunResponse":
                    response_text += response_chunk.content

            # Show tools if available
            if hasattr(response_chunk, "tools") and response_chunk.tools:
                print(f"Tools: {len(response_chunk.tools)} tool(s)")
                for i, tool in enumerate(response_chunk.tools):
                    print(f"  Tool {i+1}: {tool}")

            # Show all attributes of the chunk for debugging
            print(f"Chunk attributes: {dir(response_chunk)}")
            print(f"Chunk type: {type(response_chunk)}")

            # Show raw chunk data
            if hasattr(response_chunk, "__dict__"):
                print(f"Chunk data: {response_chunk.__dict__}")

        print("\n" + "=" * 60)
        print(f"✅ Streaming completed. Total chunks: {chunk_count}")
        print(f"📄 Final response text: {repr(response_text)}")

    except Exception as e:
        print(f"❌ Error during streaming: {e}")
        import traceback

        traceback.print_exc()


async def test_non_streaming():
    """Test the same query without streaming for comparison."""
    print("\n\n🔄 Testing non-streaming for comparison...")

    try:
        config = PersonalAgentConfig()
        agent = PersonalAgent(config=config)

        test_query = "What files are in the current directory? List them for me."
        print(f"📝 Test query: {test_query}")

        response = await agent.arun(message=test_query)

        print(f"✅ Non-streaming response: {response.content}")

        # Show tools if available
        if hasattr(response, "tools") and response.tools:
            print(f"🔧 Tools used: {len(response.tools)} tool(s)")
            for i, tool in enumerate(response.tools):
                print(f"  Tool {i+1}: {tool}")

    except Exception as e:
        print(f"❌ Error in non-streaming: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main test function."""
    print("🧪 Personal Agent Tool Streaming Test")
    print("=" * 50)

    # Activate virtual environment check
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("✅ Virtual environment is active")
    else:
        print("⚠️  Virtual environment may not be active")

    await test_tool_streaming()
    await test_non_streaming()


if __name__ == "__main__":
    asyncio.run(main())
