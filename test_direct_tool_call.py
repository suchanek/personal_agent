#!/usr/bin/env python3
"""
Direct test of agent tool execution to debug streaming output.
This script directly calls the agent with a query that requires tool execution
and displays all streaming chunks to see what's happening.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from personal_agent.agno_main import initialize_agno_system


async def test_direct_tool_call():
    """Test direct tool execution with detailed streaming output."""
    print("🚀 Starting direct tool call test...")

    # Initialize the agent
    try:
        agent = await initialize_agno_system()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return

    # Test query that should trigger tool usage
    test_query = "What files are in the current directory? List them for me."
    print(f"\n📝 Test query: {test_query}")

    try:
        print("\n🔄 Starting streaming response...")

        # Call agent with streaming enabled
        response_stream = await agent.arun(
            message=test_query,
            stream=True,
            stream_intermediate_steps=True,
        )

        response_text = ""
        chunk_count = 0

        print("\n📊 Processing streaming chunks:")
        print("-" * 60)

        # Process each chunk in the stream
        async for chunk in response_stream:
            chunk_count += 1
            print(f"\n🔹 Chunk #{chunk_count}")

            # Display chunk attributes
            if hasattr(chunk, "event"):
                print(f"   Event: {chunk.event}")

            if hasattr(chunk, "content") and chunk.content is not None:
                print(f"   Content: {repr(chunk.content)}")
                if chunk.event == "RunResponse":
                    response_text += chunk.content

            if hasattr(chunk, "tools") and chunk.tools:
                print(f"   Tools: {len(chunk.tools)} tool(s)")
                for i, tool in enumerate(chunk.tools):
                    print(f"     Tool {i+1}:")
                    if hasattr(tool, "name"):
                        print(f"       Name: {tool.name}")
                    if hasattr(tool, "arguments"):
                        print(f"       Arguments: {tool.arguments}")
                    if hasattr(tool, "result"):
                        print(f"       Result: {repr(tool.result)}")

            # Display all other attributes
            other_attrs = []
            for attr in dir(chunk):
                if not attr.startswith("_") and attr not in [
                    "event",
                    "content",
                    "tools",
                ]:
                    try:
                        value = getattr(chunk, attr)
                        if not callable(value):
                            other_attrs.append(f"{attr}: {repr(value)}")
                    except:
                        pass

            if other_attrs:
                print(f"   Other attributes: {', '.join(other_attrs)}")

        print("-" * 60)
        print(f"\n📈 Summary:")
        print(f"   Total chunks processed: {chunk_count}")
        print(f"   Final response text length: {len(response_text)}")
        print(f"   Final response: {repr(response_text)}")

    except Exception as e:
        print(f"❌ Error during streaming: {e}")
        import traceback

        traceback.print_exc()

    # Also test non-streaming for comparison
    print("\n" + "=" * 60)
    print("🔄 Testing non-streaming response for comparison...")

    try:
        response = await agent.arun(message=test_query, stream=False)
        # Handle both generator and direct response cases
        if hasattr(response, "content"):
            print(f"✅ Non-streaming response: {repr(response.content)}")
        else:
            # If it's still an async generator, consume it
            final_content = ""
            async for chunk in response:
                if hasattr(chunk, "content") and chunk.content:
                    final_content += chunk.content
            print(f"✅ Non-streaming response (consumed): {repr(final_content)}")
    except Exception as e:
        print(f"❌ Error in non-streaming: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct_tool_call())
