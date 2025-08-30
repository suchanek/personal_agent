#!/usr/bin/env python3
"""
Enhanced Streaming Response Analyzer for Agno Agents

This program demonstrates how to:
1. Collect all chunks from streaming responses with detailed inspection
2. Find exactly where the final agent response is located
3. Extract and display tool call results with full details
4. Map the complete conversation flow through streaming chunks
5. Show the complete RunResponse structure including messages

Focus: Finding final agent response location and tool call results
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union
import json
from rich.pretty import pprint
from rich.console import Console

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent, RunResponse
from agno.run.response import RunResponseEvent, RunEvent
from agno.tools.dalle import DalleTools
from agno.utils.common import dataclass_to_dict

from src.personal_agent.team.reasoning_team import create_image_agent

console = Console()


def collect_streaming_chunks_with_details(
    run_stream: Iterator[RunResponseEvent],
) -> List[Dict[str, Any]]:
    """
    Collect all chunks from a streaming response iterator with detailed analysis.

    Args:
        run_stream: Iterator of RunResponseEvent objects from agent.run(stream=True)

    Returns:
        List of detailed chunk dictionaries with full inspection
    """
    chunks = []
    for i, chunk in enumerate(run_stream):
        # Convert chunk to dict to see all fields
        chunk_dict = dataclass_to_dict(chunk)

        # Add our analysis metadata
        chunk_analysis = {
            "chunk_index": i,
            "chunk_dict": chunk_dict,
            "raw_chunk": chunk,
            "analysis": {
                "has_content": hasattr(chunk, "content") and chunk.content is not None,
                "content_preview": (
                    str(chunk.content)[:200] + "..."
                    if hasattr(chunk, "content") and chunk.content
                    else None
                ),
                "has_messages": hasattr(chunk, "messages")
                and chunk.messages is not None,
                "messages_count": (
                    len(chunk.messages)
                    if hasattr(chunk, "messages") and chunk.messages
                    else 0
                ),
                "has_tools": hasattr(chunk, "tools") and chunk.tools is not None,
                "tools_count": (
                    len(chunk.tools) if hasattr(chunk, "tools") and chunk.tools else 0
                ),
                "event_type": getattr(chunk, "event", "unknown"),
                "status": getattr(chunk, "status", None),
                "chunk_type": type(chunk).__name__,
            },
        }

        chunks.append(chunk_analysis)

    return chunks


def find_final_agent_response(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find exactly where the final agent response is located in the streaming chunks.

    Args:
        chunks: List of detailed chunk dictionaries

    Returns:
        Dictionary with final response location and content
    """
    final_response_info = {
        "found": False,
        "chunk_index": None,
        "content": None,
        "location_details": [],
        "candidate_chunks": [],
    }

    # Look for different patterns that might contain the final response
    for chunk_info in chunks:
        chunk = chunk_info["raw_chunk"]
        chunk_idx = chunk_info["chunk_index"]
        analysis = chunk_info["analysis"]

        # Check for completion status
        if analysis["status"] and "completed" in str(analysis["status"]).lower():
            final_response_info["candidate_chunks"].append(
                {
                    "chunk_index": chunk_idx,
                    "reason": "Has completion status",
                    "status": analysis["status"],
                    "content": analysis["content_preview"],
                }
            )

        # Check for final content in messages
        if hasattr(chunk, "messages") and chunk.messages:
            for msg_idx, message in enumerate(chunk.messages):
                if hasattr(message, "role") and message.role == "assistant":
                    if hasattr(message, "content") and message.content:
                        final_response_info["candidate_chunks"].append(
                            {
                                "chunk_index": chunk_idx,
                                "message_index": msg_idx,
                                "reason": "Assistant message with content",
                                "role": message.role,
                                "content": (
                                    str(message.content)[:200] + "..."
                                    if len(str(message.content)) > 200
                                    else str(message.content)
                                ),
                            }
                        )

        # Check for content in the chunk itself
        if analysis["has_content"] and analysis["content_preview"]:
            # Skip if it's just tool output
            content_str = str(chunk.content).lower()
            if not any(
                indicator in content_str
                for indicator in ["tool_call", "function_call", '{"']
            ):
                final_response_info["candidate_chunks"].append(
                    {
                        "chunk_index": chunk_idx,
                        "reason": "Chunk has meaningful content",
                        "content": analysis["content_preview"],
                    }
                )

    # Determine the most likely final response
    if final_response_info["candidate_chunks"]:
        # Prefer the last assistant message or completion status chunk
        best_candidate = final_response_info["candidate_chunks"][-1]
        final_response_info["found"] = True
        final_response_info["chunk_index"] = best_candidate["chunk_index"]
        final_response_info["content"] = best_candidate.get("content", "")

    return final_response_info


def find_tool_call_results(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find and extract tool call results from streaming chunks.

    Args:
        chunks: List of detailed chunk dictionaries

    Returns:
        Dictionary with tool call results and their locations
    """
    tool_results_info = {
        "tool_calls_found": [],
        "tool_results_found": [],
        "complete_tool_flow": [],
    }

    for chunk_info in chunks:
        chunk = chunk_info["raw_chunk"]
        chunk_idx = chunk_info["chunk_index"]
        analysis = chunk_info["analysis"]

        # Check for tool calls in messages
        if hasattr(chunk, "messages") and chunk.messages:
            for msg_idx, message in enumerate(chunk.messages):
                # Look for tool calls
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_call_info = {
                            "chunk_index": chunk_idx,
                            "message_index": msg_idx,
                            "type": "tool_call",
                            "tool_call": tool_call,
                            "details": {
                                "function_name": (
                                    tool_call.get("function", {}).get("name")
                                    if isinstance(tool_call, dict)
                                    else getattr(tool_call, "function", {}).get(
                                        "name", "unknown"
                                    )
                                ),
                                "arguments": (
                                    tool_call.get("function", {}).get("arguments")
                                    if isinstance(tool_call, dict)
                                    else getattr(tool_call, "function", {}).get(
                                        "arguments", "{}"
                                    )
                                ),
                            },
                        }
                        tool_results_info["tool_calls_found"].append(tool_call_info)

                # Look for tool results
                if hasattr(message, "role") and message.role == "tool":
                    tool_result_info = {
                        "chunk_index": chunk_idx,
                        "message_index": msg_idx,
                        "type": "tool_result",
                        "role": message.role,
                        "content": message.content,
                        "tool_name": getattr(message, "tool_name", None),
                        "tool_args": getattr(message, "tool_args", None),
                        "tool_call_error": getattr(message, "tool_call_error", None),
                    }
                    tool_results_info["tool_results_found"].append(tool_result_info)

        # Check for tools in the chunk itself
        if analysis["has_tools"]:
            for tool_idx, tool in enumerate(chunk.tools):
                tool_info = {
                    "chunk_index": chunk_idx,
                    "tool_index": tool_idx,
                    "type": "chunk_tool",
                    "tool": tool,
                    "tool_name": getattr(tool, "tool_name", "unknown"),
                    "tool_args": getattr(tool, "arguments", None)
                    or getattr(tool, "tool_args", None),
                }
                tool_results_info["tool_results_found"].append(tool_info)

    # Create complete tool flow
    all_tool_events = (
        tool_results_info["tool_calls_found"] + tool_results_info["tool_results_found"]
    )
    tool_results_info["complete_tool_flow"] = sorted(
        all_tool_events, key=lambda x: x["chunk_index"]
    )

    return tool_results_info


def print_comprehensive_analysis(
    chunks: List[Dict[str, Any]],
    final_response: Dict[str, Any],
    tool_results: Dict[str, Any],
) -> None:
    """
    Print a comprehensive analysis of the streaming response with focus on final response and tool results.
    """
    console.print("\n🎯 ENHANCED STREAMING RESPONSE ANALYSIS", style="bold blue")
    console.print("=" * 60, style="blue")

    console.print(f"\n📊 OVERVIEW", style="bold green")
    console.print(f"   Total chunks processed: {len(chunks)}")
    console.print(f"   Tool calls found: {len(tool_results['tool_calls_found'])}")
    console.print(f"   Tool results found: {len(tool_results['tool_results_found'])}")

    # Show final agent response location
    console.print(f"\n🎯 FINAL AGENT RESPONSE LOCATION", style="bold yellow")
    console.print("-" * 40, style="yellow")

    if final_response["found"]:
        console.print(
            f"✅ Final response found in chunk #{final_response['chunk_index']}"
        )
        console.print(f"📝 Content: {final_response['content']}")

        console.print(f"\n🔍 All candidate locations:")
        for i, candidate in enumerate(final_response["candidate_chunks"]):
            console.print(
                f"   {i+1}. Chunk #{candidate['chunk_index']}: {candidate['reason']}"
            )
            if candidate.get("content"):
                console.print(f"      Content preview: {candidate['content'][:100]}...")
    else:
        console.print("❌ No clear final agent response found")

    # Show tool call results
    console.print(f"\n🔧 TOOL CALL RESULTS ANALYSIS", style="bold cyan")
    console.print("-" * 40, style="cyan")

    if tool_results["complete_tool_flow"]:
        console.print("📋 Complete tool execution flow:")
        for i, event in enumerate(tool_results["complete_tool_flow"]):
            console.print(
                f"\n   {i+1}. Chunk #{event['chunk_index']} - {event['type'].upper()}"
            )

            if event["type"] == "tool_call":
                console.print(f"      Function: {event['details']['function_name']}")
                console.print(f"      Arguments: {event['details']['arguments']}")

            elif event["type"] == "tool_result":
                console.print(f"      Tool: {event.get('tool_name', 'unknown')}")
                console.print(f"      Result: {str(event['content'])[:200]}...")
                if event.get("tool_call_error"):
                    console.print(
                        f"      Error: {event['tool_call_error']}", style="red"
                    )

            elif event["type"] == "chunk_tool":
                console.print(f"      Tool: {event['tool_name']}")
                console.print(f"      Args: {event['tool_args']}")
    else:
        console.print("❌ No tool calls or results found")

    # Show detailed chunk breakdown
    console.print(f"\n📈 DETAILED CHUNK BREAKDOWN", style="bold magenta")
    console.print("-" * 40, style="magenta")

    for chunk_info in chunks:
        analysis = chunk_info["analysis"]
        console.print(
            f"\nChunk #{chunk_info['chunk_index']} ({analysis['chunk_type']}):"
        )
        console.print(f"   Event: {analysis['event_type']}")
        console.print(f"   Status: {analysis['status']}")
        console.print(f"   Has content: {analysis['has_content']}")
        console.print(f"   Messages: {analysis['messages_count']}")
        console.print(f"   Tools: {analysis['tools_count']}")

        if analysis["content_preview"]:
            console.print(f"   Content preview: {analysis['content_preview'][:100]}...")


def print_raw_chunk_details(chunks: List[Dict[str, Any]], chunk_index: int) -> None:
    """Print raw details of a specific chunk for deep inspection."""
    if 0 <= chunk_index < len(chunks):
        console.print(f"\n🔍 RAW CHUNK #{chunk_index} DETAILS", style="bold red")
        console.print("=" * 50, style="red")

        chunk_info = chunks[chunk_index]

        console.print("📋 Chunk Dictionary (excluding messages for readability):")
        chunk_dict_copy = chunk_info["chunk_dict"].copy()
        if "messages" in chunk_dict_copy:
            messages_count = (
                len(chunk_dict_copy["messages"]) if chunk_dict_copy["messages"] else 0
            )
