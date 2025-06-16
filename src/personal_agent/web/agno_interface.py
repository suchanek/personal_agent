# -*- coding: utf-8 -*-
"""
Streamlit web interface module for the Personal AI Agent using agno framework.

This module provides a simplified Streamlit-based web interface with a clean,
straightforward design focused on query input and response display.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import streamlit as st

from ..config.settings import USER_ID
from ..core.memory import is_memory_connected
from ..utils.pag_logging import setup_logging

if TYPE_CHECKING:
    from logging import Logger

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
    if hasattr(st, 'session_state'):
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

    if result_container["error"]:
        error = result_container["error"]
        if isinstance(error, Exception):
            raise error
        else:
            raise RuntimeError(f"Async operation failed: {error}")

    if not result_container["done"]:
        raise TimeoutError("Async operation timed out")

    return result_container["result"]


def clean_response_content(response: str) -> str:
    """
    Clean the response content by removing thinking tags and other unwanted elements.

    :param response: Raw response from the agent
    :return: Cleaned response content
    """
    import re

    if not response:
        return response

    # Convert to string if it's not already
    if not isinstance(response, str):
        response = str(response)

    # Check if response is ONLY thinking content
    response_stripped = response.strip()

    if response_stripped.startswith("<think>") or response_stripped.startswith(
        "<think"
    ):
        think_close_match = re.search(
            r"</think\s*>", response, re.IGNORECASE | re.DOTALL
        )

        if not think_close_match:
            return "I'm processing your request, but my response was incomplete. Please try asking again."

        content_after_think = response[think_close_match.end() :].strip()
        if not content_after_think:
            return "I was thinking about your request but didn't provide a complete answer. Please try asking again."

    # Remove <think>...</think> tags and their content
    think_pattern = r"<think\s*>.*?</think\s*>"
    cleaned = re.sub(think_pattern, "", response, flags=re.DOTALL | re.IGNORECASE)

    # Remove any standalone opening or closing think tags
    cleaned = re.sub(r"</?think\s*>", "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    cleaned = cleaned.strip()

    # If cleaning removed everything, return a helpful message
    if not cleaned and response:
        if "<think>" in response.lower():
            return "I was processing your request but only generated thinking content. Please try asking again."
        else:
            return (
                "I generated an empty response. Please try asking your question again."
            )

    return cleaned


def main():
    """Main Streamlit application."""
    # Page configuration
    st.set_page_config(
        page_title="Personal AI Agent",
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

    # Check if agent is initialized (prefer session state, fallback to global)
    current_agent = st.session_state.get('agno_agent', agno_agent)
    if current_agent is None:
        st.error("⚠️ Agent not initialized. Please start the agent first.")
        st.info("Run the agent using: `python -m personal_agent.agno_main --web`")
        return
    
    # Ensure session state has the agent
    if 'agno_agent' not in st.session_state:
        st.session_state.agno_agent = current_agent

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    # Sidebar
    with st.sidebar:
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
            <strong>User ID:</strong> {USER_ID}
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
            clear_func = st.session_state.get('clear_knowledge_base_func', clear_knowledge_base_func)
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
            with st.spinner("🤔 Thinking..."):
                try:
                    # Run the agent asynchronously
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        response = loop.run_until_complete(current_agent.run(prompt))
                    finally:
                        loop.close()

                    # Clean the response
                    if response is None:
                        response = "No response generated by agent"
                    elif not isinstance(response, str):
                        response = str(response)

                    cleaned_response = clean_response_content(response)

                    # Display response
                    st.markdown(cleaned_response)
                    response_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.caption(f"*{response_timestamp}*")

                    # Add to chat history
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": cleaned_response,
                            "timestamp": response_timestamp,
                        }
                    )

                    # Store interaction in memory if available
                    store_func = st.session_state.get('store_interaction_func', store_interaction_func)
                    if store_func:
                        try:
                            run_async_in_thread(
                                store_func(prompt, response)
                            )
                            if logger:
                                logger.info("Interaction stored in memory")
                        except Exception as e:
                            if logger:
                                logger.warning(f"Could not store interaction: {e}")

                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)

                    # Add error to chat history
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_msg,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                    if logger:
                        logger.error(f"Error processing query: {str(e)}")

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
