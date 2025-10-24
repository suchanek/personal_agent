#!/usr/bin/env python3
"""
Streaming Response Analyzer for Agno Agents

This program demonstrates how to:
1. Collect all chunks from an iterator response when stream=True
2. Analyze the collected response intelligently 
3. Extract and print the final response and tool calls
4. Handle image URLs and other content properly

The program works with both streaming and non-streaming modes to show the difference.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent, RunResponse
from agno.run.response import RunResponseEvent, RunEvent
from agno.tools.dalle import DalleTools

from src.personal_agent.team.reasoning_team import create_image_agent


def collect_streaming_chunks(run_stream: Iterator[RunResponseEvent]) -> List[RunResponseEvent]:
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


def extract_final_response_and_toolcalls(chunks: List[RunResponseEvent]) -> Dict[str, Any]:
    """
    Intelligently analyze collected chunks to extract final response and tool calls.
    
    Args:
        chunks: List of RunResponseEvent objects
        
    Returns:
        Dictionary containing final response, tool calls, and other relevant information
    """
    result = {
        "final_content": "",
        "final_chunk": None,
        "tool_calls": [],
        "image_urls": [],
        "status": "unknown",
        "total_chunks": len(chunks),
        "chunk_analysis": []
    }
    
    # Process each chunk to build our understanding
    for i, chunk in enumerate(chunks):
        chunk_info = {
            "index": i,
            "event_type": getattr(chunk, 'event', 'unknown'),
            "has_content": hasattr(chunk, 'content') and chunk.content is not None,
            "content_length": len(str(chunk.content)) if hasattr(chunk, 'content') and chunk.content else 0,
            "status": getattr(chunk, 'status', None)
        }
        result["chunk_analysis"].append(chunk_info)
        
        # Collect tool calls from any chunk that has them
        if hasattr(chunk, 'tools') and chunk.tools:
            for tool in chunk.tools:
                # Avoid duplicates
                if tool not in result["tool_calls"]:
                    result["tool_calls"].append(tool)
        
        # Look for image URLs in content
        if hasattr(chunk, 'content') and chunk.content:
            import re
            # Find markdown image patterns ![alt](url)
            image_matches = re.findall(r'!\[([^\]]*)\]\((https?://[^\)]+)\)', str(chunk.content))
            for alt_text, url in image_matches:
                result["image_urls"].append({
                    "alt_text": alt_text,
                    "url": url,
                    "chunk_index": i
                })
        
        # Identify the final chunk (usually has RunStatus.completed)
        if hasattr(chunk, 'status') and str(chunk.status) == 'RunStatus.completed':
            result["final_chunk"] = chunk
            result["status"] = "completed"
            if hasattr(chunk, 'content'):
                result["final_content"] = chunk.content
    
    # If we didn't find a completed status chunk, use the last chunk as final
    if not result["final_content"] and chunks:
        last_chunk = chunks[-1]
        result["final_chunk"] = last_chunk
        if hasattr(last_chunk, 'content'):
            result["final_content"] = last_chunk.content
        if hasattr(last_chunk, 'status'):
            result["status"] = str(last_chunk.status)
    
    return result


def print_intelligent_analysis(analysis: Dict[str, Any]) -> None:
    """
    Print an intelligent analysis of the streaming response.
    
    Args:
        analysis: Dictionary with analysis results from extract_final_response_and_toolcalls
    """
    print("🤖 INTELLIGENT STREAMING RESPONSE ANALYSIS")
    print("=" * 50)
    
    print(f"📊 Total chunks processed: {analysis['total_chunks']}")
    print(f"🏁 Final status: {analysis['status']}")
    
    if analysis['final_content']:
        print(f"\n📝 FINAL RESPONSE CONTENT ({len(str(analysis['final_content']))} characters):")
        print("-" * 40)
        print(analysis['final_content'])
    else:
        print("\n❌ No final content found")
    
    if analysis['image_urls']:
        print(f"\n🖼️  IMAGE URLS FOUND ({len(analysis['image_urls'])} total):")
        print("-" * 30)
        for img in analysis['image_urls']:
            print(f"   Alt text: '{img['alt_text']}'")
            print(f"   URL: {img['url']}")
            print(f"   Found in chunk: {img['chunk_index']}")
            print()
    
    if analysis['tool_calls']:
        print(f"🔧 TOOL CALLS MADE ({len(analysis['tool_calls'])} total):")
        print("-" * 25)
        for i, tool in enumerate(analysis['tool_calls'], 1):
            print(f"   {i}. Tool Name: {getattr(tool, 'tool_name', 'Unknown')}")
            if hasattr(tool, 'arguments'):
                print(f"      Arguments: {tool.arguments}")
            print()
    
    # Show some statistics about chunk processing
    content_chunks = [c for c in analysis['chunk_analysis'] if c['has_content']]
    if content_chunks:
        print(f"📈 CHUNK STATISTICS:")
        print(f"   Chunks with content: {len(content_chunks)}")
        print(f"   First content chunk: #{content_chunks[0]['index']}")
        print(f"   Last content chunk: #{content_chunks[-1]['index']}")
    
    print("\n" + "=" * 50)


async def demonstrate_streaming_analysis():
    """Demonstrate the streaming response analysis with the image agent."""
    print("🎨 DEMONSTRATING STREAMING RESPONSE ANALYSIS")
    print("=" * 50)
    
    # Create the image agent
    image_agent = create_image_agent(debug=False, use_remote=False)
    
    prompt = "Create an image of a futuristic city with flying cars"
    print(f"Prompt: '{prompt}'")
    
    # Test 1: Streaming with intermediate steps
    print(f"\n1️⃣  STREAMING MODE (stream=True, stream_intermediate_steps=True)")
    print("-" * 60)
    
    try:
        run_stream = image_agent.run(
            prompt,
            stream=True,
            stream_intermediate_steps=True,
        )
        
        # Collect all chunks
        chunks = collect_streaming_chunks(run_stream)
        print(f"✅ Successfully collected {len(chunks)} chunks")
        
        # Analyze the chunks intelligently
        analysis = extract_final_response_and_toolcalls(chunks)
        
        # Print intelligent analysis
        print_intelligent_analysis(analysis)
        
    except Exception as e:
        print(f"❌ Error in streaming test: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Non-streaming for comparison
    print(f"\n2️⃣  NON-STREAMING MODE (stream=False)")
    print("-" * 40)
    
    try:
        response = await image_agent.arun(prompt, stream=False)
        print(f"✅ Non-streaming response received")
        print(f"Content length: {len(str(response.content)) if response.content else 0} characters")
        
        if response.content:
            print("\n📝 NON-STREAMING RESPONSE:")
            print("-" * 25)
            print(response.content)
            
            # Check for image URLs in non-streaming response
            import re
            image_matches = re.findall(r'!\[([^\]]*)\]\((https?://[^\)]+)\)', str(response.content))
            if image_matches:
                print(f"\n🖼️  IMAGE URLS FOUND:")
                for alt_text, url in image_matches:
                    print(f"   Alt text: '{alt_text}'")
                    print(f"   URL: {url}")
        
        if response.tools:
            print(f"\n🔧 TOOL CALLS IN NON-STREAMING RESPONSE:")
            for i, tool in enumerate(response.tools, 1):
                print(f"   {i}. Tool: {getattr(tool, 'tool_name', 'Unknown')}")
                
    except Exception as e:
        print(f"❌ Error in non-streaming test: {e}")
        import traceback
        traceback.print_exc()


def analyze_runresponse_class():
    """Analyze the RunResponse class structure to understand its elements."""
    print("\n📚 RUNRESPONSE CLASS ANALYSIS")
    print("=" * 40)
    
    # Create a sample RunResponse to examine its structure
    sample_response = RunResponse(
        run_id="test-run-123",
        content="Sample content",
        agent_id="test-agent-456"
    )
    
    print("Key elements of RunResponse class:")
    print("  - content: The main response content")
    print("  - run_id: Unique identifier for the run")
    print("  - agent_id: Identifier for the agent")
    print("  - session_id: Session identifier")
    print("  - tools: List of tool executions")
    print("  - images: List of image artifacts")
    print("  - status: Current status of the run")
    print("  - created_at: Timestamp of creation")
    print("  - events: List of events during the run")
    
    print("\nFor streaming responses, RunResponseEvent types include:")
    print("  - RunResponseStartedEvent")
    print("  - RunResponseContentEvent")
    print("  - RunResponseCompletedEvent")
    print("  - ToolCallStartedEvent")
    print("  - ToolCallCompletedEvent")
    print("  - etc.")


async def main():
    """Main function to run the streaming response analyzer."""
    print("🚀 AGNO STREAMING RESPONSE ANALYZER")
    print("This program demonstrates intelligent analysis of streaming responses from Agno agents.\n")
    
    # Analyze the RunResponse class structure
    analyze_runresponse_class()
    
    # Demonstrate streaming analysis
    await demonstrate_streaming_analysis()
    
    print("\n🎯 ANALYSIS COMPLETE")
    print("=" * 30)
    print("The program successfully:")
    print("1. Collected all chunks from streaming iterator")
    print("2. Analyzed chunks intelligently for final response")
    print("3. Extracted image URLs and tool calls")
    print("4. Compared streaming vs non-streaming modes")


if __name__ == "__main__":
    asyncio.run(main())