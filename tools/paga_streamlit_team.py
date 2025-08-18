"""
Personal Agent Team Streamlit Web UI (PAGA Team)
===============================================

This module provides the main web-based user interface for the Personal Agent Team system,
built using Streamlit. It serves as a comprehensive dashboard for interacting with
a team of specialized AI agents that work together to provide memory, knowledge management,
web research, finance, calculator, and file operations capabilities.

Key Features
-----------
🤖 **Team-Based Conversational AI Interface**
    - Real-time chat with Personal Agent Team
    - Streaming responses with tool call visualization
    - Support for multiple LLM models via Ollama
    - Advanced debugging and performance metrics

🧠 **Memory Management System**
    - Store, search, and manage personal facts and memories
    - Semantic similarity search with configurable thresholds
    - Topic-based categorization and organization
    - Synchronization between local SQLite and graph-based storage
    - Comprehensive memory statistics and analytics

📚 **Knowledge Base Management**
    - Multi-format file upload support (PDF, DOCX, TXT, MD, HTML, etc.)
    - Direct text content ingestion with format selection
    - Web content extraction from URLs
    - Dual search capabilities: SQLite/LanceDB and RAG-based
    - Advanced RAG query modes (naive, hybrid, local, global, mix, bypass)

⚙️ **System Configuration**
    - Dynamic model selection and switching
    - Ollama server configuration (local/remote)
    - RAG server location management (localhost/tesla.tail19187e.ts.net)
    - Theme switching (light/dark mode)
    - Debug mode with detailed performance analytics

🔧 **Advanced Features**
    - Real-time tool call monitoring and visualization
    - Performance metrics tracking (response times, token usage)
    - Memory-knowledge synchronization status monitoring
    - Comprehensive error handling and logging
    - Session state management for persistent user experience

Architecture
-----------
The application is built around three main components:

1. **Personal Agent Team**: Team of specialized agents working together
2. **Streamlit Interface**: Multi-tab web UI with chat, memory, and knowledge sections
3. **Helper Classes**: StreamlitMemoryHelper and StreamlitKnowledgeHelper for data operations

Technical Stack
--------------
- **Frontend**: Streamlit with custom CSS theming
- **AI Team**: Personal Agent Team with specialized agents
- **Memory Storage**: SQLite with semantic search via embeddings
- **Knowledge Storage**: SQLite/LanceDB + RAG server integration
- **LLM Integration**: Ollama with support for multiple models
- **Visualization**: Altair charts for performance metrics

Usage
-----
Run the application with:
    ```bash
    streamlit run tools/paga_streamlit_team.py [--remote] [--recreate]
    ```

Command Line Arguments:
    --remote: Use remote Ollama URL instead of local
    --recreate: Recreate knowledge base and clear all memories

Environment Variables:
    - AGNO_STORAGE_DIR: Directory for agent storage
    - AGNO_KNOWLEDGE_DIR: Directory for knowledge files
    - LLM_MODEL: Default language model to use
    - OLLAMA_URL: Local Ollama server URL
    - REMOTE_OLLAMA_URL: Remote Ollama server URL
    - USER_ID: Current user identifier

Session Management
-----------------
The application maintains persistent session state across interactions:
- Chat message history
- Team configuration and initialization
- Performance metrics and debug information
- User preferences (theme, model selection)
- Memory and knowledge helper instances

Author: Personal Agent Development Team
Version: v0.2.0
Last Revision: 2025-08-17 20:34:33
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import requests
import streamlit as st

# Apply dashboard-style layout but keep original page title/icon
st.set_page_config(
    page_title="Personal AI Team with Specialized Agents",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from the correct path
from personal_agent.config import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    DATA_DIR,
    LIGHTRAG_URL,
    LLM_MODEL,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    get_current_user_id,
)
from personal_agent.team.personal_agent_team import create_personal_agent_team
from personal_agent.tools.streamlit_helpers import (
    StreamlitKnowledgeHelper,
    StreamlitMemoryHelper,
)

# Constants for session state keys
SESSION_KEY_MESSAGES = "messages"
SESSION_KEY_TEAM = "team"
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

# Optional imports
try:
    import altair as alt
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# Parse command line arguments
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Personal Agent Team Streamlit App")
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama URL instead of local"
    )
    parser.add_argument("--debug", action="store_true", help="Set debug mode")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the knowledge base and clear all memories",
    )
    return parser.parse_known_args()  # Use parse_known_args to ignore Streamlit's args


# Parse arguments and determine Ollama URL and recreate flag
args, unknown = parse_args()
EFFECTIVE_OLLAMA_URL = REMOTE_OLLAMA_URL if args.remote else OLLAMA_URL
RECREATE_FLAG = args.recreate
DEBUG_FLAG = args.debug

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

        # Create memory system for Streamlit compatibility
        from personal_agent.core.agno_storage import create_agno_memory

        agno_memory = create_agno_memory(AGNO_STORAGE_DIR, debug_mode=True)

        # Attach memory to team for Streamlit access
        team.agno_memory = agno_memory

        return team
    except Exception as e:
        st.error(f"Failed to initialize team: {str(e)}")
        return None


def apply_custom_theme():
    """Apply custom CSS for theme switching."""
    is_dark_theme = st.session_state.get(SESSION_KEY_DARK_THEME, False)
    css_file = "tools/dark_theme.css" if is_dark_theme else "tools/light_theme.css"
    try:
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback to inline CSS if files don't exist
        if is_dark_theme:
            st.markdown(
                """
            <style>
            .stApp {
                background-color: #0e1117 !important;
                color: #fafafa !important;
            }
            .stSidebar {
                background-color: #262730 !important;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )


def initialize_session_state():
    """Initialize all session state variables."""
    if SESSION_KEY_CURRENT_OLLAMA_URL not in st.session_state:
        st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = EFFECTIVE_OLLAMA_URL

    if SESSION_KEY_CURRENT_MODEL not in st.session_state:
        st.session_state[SESSION_KEY_CURRENT_MODEL] = LLM_MODEL

    if SESSION_KEY_DARK_THEME not in st.session_state:
        st.session_state[SESSION_KEY_DARK_THEME] = False

    if SESSION_KEY_TEAM not in st.session_state:
        st.session_state[SESSION_KEY_TEAM] = initialize_team(
            st.session_state[SESSION_KEY_CURRENT_MODEL],
            st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL],
            recreate=RECREATE_FLAG,
        )

    # Create a wrapper agent for the helper classes
    if SESSION_KEY_MEMORY_HELPER not in st.session_state:
        # Create a wrapper that makes the team look like an agent for the helpers
        class TeamWrapper:
            def __init__(self, team):
                self.team = team
                self.user_id = USER_ID
                self.agno_memory = getattr(team, "agno_memory", None)

            def store_user_memory(self, content, topics=None):
                # Use team's memory functionality if available
                if hasattr(self.team, "agno_memory") and self.team.agno_memory:
                    return self.team.agno_memory.store_user_memory(
                        user_id=self.user_id, memory_text=content, topics=topics
                    )
                else:
                    raise Exception("Team memory not available")

        team_wrapper = TeamWrapper(st.session_state[SESSION_KEY_TEAM])
        st.session_state[SESSION_KEY_MEMORY_HELPER] = StreamlitMemoryHelper(
            team_wrapper
        )

    if SESSION_KEY_KNOWLEDGE_HELPER not in st.session_state:
        # For knowledge helper, we'll need to create a more sophisticated wrapper
        # For now, use the team directly and handle missing methods gracefully
        st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = StreamlitKnowledgeHelper(
            st.session_state[SESSION_KEY_TEAM]
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
    st.markdown("### Chat with your AI Team")

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

            with st.spinner("🤔 Team is thinking..."):
                start_time = time.time()
                start_timestamp = datetime.now()
                response = ""
                tool_calls_made = 0
                tool_call_details = []
                all_tools_used = []

                try:
                    team = st.session_state[SESSION_KEY_TEAM]

                    if team:
                        # Use the standard agno Team arun method (async)
                        response_obj = asyncio.run(team.arun(prompt, user_id=USER_ID))
                        response = (
                            response_obj.content
                            if hasattr(response_obj, "content")
                            else str(response_obj)
                        )

                        # Extract tool call information from response
                        if hasattr(response_obj, "messages") and response_obj.messages:
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

                    # Display the final response
                    resp_container.markdown(response)

                    end_time = time.time()
                    response_time = end_time - start_time

                    # Calculate token estimates
                    input_tokens = len(prompt.split()) * 1.3
                    output_tokens = len(response.split()) * 1.3 if response else 0
                    total_tokens = input_tokens + output_tokens

                    # Update performance stats
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

                    # Store debug metrics
                    debug_entry = {
                        "timestamp": start_timestamp.strftime("%H:%M:%S"),
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "response_time": round(response_time, 3),
                        "input_tokens": round(input_tokens),
                        "output_tokens": round(output_tokens),
                        "total_tokens": round(total_tokens),
                        "tool_calls": tool_calls_made,
                        "tool_call_details": tool_call_details,
                        "response_type": "PersonalAgentTeam",
                        "success": True,
                    }
                    st.session_state[SESSION_KEY_DEBUG_METRICS].append(debug_entry)
                    if len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 10:
                        st.session_state[SESSION_KEY_DEBUG_METRICS].pop(0)

                    # Display debug info if enabled
                    if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
                        with st.expander("🔍 **Team Debug Info**", expanded=False):
                            st.write(f"**Response Type:** PersonalAgentTeam")
                            st.write(f"**Tool Calls Made:** {tool_calls_made}")
                            st.write(f"**Response Time:** {response_time:.3f}s")
                            st.write(f"**Total Tokens:** {total_tokens:.0f}")

                            if tool_call_details:
                                st.write("**🛠️ Tool Calls Made by Team:**")
                                for i, tool_call in enumerate(tool_call_details, 1):
                                    st.write(f"**Tool Call {i}:**")
                                    st.write(
                                        f"  - Function: {tool_call.get('name', 'unknown')}"
                                    )
                                    args = tool_call.get("arguments", {})
                                    if args:
                                        st.write(f"  - Arguments: {args}")

                            # Show team info
                            if team:
                                st.write("**🤝 Team Information:**")
                                st.write(f"  - Framework: agno")
                                st.write(
                                    f"  - Team Name: {getattr(team, 'name', 'Personal Agent Team')}"
                                )
                                members = getattr(team, "members", [])
                                st.write(f"  - Member Count: {len(members)}")

                                if members:
                                    st.write("**👥 Team Members:**")
                                    for member in members:
                                        member_name = getattr(member, "name", "Unknown")
                                        member_role = getattr(member, "role", "Unknown")
                                        member_tools = len(getattr(member, "tools", []))
                                        st.write(
                                            f"  - {member_name}: {member_role} ({member_tools} tools)"
                                        )

                    # Store message
                    message_data = {
                        "role": "assistant",
                        "content": response,
                        "response_type": "PersonalAgentTeam",
                        "tool_calls": tool_call_details,
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
        success, message, memory_id, _ = memory_helper.add_memory(
            memory_text=fact_input.strip(),
            topics=topic_list,
            input_text="Direct fact storage",
        )
        if success:
            # Transient success popup/toast with short delay before rerun
            try:
                st.toast("🎉 Fact saved to memory", icon="✅")
                time.sleep(1.25)
            except Exception:
                _popup = st.empty()
                _popup.success("🎉 Fact saved to memory")
                time.sleep(1.25)
                _popup.empty()
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
            st.caption(f"**Data Dir:** {DATA_DIR}")
            st.caption(f"**Knowledge Dir:** {AGNO_KNOWLEDGE_DIR}")

            # For team, we don't have the same initialization pattern as AgnoPersonalAgent
            # So we'll provide a simpler status check
            try:
                km = knowledge_helper.knowledge_manager
                if km:
                    st.success("✅ Ready")
                    st.caption("Knowledge base loaded")
                else:
                    st.warning("⚠️ Offline")
                    st.caption("Knowledge manager not available")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.caption("Failed to access knowledge system")

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

            # Check RAG server status
            try:
                health_response = requests.get(f"{rag_url}/health", timeout=10)
                if health_response.status_code == 200:
                    try:
                        pipeline_response = requests.get(
                            f"{rag_url}/documents/pipeline_status", timeout=10
                        )
                        if pipeline_response.status_code == 200:
                            pipeline_data = pipeline_response.json()

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

                            if pipeline_data.get("last_processed"):
                                st.caption(f"Last: {pipeline_data['last_processed']}")
                        else:
                            st.success("✅ Ready")
                            st.caption("(Pipeline status unavailable)")
                    except requests.exceptions.RequestException:
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
                        # For team, we'll need to handle knowledge ingestion differently
                        # Since teams don't have the same tool structure as individual agents
                        results.append(
                            f"**{uploaded_file.name}**: ⚠️ Knowledge ingestion not yet implemented for teams"
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
            st.warning("⚠️ Knowledge ingestion not yet implemented for teams")
        else:
            st.warning("⚠️ Please provide both title and content")

    # URL Input Section
    st.markdown("---")
    st.subheader("🌐 Add Knowledge from URL")
    st.markdown("*Extract and add content from web pages*")

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
            st.warning("⚠️ Knowledge ingestion from URL not yet implemented for teams")
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
        is_dark = st.session_state.get(SESSION_KEY_DARK_THEME, False)
        theme_icon = "🌙" if is_dark else "☀️"
        theme_text = "Dark" if is_dark else "Light"
        if st.button(f"{theme_icon} {theme_text} Mode", key="sidebar_theme_toggle"):
            st.session_state[SESSION_KEY_DARK_THEME] = not st.session_state[
                SESSION_KEY_DARK_THEME
            ]
            st.rerun()

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
                    with st.spinner("Reinitializing team..."):
                        st.session_state[SESSION_KEY_CURRENT_MODEL] = selected_model
                        st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = (
                            new_ollama_url
                        )
                        st.session_state[SESSION_KEY_TEAM] = initialize_team(
                            selected_model,
                            new_ollama_url,
                            st.session_state[SESSION_KEY_TEAM],
                        )

                        # Update helper classes with new team
                        class TeamWrapper:
                            def __init__(self, team):
                                self.team = team
                                self.user_id = USER_ID
                                self.agno_memory = getattr(team, "agno_memory", None)

                            def store_user_memory(self, content, topics=None):
                                if (
                                    hasattr(self.team, "agno_memory")
                                    and self.team.agno_memory
                                ):
                                    return self.team.agno_memory.store_user_memory(
                                        user_id=self.user_id,
                                        memory_text=content,
                                        topics=topics,
                                    )
                                else:
                                    raise Exception("Team memory not available")

                        team_wrapper = TeamWrapper(st.session_state[SESSION_KEY_TEAM])
                        st.session_state[SESSION_KEY_MEMORY_HELPER] = (
                            StreamlitMemoryHelper(team_wrapper)
                        )
                        st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                            StreamlitKnowledgeHelper(st.session_state[SESSION_KEY_TEAM])
                        )

                        st.session_state[SESSION_KEY_MESSAGES] = []
                        st.success(f"Team updated to use model: {selected_model}")
                        st.rerun()
                else:
                    st.info("Model and URL are already current")
        else:
            st.info("Click 'Fetch Available Models' to see available models")

        st.header("Team Information")
        st.write(f"**Current Model:** {st.session_state[SESSION_KEY_CURRENT_MODEL]}")
        st.write(
            f"**Current Ollama URL:** {st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]}"
        )

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

                # Show team's actual configuration if available
                team = st.session_state.get(SESSION_KEY_TEAM)
                if team and hasattr(team, "ollama_base_url"):
                    st.write(f"**Team's Ollama URL:** {team.ollama_base_url}")
                else:
                    st.write("**Team URL:** Not accessible")

        # Show team composition
        if st.session_state[SESSION_KEY_TEAM]:
            st.write(f"**Team Framework:** agno")
            members = getattr(st.session_state[SESSION_KEY_TEAM], "members", [])
            st.write(f"**Team Members:** {len(members)}")

            if members:
                st.write("**Specialized Agents:**")
                for member in members:
                    member_name = getattr(member, "name", "Unknown")
                    member_role = getattr(member, "role", "Unknown")
                    st.write(f"• **{member_name}**: {member_role}")

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

            if (
                len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 1
                and PANDAS_AVAILABLE
            ):
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
    st.title("🤖 Personal AI Team with Specialized Agents")
    st.markdown(
        "*A team of specialized AI agents working together: Memory, Web Research, Finance, Calculator, and File Operations*"
    )

    # Sidebar navigation (replaces top-level tabs)
    st.sidebar.title(f"🤖 {USER_ID}'s Personal Agent")
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
