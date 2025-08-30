#!/usr/bin/env python3
"""
Enhanced Debug script to examine the team's response structure using streaming analysis
to understand where image URLs and tool call results are located.
"""

import asyncio
import logging
import re
from pathlib import Path
import sys
import os
from typing import Any, Dict, Iterator, List

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.team.reasoning_team import create_team
from rich.console import Console
from agno.run.response import RunResponseEvent
from agno.utils.common import dataclass_to_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console = Console()


def extract_actual_final_response(content: str) -> str:
    """Extract the actual final response from content after </think> tags."""
    if '</think>' in content:
        parts = content.split('</think>')
        if len(parts) > 1:
            actual_response = parts[-1].strip()
            if actual_response:
                return actual_response
    return content


def collect_and_examine_team_chunks(run_stream: Iterator[RunResponseEvent]) -> List[Dict[str, Any]]:
    """
    Collect all chunks from team streaming response and examine each one.
    
    Args:
        run_stream: Iterator from team.run(stream=True)
        
    Returns:
        List of dictionaries with chunk data and analysis
    """
    chunks_data = []

    for i, chunk in enumerate(run_stream):
        chunk_info = {
            "index": i,
            "chunk_object": chunk,
            "event_type": getattr(chunk, "event", "unknown"),
            "has_content": hasattr(chunk, "content") and chunk.content is not None,
            "content_length": (
                len(str(chunk.content))
                if hasattr(chunk, "content") and chunk.content
                else 0
            ),
            "has_status": hasattr(chunk, "status"),
            "status": str(chunk.status) if hasattr(chunk, "status") else None,
            "has_member_responses": hasattr(chunk, "member_responses") and chunk.member_responses is not None,
            "member_responses_count": (
                len(chunk.member_responses) if hasattr(chunk, "member_responses") and chunk.member_responses else 0
            ),
            "has_tools": hasattr(chunk, "tools") and chunk.tools is not None,
            "has_tool": hasattr(chunk, "tool") and chunk.tool is not None,
            "image_urls_found": [],
            "tool_calls_found": [],
        }

        # Extract image URLs from content
        if hasattr(chunk, "content") and chunk.content:
            image_matches = re.findall(
                r"!\[([^\]]*)\]\((https?://[^\)]+)\)", str(chunk.content)
            )
            for alt_text, url in image_matches:
                chunk_info["image_urls_found"].append(
                    {"alt_text": alt_text, "url": url}
                )

        # Extract tool calls from tool attribute (single)
        if hasattr(chunk, "tool") and chunk.tool:
            tool_info = {
                "source": "tool_single",
                "name": getattr(chunk.tool, "tool_name", "Unknown"),
                "arguments": getattr(chunk.tool, "arguments", {}),
                "result": getattr(chunk.tool, "result", None),
                "status": getattr(chunk.tool, "status", "unknown"),
            }
            chunk_info["tool_calls_found"].append(tool_info)

        # Extract tool calls from tools attribute (list)
        if hasattr(chunk, "tools") and chunk.tools:
            for tool in chunk.tools:
                tool_info = {
                    "source": "tools_list",
                    "name": getattr(tool, "tool_name", "Unknown"),
                    "arguments": getattr(tool, "arguments", {}),
                    "result": getattr(tool, "result", None),
                    "status": getattr(tool, "status", "unknown"),
                }
                chunk_info["tool_calls_found"].append(tool_info)

        chunks_data.append(chunk_info)

    return chunks_data


def analyze_team_response(chunks_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze team response chunks to extract final response and member responses.
    
    Args:
        chunks_data: List of chunk information
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "final_content": "",
        "actual_final_response": "",
        "final_chunk": None,
        "member_responses": [],
        "image_urls": [],
        "tool_calls": [],
        "status": "unknown",
        "total_chunks": len(chunks_data),
    }

    # Process all chunks
    for chunk_info in chunks_data:
        chunk = chunk_info["chunk_object"]
        
        # Collect image URLs
        for image_url in chunk_info["image_urls_found"]:
            if image_url not in analysis["image_urls"]:
                analysis["image_urls"].append(image_url)
        
        # Collect tool calls
        for tool_call in chunk_info["tool_calls_found"]:
            if tool_call not in analysis["tool_calls"]:
                analysis["tool_calls"].append(tool_call)
        
        # Extract member responses
        if hasattr(chunk, "member_responses") and chunk.member_responses:
            for member_response in chunk.member_responses:
                member_info = {
                    "agent_name": getattr(member_response, "agent_name", "Unknown"),
                    "content": getattr(member_response, "content", ""),
                    "chunk_index": chunk_info["index"]
                }
                
                # Extract actual response from member (after </think> tags)
                if member_info["content"]:
                    member_info["actual_response"] = extract_actual_final_response(member_info["content"])
                    
                    # Check for image URLs in member response
                    member_images = re.findall(
                        r"!\[([^\]]*)\]\((https?://[^\)]+)\)", member_info["actual_response"]
                    )
                    if member_images:
                        member_info["image_urls"] = [{"alt_text": alt, "url": url} for alt, url in member_images]
                
                analysis["member_responses"].append(member_info)
        
        # Identify final chunk
        if chunk_info["has_status"] and chunk_info["status"] == "RunStatus.completed":
            analysis["final_chunk"] = chunk
            analysis["status"] = "completed"
            if chunk_info["has_content"]:
                analysis["final_content"] = chunk.content

    # Fallback to last chunk if no completed status found
    if not analysis["final_content"] and chunks_data:
        last_chunk_info = chunks_data[-1]
        analysis["final_chunk"] = last_chunk_info["chunk_object"]
        if last_chunk_info["has_content"]:
            analysis["final_content"] = last_chunk_info["chunk_object"].content
        if last_chunk_info["has_status"]:
            analysis["status"] = last_chunk_info["status"]

    # Extract actual final response
    if analysis["final_content"]:
        analysis["actual_final_response"] = extract_actual_final_response(analysis["final_content"])

    return analysis


async def debug_team_streaming_response():
    """Debug the team's streaming response structure to understand image URL extraction."""
    
    console.print("🔍 [bold blue]Enhanced Team Response Streaming Analysis[/bold blue]")
    console.print("=" * 60)
    
    try:
        # Create the team
        console.print("Creating team...")
        team = await create_team(use_remote=False)
        
        # Test image creation request
        test_query = "create an image of a robot with a balloon"
        console.print(f"\n🤖 Testing query: '{test_query}'")
        
        # Get streaming response
        console.print("\n📡 [bold yellow]Getting streaming response...[/bold yellow]")
        run_stream = team.run(test_query, stream=True, stream_intermediate_steps=True)
        
        # Collect and examine all chunks
        console.print("📦 Collecting and examining ALL chunks...")
        chunks_data = collect_and_examine_team_chunks(run_stream)
        console.print(f"✅ Examined {len(chunks_data)} chunks in detail")
        
        # Analyze the team response
        console.print("🧠 Performing team response analysis...")
        analysis = analyze_team_response(chunks_data)
        
        # Display results
        console.print(f"\n📊 [bold yellow]TEAM RESPONSE ANALYSIS RESULTS:[/bold yellow]")
        console.print(f"Total chunks: {analysis['total_chunks']}")
        console.print(f"Final status: {analysis['status']}")
        console.print(f"Member responses found: {len(analysis['member_responses'])}")
        console.print(f"Tool calls found: {len(analysis['tool_calls'])}")
        console.print(f"Image URLs found: {len(analysis['image_urls'])}")
        
        # Show member responses
        if analysis["member_responses"]:
            console.print(f"\n👥 [bold green]MEMBER RESPONSES ({len(analysis['member_responses'])}):[/bold green]")
            for i, member in enumerate(analysis["member_responses"], 1):
                console.print(f"\n--- Member Response {i} ---")
                console.print(f"Agent: [bold]{member['agent_name']}[/bold]")
                console.print(f"Chunk: #{member['chunk_index']}")
                console.print(f"Content length: {len(member['content'])} characters")
                console.print(f"Actual response length: {len(member.get('actual_response', ''))} characters")
                
                # Show the FULL member content to see what the Image Agent actually returned
                console.print(f"\n📄 [bold yellow]FULL MEMBER CONTENT (What Image Agent returned to coordinator):[/bold yellow]")
                console.print("-" * 60)
                console.print(member['content'])
                console.print("-" * 60)
                
                if member.get('actual_response'):
                    console.print(f"\n✨ [bold cyan]EXTRACTED ACTUAL RESPONSE (After </think> tags):[/bold cyan]")
                    console.print("-" * 50)
                    console.print(member['actual_response'])
                    console.print("-" * 50)
                
                if member.get('image_urls'):
                    console.print(f"🖼️  [bold green]Image URLs found in this member:[/bold green]")
                    for img in member['image_urls']:
                        console.print(f"  - Alt: '{img['alt_text']}'")
                        console.print(f"  - URL: {img['url'][:80]}...")
                else:
                    console.print(f"❌ [bold red]No image URLs extracted from member response[/bold red]")
                    
                    # Check if there are image URLs in the raw content
                    raw_images = re.findall(r"!\[([^\]]*)\]\((https?://[^\)]+)\)", member['content'])
                    if raw_images:
                        console.print(f"🔍 [bold yellow]But found {len(raw_images)} image URLs in raw content:[/bold yellow]")
                        for alt, url in raw_images:
                            console.print(f"  - Alt: '{alt}'")
                            console.print(f"  - URL: {url[:80]}...")
        
        # Show tool calls
        if analysis["tool_calls"]:
            console.print(f"\n🔧 [bold yellow]TOOL CALLS FOUND ({len(analysis['tool_calls'])}):[/bold yellow]")
            for i, tool_call in enumerate(analysis["tool_calls"], 1):
                console.print(f"\n--- Tool Call {i} ---")
                console.print(f"Name: {tool_call['name']}")
                console.print(f"Source: {tool_call['source']}")
                console.print(f"Status: {tool_call['status']}")
                if tool_call.get('arguments'):
                    console.print(f"Arguments: {tool_call['arguments']}")
                if tool_call.get('result'):
                    console.print(f"Result: {str(tool_call['result'])[:200]}...")
        
        # Show final team response
        if analysis["actual_final_response"]:
            console.print(f"\n🎯 [bold cyan]ACTUAL FINAL TEAM RESPONSE:[/bold cyan]")
            console.print(f"Length: {len(analysis['actual_final_response'])} characters")
            console.print("-" * 50)
            console.print(analysis["actual_final_response"])
            console.print("-" * 50)
        
        # Show raw final content for comparison
        if analysis["final_content"]:
            console.print(f"\n🔍 [bold yellow]RAW FINAL CONTENT (Including thinking):[/bold yellow]")
            console.print(f"Length: {len(analysis['final_content'])} characters")
            console.print("-" * 50)
            # Show first 300 and last 300 characters
            content_str = str(analysis["final_content"])
            if len(content_str) > 600:
                console.print(f"{content_str[:300]}...")
                console.print("...")
                console.print(f"...{content_str[-300:]}")
            else:
                console.print(content_str)
            console.print("-" * 50)
        
        # Diagnosis
        console.print(f"\n💡 [bold cyan]DIAGNOSIS:[/bold cyan]")
        
        # Check if image URLs are in member responses but not in final response
        member_has_images = any(member.get('image_urls') for member in analysis['member_responses'])
        final_has_images = len(analysis['image_urls']) > 0
        
        if member_has_images and not final_has_images:
            console.print("🚨 [bold red]ISSUE FOUND:[/bold red] Image URLs are present in member responses but NOT in the final team response!")
            console.print("The team coordinator is not properly extracting and including image URLs from member responses.")
        elif member_has_images and final_has_images:
            console.print("✅ [bold green]SUCCESS:[/bold green] Image URLs found in both member responses AND final team response!")
        elif not member_has_images:
            console.print("❌ [bold red]NO IMAGES:[/bold red] No image URLs found in any member responses. Check if image agent is working properly.")
        else:
            console.print("🤔 [bold yellow]UNCLEAR:[/bold yellow] Need to investigate further...")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Error during debugging:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())


async def main():
    """Main debug function."""
    await debug_team_streaming_response()


if __name__ == "__main__":
    asyncio.run(main())
