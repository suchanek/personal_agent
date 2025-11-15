#!/usr/bin/env python3
"""
Program to analyze streaming response from Agno agents and extract final response with tool calls.
This program collects all chunks from a streaming response and intelligently analyzes them
to extract the final response content and any tool calls made during the process.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent, RunResponse
from agno.run.response import RunResponseEvent
from agno.tools.dalle import DalleTools
from agno.utils.common import dataclass_to_dict

from src.personal_agent.team.reasoning_team import create_image_agent


def collect_streaming_response(run_stream: Iterator[RunResponseEvent]) -> List[RunResponseEvent]:
    """
    Collect all chunks from a streaming response iterator.
    
    Args:
        run_stream: Iterator of RunResponseEvent objects from agent.run(stream=True)
        
    Returns:
        List of all RunResponseEvent chunks
    """
    chunks = []
    for chunk in run_stream:
        chunks.append(chunk)
    return chunks


def analyze_response_chunks(chunks: List[RunResponseEvent]) -> Dict[str, Any]:
    """
    Analyze collected chunks to extract final response and tool calls.
    
    Args:
        chunks: List of RunResponseEvent objects
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "total_chunks": len(chunks),
        "final_content": "",
        "final_chunk": None,
        "tool_calls": [],
        "image_urls": [],
        "status_flow": [],
        "errors": [],
    }
    
    # Process each chunk
    for i, chunk in enumerate(chunks):
        # Add to status flow for debugging
        if hasattr(chunk, 'status'):
            analysis["status_flow"].append({
                "chunk_index": i,
                "status": str(chunk.status),
                "content_preview": str(chunk.content)[:100] if hasattr(chunk, 'content') and chunk.content else ""
            })
        
        # Collect tool calls
        if hasattr(chunk, 'tools') and chunk.tools:
            for tool in chunk.tools:
                if tool not in analysis["tool_calls"]:
                    analysis["tool_calls"].append(tool)
        
        # Check for image URLs in content
        if hasattr(chunk, 'content') and chunk.content:
            import re
            # Look for markdown image pattern ![alt](url)
            image_matches = re.findall(r'!\[([^\]]*)\]\((https?://[^\)]+)\)', str(chunk.content))
            for alt_text, url in image_matches:
                analysis["image_urls"].append({
                    "alt_text": alt_text,
                    "url": url,
                    "chunk_index": i
                })
        
        # Check if this is the final chunk
        if hasattr(chunk, 'status') and str(chunk.status) == 'RunStatus.completed':
            analysis["final_chunk"] = chunk
            if hasattr(chunk, 'content'):
                analysis["final_content"] = chunk.content
    
    # If we didn't find a final chunk with completed status, use the last chunk's content
    if not analysis["final_content"] and chunks:
        last_chunk = chunks[-1]
        if hasattr(last_chunk, 'content'):
            analysis["final_content"] = last_chunk.content
            analysis["final_chunk"] = last_chunk
    
    return analysis


def print_analysis_results(analysis: Dict[str, Any]) -> None:
    """
    Print formatted analysis results.
    
    Args:
        analysis: Dictionary with analysis results
    """
    print("📊 STREAMING RESPONSE ANALYSIS")
    print("=" * 50)
    
    print(f"Total chunks received: {analysis['total_chunks']}")
    
    if analysis['final_content']:
        print(f"Final content length: {len(str(analysis['final_content']))} characters")
        print("\n📝 FINAL CONTENT:")
        print("-" * 20)
        print(analysis['final_content'])
    else:
        print("❌ No final content found")
    
    if analysis['image_urls']:
        print(f"\n🖼️  IMAGE URLS FOUND ({len(analysis['image_urls'])}):")
        print("-" * 30)
        for img in analysis['image_urls']:
            print(f"   Alt text: '{img['alt_text']}'")
            print(f"   URL: {img['url']}")
            print(f"   Found in chunk: {img['chunk_index']}")
            print()
    
    if analysis['tool_calls']:
        print(f"🔧 TOOL CALLS MADE ({len(analysis['tool_calls'])}):")
        print("-" * 25)
        for tool in analysis['tool_calls']:
            print(f"   - {tool.tool_name}")
            if hasattr(tool, 'arguments'):
                print(f"     Arguments: {tool.arguments}")
    
    # Show status flow for debugging
    print(f"\n🔄 STATUS FLOW:")
    print("-" * 15)
    for status_info in analysis['status_flow']:
        print(f"   Chunk {status_info['chunk_index']:2d}: {status_info['status']:<20} | Content: {status_info['content_preview']}")
    
    if analysis['errors']:
        print(f"\n❌ ERRORS:")
        print("-" * 10)
        for error in analysis['errors']:
            print(f"   - {error}")


async def test_with_image_agent():
    """Test the analysis with the image agent from reasoning_team."""
    print("🎨 Testing with Image Agent")
    print("=" * 30)
    
    # Create the image agent
    image_agent = create_image_agent(debug=True, use_remote=False)
    
    prompt = "Create an image of a robot riding a monkey"
    print(f"Testing prompt: '{prompt}'")
    
    try:
        # Test streaming with intermediate steps
        print("\n1️⃣  Testing with streaming=True, stream_intermediate_steps=True")
        run_stream = image_agent.run(
            prompt,
            stream=True,
            stream_intermediate_steps=True,
        )
        
        # Collect all chunks
        chunks = collect_streaming_response(run_stream)
        print(f"✅ Collected {len(chunks)} chunks")
        
        # Analyze the chunks
        analysis = analyze_response_chunks(chunks)
        
        # Print results
        print_analysis_results(analysis)
        
    except Exception as e:
        print(f"❌ Error during streaming test: {e}")
        import traceback
        traceback.print_exc()


async def test_with_simple_agent():
    """Test with a simple agent to compare behavior."""
    print("\n🔍 Testing with Simple Agent")
    print("=" * 30)
    
    # Create a simple agent
    agent = Agent(
        name="Test Agent",
        tools=[DalleTools(model="dall-e-3")],
        instructions=[
            "When asked to create an image, use the DALL-E tool to create an image.",
            "Return the image URL in markdown format: `![description](URL)`",
        ],
        markdown=True,
    )
    
    prompt = "Create an image of a yellow siamese cat"
    print(f"Testing prompt: '{prompt}'")
    
    try:
        # Test streaming with intermediate steps
        print("\n1️⃣  Testing with streaming=True, stream_intermediate_steps=True")
        run_stream = agent.run(
            prompt,
            stream=True,
            stream_intermediate_steps=True,
        )
        
        # Collect all chunks
        chunks = collect_streaming_response(run_stream)
        print(f"✅ Collected {len(chunks)} chunks")
        
        # Analyze the chunks
        analysis = analyze_response_chunks(chunks)
        
        # Print results
        print_analysis_results(analysis)
        
    except Exception as e:
        print(f"❌ Error during streaming test: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function to run the analysis."""
    print("🚀 STREAMING RESPONSE ANALYZER")
    print("This program analyzes streaming responses from Agno agents.\n")
    
    try:
        # Test with image agent from reasoning_team
        await test_with_image_agent()
        
        # Test with simple agent
        await test_with_simple_agent()
        
        print("\n" + "=" * 60)
        print("🎯 ANALYSIS COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())