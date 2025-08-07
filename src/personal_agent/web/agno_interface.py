# -*- coding: utf-8 -*-
"""
Streamlit web interface module for the Personal AI Agent using agno framework.

This module provides a simplified Streamlit-based web interface with a clean,
straightforward design focused on query input and response display.
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional

import requests
import streamlit as st

# Optional imports for performance visualization
try:
    import altair as alt
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Add the src directory to the path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from personal_agent.config.settings import get_userid
    from personal_agent.core.agno_agent import AgnoPersonalAgent
    from personal_agent.core.memory import is_memory_connected
    from personal_agent.utils.pag_logging import setup_logging
except ImportError:
    # Fallback for relative imports
    from ..config.settings import get_userid
    from ..core.memory import is_memory_connected
    from ..utils.pag_logging import setup_logging

if TYPE_CHECKING:
    from logging import Logger

    try:
        from personal_agent.core.agno_agent import AgnoPersonalAgent
    except ImportError:
        from ..core.agno_agent import AgnoPersonalAgent

# Global variables
logger: "Logger" = setup_logging()
agno_agent: Optional["AgnoPersonalAgent"] = None

# Memory function references (async functions from agno)
query_knowledge_base_func: Optional[callable] = None
store_interaction_func: Optional[callable] = None
clear_knowledge_base_func: Optional[callable] = None


def initialize_agent(
    agent: "AgnoPersonalAgent", query_kb_func, store_int_func, clear_kb_func
):
    """
    Initialize the global agent and memory functions.

    :param agent: Agno agent instance
    :param query_kb_func: Function to query knowledge base (async)
    :param store_int_func: Function to store interactions (async)
    :param clear_kb_func: Function to clear knowledge base (async)
    """
    global agno_agent, query_knowledge_base_func, store_interaction_func, clear_knowledge_base_func

    agno_agent = agent
    query_knowledge_base_func = query_kb_func
    store_interaction_func = store_int_func
    clear_knowledge_base_func = clear_kb_func

    # Store in Streamlit session state for proper access
    if hasattr(st, "session_state"):
        st.session_state.agno_agent = agent
        st.session_state.query_knowledge_base_func = query_kb_func
        st.session_state.store_interaction_func = store_int_func
        st.session_state.clear_knowledge_base_func = clear_kb_func

    if logger:
        logger.info(
            "Agno agent and memory functions initialized for Streamlit interface"
        )


def run_async_in_thread(coroutine):
    """Helper function to run async functions in a thread with a new event loop."""

    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()

    import threading

    result_container = {"result": None, "error": None, "done": False}

    def worker():
        try:
            result_container["result"] = thread_target()
        except Exception as e:
            result_container["error"] = e
        finally:
            result_container["done"] = True

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout=60)  # 60 second timeout

    error = result_container["error"]
    if error is not None:
        if isinstance(error, Exception):
            raise error
        else:
            raise RuntimeError(f"Async operation failed: {error}")

    if not result_container["done"]:
        raise TimeoutError("Async operation timed out")

    return result_container["result"]


def get_ollama_models(ollama_url):
    """Query Ollama API to get available models."""
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
        else:
            st.error(f"Failed to fetch models from Ollama: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to Ollama at {ollama_url}: {str(e)}")
        return []


async def create_agno_agent_with_params(model_name, ollama_url):
    """Create an agno agent with specific model and URL parameters."""
    try:
        from personal_agent.config.settings import (
            AGNO_KNOWLEDGE_DIR,
            AGNO_STORAGE_DIR,
            USE_MCP,
        )
        from personal_agent.core.agno_agent import create_agno_agent
    except ImportError:
        from ..config.settings import AGNO_KNOWLEDGE_DIR, AGNO_STORAGE_DIR, USE_MCP
        from ..core.agno_agent import create_agno_agent

    agent = await create_agno_agent(
        model_provider="ollama",
        model_name=model_name,
        enable_memory=True,
        enable_mcp=USE_MCP,
        storage_dir=AGNO_STORAGE_DIR,
        knowledge_dir=AGNO_KNOWLEDGE_DIR,
        debug=True,
        user_id=get_userid(),
        ollama_base_url=ollama_url,
        alltools=True,  # Ensure all tools are initialized
    )
    return agent


def handle_agno_response(run_stream: Iterator, display_metrics: bool = False) -> str:
    """
    Handle agno RunResponse stream and extract the content properly.

    :param run_stream: Iterator of RunResponse objects from agno
    :param display_metrics: Whether to display metrics in Streamlit
    :return: The response content as string
    """
    try:
        # Import agno utilities for response handling
        from agno.utils.pprint import pprint_run_response

        # Process the stream - this will handle the response properly
        # For now, we'll collect the stream and extract content
        response_content = ""

        # Collect all responses from the stream
        for response in run_stream:
            if hasattr(response, "content") and response.content:
                response_content += response.content

        # If we have an agent with run_response, get the final content
        # This is where the actual response content will be after streaming
        return response_content.strip() if response_content else "No response generated"

    except Exception as e:
        logger.error(f"Error handling agno response: {e}")
        return f"Error processing response: {str(e)}"


def extract_response_content(agent, display_metrics: bool = False, display_tool_calls: bool = False) -> tuple[str, dict, list, list]:
    """
    Extract response content, metrics, tool calls, and per-message data from agno agent after run.
    Uses the correct method to get tool calls from the agent.

    :param agent: The agno agent instance
    :param display_metrics: Whether to return metrics
    :param display_tool_calls: Whether to return tool calls
    :return: Tuple of (response_content, metrics, tool_calls, message_data)
    """
    response_content = ""
    metrics = {}
    tool_calls = []
    message_data = []

    try:
        # Get the response content from the agent's run_response
        if hasattr(agent, "run_response") and agent.run_response:
            if hasattr(agent.run_response, "messages") and agent.run_response.messages:
                # Get content from the last assistant message
                for message in agent.run_response.messages:
                    if message.role == "assistant" and hasattr(message, "content") and message.content:
                        response_content = message.content

            # Get aggregated metrics if requested
            if display_metrics and hasattr(agent.run_response, "metrics"):
                metrics = agent.run_response.metrics

        # Use the correct method to get tool calls from the agent
        if display_tool_calls and hasattr(agent, "get_last_tool_calls"):
            try:
                tools_used = agent.get_last_tool_calls()
                if tools_used:
                    for tool_call in tools_used:
                        formatted_tool = format_tool_call_for_debug(tool_call)
                        tool_calls.append(formatted_tool)
            except Exception as e:
                logger.warning(f"Error getting tool calls from agent: {e}")

        return (
            response_content.strip() if response_content else "No response generated"
        ), metrics, tool_calls, message_data

    except Exception as e:
        logger.error(f"Error extracting response content: {e}")
        return f"Error extracting response: {str(e)}", {}, [], []


def sanitize_for_json_display(data):
    """
    Sanitize data for safe JSON display in Streamlit.
    Handles circular references, non-serializable objects, and other JSON issues.
    """
    try:
        # Try to serialize to JSON first to check if it's valid
        json.dumps(data)
        return data
    except (TypeError, ValueError, RecursionError) as e:
        # If serialization fails, create a safe representation
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                try:
                    # Try to serialize individual values
                    json.dumps(value)
                    sanitized[key] = value
                except (TypeError, ValueError, RecursionError):
                    # Convert problematic values to string representation
                    sanitized[key] = f"<Non-serializable: {type(value).__name__}>"
            return sanitized
        elif isinstance(data, (list, tuple)):
            sanitized = []
            for item in data:
                try:
                    json.dumps(item)
                    sanitized.append(item)
                except (TypeError, ValueError, RecursionError):
                    sanitized.append(f"<Non-serializable: {type(item).__name__}>")
            return sanitized
        else:
            # For other types, return a string representation
            return f"<Non-serializable: {type(data).__name__}>"


def format_tool_call_for_debug(tool_call):
    """Standardize tool call format for consistent storage and display."""
    
    # Add debugging information to understand the object structure
    tool_type = type(tool_call).__name__
    available_attributes = [attr for attr in dir(tool_call) if not attr.startswith('_')]
    
    if logger:
        logger.debug(f"Processing tool call of type: {tool_type}")
        logger.debug(f"Available attributes: {available_attributes}")
    
    # Handle ToolExecution objects specifically
    if hasattr(tool_call, "tool_name") and hasattr(tool_call, "tool_args"):
        # ToolExecution object format
        tool_name = getattr(tool_call, "tool_name", "Unknown")
        tool_args = getattr(tool_call, "tool_args", {})
        tool_result = getattr(tool_call, "result", None)
        tool_error = getattr(tool_call, "tool_call_error", False)
        
        return {
            "name": tool_name,
            "arguments": tool_args,
            "result": tool_result,
            "status": "error" if tool_error else "success",
            "raw_type": tool_type,
            "available_attributes": available_attributes,
            "name_source": "tool_name",
            "args_source": "tool_args",
            "result_source": "result",
        }
    elif hasattr(tool_call, "name"):
        # Direct tool object
        return {
            "name": getattr(tool_call, "name", "Unknown"),
            "arguments": getattr(tool_call, "arguments", {}),
            "result": getattr(tool_call, "result", None),
            "status": "success",
            "raw_type": tool_type,
            "available_attributes": available_attributes,
            "name_source": "name",
            "args_source": "arguments",
            "result_source": "result",
        }
    elif hasattr(tool_call, "function"):
        # Tool call with function attribute
        return {
            "name": getattr(tool_call.function, "name", "Unknown"),
            "arguments": getattr(tool_call.function, "arguments", {}),
            "result": getattr(tool_call, "result", None),
            "status": "success",
            "raw_type": tool_type,
            "available_attributes": available_attributes,
            "name_source": "function.name",
            "args_source": "function.arguments",
            "result_source": "result",
        }
    else:
        # Fallback for unknown format - include debugging info
        return {
            "name": tool_type,
            "arguments": {},
            "result": str(tool_call),
            "status": "unknown",
            "raw_type": tool_type,
            "available_attributes": available_attributes,
            "raw_str": str(tool_call),
            "name_source": "type_name",
            "args_source": "none",
            "result_source": "str_conversion",
        }


def display_tool_calls_inline(container, tools):
    """Display tool calls in real-time during streaming."""
    if not tools:
        return

    with container.container():
        st.markdown("**🔧 Tool Calls:**")
        for i, tool in enumerate(tools, 1):
            tool_name = getattr(tool, "name", "Unknown Tool")
            tool_args = getattr(tool, "arguments", {})

            with st.expander(f"Tool {i}: {tool_name}", expanded=False):
                if tool_args:
                    st.json(tool_args)
                else:
                    st.write("No arguments")


def main():
    """Main Streamlit application."""
    # Page configuration
    st.set_page_config(
        page_title="Personal Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for better styling
    st.markdown(
        """
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-connected {
        background-color: #10b981;
        animation: pulse 2s infinite;
    }
    .status-disconnected {
        background-color: #ef4444;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #2563eb;
        color: white;
        margin-left: 2rem;
    }
    .agent-message {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        margin-right: 2rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Main header
    st.markdown(
        """
    <div class="main-header">
        <h1>🤖 Personal AI Agent</h1>
        <p>Powered by Agno Framework with MCP Tools</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize session state for model selection
    if "current_ollama_url" not in st.session_state:
        try:
            from personal_agent.config.settings import OLLAMA_URL
        except ImportError:
            from ..config.settings import OLLAMA_URL
        st.session_state.current_ollama_url = OLLAMA_URL

    if "current_model" not in st.session_state:
        try:
            from personal_agent.config.settings import LLM_MODEL
        except ImportError:
            from ..config.settings import LLM_MODEL
        st.session_state.current_model = LLM_MODEL

    # Check if agent is initialized (prefer session state, fallback to global)
    global agno_agent
    current_agent = st.session_state.get("agno_agent", agno_agent)
    if current_agent is None:
        # Try to initialize the agent if running directly
        st.info("🔄 Initializing agent...")
        try:
            # Import the agent creation function
            try:
                from personal_agent.config.settings import (
                    AGNO_KNOWLEDGE_DIR,
                    AGNO_STORAGE_DIR,
                    LLM_MODEL,
                    OLLAMA_URL,
                    USE_MCP,
                )
                from personal_agent.core.agno_agent import create_agno_agent
            except ImportError:
                from ..config.settings import (
                    AGNO_KNOWLEDGE_DIR,
                    AGNO_STORAGE_DIR,
                    LLM_MODEL,
                    OLLAMA_URL,
                    USE_MCP,
                )
                from ..core.agno_agent import create_agno_agent

            # Initialize the agent
            with st.spinner("Creating agno agent..."):

                async def init_agent():
                    agent = await create_agno_agent(
                        model_provider="ollama",
                        model_name=st.session_state.current_model,
                        enable_memory=True,
                        enable_mcp=USE_MCP,
                        storage_dir=AGNO_STORAGE_DIR,
                        knowledge_dir=AGNO_KNOWLEDGE_DIR,
                        debug=True,
                        user_id=get_userid(),
                        ollama_base_url=st.session_state.current_ollama_url,
                        alltools=True,  # Ensure all tools are initialized
                    )
                    return agent

                # Run the async initialization
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    current_agent = loop.run_until_complete(init_agent())
                finally:
                    loop.close()

                # Store in session state and globals
                st.session_state.agno_agent = current_agent
                agno_agent = current_agent

                # Create dummy memory functions for compatibility
                async def dummy_query_kb(query: str) -> str:
                    return "Memory handled by Agno"

                async def dummy_store_interaction(query: str, response: str) -> bool:
                    return True

                async def dummy_clear_kb() -> bool:
                    return True

                # Store memory functions
                st.session_state.query_knowledge_base_func = dummy_query_kb
                st.session_state.store_interaction_func = dummy_store_interaction
                st.session_state.clear_knowledge_base_func = dummy_clear_kb

                st.success("✅ Agent initialized successfully!")
                st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to initialize agent: {str(e)}")
            st.info(
                "Please run the agent using: `python -m personal_agent.agno_main --web`"
            )
            st.info("Or ensure all dependencies are properly installed.")
            return

    # Ensure session state has the agent
    if "agno_agent" not in st.session_state:
        st.session_state.agno_agent = current_agent

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    # Initialize performance tracking session state
    if "performance_stats" not in st.session_state:
        st.session_state.performance_stats = {
            "total_requests": 0,
            "total_response_time": 0,
            "average_response_time": 0,
            "total_tokens": 0,
            "average_tokens": 0,
            "fastest_response": float("inf"),
            "slowest_response": 0,
            "tool_calls_count": 0,
            "memory_operations": 0,
        }

    if "debug_metrics" not in st.session_state:
        st.session_state.debug_metrics = []

    # Sidebar
    with st.sidebar:
        st.header("🤖 Model Selection")

        # Ollama URL input
        new_ollama_url = st.text_input(
            "Ollama URL:",
            value=st.session_state.current_ollama_url,
            help="Enter the Ollama server URL (e.g., http://localhost:11434)",
        )

        # Button to fetch models
        if st.button("🔄 Fetch Available Models", use_container_width=True):
            with st.spinner("Fetching models..."):
                available_models = get_ollama_models(new_ollama_url)
                if available_models:
                    st.session_state.available_models = available_models
                    st.session_state.current_ollama_url = new_ollama_url
                    st.success(f"Found {len(available_models)} models!")
                else:
                    st.error("No models found or connection failed")

        # Model selection dropdown
        if "available_models" in st.session_state and st.session_state.available_models:
            current_model_index = 0
            if st.session_state.current_model in st.session_state.available_models:
                current_model_index = st.session_state.available_models.index(
                    st.session_state.current_model
                )

            selected_model = st.selectbox(
                "Select Model:",
                st.session_state.available_models,
                index=current_model_index,
                help="Choose an Ollama model to use for the agent",
            )

            # Button to apply model selection
            if st.button("🚀 Apply Model Selection", use_container_width=True):
                if (
                    selected_model != st.session_state.current_model
                    or new_ollama_url != st.session_state.current_ollama_url
                ):
                    with st.spinner("Reinitializing agent with new model..."):
                        try:
                            # Update session state
                            st.session_state.current_model = selected_model
                            st.session_state.current_ollama_url = new_ollama_url

                            # Reinitialize agent asynchronously
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                new_agent = loop.run_until_complete(
                                    create_agno_agent_with_params(
                                        selected_model, new_ollama_url
                                    )
                                )
                            finally:
                                loop.close()

                            # Update session state and globals
                            st.session_state.agno_agent = new_agent
                            agno_agent = new_agent

                            # Update current_agent reference
                            current_agent = new_agent

                            # Create dummy memory functions for compatibility
                            async def dummy_query_kb(query: str) -> str:
                                return "Memory handled by Agno"

                            async def dummy_store_interaction(
                                query: str, response: str
                            ) -> bool:
                                return True

                            async def dummy_clear_kb() -> bool:
                                return True

                            # Store memory functions
                            st.session_state.query_knowledge_base_func = dummy_query_kb
                            st.session_state.store_interaction_func = (
                                dummy_store_interaction
                            )
                            st.session_state.clear_knowledge_base_func = dummy_clear_kb

                            # Clear chat history for new model
                            st.session_state.messages = []

                            st.success(f"Agent updated to use model: {selected_model}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to initialize agent: {str(e)}")
                            if logger:
                                logger.error(f"Failed to reinitialize agent: {str(e)}")
                else:
                    st.info("Model and URL are already current")
        else:
            st.info("Click 'Fetch Available Models' to see available models")

        st.divider()

        st.header("🔧 Agent Status")

        # Memory status
        memory_status = is_memory_connected()
        memory_indicator = (
            "status-connected" if memory_status else "status-disconnected"
        )
        memory_text = "Connected" if memory_status else "Disconnected"

        st.markdown(
            f"""
        <div>
            <span class="status-indicator {memory_indicator}"></span>
            <strong>Memory:</strong> {memory_text}
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Agent info
        st.markdown(
            f"""
        <div style="margin-top: 1rem;">
            <span class="status-indicator status-connected"></span>
            <strong>Agent:</strong> Active
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div style="margin-top: 0.5rem;">
            <strong>Current Model:</strong> {st.session_state.current_model}
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div style="margin-top: 0.5rem;">
            <strong>Current Ollama URL:</strong> {st.session_state.current_ollama_url}
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div style="margin-top: 0.5rem;">
            <strong>User ID:</strong> {get_userid()}
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div style="margin-top: 0.5rem;">
            <strong>Session:</strong> {st.session_state.session_id[:8]}...
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.divider()

        # Controls
        st.header("🎛️ Controls")

        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        if st.button("🧠 Clear Memory", use_container_width=True):
            clear_func = st.session_state.get(
                "clear_knowledge_base_func", clear_knowledge_base_func
            )
            if clear_func:
                try:
                    with st.spinner("Clearing memory..."):
                        result = run_async_in_thread(clear_func())
                    st.success(f"Memory cleared: {result}")
                except Exception as e:
                    st.error(f"Error clearing memory: {str(e)}")
            else:
                st.warning("Clear memory function not available")

        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()

        if st.button("🧠 Show All Memories", use_container_width=True):
            if current_agent and hasattr(current_agent, "agno_memory"):
                try:
                    with st.spinner("Retrieving memories..."):
                        # Get memories for the specific user using the native memory manager
                        memories = current_agent.agno_memory.get_user_memories(
                            user_id=get_userid()
                        )

                    if memories:
                        st.subheader("📚 Stored Memories")
                        for i, memory in enumerate(memories, 1):
                            # Handle memory content - UserMemory objects have direct attributes
                            memory_content = getattr(memory, "memory", "No content")
                            if not memory_content:
                                memory_content = "No content"

                            # Create expandable section with truncated title
                            title_preview = (
                                memory_content[:50] + "..."
                                if len(memory_content) > 50
                                else memory_content
                            )

                            with st.expander(f"Memory {i}: {title_preview}"):
                                st.write(f"**Content:** {memory_content}")

                                # Display additional memory attributes if available
                                memory_id = getattr(memory, "memory_id", "N/A")
                                if memory_id != "N/A":
                                    st.write(f"**Memory ID:** {memory_id}")

                                last_updated = getattr(memory, "last_updated", "N/A")
                                if last_updated != "N/A":
                                    st.write(f"**Last Updated:** {last_updated}")

                                input_text = getattr(memory, "input", "N/A")
                                if input_text != "N/A":
                                    st.write(f"**Input:** {input_text}")

                                topics = getattr(memory, "topics", [])
                                if topics:
                                    st.write(f"**Topics:** {', '.join(topics)}")
                    else:
                        st.info(
                            "📝 No memories stored yet. Start chatting to create some memories!"
                        )

                except Exception as e:
                    st.error(f"❌ Error retrieving memories: {str(e)}")
                    if logger:
                        logger.error(f"Error retrieving memories: {str(e)}")
            else:
                st.warning(
                    "⚠️ Agno memory system not available or agent not properly initialized"
                )

        # Debug Section
        st.header("🐛 Debug")

        # Metrics toggle
        if st.button("📊 Toggle Response Metrics", use_container_width=True):
            st.session_state.show_metrics = not st.session_state.get(
                "show_metrics", False
            )

        if st.session_state.get("show_metrics", False):
            st.success("✅ Metrics display enabled")

            # Display last response metrics if available
            if "last_response_metrics" in st.session_state:
                st.subheader("📊 Last Response Metrics")
                with st.expander("View Metrics Details", expanded=True):
                    try:
                        sanitized_metrics = sanitize_for_json_display(st.session_state.last_response_metrics)
                        st.json(sanitized_metrics)
                    except Exception as e:
                        st.error(f"Error displaying metrics: {str(e)}")
                        st.write("**Raw Metrics:**")
                        st.write(str(st.session_state.last_response_metrics))
            else:
                st.info("No metrics available yet. Send a message to see metrics.")
        else:
            st.info("📊 Metrics display disabled")

        # Tool calls toggle
        if st.button("🔧 Toggle Tool Calls", use_container_width=True):
            st.session_state.show_tool_calls = not st.session_state.get(
                "show_tool_calls", False
            )

        if st.session_state.get("show_tool_calls", False):
            st.success("✅ Tool calls display enabled")

            # Display last response tool calls if available
            if "last_response_tool_calls" in st.session_state:
                tool_calls = st.session_state.last_response_tool_calls
                if tool_calls:
                    st.subheader("🔧 Last Response Tool Calls")
                    with st.expander("View Tool Calls Details", expanded=True):
                        for i, tool_call in enumerate(tool_calls, 1):
                            # Handle both old and new format
                            tool_name = tool_call.get("name", "Unknown")
                            tool_status = tool_call.get("status", "unknown")
                            
                            # Status indicator
                            status_icon = "✅" if tool_status == "success" else "❓" if tool_status == "unknown" else "❌"
                            
                            st.write(f"**Tool Call {i}:** {status_icon} {tool_name}")
                            
                            # Show ID and type if available (old format)
                            if "id" in tool_call:
                                st.write(f"- **ID:** {tool_call.get('id', 'N/A')}")
                            if "type" in tool_call:
                                st.write(f"- **Type:** {tool_call.get('type', 'N/A')}")
                            
                            # Show status
                            st.write(f"- **Status:** {tool_status}")
                            
                            # Handle arguments (both old and new format)
                            args = None
                            if 'function' in tool_call and isinstance(tool_call['function'], dict):
                                # Old format
                                args = tool_call['function'].get('arguments', '{}')
                                st.write(f"- **Function Name:** {tool_call['function'].get('name', 'N/A')}")
                            elif 'arguments' in tool_call:
                                # New format
                                args = tool_call.get('arguments', {})
                            
                            if args is not None:
                                st.write(f"- **Arguments:**")
                                try:
                                    if isinstance(args, str):
                                        import json
                                        parsed_args = json.loads(args)
                                        st.json(parsed_args)
                                    elif isinstance(args, dict) and args:
                                        st.json(args)
                                    else:
                                        st.write(f"  {args}")
                                except (json.JSONDecodeError, Exception):
                                    st.write(f"  {args}")
                            
                            # Show result if available
                            if "result" in tool_call and tool_call["result"]:
                                st.write(f"- **Result:**")
                                result = tool_call["result"]
                                if isinstance(result, str) and len(result) > 200:
                                    st.write(f"  {result[:200]}...")
                                else:
                                    st.write(f"  {result}")
                            
                            # Show error if available
                            if "error" in tool_call:
                                st.write(f"- **Error:** {tool_call['error']}")
                            
                            # Show debugging information
                            if "raw_type" in tool_call:
                                st.write(f"- **Raw Type:** {tool_call['raw_type']}")
                            
                            if "available_attributes" in tool_call:
                                with st.expander("🔍 Debug: Available Attributes", expanded=False):
                                    st.write("**All object attributes:**")
                                    st.write(tool_call["available_attributes"])
                            
                            if "name_source" in tool_call:
                                st.write(f"- **Name Source:** {tool_call['name_source']}")
                            if "args_source" in tool_call:
                                st.write(f"- **Args Source:** {tool_call['args_source']}")
                            if "result_source" in tool_call:
                                st.write(f"- **Result Source:** {tool_call['result_source']}")
                            
                            if "raw_str" in tool_call:
                                with st.expander("🔍 Debug: Raw Object String", expanded=False):
                                    st.code(tool_call["raw_str"])
                            
                            st.write("---")
                else:
                    st.info("No tool calls in last response.")
            
            # Display per-message data if available
            if "last_response_message_data" in st.session_state:
                message_data = st.session_state.last_response_message_data
                if message_data:
                    st.subheader("📝 Per-Message Details")
                    with st.expander("View Message-by-Message Breakdown", expanded=False):
                        # Handle both single message dict and list of messages
                        if isinstance(message_data, list):
                            message_list = message_data
                        else:
                            message_list = [message_data]
                        
                        for i, msg_data in enumerate(message_list, 1):
                            st.write(f"**Assistant Message {i}:**")
                            if isinstance(msg_data, dict) and msg_data.get("content"):
                                st.write(f"- **Content:** {msg_data['content'][:100]}{'...' if len(msg_data['content']) > 100 else ''}")
                            if isinstance(msg_data, dict) and msg_data.get("tool_calls"):
                                st.write(f"- **Tool Calls:** {len(msg_data['tool_calls'])} calls")
                                for j, tc in enumerate(msg_data['tool_calls'], 1):
                                    # Handle both old and new format
                                    tool_name = tc.get("name", "Unknown")
                                    if not tool_name or tool_name == "Unknown":
                                        # Try old format
                                        if 'function' in tc and isinstance(tc['function'], dict):
                                            tool_name = tc['function'].get('name', 'Unknown')
                                    
                                    tool_status = tc.get("status", "unknown")
                                    status_icon = "✅" if tool_status == "success" else "❓" if tool_status == "unknown" else "❌"
                                    st.write(f"  - Call {j}: {status_icon} {tool_name}")
                            if isinstance(msg_data, dict) and msg_data.get("metrics"):
                                st.write(f"- **Message Metrics:**")
                                try:
                                    sanitized_metrics = sanitize_for_json_display(msg_data["metrics"])
                                    st.json(sanitized_metrics)
                                except Exception as e:
                                    st.error(f"Error displaying message metrics: {str(e)}")
                                    st.write(f"**Raw Metrics:** {str(msg_data['metrics'])}")
                            st.write("---")
            else:
                st.info("No tool calls available yet. Send a message that triggers tools to see tool calls.")
        else:
            st.info("🔧 Tool calls display disabled")

        # Performance Statistics Section
        if PANDAS_AVAILABLE and st.session_state.performance_stats["total_requests"] > 0:
            st.subheader("📊 Performance Statistics")
            stats = st.session_state.performance_stats
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Requests", stats["total_requests"])
                st.metric("Avg Response Time", f"{stats['average_response_time']:.3f}s")
                st.metric(
                    "Fastest Response",
                    f"{stats['fastest_response']:.3f}s" if stats["fastest_response"] != float("inf") else "N/A"
                )
            with col2:
                st.metric("Total Tool Calls", stats["tool_calls_count"])
                st.metric("Avg Tokens/Request", f"{stats['average_tokens']:.0f}")
                st.metric("Slowest Response", f"{stats['slowest_response']:.3f}s")

            # Response Time Trend Chart
            if len(st.session_state.debug_metrics) > 1:
                st.subheader("📈 Response Time Trend")
                df = pd.DataFrame(st.session_state.debug_metrics)
                df = df[df["success"]]  # Only show successful requests
                if not df.empty and len(df) > 1:
                    chart_data = df[["timestamp", "response_time"]].copy().set_index("timestamp")
                    chart = (
                        alt.Chart(chart_data.reset_index())
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("timestamp:O", title="Time"),
                            y=alt.Y("response_time:Q", title="Response Time (s)"),
                            tooltip=["timestamp:O", "response_time:Q"],
                        )
                        .properties(title="Response Time Trend", height=200)
                    )
                    st.altair_chart(chart, use_container_width=True)

            # Recent Request Details
            st.subheader("🔍 Recent Request Details")
            if st.session_state.debug_metrics:
                for entry in reversed(st.session_state.debug_metrics[-5:]):  # Show last 5
                    success_icon = "✅" if entry["success"] else "❌"
                    with st.expander(f"{success_icon} {entry['timestamp']} - {entry['response_time']}s"):
                        st.write(f"**Prompt:** {entry['prompt']}")
                        st.write(f"**Response Time:** {entry['response_time']}s")
                        st.write(f"**Input Tokens:** {entry['input_tokens']}")
                        st.write(f"**Output Tokens:** {entry['output_tokens']}")
                        st.write(f"**Total Tokens:** {entry['total_tokens']}")
                        st.write(f"**Tool Calls:** {entry['tool_calls']}")
                        if not entry["success"]:
                            st.write(f"**Error:** {entry.get('error', 'Unknown error')}")
            else:
                st.info("No debug metrics available yet.")

        elif not PANDAS_AVAILABLE:
            st.warning("📊 Performance charts require pandas and altair. Install with: `pip install pandas altair`")
        else:
            st.info("📊 No performance data yet. Send a message to see statistics.")

        st.divider()

        # Agent Information
        if st.button("ℹ️ Show Agent Info", use_container_width=True):
            st.session_state.show_agent_info = not st.session_state.get(
                "show_agent_info", False
            )

        if st.session_state.get("show_agent_info", False):
            st.subheader("Agent Details")
            if current_agent:
                agent_info = current_agent.get_agent_info()
                for key, value in agent_info.items():
                    if isinstance(value, dict):
                        st.write(
                            f"**{key.replace('_', ' ').title()}:** {len(value)} items"
                        )
                    elif isinstance(value, list):
                        st.write(
                            f"**{key.replace('_', ' ').title()}:** {len(value)} items"
                        )
                    else:
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")

    # Main chat interface
    st.header("💬 Chat with Your Agent")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"*{message['timestamp']}*")

    # Chat input
    if prompt := st.chat_input(
        "Ask me anything... I can help with research, analysis, and more!"
    ):
        # Add user message to chat history
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.messages.append(
            {"role": "user", "content": prompt, "timestamp": timestamp}
        )

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"*{timestamp}*")

        # Get agent response
        with st.chat_message("assistant"):
            # Create containers for tool calls and response
            tool_calls_container = st.empty()
            resp_container = st.empty()
            
            with st.spinner("🤔 Thinking..."):
                start_time = time.time()
                start_timestamp = datetime.now()
                tool_calls_made = 0
                tool_call_details = []
                all_tools_used = []
                
                try:
                    # Handle AgnoPersonalAgent with proper tool call collection
                    if isinstance(current_agent, AgnoPersonalAgent):
                        
                        async def run_agent_with_streaming():
                            nonlocal tool_calls_made, tool_call_details, all_tools_used
                            
                            try:
                                # Use the simplified agent.run() method
                                response_content = await current_agent.run(
                                    prompt, add_thought_callback=None
                                )
                                
                                # Get tool calls using the correct method that collects from streaming events
                                tools_used = current_agent.get_last_tool_calls()
                                
                                # Process and display tool calls
                                if tools_used:
                                    tool_calls_made = len(tools_used)
                                    if logger:
                                        logger.info(f"Processing {len(tools_used)} tool calls from streaming events")
                                    
                                    for i, tool_call in enumerate(tools_used):
                                        if logger:
                                            logger.debug(f"Tool call {i}: {tool_call}")
                                        formatted_tool = format_tool_call_for_debug(tool_call)
                                        tool_call_details.append(formatted_tool)
                                        all_tools_used.append(tool_call)
                                    
                                    # Display tool calls in real-time
                                    display_tool_calls_inline(tool_calls_container, all_tools_used)
                                
                                return response_content
                                
                            except Exception as e:
                                raise Exception(f"Error in agent execution: {e}") from e
                        
                        # Run the async agent execution
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            response_content = loop.run_until_complete(run_agent_with_streaming())
                        finally:
                            loop.close()
                        
                        # Use the response content directly
                        if not response_content:
                            response_content = "No response generated by agent"
                    
                    else:
                        # Fallback for non-AgnoPersonalAgent
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            agent_response = loop.run_until_complete(current_agent.run(prompt))
                            response_content = (
                                agent_response.content
                                if hasattr(agent_response, "content")
                                else str(agent_response)
                            )
                        finally:
                            loop.close()

                    # Display the final response
                    resp_container.markdown(response_content)

                    # Calculate response time and performance metrics
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Calculate token estimates
                    input_tokens = len(prompt.split()) * 1.3
                    output_tokens = len(response_content.split()) * 1.3 if response_content else 0
                    total_tokens = input_tokens + output_tokens

                    # Update performance stats with real-time tool call count
                    stats = st.session_state.performance_stats
                    stats["total_requests"] += 1
                    stats["total_response_time"] += response_time
                    stats["average_response_time"] = stats["total_response_time"] / stats["total_requests"]
                    stats["total_tokens"] += total_tokens
                    stats["average_tokens"] = stats["total_tokens"] / stats["total_requests"]
                    stats["fastest_response"] = min(stats["fastest_response"], response_time)
                    stats["slowest_response"] = max(stats["slowest_response"], response_time)
                    stats["tool_calls_count"] += tool_calls_made

                    # Store debug metrics with standardized format
                    debug_entry = {
                        "timestamp": start_timestamp.strftime("%H:%M:%S"),
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "response_time": round(response_time, 3),
                        "input_tokens": round(input_tokens),
                        "output_tokens": round(output_tokens),
                        "total_tokens": round(total_tokens),
                        "tool_calls": tool_calls_made,
                        "tool_call_details": tool_call_details,
                        "response_type": (
                            "AgnoPersonalAgent"
                            if isinstance(current_agent, AgnoPersonalAgent)
                            else "Unknown"
                        ),
                        "success": True,
                    }
                    st.session_state.debug_metrics.append(debug_entry)
                    # Keep only last 10 entries
                    if len(st.session_state.debug_metrics) > 10:
                        st.session_state.debug_metrics.pop(0)

                    # Extract metrics and tool calls for sidebar display
                    final_response, metrics, tool_calls, message_data = extract_response_content(
                        current_agent, display_metrics=True, display_tool_calls=True
                    )

                    # Add to chat history with metadata for future reference
                    chat_message_data = {
                        "role": "assistant",
                        "content": response_content,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "tool_calls": tool_call_details,  # Store the standardized list
                        "response_time": response_time,
                    }
                    st.session_state.messages.append(chat_message_data)

                    # Store metrics in session state for sidebar display
                    if metrics and st.session_state.get("show_metrics", False):
                        st.session_state.last_response_metrics = metrics

                    # Store tool calls and message data in session state for sidebar display
                    if st.session_state.get("show_tool_calls", False):
                        st.session_state.last_response_tool_calls = tool_call_details if tool_call_details else []
                        st.session_state.last_response_message_data = message_data if message_data else []
                    
                    # Also add session metrics if available
                    if st.session_state.get("show_metrics", False) and hasattr(current_agent, "session_metrics"):
                        try:
                            session_metrics = current_agent.session_metrics
                            if session_metrics:
                                st.session_state.last_session_metrics = session_metrics
                        except Exception as e:
                            logger.warning(f"Could not extract session metrics: {e}")

                    # Store interaction in memory if available (do this in background)
                    store_func = st.session_state.get(
                        "store_interaction_func", store_interaction_func
                    )
                    if store_func:
                        try:
                            run_async_in_thread(store_func(prompt, response_content))
                            if logger:
                                logger.info("Interaction stored in memory")
                        except Exception as e:
                            if logger:
                                logger.warning(f"Could not store interaction: {e}")

                    # Force immediate UI refresh to show the response
                    st.rerun()

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)

                    # Add error to chat history immediately
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_msg,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                    # Log failed request in debug metrics
                    debug_entry = {
                        "timestamp": start_timestamp.strftime("%H:%M:%S"),
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "response_time": round(response_time, 3),
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "tool_calls": 0,
                        "tool_call_details": [],
                        "response_type": "Error",
                        "success": False,
                        "error": str(e),
                    }
                    st.session_state.debug_metrics.append(debug_entry)
                    if len(st.session_state.debug_metrics) > 10:
                        st.session_state.debug_metrics.pop(0)

                    if logger:
                        logger.error(f"Error processing query: {str(e)}")

                    # Force immediate UI refresh to show the error
                    st.rerun()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #64748b;'>"
        "Personal AI Agent • Powered by Agno Framework • "
        f"Session: {st.session_state.session_id[:8]}..."
        "</div>",
        unsafe_allow_html=True,
    )


# Legacy Flask compatibility functions (for backward compatibility)
def create_app():
    """Legacy function for Flask compatibility."""
    st.warning(
        "Flask interface has been replaced with Streamlit. Use main() function instead."
    )
    return None


def register_routes(*args, **kwargs):
    """Legacy function for Flask compatibility."""
    st.warning("Flask routes are no longer used. The interface now uses Streamlit.")


if __name__ == "__main__":
    main()
