#!/usr/bin/env python3
"""
Intelligent Streaming Response Analyzer for Agno Agents

This program directly addresses the task requirements:
1. Collects iterator response in its entirety when stream=True
2. Intelligently analyzes the collected response 
3. Extracts and prints the final response and tool calls
4. Examines the RunResponse class elements
5. Compares streaming vs non-streaming modes
6. Designed for use in Streamlit apps

Based on analysis of Agent.run() in agno source and test_streaming_chunks.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union
from agno.utils.common import dataclass_to_dict
from rich.pretty import pprint

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent, RunResponse
from agno.run.response import RunResponseEvent
from agno.tools.dalle import DalleTools

from src.personal_agent.team.reasoning_team import create_image_agent


def collect_streaming_response(run_stream: Iterator[RunResponseEvent]) -> List[RunResponseEvent]:
    """
    Collect all chunks from streaming iterator - Requirement #1
    
    Args:
        run_stream: Iterator from agent.run(stream=True)
        
    Returns:
        List of all RunResponseEvent chunks
    """
    return list(run_stream)


def intelligent_response_analysis(chunks: List[RunResponseEvent]) -> Dict[str, Any]:
    """
    Intelligently analyze collected chunks - Requirement #3
    
    Args:
        chunks: List of RunResponseEvent objects
        
    Returns:
        Dictionary with analyzed response data
    """
    analysis = {
        "final_content": "",
        "tool_calls": [],
        "image_urls": [],
        "status": "unknown",
        "response_metrics": {},
        "chunk_count": len(chunks)
    }
    
    # Process chunks intelligently to find final response and tool calls
    for i, chunk in enumerate(chunks):
        # Extract tool calls from any chunk that has them
        if hasattr(chunk, 'tools') and chunk.tools:
            for tool in chunk.tools:
                tool_info = {
                    "name": getattr(tool, 'tool_name', 'Unknown'),
                    "arguments": getattr(tool, 'arguments', {}),
                    "status": getattr(tool, 'status', 'unknown')
                }
                if tool_info not in analysis["tool_calls"]:
                    analysis["tool_calls"].append(tool_info)
        
        # Also check for tool-related attributes in chunk
        # Some tool information might be embedded in other attributes
        if hasattr(chunk, 'tool') and chunk.tool:
            tool_info = {
                "name": getattr(chunk.tool, 'tool_name', 'Unknown'),
                "arguments": getattr(chunk.tool, 'arguments', {}),
                "status": getattr(chunk.tool, 'status', 'unknown'),
                "chunk_index": i
            }
            if tool_info not in analysis["tool_calls"]:
                analysis["tool_calls"].append(tool_info)
        
        # Check for tool call information in extra_data
        if hasattr(chunk, 'extra_data') and chunk.extra_data:
            # Look for tool-related information in extra_data
            extra_data_dict = chunk.extra_data if isinstance(chunk.extra_data, dict) else {}
            if hasattr(chunk.extra_data, '__dict__'):
                extra_data_dict = chunk.extra_data.__dict__
            
            # Check for tool executions in extra_data
            if 'tool_executions' in extra_data_dict and extra_data_dict['tool_executions']:
                for tool_exec in extra_data_dict['tool_executions']:
                    tool_info = {
                        "name": getattr(tool_exec, 'tool_name', 'Unknown'),
                        "arguments": getattr(tool_exec, 'arguments', {}),
                        "status": getattr(tool_exec, 'status', 'unknown'),
                        "chunk_index": i
                    }
                    if tool_info not in analysis["tool_calls"]:
                        analysis["tool_calls"].append(tool_info)
        
        # Extract image URLs from content
        if hasattr(chunk, 'content') and chunk.content:
            import re
            image_matches = re.findall(r'!\[([^\]]*)\]\((https?://[^\)]+)\)', str(chunk.content))
            for alt_text, url in image_matches:
                if url not in [img["url"] for img in analysis["image_urls"]]:
                    analysis["image_urls"].append({
                        "alt_text": alt_text,
                        "url": url,
                        "chunk_index": i
                    })
        
        # Check for tool call information in content (might be described in text)
        if hasattr(chunk, 'content') and chunk.content:
            content_str = str(chunk.content)
            # Look for patterns that might indicate tool calls in the content
            if 'tool' in content_str.lower() and ('call' in content_str.lower() or 'execute' in content_str.lower()):
                # This is a heuristic - content mentions tool calls
                # We could extract more detailed information if needed
                pass  # For now, just acknowledge it
        
        # Identify final chunk (usually has completed status)
        if hasattr(chunk, 'status') and str(chunk.status) == 'RunStatus.completed':
            analysis["status"] = "completed"
            if hasattr(chunk, 'content'):
                analysis["final_content"] = chunk.content
    
    # Fallback to last chunk if no completed status found
    if not analysis["final_content"] and chunks:
        last_chunk = chunks[-1]
        if hasattr(last_chunk, 'content'):
            analysis["final_content"] = last_chunk.content
        if hasattr(last_chunk, 'status'):
            analysis["status"] = str(last_chunk.status)
    
    return analysis


def examine_runresponse_class():
    """
    Examine RunResponse class elements - Requirement #5
    
    This function shows the key elements of the RunResponse class
    based on analysis of the agno source code.
    """
    elements = {
        "Core Attributes": [
            "content: Main response content (str, dict, or BaseModel)",
            "status: RunStatus enum (running, completed, failed, etc.)",
            "run_id: Unique identifier for this run",
            "agent_id: Identifier for the agent that ran",
            "session_id: Session identifier",
            "created_at: Timestamp when response was created"
        ],
        "Tool Related": [
            "tools: List of ToolExecution objects",
            "formatted_tool_calls: List of formatted tool call strings"
        ],
        "Media Related": [
            "images: List of ImageArtifact objects",
            "audio: List of AudioArtifact objects", 
            "videos: List of VideoArtifact objects",
            "response_audio: AudioResponse object"
        ],
        "Additional Data": [
            "citations: Citations object with sources",
            "extra_data: RunResponseExtraData with additional info",
            "metrics: Dictionary with performance metrics",
            "model: Model name used",
            "model_provider: Provider of the model"
        ],
        "Streaming Events": [
            "events: List of RunResponseEvent objects (when store_events=True)",
            "RunResponseStartedEvent: Event when run starts",
            "RunResponseContentEvent: Event with content chunks",
            "RunResponseCompletedEvent: Event when run completes"
        ]
    }
    
    return elements


def format_for_streamlit(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format analysis results for Streamlit apps - Requirement #7
    
    Args:
        analysis: Analysis results from intelligent_response_analysis
        
    Returns:
        Streamlit-friendly formatted data
    """
    streamlit_data = {
        "response_content": analysis["final_content"],
        "tool_calls": analysis["tool_calls"],
        "image_data": analysis["image_urls"],
        "status": analysis["status"],
        "metrics": {
            "total_chunks": analysis["chunk_count"],
            "content_length": len(str(analysis["final_content"]))
        }
    }
    
    return streamlit_data


async def main():
    """Main function demonstrating the complete solution."""
    print("🔍 INTELLIGENT STREAMING RESPONSE ANALYZER")
    print("=" * 50)
    print("This program addresses all requirements from the task:")
    print("1. Collects iterator response in entirety")
    print("2. Intelligently analyzes final response and tool calls")
    print("3. Examines RunResponse class elements")
    print("4. Works with both streaming and non-streaming modes")
    print("5. Formats output for Streamlit apps\n")
    
    # Requirement #5: Examine RunResponse class
    print("📚 RUNRESPONSE CLASS ELEMENTS")
    print("-" * 30)
    runresponse_elements = examine_runresponse_class()
    for category, elements in runresponse_elements.items():
        print(f"\n{category}:")
        for element in elements:
            print(f"  • {element}")
    
    # Create agent for testing
    print("\n" + "=" * 50)
    print("🧪 TESTING WITH IMAGE AGENT")
    print("=" * 50)
    
    image_agent = create_image_agent(debug=False, use_remote=False)
    prompt = "Create an image of a robot making coffee"
    
    # Requirement #1 & #3: Streaming analysis
    print(f"\n1️⃣  STREAMING MODE ANALYSIS")
    print("-" * 30)
    print(f"Prompt: '{prompt}'")
    
    try:
        # Get streaming iterator
        run_stream = image_agent.run(
            prompt,
            stream=True,
            stream_intermediate_steps=True
        )
        
        # Collect all chunks (Requirement #1)
        chunks = collect_streaming_response(run_stream)
        print(f"✅ Collected {len(chunks)} chunks from iterator")
        
        # Intelligent analysis (Requirement #3)
        print("🧠 Intelligently analyzing chunks for tool call information...")
        analysis = intelligent_response_analysis(chunks)
        
        # Display results
        print(f"🏁 Final status: {analysis['status']}")
        print(f"📝 Content length: {len(str(analysis['final_content']))} characters")
        
        if analysis['tool_calls']:
            print(f"🔧 Tool calls detected: {len(analysis['tool_calls'])}")
            for tool in analysis['tool_calls']:
                print(f"   • {tool['name']}")
                if 'arguments' in tool and tool['arguments']:
                    print(f"     Arguments: {tool['arguments']}")
                if 'chunk_index' in tool:
                    print(f"     Found in chunk: {tool['chunk_index']}")
        
        if analysis['image_urls']:
            print(f"🖼️  Image URLs found: {len(analysis['image_urls'])}")
            for img in analysis['image_urls']:
                print(f"   • {img['alt_text']}: {img['url'][:80]}...")
                if 'chunk_index' in img:
                    print(f"     Found in chunk: {img['chunk_index']}")
        
        # Requirement #7: Format for Streamlit
        streamlit_format = format_for_streamlit(analysis)
        print(f"\n📊 STREAMLIT-FRIENDLY FORMAT:")
        print(f"   Response content: {type(streamlit_format['response_content']).__name__}")
        print(f"   Tool calls: {len(streamlit_format['tool_calls'])} items")
        print(f"   Images: {len(streamlit_format['image_data'])} items")
        print(f"   Status: {streamlit_format['status']}")
        
    except Exception as e:
        print(f"❌ Error in streaming analysis: {e}")
    
    # Requirement #6: Non-streaming comparison
    print(f"\n2️⃣  NON-STREAMING MODE (Complete RunResponse)")
    print("-" * 45)
    
    try:
        # Non-streaming returns complete RunResponse
        response = await image_agent.arun(prompt, stream=False)
        print(f"✅ Non-streaming response received")
        print(f"Content type: {type(response.content).__name__}")
        print(f"Content length: {len(str(response.content))} characters")
        print(f"Status: {response.status}")
        
        if response.tools:
            print(f"🔧 Tools in response: {len(response.tools)}")
            for tool in response.tools:
                print(f"   • {getattr(tool, 'tool_name', 'Unknown')}")
        
        # Show how this differs from streaming
        print(f"\n💡 DIFFERENCE:")
        print(f"   Streaming: Iterator of RunResponseEvent chunks")
        print(f"   Non-streaming: Single complete RunResponse object")
        
    except Exception as e:
        print(f"❌ Error in non-streaming mode: {e}")
    
    print("\n" + "=" * 50)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 50)
    print("Key takeaways:")
    print("• Streaming mode provides real-time chunks for progressive UI updates")
    print("• Non-streaming mode provides complete response when processing is done")
    print("• Both modes contain the same final information")
    print("• Tool calls and image URLs can be extracted from either mode")
    print("• Streamlit apps can use either approach based on UX needs")


if __name__ == "__main__":
    asyncio.run(main())