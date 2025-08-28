#!/usr/bin/env python3
"""
Comprehensive Streaming Response Analyzer for Agno Agents

This program provides a complete analysis of streaming responses from Agno agents,
with detailed examination of each chunk to find tool call information.
"""

import asyncio
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent, RunResponse
from agno.run.response import RunResponseEvent
from agno.utils.common import dataclass_to_dict

from src.personal_agent.team.reasoning_team import create_image_agent


def collect_and_examine_chunks(run_stream: Iterator[RunResponseEvent]) -> List[Dict[str, Any]]:
    """
    Collect all chunks and examine each one in detail for tool call information.
    
    Args:
        run_stream: Iterator from agent.run(stream=True)
        
    Returns:
        List of dictionaries with chunk data and analysis
    """
    chunks_data = []
    
    for i, chunk in enumerate(run_stream):
        chunk_info = {
            "index": i,
            "chunk_object": chunk,
            "event_type": getattr(chunk, 'event', 'unknown'),
            "has_content": hasattr(chunk, 'content') and chunk.content is not None,
            "content_length": len(str(chunk.content)) if hasattr(chunk, 'content') and chunk.content else 0,
            "has_status": hasattr(chunk, 'status'),
            "status": str(chunk.status) if hasattr(chunk, 'status') else None,
            "has_tools": hasattr(chunk, 'tools') and chunk.tools is not None,
            "tools_count": len(chunk.tools) if hasattr(chunk, 'tools') and chunk.tools else 0,
            "has_tool": hasattr(chunk, 'tool') and chunk.tool is not None,
            "has_extra_data": hasattr(chunk, 'extra_data') and chunk.extra_data is not None,
            "tool_calls_found": [],
            "image_urls_found": []
        }
        
        # Extract tool calls from tools attribute (list)
        if hasattr(chunk, 'tools') and chunk.tools:
            for tool in chunk.tools:
                tool_info = {
                    "source": "tools_list",
                    "name": getattr(tool, 'tool_name', 'Unknown'),
                    "arguments": getattr(tool, 'arguments', {}),
                    "status": getattr(tool, 'status', 'unknown')
                }
                chunk_info["tool_calls_found"].append(tool_info)
        
        # Extract tool call from tool attribute (single)
        if hasattr(chunk, 'tool') and chunk.tool:
            tool_info = {
                "source": "tool_single",
                "name": getattr(chunk.tool, 'tool_name', 'Unknown'),
                "arguments": getattr(chunk.tool, 'arguments', {}),
                "status": getattr(chunk.tool, 'status', 'unknown')
            }
            chunk_info["tool_calls_found"].append(tool_info)
        
        # Extract image URLs from content
        if hasattr(chunk, 'content') and chunk.content:
            image_matches = re.findall(r'!\[([^\]]*)\]\((https?://[^\)]+)\)', str(chunk.content))
            for alt_text, url in image_matches:
                chunk_info["image_urls_found"].append({
                    "alt_text": alt_text,
                    "url": url
                })
        
        chunks_data.append(chunk_info)
    
    return chunks_data


def comprehensive_analysis(chunks_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of all collected chunk data.
    
    Args:
        chunks_data: List of chunk information from collect_and_examine_chunks
        
    Returns:
        Dictionary with comprehensive analysis results
    """
    analysis = {
        "final_content": "",
        "final_chunk": None,
        "all_tool_calls": [],
        "image_urls": [],
        "status": "unknown",
        "total_chunks": len(chunks_data),
        "chunks_with_content": 0,
        "chunks_with_tools": 0,
        "chunks_with_tool": 0,
        "tool_call_chunks": [],
        "image_url_chunks": []
    }
    
    # Process all chunks for comprehensive analysis
    for chunk_info in chunks_data:
        # Count chunks with different attributes
        if chunk_info["has_content"]:
            analysis["chunks_with_content"] += 1
        if chunk_info["has_tools"]:
            analysis["chunks_with_tools"] += 1
        if chunk_info["has_tool"]:
            analysis["chunks_with_tool"] += 1
        
        # Collect all tool calls
        for tool_call in chunk_info["tool_calls_found"]:
            if tool_call not in analysis["all_tool_calls"]:
                analysis["all_tool_calls"].append(tool_call)
        
        # Collect all image URLs
        for image_url in chunk_info["image_urls_found"]:
            if image_url not in analysis["image_urls"]:
                analysis["image_urls"].append(image_url)
        
        # Track chunks with tool calls or image URLs
        if chunk_info["tool_calls_found"]:
            analysis["tool_call_chunks"].append(chunk_info["index"])
        if chunk_info["image_urls_found"]:
            analysis["image_url_chunks"].append(chunk_info["index"])
        
        # Identify final chunk (usually has completed status)
        if chunk_info["has_status"] and chunk_info["status"] == 'RunStatus.completed':
            analysis["final_chunk"] = chunk_info["chunk_object"]
            analysis["status"] = "completed"
            if chunk_info["has_content"]:
                analysis["final_content"] = chunk_info["chunk_object"].content
    
    # Fallback to last chunk if no completed status found
    if not analysis["final_content"] and chunks_data:
        last_chunk_info = chunks_data[-1]
        analysis["final_chunk"] = last_chunk_info["chunk_object"]
        if last_chunk_info["has_content"]:
            analysis["final_content"] = last_chunk_info["chunk_object"].content
        if last_chunk_info["has_status"]:
            analysis["status"] = last_chunk_info["status"]
    
    return analysis


def print_detailed_findings(chunks_data: List[Dict[str, Any]], analysis: Dict[str, Any]):
    """
    Print detailed findings from the comprehensive analysis.
    
    Args:
        chunks_data: List of chunk information
        analysis: Analysis results from comprehensive_analysis
    """
    print("🔍 DETAILED CHUNK ANALYSIS")
    print("=" * 40)
    
    print(f"Total chunks processed: {analysis['total_chunks']}")
    print(f"Chunks with content: {analysis['chunks_with_content']}")
    print(f"Chunks with tools list: {analysis['chunks_with_tools']}")
    print(f"Chunks with single tool: {analysis['chunks_with_tool']}")
    
    # Show tool call findings
    if analysis["all_tool_calls"]:
        print(f"\n🔧 TOOL CALLS FOUND ({len(analysis['all_tool_calls'])} unique):")
        print("-" * 30)
        for i, tool_call in enumerate(analysis["all_tool_calls"], 1):
            print(f"   {i}. Name: {tool_call['name']}")
            print(f"      Source: {tool_call['source']}")
            print(f"      Status: {tool_call['status']}")
            if tool_call['arguments']:
                print(f"      Arguments: {tool_call['arguments']}")
    
    # Show chunks where tool calls were found
    if analysis["tool_call_chunks"]:
        print(f"\n📦 CHUNKS CONTAINING TOOL CALLS:")
        print("-" * 35)
        # Show first few and last few for brevity
        if len(analysis["tool_call_chunks"]) <= 10:
            for chunk_idx in analysis["tool_call_chunks"]:
                print(f"   Chunk #{chunk_idx}")
        else:
            first_chunks = analysis["tool_call_chunks"][:5]
            last_chunks = analysis["tool_call_chunks"][-5:]
            for chunk_idx in first_chunks:
                print(f"   Chunk #{chunk_idx}")
            print("   ...")
            for chunk_idx in last_chunks:
                print(f"   Chunk #{chunk_idx}")
    
    # Show image URL findings
    if analysis["image_urls"]:
        print(f"\n🖼️  IMAGE URLS FOUND ({len(analysis['image_urls'])}):")
        print("-" * 25)
        for i, image_url in enumerate(analysis["image_urls"], 1):
            print(f"   {i}. Alt text: {image_url['alt_text']}")
            print(f"      URL: {image_url['url'][:80]}...")
    
    # Show chunks where image URLs were found
    if analysis["image_url_chunks"]:
        print(f"\n📦 CHUNKS CONTAINING IMAGE URLS:")
        print("-" * 35)
        # Show first few and last few for brevity
        if len(analysis["image_url_chunks"]) <= 10:
            for chunk_idx in analysis["image_url_chunks"]:
                print(f"   Chunk #{chunk_idx}")
        else:
            first_chunks = analysis["image_url_chunks"][:5]
            last_chunks = analysis["image_url_chunks"][-5:]
            for chunk_idx in first_chunks:
                print(f"   Chunk #{chunk_idx}")
            print("   ...")
            for chunk_idx in last_chunks:
                print(f"   Chunk #{chunk_idx}")


async def main():
    """Main function demonstrating comprehensive chunk analysis."""
    print("🔍 COMPREHENSIVE STREAMING RESPONSE ANALYZER")
    print("=" * 50)
    print("This program provides detailed analysis of each chunk")
    print("to find tool call information in streaming responses.\n")
    
    # Create image agent for testing
    image_agent = create_image_agent(debug=False, use_remote=False)
    prompt = "Create an image of a cyberpunk cityscape"
    
    print(f"Prompt: '{prompt}'")
    
    # Streaming analysis with comprehensive chunk examination
    print(f"\n1️⃣  COMPREHENSIVE CHUNK EXAMINATION")
    print("-" * 40)
    
    try:
        # Get streaming iterator
        run_stream = image_agent.run(
            prompt,
            stream=True,
            stream_intermediate_steps=True
        )
        
        # Collect and examine ALL chunks in detail
        print("📦 Collecting and examining ALL chunks...")
        chunks_data = collect_and_examine_chunks(run_stream)
        print(f"✅ Examined {len(chunks_data)} chunks in detail")
        
        # Perform comprehensive analysis
        print("🧠 Performing comprehensive analysis...")
        analysis = comprehensive_analysis(chunks_data)
        
        # Display detailed findings
        print_detailed_findings(chunks_data, analysis)
        
        # Summary
        print(f"\n📊 FINAL SUMMARY:")
        print("-" * 20)
        print(f"Final status: {analysis['status']}")
        print(f"Final content length: {len(str(analysis['final_content']))} characters")
        print(f"Unique tool calls found: {len(analysis['all_tool_calls'])}")
        print(f"Image URLs found: {len(analysis['image_urls'])}")
        
    except Exception as e:
        print(f"❌ Error in comprehensive analysis: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("✅ COMPREHENSIVE ANALYSIS COMPLETE")
    print("=" * 50)
    print("Key findings:")
    print("• Tool calls can appear in both 'tools' (list) and 'tool' (single) attributes")
    print("• Image URLs are embedded in content as markdown")
    print("• Different chunks contain different types of information")
    print("• The final response is in the last chunk or completed status chunk")


if __name__ == "__main__":
    asyncio.run(main())