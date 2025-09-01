"""
Agent Utilities for Streamlit Applications

This module provides utilities for working with Agno agents in Streamlit applications,
specifically for handling streaming responses and extracting final results with tool calls.

Key Features:
- Collect streaming responses from Agno agents
- Intelligently analyze and extract final content
- Extract tool calls and image URLs
- Format results for Streamlit display
"""

import re
from typing import Any, Dict, Iterator, List, Optional, Union

from agno.agent import Agent, RunResponse
from agno.run.response import RunResponseEvent
from agno.models.response import ToolExecution

try:
    import streamlit as st
except ImportError:
    # Fallback for non-Streamlit environments
    st = None


def get_agent_instance():
    """
    Get the current agent instance from Streamlit session state.
    
    This function handles both single agent and team modes, returning the appropriate
    agent instance for use with StreamlitMemoryHelper and other utilities.
    
    Returns:
        AgnoPersonalAgent or TeamWrapper: The current agent instance, or None if not available
    """
    if st is None:
        return None
        
    # Check current mode from session state
    agent_mode = st.session_state.get("agent_mode", "single")
    
    if agent_mode == "team":
        # Team mode - return the team or team wrapper
        team = st.session_state.get("team")
        if team:
            # Check if it's already a wrapper or needs wrapping
            if hasattr(team, 'agno_memory') and hasattr(team, 'user_id'):
                return team  # Already wrapped
            else:
                # Return the team directly - the helpers will handle wrapping
                return team
        return None
    else:
        # Single agent mode
        return st.session_state.get("agent")


def check_agent_status(agent):
    """
    Check the status of an agent instance and return comprehensive status information.
    
    Args:
        agent: The agent instance to check (AgnoPersonalAgent, Team, or TeamWrapper)
        
    Returns:
        dict: Status dictionary with keys:
            - initialized: bool - Whether the agent is properly initialized
            - memory_available: bool - Whether memory system is available
            - user_id: str - The user ID associated with the agent
            - error: str - Error message if any issues detected
    """
    status = {
        "initialized": False,
        "memory_available": False,
        "user_id": None,
        "error": None
    }
    
    if agent is None:
        status["error"] = "Agent instance is None"
        return status
    
    try:
        # Check if it's a team or single agent
        if hasattr(agent, 'members'):
            # Team mode
            status["initialized"] = len(getattr(agent, 'members', [])) > 0
            
            # Check memory availability through team
            if hasattr(agent, 'agno_memory'):
                status["memory_available"] = agent.agno_memory is not None
            elif hasattr(agent, 'members') and agent.members:
                # Check first member (knowledge agent) for memory
                knowledge_agent = agent.members[0]
                status["memory_available"] = hasattr(knowledge_agent, 'agno_memory') and knowledge_agent.agno_memory is not None
            
            # Get user ID from team or first member
            if hasattr(agent, 'user_id'):
                status["user_id"] = agent.user_id
            elif hasattr(agent, 'members') and agent.members and hasattr(agent.members[0], 'user_id'):
                status["user_id"] = agent.members[0].user_id
                
        else:
            # Single agent mode
            status["initialized"] = getattr(agent, '_initialized', False)
            status["memory_available"] = hasattr(agent, 'agno_memory') and agent.agno_memory is not None
            status["user_id"] = getattr(agent, 'user_id', None)
            
    except Exception as e:
        status["error"] = f"Error checking agent status: {str(e)}"
    
    return status


def collect_streaming_response(run_stream: Iterator[RunResponseEvent]) -> List[RunResponseEvent]:
    """
    Collect all chunks from a streaming response iterator.
    
    Args:
        run_stream: Iterator of RunResponseEvent objects from agent.run(stream=True)
        
    Returns:
        List of all RunResponseEvent chunks
    """
    return list(run_stream)


def extract_final_response_and_tools(
    chunks: List[RunResponseEvent]
) -> Dict[str, Any]:
    """
    Intelligently extract final response content and tool calls from streaming chunks.
    
    This function analyzes all chunks from a streaming response to reconstruct
    the complete final response, including any tool calls made and image URLs generated.
    
    Args:
        chunks: List of RunResponseEvent objects from streaming response
        
    Returns:
        Dictionary containing:
            - final_content: The complete final response content
            - tool_calls: List of tool calls made during the response
            - image_urls: List of image URLs found in the content
            - status: Final status of the run
            - chunk_count: Total number of chunks processed
    """
    result = {
        "final_content": "",
        "tool_calls": [],
        "image_urls": [],
        "status": "unknown",
        "chunk_count": len(chunks)
    }
    
    # Process each chunk to build complete response
    for chunk in chunks:
        # Extract tool calls from any chunk that has them
        # Check for tool in 'tool' attribute (single tool) - primary source in streaming
        if hasattr(chunk, 'tool') and chunk.tool:
            tool_info = {
                "name": getattr(chunk.tool, 'tool_name', 'Unknown'),
                "arguments": getattr(chunk.tool, 'arguments', {}),
                "status": getattr(chunk.tool, 'status', 'unknown')
            }
            if tool_info not in result["tool_calls"]:
                result["tool_calls"].append(tool_info)
        
        # Check for tools in 'tools' attribute (list of tools) - secondary source
        if hasattr(chunk, 'tools') and chunk.tools:
            for tool in chunk.tools:
                tool_info = {
                    "name": getattr(tool, 'tool_name', 'Unknown'),
                    "arguments": getattr(tool, 'arguments', {}),
                    "status": getattr(tool, 'status', 'unknown')
                }
                if tool_info not in result["tool_calls"]:
                    result["tool_calls"].append(tool_info)
        
        # Extract image URLs from content
        if hasattr(chunk, 'content') and chunk.content:
            # Find markdown image patterns ![alt](url)
            image_matches = re.findall(r'!\[([^\]]*)\]\((https?://[^\)]+)\)', str(chunk.content))
            for alt_text, url in image_matches:
                if url not in [img["url"] for img in result["image_urls"]]:
                    result["image_urls"].append({
                        "alt_text": alt_text,
                        "url": url
                    })
        
        # Identify the final chunk (usually has completed status)
        if hasattr(chunk, 'status') and str(chunk.status) == 'RunStatus.completed':
            result["status"] = "completed"
            if hasattr(chunk, 'content'):
                result["final_content"] = chunk.content
    
    # Fallback to last chunk if no completed status found
    if not result["final_content"] and chunks:
        last_chunk = chunks[-1]
        if hasattr(last_chunk, 'content'):
            result["final_content"] = last_chunk.content
        if hasattr(last_chunk, 'status'):
            result["status"] = str(last_chunk.status)
    
    return result


def format_for_streamlit_display(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format analysis results for Streamlit application display.
    
    This function prepares the analysis results in a format that's easy to use
    in Streamlit applications, with proper data types and organization.
    
    Args:
        analysis_result: Dictionary from extract_final_response_and_tools
        
    Returns:
        Streamlit-friendly formatted dictionary
    """
    return {
        "response_content": analysis_result["final_content"],
        "tool_calls": analysis_result["tool_calls"],
        "images": analysis_result["image_urls"],
        "status": analysis_result["status"],
        "metrics": {
            "total_chunks": analysis_result["chunk_count"],
            "content_length": len(str(analysis_result["final_content"])),
            "tool_call_count": len(analysis_result["tool_calls"]),
            "image_count": len(analysis_result["image_urls"])
        }
    }


def get_complete_response_from_agent(
    agent: Agent,
    message: str,
    stream: bool = False,
    **kwargs
) -> Union[RunResponse, Dict[str, Any]]:
    """
    Get complete response from an Agno agent, handling both streaming and non-streaming modes.
    
    This function provides a unified interface for getting responses from Agno agents,
    whether in streaming or non-streaming mode, and returns data formatted for Streamlit.
    
    Args:
        agent: Agno Agent instance
        message: Input message/prompt for the agent
        stream: Whether to use streaming mode
        **kwargs: Additional arguments to pass to agent.run()
        
    Returns:
        For streaming: Dictionary with analyzed results
        For non-streaming: RunResponse object
    """
    if stream:
        # Streaming mode - collect and analyze chunks
        run_stream = agent.run(message, stream=True, **kwargs)
        chunks = collect_streaming_response(run_stream)
        analysis = extract_final_response_and_tools(chunks)
        return format_for_streamlit_display(analysis)
    else:
        # Non-streaming mode - return complete response
        return agent.run(message, stream=False, **kwargs)


# Example usage for Streamlit apps:
"""
import streamlit as st
from src.personal_agent.streamlit.utils.agent_utils import get_complete_response_from_agent

# In your Streamlit app:
def run_agent_and_display_results(agent, prompt):
    # For real-time streaming updates
    with st.spinner("Processing..."):
        result = get_complete_response_from_agent(
            agent, 
            prompt, 
            stream=True,
            stream_intermediate_steps=True
        )
    
    # Display results
    st.markdown(result["response_content"])
    
    # Display images if any
    for img in result["images"]:
        st.image(img["url"], caption=img["alt_text"])
    
    # Display tool calls
    if result["tool_calls"]:
        st.subheader("Tools Used")
        for tool in result["tool_calls"]:
            st.write(f"• {tool['name']}")
"""
