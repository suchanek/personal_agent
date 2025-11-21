#!/usr/bin/env python3
"""
Test script to analyze streaming response chunks and identify missing final response.
"""

import asyncio
import sys
from pathlib import Path
from typing import Iterator

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.agent import Agent, RunResponse
from agno.utils.common import dataclass_to_dict
from rich.pretty import pprint

from personal_agent.team.reasoning_team import create_image_agent


@pytest.mark.asyncio
async def test_streaming_chunks():
    """Test streaming response chunks to find the missing final response."""
    print("🔍 TESTING STREAMING RESPONSE CHUNKS")
    print("=" * 60)
    
    # Create the image agent
    image_agent = create_image_agent(debug=True, use_remote=False)
    
    prompt = "Create an image of a robot riding a monkey"
    
    print(f"Testing prompt: '{prompt}'")
    print("\n1️⃣  Testing with streaming=True, stream_intermediate_steps=True")
    print("-" * 50)
    
    try:
        # Test streaming with intermediate steps (like the working example)
        run_stream: Iterator[RunResponse] = image_agent.run(
            prompt,
            stream=True,
            stream_intermediate_steps=True,
        )
        
        chunk_count = 0
        final_content = ""
        final_chunk = None
        
        for chunk in run_stream:
            chunk_count += 1
            print(f"\n📦 CHUNK {chunk_count}:")
            
            # Convert to dict and analyze
            chunk_dict = dataclass_to_dict(chunk)
            if "messages" in chunk_dict:
                chunk_dict.pop("messages")
            
            # Check for content
            if hasattr(chunk, 'content') and chunk.content:
                content_preview = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                print(f"   Content: '{content_preview}'")
                final_content = chunk.content  # Keep updating with latest content
                
                # Check for image markdown
                if "![" in chunk.content and "](" in chunk.content:
                    print("   ✅ FOUND IMAGE MARKDOWN IN THIS CHUNK!")
                    import re
                    image_match = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", chunk.content)
                    if image_match:
                        alt_text, url = image_match.groups()
                        print(f"   🖼️  Alt text: '{alt_text}'")
                        print(f"   🔗 URL: '{url}'")
            
            # Check status
            if hasattr(chunk, 'status'):
                print(f"   Status: {chunk.status}")
            
            # Check if this is the final chunk
            if hasattr(chunk, 'status') and str(chunk.status) == 'RunStatus.completed':
                print("   🏁 THIS IS THE FINAL CHUNK!")
                final_chunk = chunk
            
            print(f"   Full chunk: {chunk_dict}")
            print("-" * 30)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total chunks: {chunk_count}")
        print(f"   Final content length: {len(final_content)}")
        
        if final_chunk:
            print("   ✅ Found final chunk")
            if hasattr(final_chunk, 'content') and final_chunk.content:
                if "![" in final_chunk.content and "](" in final_chunk.content:
                    print("   ✅ Final chunk contains image markdown!")
                else:
                    print("   ❌ Final chunk does NOT contain image markdown")
            else:
                print("   ❌ Final chunk has no content")
        else:
            print("   ❌ No final chunk found")
            
        # Check if ANY chunk had the image URL
        if "![" in final_content and "](" in final_content:
            print("   ✅ Image URL found in streaming chunks")
        else:
            print("   ❌ No image URL found in any chunk")
            
    except Exception as e:
        print(f"❌ Error during streaming test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("2️⃣  Testing with aprint_response (non-streaming)")
    print("-" * 50)
    
    try:
        # Test non-streaming (what works in your test script)
        await image_agent.aprint_response(prompt, stream=False)
        
    except Exception as e:
        print(f"❌ Error during non-streaming test: {e}")
        import traceback
        traceback.print_exc()


@pytest.mark.asyncio
async def main():
    """Main test function."""
    print("🚀 STREAMING CHUNKS ANALYSIS")
    print("This script analyzes streaming response chunks to find missing image URLs.\n")
    
    try:
        await test_streaming_chunks()
        
        print("\n" + "=" * 60)
        print("🎯 ANALYSIS COMPLETE")
        print("=" * 60)
        
        print("\n🔍 WHAT TO LOOK FOR:")
        print("1. Does the final chunk contain the image URL?")
        print("2. Is the team missing the final chunk in streaming mode?")
        print("3. Are intermediate chunks being processed but final chunk ignored?")
        print("4. Does non-streaming show the complete response?")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())