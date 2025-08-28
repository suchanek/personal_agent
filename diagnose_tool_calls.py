#!/usr/bin/env python3
"""
Diagnostic script to understand tool calls in streaming responses
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent, RunResponse
from agno.models.response import ToolExecution
from agno.utils.common import dataclass_to_dict

from src.personal_agent.team.reasoning_team import create_image_agent


async def diagnose_tool_calls():
    """Diagnose how tool calls appear in streaming responses."""
    print("🔍 DIAGNOSING TOOL CALLS IN STREAMING RESPONSES")
    print("=" * 50)
    
    # Create image agent
    image_agent = create_image_agent(debug=True, use_remote=False)
    prompt = "Create an image of a dog wearing a hat"
    
    print(f"Prompt: '{prompt}'")
    
    # Test streaming with intermediate steps
    print(f"\n1️⃣  Streaming with intermediate steps")
    print("-" * 40)
    
    try:
        run_stream = image_agent.run(
            prompt,
            stream=True,
            stream_intermediate_steps=True,
        )
        
        chunk_count = 0
        tool_call_chunks = 0
        
        for chunk in run_stream:
            chunk_count += 1
            
            # Check for tools in chunk
            if hasattr(chunk, 'tools') and chunk.tools:
                tool_call_chunks += 1
                print(f"📦 Chunk {chunk_count}: Found tools attribute")
                print(f"   Tools type: {type(chunk.tools)}")
                print(f"   Tools content: {chunk.tools}")
                
                # Check individual tool objects
                for i, tool in enumerate(chunk.tools):
                    print(f"   Tool {i}:")
                    print(f"     Type: {type(tool)}")
                    print(f"     Tool name: {getattr(tool, 'tool_name', 'NO NAME')}")
                    print(f"     Arguments: {getattr(tool, 'arguments', 'NO ARGS')}")
            
            # Also check if this chunk has tool-related event type
            if hasattr(chunk, 'event'):
                if 'tool' in str(chunk.event).lower():
                    print(f"📦 Chunk {chunk_count}: Tool-related event - {chunk.event}")
            
            # Limit output for readability
            if chunk_count > 100:
                print("... (truncated for readability)")
                break
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total chunks processed: {chunk_count}")
        print(f"   Chunks with tools: {tool_call_chunks}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test non-streaming for comparison
    print(f"\n2️⃣  Non-streaming comparison")
    print("-" * 30)
    
    try:
        response = await image_agent.arun(prompt, stream=False)
        print(f"✅ Non-streaming response received")
        print(f"   Response type: {type(response)}")
        print(f"   Has tools attribute: {hasattr(response, 'tools')}")
        
        if hasattr(response, 'tools') and response.tools:
            print(f"   Tools count: {len(response.tools)}")
            for i, tool in enumerate(response.tools):
                print(f"   Tool {i}:")
                print(f"     Type: {type(tool)}")
                print(f"     Tool name: {getattr(tool, 'tool_name', 'NO NAME')}")
                print(f"     Arguments: {getattr(tool, 'arguments', 'NO ARGS')}")
        else:
            print("   No tools found in non-streaming response")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(diagnose_tool_calls())