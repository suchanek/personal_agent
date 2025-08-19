"""
Personal Agent Streamlit Web UI (Persag) - Unified Interface
============================================================

This module provides the main web-based user interface for the Personal Agent system,
built using Streamlit. It serves as a unified, comprehensive dashboard for interacting
with both a single AI personal assistant and a multi-agent team, featuring memory,
knowledge management, and advanced conversational capabilities.

The application allows users to dynamically switch between a single-agent mode for
direct interaction and a team-based mode that leverages multiple specialized agents
to accomplish complex tasks.

Key Features
-----------
🤖 **Dual-Mode Conversational AI Interface**
    - Real-time chat with a single agent (AgnoPersonalAgent) or a multi-agent team (PersonalAgentTeam).
    - Dynamic mode switching between single-agent and team-based interaction at runtime.
    - Streaming responses with real-time tool call visualization.
    - Support for multiple LLM models via Ollama.
    - Advanced debugging and performance metrics.

🧠 **Memory Management System**
    - Store, search, and manage personal facts and memories.
    - Semantic similarity search with configurable thresholds.
    - Topic-based categorization and organization.
    - Synchronization between local SQLite and graph-based storage.
    - Comprehensive memory statistics and analytics.

📚 **Knowledge Base Management**
    - Multi-format file upload support (PDF, DOCX, TXT, MD, HTML, etc.).
    - Direct text content ingestion with format selection.
    - Web content extraction from URLs.
    - Dual search capabilities: SQLite/LanceDB and RAG-based.
    - Advanced RAG query modes (naive, hybrid, local, global, mix, bypass).

⚙️ **System Configuration**
    - Dynamic agent/team mode selection.
    - Dynamic model selection and switching.
    - Ollama server configuration (local/remote).
    - RAG server location management.
    - Theme switching (light/dark mode).
    - Debug mode with detailed performance analytics.

🔧 **Advanced Features**
    - Real-time tool call monitoring and visualization.
    - Performance metrics tracking (response times, token usage).
    - Memory-knowledge synchronization status monitoring.
    - Comprehensive error handling and logging.
    - Session state management for a persistent user experience.

Architecture
-----------
The application is built around three main components:

1. **AgnoPersonalAgent & PersonalAgentTeam**: Core conversational AI systems, supporting both single-agent and multi-agent team configurations.
2. **Streamlit Interface**: A multi-tab web UI with a unified chat interface and dedicated tabs for memory and knowledge management.
3. **Helper Classes**: StreamlitMemoryHelper and StreamlitKnowledgeHelper for abstracting data operations from the UI.

Technical Stack
--------------
- **Frontend**: Streamlit with custom CSS theming
- **AI Systems**: AgnoPersonalAgent and PersonalAgentTeam with tool-calling capabilities
- **Memory Storage**: SQLite with semantic search via embeddings
- **Knowledge Storage**: SQLite/LanceDB + RAG server integration
- **LLM Integration**: Ollama with support for multiple models
- **Visualization**: Altair charts for performance metrics

Usage
-----
Run the application with:
    ```bash
    streamlit run tools/paga_streamlit_agno.py [--remote] [--recreate] [--team]
    ```

Command Line Arguments:
    --remote: Use remote Ollama URL instead of local.
    --recreate: Recreate the knowledge base and clear all memories.

Environment Variables:
    - AGNO_STORAGE_DIR: Directory for agent storage.
    - AGNO_KNOWLEDGE_DIR: Directory for knowledge files.
    - LLM_MODEL: Default language model to use.
    - OLLAMA_URL: Local Ollama server URL.
    - REMOTE_OLLAMA_URL: Remote Ollama server URL.
    - USER_ID: Current user identifier.

Session Management
-----------------
The application maintains a persistent session state across interactions, managing:
- Chat message history.
- Agent/Team configuration, mode, and initialization.
- Performance metrics and debug information.
- User preferences (theme, model selection).
- Memory and knowledge helper instances.

Author: Personal Agent Development Team
Version: v0.2.1
Last Revision: 2025-08-17
"""

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import altair as alt
import pandas as pd
import requests
import streamlit as st

PANDAS_AVAILABLE = True

# Set up logging
logger = logging.getLogger(__name__)


sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent import __version__

# Import from the correct path
from personal_agent.config import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    LIGHTRAG_MEMORY_URL,
    LIGHTRAG_URL,
    LLM_MODEL,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    USER_DATA_DIR,
    get_current_user_id,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.team.personal_agent_team import create_personal_agent_team
from personal_agent.tools.streamlit_helpers import (
    StreamlitKnowledgeHelper,
    StreamlitMemoryHelper,
)

# Apply dashboard-style layout but keep original page title/icon
st.set_page_config(
    page_title=f"Personal Agent Friendly Assistant {__version__}",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants for session state keys
SESSION_KEY_MESSAGES = "messages"
SESSION_KEY_AGENT = "agent"
SESSION_KEY_TEAM = "team"
SESSION_KEY_AGENT_MODE = "agent_mode"  # "single" or "team"
SESSION_KEY_DARK_THEME = "dark_theme"
SESSION_KEY_CURRENT_MODEL = "current_model"
SESSION_KEY_CURRENT_OLLAMA_URL = "current_ollama_url"
SESSION_KEY_AVAILABLE_MODELS = "available_models"
SESSION_KEY_SHOW_MEMORY_CONFIRMATION = "show_memory_confirmation"
SESSION_KEY_DEBUG_METRICS = "debug_metrics"
SESSION_KEY_PERFORMANCE_STATS = "performance_stats"
SESSION_KEY_SHOW_DEBUG = "show_debug"
SESSION_KEY_MEMORY_HELPER = "memory_helper"
SESSION_KEY_KNOWLEDGE_HELPER = "knowledge_helper"
SESSION_KEY_RAG_SERVER_LOCATION = "rag_server_location"
SESSION_KEY_DELETE_CONFIRMATIONS = "delete_confirmations"

USER_ID = get_current_user_id()


# Parse command line arguments
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Personal Agent Streamlit App")
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama URL instead of local"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Set debug mode",
        default=False,
    )

    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the knowledge base and clear all memories",
        default=True,
    )

    parser.add_argument(
        "--team",
        action="store_true",
        help="Launch the team-based mode",
        default=True,
    )

    return parser.parse_known_args()  # Use parse_known_args to ignore Streamlit's args


# Parse arguments and determine Ollama URL and recreate flag
args, unknown = parse_args()
EFFECTIVE_OLLAMA_URL = REMOTE_OLLAMA_URL if args.remote else OLLAMA_URL
RECREATE_FLAG = args.recreate
DEBUG_FLAG = args.debug
TEAM_FLAG = args.team

db_path = Path(AGNO_STORAGE_DIR) / "agent_memory.db"


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


async def initialize_agent_async(
    model_name, ollama_url, existing_agent=None, recreate=False
):
    """Initialize AgnoPersonalAgent with proper async handling."""
    # Always create a new agent when URL or model changes to ensure proper configuration
    # This is more reliable than trying to update existing agent configuration
    return await AgnoPersonalAgent.create_with_init(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url=ollama_url,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=True,
        storage_dir=AGNO_STORAGE_DIR,
        knowledge_dir=AGNO_KNOWLEDGE_DIR,
        recreate=recreate,
    )


def initialize_agent(model_name, ollama_url, existing_agent=None, recreate=False):
    """Sync wrapper for agent initialization."""
    return asyncio.run(
        initialize_agent_async(model_name, ollama_url, existing_agent, recreate)
    )


def initialize_team(model_name, ollama_url, existing_team=None, recreate=False):
    """Initialize the team using the standard agno Team class."""
    try:
        # Create team using the factory function
        team = create_personal_agent_team(
            model_provider="ollama",
            model_name=model_name,
            ollama_base_url=ollama_url,
            storage_dir=AGNO_STORAGE_DIR,
            user_id=USER_ID,
            debug=True,
        )

        # The refactored team now has a knowledge agent as the first member
        # which contains the memory system, so we don't need to create it separately
        # But we'll add a fallback for backward compatibility
        if hasattr(team, "members") and team.members:
            knowledge_agent = team.members[0]
            if hasattr(knowledge_agent, "agno_memory"):
                # Expose the knowledge agent's memory for Streamlit compatibility
                team.agno_memory = knowledge_agent.agno_memory
            else:
                # Fallback: create memory system for compatibility
                from personal_agent.core.agno_storage import create_agno_memory

                team.agno_memory = create_agno_memory(AGNO_STORAGE_DIR, debug_mode=True)
        else:
            # Fallback: create memory system for compatibility
            from personal_agent.core.agno_storage import create_agno_memory

            team.agno_memory = create_agno_memory(AGNO_STORAGE_DIR, debug_mode=True)

        return team
    except Exception as e:
        st.error(f"Failed to initialize team: {str(e)}")
        return None


def create_team_wrapper(team):
    """Create a wrapper that makes the team look like an agent for the helpers."""

    class TeamWrapper:
        def __init__(self, team):
            self.team = team
            self.user_id = USER_ID
            # Try to get memory from the knowledge agent (first team member)
            self.agno_memory = self._get_team_memory()

        def _get_team_memory(self):
            """Get memory system from the knowledge agent in the team."""
            if hasattr(self.team, "members") and self.team.members:
                # The first member should be the knowledge agent (PersonalAgnoAgent)
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "agno_memory"):
                    return knowledge_agent.agno_memory
                elif hasattr(knowledge_agent, "memory"):
                    return knowledge_agent.memory

            # Fallback: check if team has direct memory access
            return getattr(self.team, "agno_memory", None)

        def store_user_memory(self, content, topics=None):
            # Use the knowledge agent (first team member) for memory storage with fact restating
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[
                    0
                ]  # First member is the knowledge agent
                if hasattr(knowledge_agent, "store_user_memory"):
                    import asyncio

                    # This will properly restate facts and process them through the LLM
                    return asyncio.run(
                        knowledge_agent.store_user_memory(
                            content=content, topics=topics
                        )
                    )

            # Fallback to direct memory storage (bypasses LLM processing)
            if self.agno_memory and hasattr(self.agno_memory, "memory_manager"):
                # Use the SemanticMemoryManager's add_memory method directly
                result = self.agno_memory.memory_manager.add_memory(
                    memory_text=content,
                    db=self.agno_memory.db,
                    user_id=self.user_id,
                    topics=topics,
                )
                logger.warning(f"Memory stored in team memory: {result}")
                return result

            raise Exception("Team memory not available")

    return TeamWrapper(team)


def apply_custom_theme():
    """Apply custom CSS for theme switching."""
    is_dark_theme = st.session_state.get(SESSION_KEY_DARK_THEME, False)
    css_file = "tools/dark_theme.css" if is_dark_theme else "tools/light_theme.css"
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize all session state variables."""
    if SESSION_KEY_CURRENT_OLLAMA_URL not in st.session_state:
        st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = EFFECTIVE_OLLAMA_URL

    if SESSION_KEY_CURRENT_MODEL not in st.session_state:
        st.session_state[SESSION_KEY_CURRENT_MODEL] = LLM_MODEL

    if SESSION_KEY_DARK_THEME not in st.session_state:
        st.session_state[SESSION_KEY_DARK_THEME] = False

    # Initialize agent mode - use --team flag if provided, otherwise default to single agent
    if SESSION_KEY_AGENT_MODE not in st.session_state:
        st.session_state[SESSION_KEY_AGENT_MODE] = "team" if TEAM_FLAG else "single"

    # Initialize based on mode
    if st.session_state[SESSION_KEY_AGENT_MODE] == "team":
        # Team mode initialization
        if SESSION_KEY_TEAM not in st.session_state:
            st.session_state[SESSION_KEY_TEAM] = initialize_team(
                st.session_state[SESSION_KEY_CURRENT_MODEL],
                st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL],
                recreate=RECREATE_FLAG,
            )

        # Create team wrapper for helpers
        if SESSION_KEY_MEMORY_HELPER not in st.session_state:
            team_wrapper = create_team_wrapper(st.session_state[SESSION_KEY_TEAM])
            st.session_state[SESSION_KEY_MEMORY_HELPER] = StreamlitMemoryHelper(
                team_wrapper
            )

        if SESSION_KEY_KNOWLEDGE_HELPER not in st.session_state:
            # For team mode, pass the knowledge agent (first team member) to the knowledge helper
            team = st.session_state[SESSION_KEY_TEAM]
            if hasattr(team, "members") and team.members:
                knowledge_agent = team.members[0]  # First member is the knowledge agent
                st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                    StreamlitKnowledgeHelper(knowledge_agent)
                )
            else:
                # Fallback: create with team object
                st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                    StreamlitKnowledgeHelper(team)
                )
    else:
        # Single agent mode initialization (default)
        if SESSION_KEY_AGENT not in st.session_state:
            st.session_state[SESSION_KEY_AGENT] = initialize_agent(
                st.session_state[SESSION_KEY_CURRENT_MODEL],
                st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL],
                recreate=RECREATE_FLAG,
            )

        if SESSION_KEY_MEMORY_HELPER not in st.session_state:
            st.session_state[SESSION_KEY_MEMORY_HELPER] = StreamlitMemoryHelper(
                st.session_state[SESSION_KEY_AGENT]
            )

        if SESSION_KEY_KNOWLEDGE_HELPER not in st.session_state:
            st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = StreamlitKnowledgeHelper(
                st.session_state[SESSION_KEY_AGENT]
            )

    if SESSION_KEY_MESSAGES not in st.session_state:
        st.session_state[SESSION_KEY_MESSAGES] = []

    if SESSION_KEY_SHOW_MEMORY_CONFIRMATION not in st.session_state:
        st.session_state[SESSION_KEY_SHOW_MEMORY_CONFIRMATION] = False

    if SESSION_KEY_DEBUG_METRICS not in st.session_state:
        st.session_state[SESSION_KEY_DEBUG_METRICS] = []

    if SESSION_KEY_PERFORMANCE_STATS not in st.session_state:
        st.session_state[SESSION_KEY_PERFORMANCE_STATS] = {
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

    if SESSION_KEY_RAG_SERVER_LOCATION not in st.session_state:
        st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] = "localhost"

    if SESSION_KEY_DELETE_CONFIRMATIONS not in st.session_state:
        st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS] = {}

    # Initialize debug mode based on command line flag
    if SESSION_KEY_SHOW_DEBUG not in st.session_state:
        st.session_state[SESSION_KEY_SHOW_DEBUG] = DEBUG_FLAG


def display_tool_calls(container, tools):
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


def format_tool_call_for_debug(tool_call):
    """Standardize tool call format for consistent storage and display."""
    if hasattr(tool_call, "name"):
        # Direct tool object
        return {
            "name": getattr(tool_call, "name", "Unknown"),
            "arguments": getattr(tool_call, "arguments", {}),
            "result": getattr(tool_call, "result", None),
            "status": "success",
        }
    elif hasattr(tool_call, "function"):
        # Tool call with function attribute
        return {
            "name": getattr(tool_call.function, "name", "Unknown"),
            "arguments": getattr(tool_call.function, "arguments", {}),
            "result": getattr(tool_call, "result", None),
            "status": "success",
        }
    else:
        # Fallback for unknown format
        return {
            "name": str(type(tool_call).__name__),
            "arguments": {},
            "result": str(tool_call),
            "status": "unknown",
        }


def render_chat_tab():
    # Dynamic title based on mode
    if st.session_state[SESSION_KEY_AGENT_MODE] == "team":
        st.markdown("### Chat with your AI Team")
    else:
        st.markdown("### Have a conversation with your AI friend")

    for message in st.session_state[SESSION_KEY_MESSAGES]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to talk about?"):
        st.session_state[SESSION_KEY_MESSAGES].append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Create containers for tool calls and response
            tool_calls_container = st.empty()
            resp_container = st.empty()

            # Dynamic spinner message based on mode
            spinner_message = (
                "🤖 Team is thinking..."
                if st.session_state[SESSION_KEY_AGENT_MODE] == "team"
                else "🤔 Thinking..."
            )

            with st.spinner(spinner_message):
                start_time = time.time()
                start_timestamp = datetime.now()
                response = ""
                tool_calls_made = 0
                tool_call_details = []
                all_tools_used = []

                try:
                    if st.session_state[SESSION_KEY_AGENT_MODE] == "team":
                        # Team mode handling
                        team = st.session_state[SESSION_KEY_TEAM]

                        if team:
                            # Use the standard agno Team arun method (async)
                            response_obj = asyncio.run(
                                team.arun(prompt, user_id=USER_ID)
                            )
                            response = (
                                response_obj.content
                                if hasattr(response_obj, "content")
                                else str(response_obj)
                            )

                            # Extract tool call information from response
                            if (
                                hasattr(response_obj, "messages")
                                and response_obj.messages
                            ):
                                for message in response_obj.messages:
                                    if (
                                        hasattr(message, "tool_calls")
                                        and message.tool_calls
                                    ):
                                        tool_calls_made += len(message.tool_calls)
                                        for tool_call in message.tool_calls:
                                            tool_info = {
                                                "name": getattr(
                                                    tool_call, "name", "unknown"
                                                ),
                                                "arguments": getattr(
                                                    tool_call, "input", {}
                                                ),
                                                "status": "success",
                                            }
                                            tool_call_details.append(tool_info)
                                            all_tools_used.append(tool_call)

                            # Display tool calls if any
                            if all_tools_used:
                                display_tool_calls(tool_calls_container, all_tools_used)
                        else:
                            response = "Team not initialized properly"
                    else:
                        # Single agent mode handling
                        agent = st.session_state[SESSION_KEY_AGENT]

                        # Handle AgnoPersonalAgent with simplified response handling
                        if isinstance(agent, AgnoPersonalAgent):

                            async def run_agent_with_streaming():
                                nonlocal response, tool_calls_made, tool_call_details, all_tools_used

                                try:
                                    # Use the simplified agent.run() method
                                    response_content = await agent.run(
                                        prompt, add_thought_callback=None
                                    )

                                    # Get tool calls using the new method that collects from streaming events
                                    tools_used = agent.get_last_tool_calls()

                                    # Process and display tool calls
                                    if tools_used:
                                        print(
                                            f"DEBUG: Processing {len(tools_used)} tool calls from streaming events"
                                        )
                                        for i, tool_call in enumerate(tools_used):
                                            print(f"DEBUG: Tool call {i}: {tool_call}")
                                            formatted_tool = format_tool_call_for_debug(
                                                tool_call
                                            )
                                            tool_call_details.append(formatted_tool)
                                            all_tools_used.append(tool_call)
                                            tool_calls_made += 1

                                        # Display tool calls
                                        display_tool_calls(
                                            tool_calls_container, all_tools_used
                                        )
                                    else:
                                        print(
                                            "DEBUG: No tool calls collected from streaming events"
                                        )

                                    return response_content

                                except Exception as e:
                                    raise Exception(
                                        f"Error in agent execution: {e}"
                                    ) from e

                            response_content = asyncio.run(run_agent_with_streaming())
                            response = response_content if response_content else ""
                        else:
                            # Non-AgnoPersonalAgent fallback
                            agent_response = agent.run(prompt)
                            response = (
                                agent_response.content
                                if hasattr(agent_response, "content")
                                else str(agent_response)
                            )

                    # Display the final response
                    resp_container.markdown(response)

                    end_time = time.time()
                    response_time = end_time - start_time

                    # Calculate token estimates
                    input_tokens = len(prompt.split()) * 1.3
                    output_tokens = len(response.split()) * 1.3 if response else 0
                    total_tokens = input_tokens + output_tokens

                    response_metadata = {}
                    response_type = "AgnoResponse"

                    # Update performance stats with real-time tool call count
                    stats = st.session_state[SESSION_KEY_PERFORMANCE_STATS]
                    stats["total_requests"] += 1
                    stats["total_response_time"] += response_time
                    stats["average_response_time"] = (
                        stats["total_response_time"] / stats["total_requests"]
                    )
                    stats["total_tokens"] += total_tokens
                    stats["average_tokens"] = (
                        stats["total_tokens"] / stats["total_requests"]
                    )
                    stats["fastest_response"] = min(
                        stats["fastest_response"], response_time
                    )
                    stats["slowest_response"] = max(
                        stats["slowest_response"], response_time
                    )
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
                            "PersonalAgentTeam"
                            if st.session_state[SESSION_KEY_AGENT_MODE] == "team"
                            else (
                                "AgnoPersonalAgent"
                                if st.session_state[SESSION_KEY_AGENT_MODE] == "single"
                                else "Unknown"
                            )
                        ),
                        "success": True,
                    }
                    st.session_state[SESSION_KEY_DEBUG_METRICS].append(debug_entry)
                    if len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 10:
                        st.session_state[SESSION_KEY_DEBUG_METRICS].pop(0)

                    # Display structured response metadata if available
                    if response_metadata and response_type == "StructuredResponse":
                        confidence = response_metadata.get("confidence")
                        sources = response_metadata.get("sources", [])
                        metadata_response_type = response_metadata.get(
                            "response_type", "structured"
                        )

                        # Create a compact metadata display
                        metadata_parts = []
                        if confidence is not None:
                            confidence_color = (
                                "🟢"
                                if confidence > 0.8
                                else "🟡" if confidence > 0.6 else "🔴"
                            )
                            metadata_parts.append(
                                f"{confidence_color} **Confidence:** {confidence:.2f}"
                            )

                        if sources:
                            metadata_parts.append(
                                f"📚 **Sources:** {', '.join(sources[:3])}"
                            )  # Show first 3 sources

                        metadata_parts.append(f"🔧 **Type:** {metadata_response_type}")

                        if metadata_parts:
                            with st.expander("📊 Response Metadata", expanded=False):
                                st.markdown(" | ".join(metadata_parts))
                                if len(sources) > 3:
                                    st.markdown(
                                        f"**All Sources:** {', '.join(sources)}"
                                    )

                    # Display debug info if enabled (moved to sidebar)
                    if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
                        with st.expander("🔍 **Basic Debug Info**", expanded=False):
                            st.write(f"**Response Type:** {response_type}")
                            st.write(f"**Tool Calls Made:** {tool_calls_made}")
                            st.write(f"**Response Time:** {response_time:.3f}s")
                            st.write(f"**Total Tokens:** {total_tokens:.0f}")

                            if response_metadata:
                                st.write("**Structured Response Metadata:**")
                                st.json(response_metadata)

                    # Store message with metadata for future reference
                    message_data = {
                        "role": "assistant",
                        "content": response,
                        "metadata": (
                            response_metadata
                            if response_type == "StructuredResponse"
                            else None
                        ),
                        "response_type": response_type,
                        "tool_calls": tool_call_details,  # Store the standardized list
                        "response_time": response_time,
                    }
                    st.session_state[SESSION_KEY_MESSAGES].append(message_data)
                    st.rerun()

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state[SESSION_KEY_MESSAGES].append(
                        {"role": "assistant", "content": error_msg}
                    )

                    # Log failed request
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
                    st.session_state[SESSION_KEY_DEBUG_METRICS].append(debug_entry)
                    if len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 10:
                        st.session_state[SESSION_KEY_DEBUG_METRICS].pop(0)

                    if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
                        with st.expander("❌ **Error Debug Info**", expanded=True):
                            import traceback

                            st.write(f"**Error Time:** {response_time:.3f}s")
                            st.write(f"**Error Type:** {type(e).__name__}")
                            st.write(f"**Error Message:** {str(e)}")
                            st.code(traceback.format_exc())
                    st.rerun()


def render_memory_tab():
    st.markdown("### Comprehensive Memory Management")
    memory_helper = st.session_state[SESSION_KEY_MEMORY_HELPER]

    # Store New Facts Section
    st.markdown("---")
    st.subheader("📝 Store New Facts")
    st.markdown("*Add facts directly to memory without agent inference*")
    categories = [
        "automatic",
        "personal",
        "work",
        "education",
        "hobbies",
        "preferences",
        "goals",
        "health",
        "family",
        "travel",
        "technology",
        "other",
    ]
    selected_category = st.selectbox("Category:", categories, key="fact_category")
    # Inline input for storing facts (uniform with knowledge tools)
    # Clear-on-success using a flag to avoid Streamlit key mutation errors
    if st.session_state.get("clear_fact_input_text", False):
        st.session_state["fact_input_text"] = ""
        st.session_state["clear_fact_input_text"] = False

    with st.form("store_fact_form"):
        fact_input = st.text_input(
            "Enter a fact to store (e.g., I work at Google as a software engineer)",
            key="fact_input_text",
        )
        submitted = st.form_submit_button("💾 Save Fact")
    if submitted and fact_input and fact_input.strip():
        topic_list = None if selected_category == "automatic" else [selected_category]
        result = memory_helper.add_memory(
            memory_text=fact_input.strip(),
            topics=topic_list,
            input_text="Direct fact storage",
        )

        # Handle both MemoryStorageResult objects and legacy tuple returns
        if hasattr(result, "is_success"):
            # MemoryStorageResult object
            success = result.is_success
            message = result.message
            memory_id = getattr(result, "memory_id", None)
        elif isinstance(result, tuple) and len(result) >= 2:
            # Legacy tuple format (success, message, memory_id, topics)
            success, message = result[0], result[1]
            memory_id = result[2] if len(result) > 2 else None
        else:
            # Fallback
            success = False
            message = f"Unexpected result format: {result}"
            memory_id = None

        if success:
            # Show success notification
            st.toast("🎉 Fact saved to memory", icon="✅")
            time.sleep(2.0)  # 2 second delay
            # Defer clearing the input to the next run to comply with Streamlit rules
            st.session_state["clear_fact_input_text"] = True
            st.rerun()
        else:
            st.error(f"❌ Failed to store fact: {message}")

    # Search Memories Section
    st.markdown("---")
    st.subheader("🔍 Search Memories")
    st.markdown("*Search through stored memories using semantic similarity*")
    col1, col2 = st.columns(2)
    with col1:
        similarity_threshold = st.slider(
            "Similarity Threshold",
            0.1,
            1.0,
            0.3,
            0.1,
            key="memory_similarity_threshold",
        )
    with col2:
        search_limit = st.number_input(
            "Max Results", 1, 50, 10, key="memory_search_limit"
        )
    with st.form("memory_search_form"):
        search_query = st.text_input(
            "Enter keywords to search your memories",
            key="memory_search_query_text",
        )
        submitted_memory_search = st.form_submit_button("🔎 Search")
    if submitted_memory_search and search_query and search_query.strip():
        search_results = memory_helper.search_memories(
            query=search_query.strip(),
            limit=search_limit,
            similarity_threshold=similarity_threshold,
        )
        if search_results:
            st.subheader(f"🔍 Search Results for: '{search_query.strip()}'")
            for i, (memory, score) in enumerate(search_results, 1):
                with st.expander(
                    f"Result {i} (Score: {score:.3f}): {memory.memory[:50]}..."
                ):
                    st.write(f"**Memory:** {memory.memory}")
                    st.write(f"**Similarity Score:** {score:.3f}")
                    topics = getattr(memory, "topics", [])
                    if topics:
                        st.write(f"**Topics:** {', '.join(topics)}")
                    st.write(
                        f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                    )
                    st.write(f"**Memory ID:** {getattr(memory, 'memory_id', 'N/A')}")

                    # Memory deletion with confirmation
                    delete_key = f"delete_search_{memory.memory_id}"
                    if (
                        delete_key
                        not in st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS]
                    ):
                        st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS][
                            delete_key
                        ] = False

                    if not st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS][
                        delete_key
                    ]:
                        if st.button(f"🗑️ Delete Memory", key=delete_key):
                            st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS][
                                delete_key
                            ] = True
                            st.rerun()
                    else:
                        st.warning(
                            "⚠️ **Confirm Deletion** - This action cannot be undone!"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("❌ Cancel", key=f"cancel_{delete_key}"):
                                st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS][
                                    delete_key
                                ] = False
                                st.rerun()
                        with col2:
                            if st.button(
                                "🗑️ Yes, Delete",
                                key=f"confirm_{delete_key}",
                                type="primary",
                            ):
                                with st.spinner("Deleting memory..."):
                                    success, message = memory_helper.delete_memory(
                                        memory.memory_id
                                    )
                                    if success:
                                        st.success(f"Memory deleted: {message}")
                                        # Clear the confirmation state
                                        st.session_state[
                                            SESSION_KEY_DELETE_CONFIRMATIONS
                                        ][delete_key] = False
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete memory: {message}")
                                        st.session_state[
                                            SESSION_KEY_DELETE_CONFIRMATIONS
                                        ][delete_key] = False
        else:
            st.info("No matching memories found.")

    # Browse All Memories Section
    st.markdown("---")
    st.subheader("📚 Browse All Memories")
    st.markdown("*View, edit, and manage all stored memories*")
    if st.button("📋 Load All Memories", key="load_all_memories_btn"):
        memories = memory_helper.get_all_memories()
        if memories:
            st.info(f"Found {len(memories)} total memories")
            for memory in memories:
                with st.expander(f"Memory: {memory.memory[:50]}..."):
                    st.write(f"**Content:** {memory.memory}")
                    st.write(f"**Memory ID:** {getattr(memory, 'memory_id', 'N/A')}")
                    st.write(
                        f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                    )
                    st.write(f"**Input:** {getattr(memory, 'input', 'N/A')}")
                    topics = getattr(memory, "topics", [])
                    if topics:
                        st.write(f"**Topics:** {', '.join(topics)}")

                    # Memory deletion with confirmation
                    delete_key = f"delete_browse_{memory.memory_id}"
                    if (
                        delete_key
                        not in st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS]
                    ):
                        st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS][
                            delete_key
                        ] = False

                    if not st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS][
                        delete_key
                    ]:
                        if st.button(f"🗑️ Delete", key=delete_key):
                            st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS][
                                delete_key
                            ] = True
                            st.rerun()
                    else:
                        st.warning(
                            "⚠️ **Confirm Deletion** - This action cannot be undone!"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("❌ Cancel", key=f"cancel_{delete_key}"):
                                st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS][
                                    delete_key
                                ] = False
                                st.rerun()
                        with col2:
                            if st.button(
                                "🗑️ Yes, Delete",
                                key=f"confirm_{delete_key}",
                                type="primary",
                            ):
                                with st.spinner("Deleting memory..."):
                                    success, message = memory_helper.delete_memory(
                                        memory.memory_id
                                    )
                                    if success:
                                        st.success(f"Memory deleted: {message}")
                                        # Clear the confirmation state
                                        st.session_state[
                                            SESSION_KEY_DELETE_CONFIRMATIONS
                                        ][delete_key] = False
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete memory: {message}")
                                        st.session_state[
                                            SESSION_KEY_DELETE_CONFIRMATIONS
                                        ][delete_key] = False
        else:
            st.info("No memories stored yet.")

    # Memory Statistics Section
    st.markdown("---")
    st.subheader("📊 Memory Statistics")
    st.markdown("*Analytics and insights about your stored memories*")
    if st.button("📈 Show Statistics", key="show_stats_btn"):
        stats = memory_helper.get_memory_stats()
        if "error" not in stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Memories", stats.get("total_memories", 0))
            with col2:
                st.metric("Recent (24h)", stats.get("recent_memories_24h", 0))
            with col3:
                avg_length = stats.get("average_memory_length", 0)
                st.metric(
                    "Avg Length", f"{avg_length:.1f} chars" if avg_length else "N/A"
                )
            topic_dist = stats.get("topic_distribution", {})
            if topic_dist:
                st.subheader("📈 Topic Distribution")
                for topic, count in sorted(
                    topic_dist.items(), key=lambda x: x[1], reverse=True
                ):
                    st.write(f"**{topic.title()}:** {count} memories")
        else:
            st.error(f"Error getting statistics: {stats['error']}")

    # Memory Sync Status Section
    st.markdown("---")
    st.subheader("🔄 Memory Sync Status")
    st.markdown(
        "*Monitor synchronization between local SQLite and LightRAG graph memories*"
    )
    if st.button("🔍 Check Sync Status", key="check_sync_btn"):
        sync_status = memory_helper.get_memory_sync_status()
        if "error" not in sync_status:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Local Memories", sync_status.get("local_memory_count", 0))
            with col2:
                st.metric("Graph Entities", sync_status.get("graph_entity_count", 0))
            with col3:
                sync_ratio = sync_status.get("sync_ratio", 0)
                st.metric("Sync Ratio", f"{sync_ratio:.2f}")

            status = sync_status.get("status", "unknown")
            if status == "synced":
                st.success(
                    "✅ Memories are synchronized between local and graph systems"
                )
            elif status == "out_of_sync":
                st.warning("⚠️ Memories may be out of sync between systems")
                if st.button("🔄 Sync Missing Memories", key="sync_missing_btn"):
                    # Sync any missing memories to graph
                    local_memories = memory_helper.get_all_memories()
                    synced_count = 0
                    for memory in local_memories:
                        try:
                            success, result = memory_helper.sync_memory_to_graph(
                                memory.memory, getattr(memory, "topics", None)
                            )
                            if success:
                                synced_count += 1
                        except Exception as e:
                            st.error(f"Error syncing memory: {e}")

                    if synced_count > 0:
                        st.success(f"✅ Synced {synced_count} memories to graph system")
                    else:
                        st.info("No memories needed syncing")
            else:
                st.error(f"❌ Sync status unknown: {status}")
        else:
            st.error(
                f"Error checking sync status: {sync_status.get('error', 'Unknown error')}"
            )

    # Memory Settings Section
    st.markdown("---")
    st.subheader("⚙️ Memory Settings")
    st.markdown("*Configure and manage memory system settings*")
    if st.button("🗑️ Reset All Memories", key="reset_memories_btn"):
        st.session_state[SESSION_KEY_SHOW_MEMORY_CONFIRMATION] = True
    if st.session_state.get(SESSION_KEY_SHOW_MEMORY_CONFIRMATION):
        st.error("**WARNING**: This will permanently delete ALL stored memories.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Cancel", key="cancel_reset"):
                st.session_state[SESSION_KEY_SHOW_MEMORY_CONFIRMATION] = False
                st.rerun()
        with col2:
            if st.button("🗑️ Yes, Delete All", type="primary", key="confirm_reset"):
                success, message = memory_helper.clear_memories()
                st.session_state[SESSION_KEY_SHOW_MEMORY_CONFIRMATION] = False
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")
                st.rerun()


def render_knowledge_status(knowledge_helper):
    """Renders the status of the knowledge bases in an expander."""
    with st.expander("ℹ️ Knowledge Base Status"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**SQLite/LanceDB**")

            # Show the knowledge directory path
            st.caption(f"**Data Dir:** {USER_DATA_DIR}")
            st.caption(f"**Knowledge Dir:** {AGNO_KNOWLEDGE_DIR}")

            # FORCE AGENT/TEAM INITIALIZATION TO CHECK REAL STATUS
            try:
                current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")

                if current_mode == "team":
                    # Handle team mode
                    team = st.session_state.get(SESSION_KEY_TEAM)
                    if team:
                        # For team mode, we don't need to trigger initialization
                        # as the team should already be initialized
                        km = (
                            knowledge_helper.knowledge_manager
                        )  # This will trigger fresh check
                        if km:
                            st.success("✅ Ready")
                            # Show additional info if available
                            if hasattr(km, "vector_db") and km.vector_db:
                                st.caption("Vector DB: Connected")
                            elif hasattr(km, "search"):
                                st.caption("Knowledge base loaded")
                        else:
                            st.warning("⚠️ Offline")
                            st.caption("Knowledge manager not available")
                    else:
                        st.error("❌ Error: Team not initialized")
                        st.caption("Failed to initialize team")
                else:
                    # Handle single agent mode
                    agent = st.session_state.get(SESSION_KEY_AGENT)
                    if agent:
                        # Show initialization status
                        if not getattr(agent, "_initialized", False):
                            with st.spinner("Initializing knowledge system..."):
                                if hasattr(agent, "_ensure_initialized"):
                                    # This will trigger initialization if not already done
                                    asyncio.run(agent._ensure_initialized())
                        else:
                            # Agent already initialized, just ensure knowledge helper is updated
                            if hasattr(agent, "_ensure_initialized"):
                                asyncio.run(agent._ensure_initialized())

                        # Now check the real status after ensuring initialization
                        km = (
                            knowledge_helper.knowledge_manager
                        )  # This will trigger fresh check
                        if km:
                            st.success("✅ Ready")
                            # Show additional info if available
                            if hasattr(km, "vector_db") and km.vector_db:
                                st.caption("Vector DB: Connected")
                            elif hasattr(km, "search"):
                                st.caption("Knowledge base loaded")
                        else:
                            st.warning("⚠️ Offline")
                            st.caption("Knowledge manager not available")
                    else:
                        st.error("❌ Error: Agent not initialized")
                        st.caption("Failed to initialize agent")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.caption("Failed to initialize knowledge system")

        with col2:
            st.markdown("**RAG**")

            # RAG Server Location Dropdown
            rag_location = st.selectbox(
                "RAG Server:",
                ["localhost", "tesla.tail19187e.ts.net"],
                index=(
                    0
                    if st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] == "localhost"
                    else 1
                ),
                key="rag_server_dropdown",
            )

            # Check if location changed and show apply button
            location_changed = (
                rag_location != st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]
            )

            if location_changed:
                if st.button(
                    "🔄 Apply & Rescan", key="apply_rag_server", type="primary"
                ):
                    # Update session state
                    st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] = rag_location

                    # Determine the new RAG URL
                    if rag_location == "localhost":
                        new_rag_url = "http://localhost:9621"
                    else:  # tesla.tail19187e.ts.net
                        new_rag_url = "http://tesla.tail19187e.ts.net:9621"

                    # Trigger rescan on the new server
                    with st.spinner(
                        f"Switching to {rag_location} and triggering rescan..."
                    ):
                        try:
                            rescan_response = requests.post(
                                f"{new_rag_url}/documents/scan", timeout=10
                            )
                            if rescan_response.status_code == 200:
                                st.success(
                                    f"✅ Switched to {rag_location} and rescan initiated!"
                                )
                            else:
                                st.warning(
                                    f"⚠️ Switched to {rag_location} but rescan failed (status: {rescan_response.status_code})"
                                )
                        except requests.exceptions.RequestException as e:
                            st.error(
                                f"❌ Failed to connect to {rag_location}: {str(e)}"
                            )

                    # Force a rerun to update the status display
                    st.rerun()

            # Determine the RAG URL based on current session state
            if st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] == "localhost":
                rag_url = "http://localhost:9621"
            else:  # tesla.tail19187e.ts.net
                rag_url = "http://tesla.tail19187e.ts.net:9621"

            # Check RAG server status with improved reliability and error handling
            try:
                # Increase timeout and add better error handling
                health_response = requests.get(
                    f"{rag_url}/health", timeout=10
                )  # Increased from 3 to 10
                if health_response.status_code == 200:
                    # Get pipeline status for more detailed information
                    try:
                        pipeline_response = requests.get(
                            f"{rag_url}/documents/pipeline_status", timeout=10
                        )
                        if pipeline_response.status_code == 200:
                            pipeline_data = pipeline_response.json()

                            # Check if pipeline is processing
                            if pipeline_data.get("is_processing", False):
                                st.warning("🔄 Processing")
                                if pipeline_data.get("current_task"):
                                    st.caption(f"Task: {pipeline_data['current_task']}")
                            elif pipeline_data.get("queue_size", 0) > 0:
                                st.info(
                                    f"📋 Queued ({pipeline_data['queue_size']} items)"
                                )
                            else:
                                st.success("✅ Ready")

                            # Show additional pipeline info if available
                            if pipeline_data.get("last_processed"):
                                st.caption(f"Last: {pipeline_data['last_processed']}")
                        else:
                            # Fallback to basic ready status if pipeline endpoint fails
                            st.success("✅ Ready")
                            st.caption("(Pipeline status unavailable)")
                    except requests.exceptions.RequestException:
                        # Pipeline status failed, but health passed
                        st.success("✅ Ready")
                        st.caption("(Basic health check passed)")
                else:
                    st.error(f"❌ Error ({health_response.status_code})")
                    st.caption(
                        f"Server responded with error: {health_response.status_code}"
                    )
            except requests.exceptions.ConnectTimeout:
                st.warning("⚠️ Timeout")
                st.caption(
                    f"Connection timeout to {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}"
                )
            except requests.exceptions.ConnectionError:
                st.warning("⚠️ Offline")
                st.caption(
                    f"Cannot connect to {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}"
                )
            except requests.exceptions.RequestException as e:
                st.warning("⚠️ Error")
                st.caption(f"Request failed: {str(e)}")

            # Show current server info
            if not location_changed:
                st.caption(
                    f"Current: {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}"
                )

        # Add debug information in an expander if debug mode is enabled
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
            with st.expander("🔍 Debug Status Info"):
                current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")
                st.write(f"**Current Mode:** {current_mode}")

                if current_mode == "team":
                    # Debug info for team mode
                    team = st.session_state.get(SESSION_KEY_TEAM)
                    if team:
                        st.write(f"**Team Type:** {type(team).__name__}")
                        st.write(
                            f"**Team Members:** {len(getattr(team, 'members', []))}"
                        )
                        if hasattr(team, "agno_memory"):
                            st.write(f"**Team Memory:** {team.agno_memory is not None}")
                    else:
                        st.write("**Team:** Not initialized")
                else:
                    # Debug info for single agent mode
                    agent = st.session_state.get(SESSION_KEY_AGENT)
                    if agent:
                        st.write(
                            f"**Agent Initialized:** {getattr(agent, '_initialized', False)}"
                        )
                        st.write(f"**Agent Type:** {type(agent).__name__}")
                        if hasattr(agent, "agno_knowledge"):
                            st.write(
                                f"**Agent Knowledge:** {agent.agno_knowledge is not None}"
                            )
                        if hasattr(agent, "agno_memory"):
                            st.write(
                                f"**Agent Memory:** {agent.agno_memory is not None}"
                            )
                    else:
                        st.write("**Agent:** Not initialized")

                st.write(
                    f"**Knowledge Manager:** {knowledge_helper.knowledge_manager is not None}"
                )
                st.write(f"**RAG URL:** {rag_url}")
                st.write(
                    f"**RAG Location:** {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}"
                )


def render_knowledge_tab():
    st.markdown("### Knowledge Base Search & Management")
    knowledge_helper = st.session_state[SESSION_KEY_KNOWLEDGE_HELPER]
    render_knowledge_status(knowledge_helper)

    # File Upload Section
    st.markdown("---")
    st.subheader("📁 Add Knowledge Files")
    st.markdown("*Upload files directly to your knowledge base*")

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to add to your knowledge base",
        accept_multiple_files=True,
        type=["txt", "md", "pdf", "docx", "doc", "html", "csv", "json"],
        key="knowledge_file_uploader",
    )

    if uploaded_files:
        st.write(f"Selected {len(uploaded_files)} file(s):")
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.size} bytes)")

        if st.button(
            "🚀 Upload and Process Files", key="upload_files_btn", type="primary"
        ):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")

                try:
                    # Save uploaded file temporarily
                    import os
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=f"_{uploaded_file.name}"
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name

                    try:
                        # Get the appropriate agent/team based on current mode
                        current_mode = st.session_state.get(
                            SESSION_KEY_AGENT_MODE, "single"
                        )

                        if current_mode == "team":
                            # Team mode - get the knowledge agent (first team member)
                            team = st.session_state.get(SESSION_KEY_TEAM)
                            if team and hasattr(team, "members") and team.members:
                                agent = team.members[
                                    0
                                ]  # First member is the knowledge agent
                            else:
                                results.append(
                                    f"**{uploaded_file.name}**: ❌ Team not properly initialized"
                                )
                                continue
                        else:
                            # Single agent mode
                            agent = st.session_state.get(SESSION_KEY_AGENT)
                            if not agent:
                                results.append(
                                    f"**{uploaded_file.name}**: ❌ Agent not initialized"
                                )
                                continue

                        # Use the knowledge ingestion tools from the agent
                        if hasattr(agent, "agent") and hasattr(agent.agent, "tools"):
                            # Find the knowledge tools (consolidated)
                            knowledge_tools = None
                            for tool in agent.agent.tools:
                                if hasattr(
                                    tool, "__class__"
                                ) and "KnowledgeTools" in str(tool.__class__):
                                    knowledge_tools = tool
                                    break

                            if knowledge_tools:
                                # Use the ingest_knowledge_file method
                                result = knowledge_tools.ingest_knowledge_file(
                                    file_path=tmp_file_path, title=uploaded_file.name
                                )
                                results.append(f"**{uploaded_file.name}**: {result}")
                            else:
                                results.append(
                                    f"**{uploaded_file.name}**: ❌ Knowledge tools not available"
                                )
                        else:
                            results.append(
                                f"**{uploaded_file.name}**: ❌ Agent tools not accessible"
                                f"**{uploaded_file.name}**: ❌ Agent tools not accessible"
                            )

                    finally:
                        # Clean up temporary file
                        try:
                            os.unlink(tmp_file_path)
                        except OSError:
                            pass

                except Exception as e:
                    results.append(f"**{uploaded_file.name}**: ❌ Error: {str(e)}")

                # Update progress
                progress_bar.progress((i + 1) / len(uploaded_files))

            # Show results
            status_text.text("Upload complete!")
            st.markdown("### Upload Results:")
            for result in results:
                st.markdown(result)

            # Clear the file uploader
            st.rerun()

    # Text Input Section
    st.markdown("---")
    st.subheader("📝 Add Text Knowledge")
    st.markdown("*Add text content directly to your knowledge base*")

    # Clear-on-success using a flag to avoid Streamlit key mutation errors
    if st.session_state.get("clear_knowledge_input_text", False):
        st.session_state["knowledge_title"] = ""
        st.session_state["knowledge_content"] = ""
        st.session_state["clear_knowledge_input_text"] = False

    col1, col2 = st.columns([3, 1])
    with col1:
        knowledge_title = st.text_input(
            "Title for your knowledge entry:", key="knowledge_title"
        )
    with col2:
        file_type = st.selectbox(
            "Format:", ["txt", "md", "html", "json"], key="knowledge_format"
        )

    knowledge_content = st.text_area(
        "Enter your knowledge content:",
        height=200,
        key="knowledge_content",
        placeholder="Enter the text content you want to add to your knowledge base...",
    )

    if st.button("💾 Save Text Knowledge", key="save_text_knowledge", type="primary"):
        if knowledge_title and knowledge_content:
            try:
                # Get the appropriate agent/team based on current mode
                current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")

                if current_mode == "team":
                    # Team mode - get the knowledge agent (first team member)
                    team = st.session_state.get(SESSION_KEY_TEAM)
                    if team and hasattr(team, "members") and team.members:
                        agent = team.members[0]  # First member is the knowledge agent
                    else:
                        st.error("❌ Team not properly initialized")
                        return
                else:
                    # Single agent mode
                    agent = st.session_state.get(SESSION_KEY_AGENT)
                    if not agent:
                        st.error("❌ Agent not initialized")
                        return

                # Use the knowledge ingestion tools from the agent
                if hasattr(agent, "agent") and hasattr(agent.agent, "tools"):
                    # Find the knowledge tools (consolidated)
                    knowledge_tools = None
                    for tool in agent.agent.tools:
                        if hasattr(tool, "__class__") and "KnowledgeTools" in str(
                            tool.__class__
                        ):
                            knowledge_tools = tool
                            break

                    if knowledge_tools:
                        # Use the ingest_knowledge_text method
                        result = knowledge_tools.ingest_knowledge_text(
                            content=knowledge_content,
                            title=knowledge_title,
                            file_type=file_type,
                        )
                        # Show success notification
                        st.toast("🎉 Knowledge saved successfully!", icon="✅")
                        time.sleep(2.0)  # 2 second delay

                        # Clear the form using flag-based approach
                        st.session_state["clear_knowledge_input_text"] = True
                        st.rerun()
                    else:
                        st.error("❌ Knowledge tools not available")
                else:
                    st.error("❌ Agent tools not accessible")
            except Exception as e:
                st.error(f"❌ Error saving knowledge: {str(e)}")
        else:
            st.warning("⚠️ Please provide both title and content")

    # URL Input Section
    st.markdown("---")
    st.subheader("🌐 Add Knowledge from URL")
    st.markdown("*Extract and add content from web pages*")

    # Clear-on-success using a flag to avoid Streamlit key mutation errors
    if st.session_state.get("clear_url_input_text", False):
        st.session_state["knowledge_url"] = ""
        st.session_state["url_title"] = ""
        st.session_state["clear_url_input_text"] = False

    col1, col2 = st.columns([3, 1])
    with col1:
        knowledge_url = st.text_input(
            "URL to extract content from:", key="knowledge_url"
        )
    with col2:
        url_title = st.text_input("Title (optional):", key="url_title")

    if st.button(
        "🌐 Extract and Save from URL", key="save_url_knowledge", type="primary"
    ):
        if knowledge_url:
            try:
                with st.spinner("Extracting content from URL..."):
                    # Get the appropriate agent/team based on current mode
                    current_mode = st.session_state.get(
                        SESSION_KEY_AGENT_MODE, "single"
                    )

                    if current_mode == "team":
                        # Team mode - get the knowledge agent (first team member)
                        team = st.session_state.get(SESSION_KEY_TEAM)
                        if team and hasattr(team, "members") and team.members:
                            agent = team.members[
                                0
                            ]  # First member is the knowledge agent
                        else:
                            st.error("❌ Team not properly initialized")
                            return
                    else:
                        # Single agent mode
                        agent = st.session_state.get(SESSION_KEY_AGENT)
                        if not agent:
                            st.error("❌ Agent not initialized")
                            return

                    # Use the knowledge ingestion tools from the agent
                    if hasattr(agent, "agent") and hasattr(agent.agent, "tools"):
                        # Find the knowledge tools (consolidated)
                        knowledge_tools = None
                        for tool in agent.agent.tools:
                            if hasattr(tool, "__class__") and "KnowledgeTools" in str(
                                tool.__class__
                            ):
                                knowledge_tools = tool
                                break

                        if knowledge_tools:
                            # Use the ingest_knowledge_from_url method
                            result = knowledge_tools.ingest_knowledge_from_url(
                                url=knowledge_url,
                                title=url_title if url_title else None,
                            )
                            # Show success notification
                            st.toast("🎉 Knowledge from URL saved successfully!", icon="✅")
                            time.sleep(2.0)  # 2 second delay

                            # Clear the form using flag-based approach
                            st.session_state["clear_url_input_text"] = True
                            st.rerun()
                        else:
                            st.error("❌ Knowledge tools not available")
                    else:
                        st.error("❌ Agent tools not accessible")
            except Exception as e:
                st.error(f"❌ Error extracting from URL: {str(e)}")
        else:
            st.warning("⚠️ Please provide a URL")

    # SQLite/LanceDB Knowledge Search Section
    st.markdown("---")
    st.subheader("🔍 SQLite/LanceDB Knowledge Search")
    st.markdown(
        "*Search through stored knowledge using the original sqlite and lancedb knowledge sources*"
    )
    knowledge_search_limit = st.number_input(
        "Max Results", 1, 50, 10, key="knowledge_search_limit"
    )
    with st.form("knowledge_sqlite_search_form"):
        knowledge_search_query = st.text_input(
            "Enter keywords to search the SQLite/LanceDB knowledge base",
            key="knowledge_search_query_text",
        )
        submitted_knowledge_sqlite = st.form_submit_button("🔎 Search")
    if (
        submitted_knowledge_sqlite
        and knowledge_search_query
        and knowledge_search_query.strip()
    ):
        search_results = knowledge_helper.search_knowledge(
            query=knowledge_search_query.strip(), limit=knowledge_search_limit
        )
        if search_results:
            st.subheader(
                f"🔍 SQLite/LanceDB Knowledge Search Results for: '{knowledge_search_query.strip()}'"
            )
            for i, knowledge_entry in enumerate(search_results, 1):
                if hasattr(knowledge_entry, "content"):
                    content = knowledge_entry.content
                    title = getattr(knowledge_entry, "title", "Untitled")
                    source = getattr(knowledge_entry, "source", "Unknown")
                    knowledge_id = getattr(knowledge_entry, "id", "N/A")
                elif isinstance(knowledge_entry, dict):
                    content = knowledge_entry.get("content", "No content")
                    title = knowledge_entry.get("title", "Untitled")
                    source = knowledge_entry.get("source", "Unknown")
                    knowledge_id = knowledge_entry.get("id", "N/A")
                else:
                    content = str(knowledge_entry)
                    title = "Untitled"
                    source = "Unknown"
                    knowledge_id = "N/A"

                with st.expander(
                    f"📚 Result {i}: {title if title != 'Untitled' else content[:50]}..."
                ):
                    st.write(f"**Title:** {title}")
                    st.write(f"**Content:** {content}")
                    st.write(f"**Source:** {source}")
                    st.write(f"**Knowledge ID:** {knowledge_id}")
        else:
            st.info("No matching knowledge found.")

    # RAG Knowledge Search Section
    st.markdown("---")
    st.subheader("🤖 RAG Knowledge Search")
    st.markdown(
        "*Search through knowledge using direct RAG query with advanced options*"
    )

    # Create a dictionary to hold the query parameters
    query_params = {}

    # Query mode
    query_params["mode"] = st.selectbox(
        "Select RAG Search Type:",
        ("naive", "hybrid", "local", "global"),
        key="rag_search_type",
    )

    # Response type
    query_params["response_type"] = st.text_input(
        "Response Format:",
        "Multiple Paragraphs",
        key="rag_response_type",
        help="Examples: 'Single Paragraph', 'Bullet Points', 'JSON'",
    )

    # Top K
    query_params["top_k"] = st.slider(
        "Top K:",
        min_value=1,
        max_value=100,
        value=10,
        key="rag_top_k",
        help="Number of items to retrieve",
    )

    # Other boolean flags
    col1, col2, col3 = st.columns(3)
    with col1:
        query_params["only_need_context"] = st.checkbox(
            "Context Only", key="rag_context_only"
        )
    with col2:
        query_params["only_need_prompt"] = st.checkbox(
            "Prompt Only", key="rag_prompt_only"
        )
    with col3:
        query_params["stream"] = st.checkbox("Stream", key="rag_stream")

    with st.form("rag_search_form"):
        rag_search_query = st.text_input(
            "Enter keywords to search the RAG knowledge base",
            key="rag_search_query_text",
        )
        submitted_rag_search = st.form_submit_button("🔎 Search RAG")
    if submitted_rag_search and rag_search_query and rag_search_query.strip():
        # Pass the entire dictionary of parameters to the helper
        search_results = knowledge_helper.search_rag(
            query=rag_search_query.strip(), params=query_params
        )
        # Check if we have actual content (not just empty string or None)
        if search_results is not None and str(search_results).strip():
            st.subheader(
                f"🤖 RAG Knowledge Search Results for: '{rag_search_query.strip()}'"
            )
            st.markdown(search_results)
        elif search_results is not None:
            st.warning(f"Query returned empty response. Raw result: '{search_results}'")
        else:
            st.info("No matching knowledge found.")


def render_sidebar():
    with st.sidebar:
        # Theme selector at the very top
        st.header("🎨 Theme")
        dark_mode = st.toggle(
            "Dark Mode", value=st.session_state.get(SESSION_KEY_DARK_THEME, False)
        )

        if dark_mode != st.session_state.get(SESSION_KEY_DARK_THEME, False):
            st.session_state[SESSION_KEY_DARK_THEME] = dark_mode
            st.rerun()

        # Agent/Team Mode Selection
        st.header("🤖 Agent Mode")
        current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")
        mode_options = ["single", "team"]
        mode_index = (
            mode_options.index(current_mode) if current_mode in mode_options else 0
        )

        selected_mode = st.selectbox(
            "Select Mode:",
            mode_options,
            index=mode_index,
            format_func=lambda x: (
                "🧠 Single Agent" if x == "single" else "🤖 Team of Agents"
            ),
            key="agent_mode_selector",
        )

        if st.button("🔄 Switch Mode", key="switch_mode_btn"):
            if selected_mode != st.session_state[SESSION_KEY_AGENT_MODE]:
                old_mode = st.session_state[SESSION_KEY_AGENT_MODE]
                print(
                    f"🔄 MODE SWITCH: Switching from {old_mode} to {selected_mode} mode"
                )

                with st.spinner(f"Switching to {selected_mode} mode..."):
                    # Update mode
                    st.session_state[SESSION_KEY_AGENT_MODE] = selected_mode

                    # Clear messages when switching modes
                    st.session_state[SESSION_KEY_MESSAGES] = []

                    # Initialize the appropriate system
                    if selected_mode == "team":
                        print(
                            f"🤖 TEAM INIT: Initializing team with model {st.session_state[SESSION_KEY_CURRENT_MODEL]}"
                        )
                        # Initialize team
                        st.session_state[SESSION_KEY_TEAM] = initialize_team(
                            st.session_state[SESSION_KEY_CURRENT_MODEL],
                            st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL],
                            recreate=False,
                        )

                        # Update helpers for team
                        team_wrapper = create_team_wrapper(
                            st.session_state[SESSION_KEY_TEAM]
                        )
                        st.session_state[SESSION_KEY_MEMORY_HELPER] = (
                            StreamlitMemoryHelper(team_wrapper)
                        )
                        # For team mode, pass the knowledge agent (first team member) to the knowledge helper
                        team = st.session_state[SESSION_KEY_TEAM]
                        if hasattr(team, "members") and team.members:
                            knowledge_agent = team.members[
                                0
                            ]  # First member is the knowledge agent
                            st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                                StreamlitKnowledgeHelper(knowledge_agent)
                            )
                        else:
                            # Fallback: create with team object
                            st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                                StreamlitKnowledgeHelper(team)
                            )
                        print(
                            f"✅ TEAM READY: Team initialized successfully with {len(getattr(st.session_state[SESSION_KEY_TEAM], 'members', []))} members"
                        )
                    else:
                        logger.info(
                            f"🧠 AGENT INIT: Initializing single agent with model {st.session_state[SESSION_KEY_CURRENT_MODEL]}"
                        )
                        # Initialize single agent
                        st.session_state[SESSION_KEY_AGENT] = initialize_agent(
                            st.session_state[SESSION_KEY_CURRENT_MODEL],
                            st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL],
                            recreate=False,
                        )

                        # Update helpers for agent
                        st.session_state[SESSION_KEY_MEMORY_HELPER] = (
                            StreamlitMemoryHelper(st.session_state[SESSION_KEY_AGENT])
                        )
                        st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                            StreamlitKnowledgeHelper(
                                st.session_state[SESSION_KEY_AGENT]
                            )
                        )
                        logger.info(
                            "✅ AGENT READY: Single agent initialized successfully"
                        )

                    logger.info(
                        f"🎯 MODE SWITCH COMPLETE: Successfully switched from {old_mode} to {selected_mode}"
                    )
                    st.success(f"✅ Switched to {selected_mode} mode!")
                    st.rerun()
            else:
                st.info("Already in selected mode")

        st.header("Model Selection")
        new_ollama_url = st.text_input(
            "Ollama URL:", value=st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]
        )
        if st.button("🔄 Fetch Available Models"):
            with st.spinner("Fetching models..."):
                available_models = get_ollama_models(new_ollama_url)
                if available_models:
                    st.session_state[SESSION_KEY_AVAILABLE_MODELS] = available_models
                    st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = new_ollama_url
                    st.success(f"Found {len(available_models)} models!")
                else:
                    st.error("No models found or connection failed")

        if (
            SESSION_KEY_AVAILABLE_MODELS in st.session_state
            and st.session_state[SESSION_KEY_AVAILABLE_MODELS]
        ):
            current_model_index = 0
            if (
                st.session_state[SESSION_KEY_CURRENT_MODEL]
                in st.session_state[SESSION_KEY_AVAILABLE_MODELS]
            ):
                current_model_index = st.session_state[
                    SESSION_KEY_AVAILABLE_MODELS
                ].index(st.session_state[SESSION_KEY_CURRENT_MODEL])
            selected_model = st.selectbox(
                "Select Model:",
                st.session_state[SESSION_KEY_AVAILABLE_MODELS],
                index=current_model_index,
            )
            if st.button("🚀 Apply Model Selection"):
                if (
                    selected_model != st.session_state[SESSION_KEY_CURRENT_MODEL]
                    or new_ollama_url
                    != st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]
                ):
                    current_mode = st.session_state.get(
                        SESSION_KEY_AGENT_MODE, "single"
                    )
                    spinner_text = (
                        "Reinitializing team..."
                        if current_mode == "team"
                        else "Reinitializing agent..."
                    )

                    with st.spinner(spinner_text):
                        old_model = st.session_state[SESSION_KEY_CURRENT_MODEL]
                        old_url = st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]

                        logger.info(
                            "🔄 MODEL UPDATE: Changing from %s to %s",
                            old_model,
                            selected_model,
                        )
                        logger.info(
                            "🔄 URL UPDATE: Changing from %s to %s",
                            old_url,
                            new_ollama_url,
                        )

                        st.session_state[SESSION_KEY_CURRENT_MODEL] = selected_model
                        st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = (
                            new_ollama_url
                        )

                        if current_mode == "team":
                            logger.info(
                                "🤖 TEAM REINIT: Reinitializing team with new model %s",
                                selected_model,
                            )
                            # Reinitialize team
                            st.session_state[SESSION_KEY_TEAM] = initialize_team(
                                selected_model,
                                new_ollama_url,
                                st.session_state.get(SESSION_KEY_TEAM),
                            )

                            # Update helper classes with new team
                            team_wrapper = create_team_wrapper(
                                st.session_state[SESSION_KEY_TEAM]
                            )
                            st.session_state[SESSION_KEY_MEMORY_HELPER] = (
                                StreamlitMemoryHelper(team_wrapper)
                            )
                            st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                                StreamlitKnowledgeHelper(
                                    st.session_state[SESSION_KEY_TEAM]
                                )
                            )

                            success_msg = f"Team updated to use model: {selected_model}"
                            logger.info("✅ TEAM UPDATE COMPLETE: %s", success_msg)
                        else:
                            logger.info(
                                "🧠 AGENT REINIT: Reinitializing agent with new model %s",
                                selected_model,
                            )
                            # Reinitialize single agent
                            st.session_state[SESSION_KEY_AGENT] = initialize_agent(
                                selected_model,
                                new_ollama_url,
                                st.session_state.get(SESSION_KEY_AGENT),
                            )

                            # Update helper classes with new agent
                            st.session_state[SESSION_KEY_MEMORY_HELPER] = (
                                StreamlitMemoryHelper(
                                    st.session_state[SESSION_KEY_AGENT]
                                )
                            )
                            st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                                StreamlitKnowledgeHelper(
                                    st.session_state[SESSION_KEY_AGENT]
                                )
                            )

                            success_msg = (
                                f"Agent updated to use model: {selected_model}"
                            )
                            logger.info("✅ AGENT UPDATE COMPLETE: %s", success_msg)

                        st.session_state[SESSION_KEY_MESSAGES] = []
                        st.success(success_msg)
                        st.rerun()
                else:
                    st.info("Model and URL are already current")
        else:
            st.info("Click 'Fetch Available Models' to see available models")

        # Dynamic header based on mode
        current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")
        if current_mode == "team":
            st.header("Team Information")
        else:
            st.header("Agent Information")

        st.write(f"**Current Model:** {st.session_state[SESSION_KEY_CURRENT_MODEL]}")
        st.write(
            f"**Current Ollama URL:** {st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]}"
        )

        # Show mode-specific information
        if current_mode == "team":
            # Team-specific information
            team = st.session_state.get(SESSION_KEY_TEAM)
            if team:
                st.write(f"**Mode:** 🤖 Team of Agents")
                st.write(f"**Framework:** agno")

                # Show team composition
                members = getattr(team, "members", [])
                st.write(f"**Team Members:** {len(members)}")

                if members:
                    st.write("**Specialized Agents:**")
                    for member in members:
                        member_name = getattr(member, "name", "Unknown")
                        member_role = getattr(member, "role", "Unknown")
                        member_tools = len(getattr(member, "tools", []))
                        st.write(
                            f"• **{member_name}**: {member_role} ({member_tools} tools)"
                        )

                # Show team capabilities
                st.write("**Team Capabilities:**")
                st.write("• 🧠 Memory Management")
                st.write("• 📚 Knowledge Base Access")
                st.write("• 🌐 Web Research")
                st.write("• 💰 Finance & Calculations")
                st.write("• 📁 File Operations")
            else:
                st.write(f"**Mode:** 🤖 Team of Agents")
                st.warning("⚠️ Team not initialized")
        else:
            # Single agent information
            agent = st.session_state.get(SESSION_KEY_AGENT)
            if agent:
                st.write(f"**Mode:** 🧠 Single Agent")
                st.write(f"**Agent Type:** {type(agent).__name__}")

                # Show agent capabilities
                st.write("**Agent Capabilities:**")
                st.write("• 🧠 Memory Management")
                st.write("• 📚 Knowledge Base Access")
                st.write("• 🔧 Tool Integration")
                if hasattr(agent, "enable_mcp") and agent.enable_mcp:
                    st.write("• 🔌 MCP Server Integration")
            else:
                st.write(f"**Mode:** 🧠 Single Agent")
                st.warning("⚠️ Agent not initialized")

        # Show debug info about URL configuration
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
            with st.expander("🔍 URL Debug Info", expanded=False):
                st.write(f"**--remote flag:** {args.remote}")
                st.write(f"**OLLAMA_URL (local):** {OLLAMA_URL}")
                st.write(f"**REMOTE_OLLAMA_URL:** {REMOTE_OLLAMA_URL}")
                st.write(f"**EFFECTIVE_OLLAMA_URL (startup):** {EFFECTIVE_OLLAMA_URL}")
                st.write(
                    f"**Session Ollama URL:** {st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]}"
                )

                # Show agent/team specific debug info
                if current_mode == "team":
                    team = st.session_state.get(SESSION_KEY_TEAM)
                    if team and hasattr(team, "ollama_base_url"):
                        st.write(f"**Team's Ollama URL:** {team.ollama_base_url}")
                    else:
                        st.write("**Team URL:** Not accessible")
                else:
                    agent = st.session_state.get(SESSION_KEY_AGENT)
                    if agent and hasattr(agent, "ollama_base_url"):
                        st.write(f"**Agent's Ollama URL:** {agent.ollama_base_url}")
                    elif (
                        agent
                        and hasattr(agent, "model_manager")
                        and hasattr(agent.model_manager, "ollama_base_url")
                    ):
                        st.write(
                            f"**Agent's Model Manager URL:** {agent.model_manager.ollama_base_url}"
                        )
                    else:
                        st.write("**Agent URL:** Not accessible")

        st.header("Controls")
        if st.button("Clear Chat History"):
            st.session_state[SESSION_KEY_MESSAGES] = []
            st.rerun()

        st.header("Debug Info")
        debug_label = "Enable Debug Mode"
        if DEBUG_FLAG:
            debug_label += " (CLI enabled)"
        st.session_state[SESSION_KEY_SHOW_DEBUG] = st.checkbox(
            debug_label,
            value=st.session_state.get(SESSION_KEY_SHOW_DEBUG, DEBUG_FLAG),
            help="Debug mode can be enabled via --debug flag or this checkbox",
        )
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG):
            st.subheader("📊 Performance Statistics")
            stats = st.session_state[SESSION_KEY_PERFORMANCE_STATS]
            if stats["total_requests"] > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Requests", stats["total_requests"])
                    st.metric(
                        "Avg Response Time", f"{stats['average_response_time']:.3f}s"
                    )
                    st.metric(
                        "Fastest Response",
                        (
                            f"{stats['fastest_response']:.3f}s"
                            if stats["fastest_response"] != float("inf")
                            else "N/A"
                        ),
                    )
                with col2:
                    st.metric("Total Tool Calls", stats["tool_calls_count"])
                    st.metric("Avg Tokens/Request", f"{stats['average_tokens']:.0f}")
                    st.metric("Slowest Response", f"{stats['slowest_response']:.3f}s")
            else:
                st.info("No requests made yet.")

            if len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 1:
                st.subheader("📈 Response Time Trend")
                df = pd.DataFrame(st.session_state[SESSION_KEY_DEBUG_METRICS])
                df = df[df["success"]]
                if not df.empty and len(df) > 1:
                    chart_data = (
                        df[["timestamp", "response_time"]].copy().set_index("timestamp")
                    )
                    chart = (
                        alt.Chart(chart_data.reset_index())
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("timestamp:O", title="Time"),
                            y=alt.Y("response_time:Q", title="Response Time (s)"),
                            tooltip=["timestamp:O", "response_time:Q"],
                        )
                        .properties(title="Response Time Trend")
                    )
                    st.altair_chart(chart, use_container_width=True)

            st.subheader("🔧 Recent Tool Calls")
            if st.session_state[SESSION_KEY_DEBUG_METRICS]:
                # Filter entries that have tool calls
                tool_call_entries = [
                    entry
                    for entry in st.session_state[SESSION_KEY_DEBUG_METRICS]
                    if entry.get("tool_calls", 0) > 0
                ]

                if tool_call_entries:
                    for entry in reversed(
                        tool_call_entries[-5:]
                    ):  # Show last 5 tool call entries
                        tool_call_details = entry.get("tool_call_details", [])
                        with st.expander(
                            f"🔧 {entry['timestamp']} - {entry['tool_calls']} tool(s) - {entry['response_time']}s"
                        ):
                            st.write(f"**Prompt:** {entry['prompt']}")
                            st.write(f"**Response Time:** {entry['response_time']}s")
                            st.write(f"**Tool Calls Made:** {entry['tool_calls']}")

                            if tool_call_details:
                                st.write("**Tool Call Details:**")
                                for i, tool_call in enumerate(tool_call_details, 1):
                                    # Use standardized format - check for 'name' field first
                                    tool_name = tool_call.get(
                                        "name",
                                        tool_call.get("function_name", "Unknown"),
                                    )
                                    tool_status = tool_call.get("status", "unknown")

                                    # Status indicator
                                    status_icon = (
                                        "✅"
                                        if tool_status == "success"
                                        else "❓" if tool_status == "unknown" else "❌"
                                    )

                                    st.write(f"**Tool {i}:** {status_icon} {tool_name}")

                                    # Show arguments
                                    tool_args = tool_call.get(
                                        "arguments", tool_call.get("function_args", {})
                                    )
                                    if tool_args:
                                        st.write("**Arguments:**")
                                        st.json(tool_args)

                                    # Show result if available
                                    tool_result = tool_call.get(
                                        "result", tool_call.get("content")
                                    )
                                    if tool_result:
                                        st.write("**Result:**")
                                        if (
                                            isinstance(tool_result, str)
                                            and len(tool_result) > 200
                                        ):
                                            st.write(f"{tool_result[:200]}...")
                                        else:
                                            st.write(str(tool_result))

                                    # Show reasoning if available (legacy field)
                                    if tool_call.get("reasoning"):
                                        st.write(
                                            f"**Reasoning:** {tool_call['reasoning']}"
                                        )

                                    if i < len(
                                        tool_call_details
                                    ):  # Add separator between tools
                                        st.markdown("---")
                else:
                    st.info("No tool calls made yet.")
            else:
                st.info("No debug metrics available yet.")

            st.subheader("🔍 Recent Request Details")
            if st.session_state[SESSION_KEY_DEBUG_METRICS]:
                for entry in reversed(st.session_state[SESSION_KEY_DEBUG_METRICS][-5:]):
                    with st.expander(
                        f"{'✅' if entry['success'] else '❌'} {entry['timestamp']} - {entry['response_time']}s"
                    ):
                        st.write(f"**Prompt:** {entry['prompt']}")
                        st.write(f"**Response Time:** {entry['response_time']}s")
                        st.write(f"**Input Tokens:** {entry['input_tokens']}")
                        st.write(f"**Output Tokens:** {entry['output_tokens']}")
                        st.write(f"**Total Tokens:** {entry['total_tokens']}")
                        st.write(f"**Tool Calls:** {entry['tool_calls']}")
                        st.write(f"**Response Type:** {entry['response_type']}")
                        if not entry["success"]:
                            st.write(
                                f"**Error:** {entry.get('error', 'Unknown error')}"
                            )
            else:
                st.info("No debug metrics available yet.")


def main():
    """Main function to run the Streamlit app."""
    initialize_session_state()
    apply_custom_theme()

    # Streamlit UI
    st.title("🤖 Personal AI Friend with Memory")
    st.markdown(
        "*A friendly AI agent that remembers your conversations and learns about you*"
    )

    # Sidebar navigation (replaces top-level tabs)
    st.sidebar.title(f"🧠 {USER_ID}'s Personal Agent")
    selected_tab = st.sidebar.radio(
        "Navigation",
        ["💬 Chat", "🧠 Memory Manager", "📚 Knowledge Base"],
        index=0,
    )

    # Route content based on sidebar selection
    if selected_tab == "💬 Chat":
        render_chat_tab()
    elif selected_tab == "🧠 Memory Manager":
        render_memory_tab()
    elif selected_tab == "📚 Knowledge Base":
        render_knowledge_tab()

    # Append the original sidebar controls (theme/model/debug/etc.)
    render_sidebar()


if __name__ == "__main__":
    main()
