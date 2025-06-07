#!/usr/bin/env python3
"""
Test script to examine streaming tool results vs non-streaming results
"""

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.agno_main import initialize_agno_system


async def test_streaming_vs_non_streaming():
    print("🔧 Initializing agent...")
    agent = await initialize_agno_system()

    print("\n🌊 Testing NON-streaming agent.arun()...")
    try:
        response = await agent.arun(message="list my home directory", stream=False)
        print(f"📄 Non-streaming response type: {type(response)}")
        print(f"📄 Non-streaming response content: {response.content[:200]}...")

        # Check if there are tools in the response
        if hasattr(response, "tools") and response.tools:
            print(f"🔧 Non-streaming tools found: {len(response.tools)}")
            for i, tool in enumerate(response.tools):
                print(f"   Tool {i}: {getattr(tool, 'tool_name', 'Unknown')}")
                result = getattr(tool, "result", None) or getattr(tool, "content", None)
                print(f"   Result: {result}")
        else:
            print("🔧 No tools found in non-streaming response")

    except Exception as e:
        print(f"❌ Non-streaming error: {e}")

    print("\n🌊 Testing STREAMING agent.arun()...")
    try:
        response_stream = await agent.arun(
            message="list my home directory",
            stream=True,
            stream_intermediate_steps=True,
        )

        tool_results = []
        final_content = ""

        async for chunk in response_stream:
            print(f"📦 Chunk event: {getattr(chunk, 'event', 'Unknown')}")

            # Check for tools
            if hasattr(chunk, "tools") and chunk.tools:
                print(f"🔧 Streaming tools found: {len(chunk.tools)}")
                for i, tool in enumerate(chunk.tools):
                    tool_name = getattr(tool, "tool_name", "Unknown")
                    result = getattr(tool, "result", None) or getattr(
                        tool, "content", None
                    )
                    print(f"   Tool {i}: {tool_name}")
                    print(f"   Result: {result}")
                    print(f"   Result type: {type(result)}")

                    # Store for comparison
                    tool_results.append({"name": tool_name, "result": result})

            # Check for content
            if hasattr(chunk, "content") and chunk.content:
                final_content += chunk.content
                print(f"📄 Content chunk: {chunk.content[:100]}...")

        print(f"\n📊 Summary:")
        print(f"   Total tool results: {len(tool_results)}")
        print(f"   Final content length: {len(final_content)}")

    except Exception as e:
        print(f"❌ Streaming error: {e}")


if __name__ == "__main__":
    asyncio.run(test_streaming_vs_non_streaming())
