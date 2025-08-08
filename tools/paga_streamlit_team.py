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

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from the correct path
from personal_agent.config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    get_current_user_id,
)
from personal_agent.team.personal_agent_team import create_personal_agent_team

USER_ID = get_current_user_id()


# Parse command line arguments
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Personal Agent Team Streamlit App")
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama URL instead of local"
    )
    return parser.parse_known_args()  # Use parse_known_args to ignore Streamlit's args


# Parse arguments and determine Ollama URL
args, unknown = parse_args()
EFFECTIVE_OLLAMA_URL = REMOTE_OLLAMA_URL if args.remote else OLLAMA_URL

db_path = Path(AGNO_STORAGE_DIR) / "agent_memory.db"


def apply_custom_theme():
    """Apply custom CSS for theme switching."""
    # Get current theme from session state
    is_dark_theme = st.session_state.get("dark_theme", False)

    if is_dark_theme:
        # Dark theme CSS
        st.markdown(
            """
        <style>
        /* Dark theme styles */
        .stApp {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        
        /* Main content area */
        .main .block-container {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        
        /* Header area */
        .stApp > header {
            background-color: #0e1117 !important;
        }
        
        /* Main content wrapper */
        .stMainBlockContainer {
            background-color: #0e1117 !important;
        }
        
        /* Bottom toolbar/footer */
        .stBottom {
            background-color: #0e1117 !important;
        }
        
        /* Chat input outer container and all wrapper elements */
        .stChatFloatingInputContainer {
            /* background-color: #0e1117 !important; */
            border-top: 1px solid #4a4a4a !important;
        }
        
        /* Additional selectors for chat input area containers */
        section[data-testid="stChatFloatingInputContainer"] {
            /* background-color: #0e1117 !important; */
        }
        
        div[data-testid="stChatInput"] {
            background-color: #0e1117 !important;
        }
        
        /* Chat input wrapper */
        .stChatInput {
            background-color: #0e1117 !important;
        }
        
        .stChatInput > div {
            background-color: #0e1117 !important;
        }
        
        /* Target any remaining white containers around chat input */
        .stChatInput div:not([data-baseweb="textarea"]) {
            background-color: #0e1117 !important;
        }
        
        /* Bottom area containers - more comprehensive targeting */
        .stApp > div:last-child {
            background-color: #0e1117 !important;
        }
        
        /* Additional bottom area selectors */
        .stApp footer {
            background-color: #0e1117 !important;
        }
        
        /* Target any remaining white divs in the bottom area */
        .stChatFloatingInputContainer div {
            background-color: #0e1117 !important;
        }
        
        /* More specific chat input container targeting */
        [data-testid="stChatFloatingInputContainer"] > div {
            background-color: #0e1117 !important;
        }
        
        [data-testid="stChatFloatingInputContainer"] > div > div {
            background-color: #0e1117 !important;
        }
        
        /* Target the main viewport and large background areas */
        .main {
            background-color: #0e1117 !important;
        }
        
        .main > div {
            background-color: #0e1117 !important;
        }
        
        /* Target any large white background containers */
        div[data-testid="stAppViewContainer"] {
            background-color: #0e1117 !important;
        }
        
        div[data-testid="stMain"] {
            background-color: #0e1117 !important;
        }
        
        /* Target the bottom section specifically */
        section[data-testid="stSidebar"] ~ div {
            background-color: #0e1117 !important;
        }
        
        /* More aggressive targeting of large containers */
        .stApp > div {
            background-color: #0e1117 !important;
        }
        
        .stApp section {
            background-color: #0e1117 !important;
        }
        
        /* Nuclear option - target everything then exclude input */
        .stApp * {
            background-color: #0e1117 !important;
        }
        
        /* Restore input box to default */
        .stChatInput textarea,
        .stChatInput input,
        textarea,
        input[type="text"] {
            background-color: unset !important;
            color: unset !important;
            border: unset !important;
        }
        
        /* Restore other interactive elements */
        button {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        
        /* Sidebar */
        .stSidebar {
            background-color: #262730 !important;
        }
        
        .stSidebar .stMarkdown {
            color: #fafafa !important;
        }
        
        .stSidebar .stSelectbox > div > div {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        
        /* Text inputs */
        .stTextInput > div > div > input {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #6a6a6a !important;
            box-shadow: 0 0 0 1px #6a6a6a !important;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        
        .stButton > button:hover {
            background-color: #3a3a3a !important;
            border: 1px solid #6a6a6a !important;
        }
        
        /* Expanders */
        .stExpander {
            background-color: #1e1e1e !important;
            border: 1px solid #4a4a4a !important;
        }
        
        .stExpander > div > div > div > div {
            background-color: #1e1e1e !important;
        }
        
        /* Chat messages */
        .stChatMessage {
            background-color: #1e1e1e !important;
        }
        
        .stChatMessage > div {
            background-color: #1e1e1e !important;
        }
        
        /* Metrics */
        .stMetric {
            background-color: #1e1e1e !important;
            border: 1px solid #4a4a4a !important;
            border-radius: 5px !important;
            padding: 10px !important;
        }
        
        /* Alerts */
        .stAlert {
            background-color: #1e1e1e !important;
            border: 1px solid #4a4a4a !important;
        }
        
        /* Selectbox */
        .stSelectbox > div > div {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        
        /* Checkbox */
        .stCheckbox > label {
            color: #fafafa !important;
        }
        
        /* Headers and text */
        h1, h2, h3, h4, h5, h6 {
            color: #fafafa !important;
        }
        
        p, div, span {
            color: #fafafa !important;
        }
        
        /* Custom scrollbar for dark theme */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #262730;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #4a4a4a;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #6a6a6a;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )
    else:
        # Light theme CSS - restore to default Streamlit appearance
        # No custom CSS needed for light mode - let Streamlit use its defaults
        pass


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


def initialize_team(model_name, ollama_url):
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


# Initialize session state variables
if "current_ollama_url" not in st.session_state:
    st.session_state.current_ollama_url = EFFECTIVE_OLLAMA_URL

if "current_model" not in st.session_state:
    st.session_state.current_model = LLM_MODEL

# Initialize theme state (start with softer default theme)
if "dark_theme" not in st.session_state:
    st.session_state.dark_theme = False

# Initialize team
if "team" not in st.session_state:
    st.session_state.team = initialize_team(
        st.session_state.current_model, st.session_state.current_ollama_url
    )

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize debug metrics
if "debug_metrics" not in st.session_state:
    st.session_state.debug_metrics = []

# Initialize performance stats
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

# Initialize confirmation dialog state
if "show_memory_confirmation" not in st.session_state:
    st.session_state.show_memory_confirmation = False

# Apply theme before rendering UI
apply_custom_theme()

# Streamlit UI
theme_icon = "🌙" if st.session_state.dark_theme else "☀️"
theme_text = "Dark" if st.session_state.dark_theme else "Light"

# Create header with theme toggle
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🤖 Personal AI Team with Specialized Agents")
    st.markdown(
        "*A team of specialized AI agents working together: Memory, Web Research, Finance, Calculator, and File Operations*"
    )
with col2:
    # Theme toggle button
    if st.button(f"{theme_icon} {theme_text} Mode", key="theme_toggle"):
        st.session_state.dark_theme = not st.session_state.dark_theme
        st.rerun()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What would you like to talk about?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get team response
    with st.chat_message("assistant"):
        with st.spinner("Team is thinking..."):
            # Start timing
            start_time = time.time()
            start_timestamp = datetime.now()

            try:
                # Use the standard agno Team arun method (async)
                if st.session_state.team:
                    response = asyncio.run(
                        st.session_state.team.arun(prompt, user_id=USER_ID)
                    )
                    response_content = (
                        response.content
                        if hasattr(response, "content")
                        else str(response)
                    )
                else:
                    response_content = "Team not initialized properly"

                # End timing
                end_time = time.time()
                response_time = end_time - start_time

                # Calculate token estimates (rough approximation)
                input_tokens = len(prompt.split()) * 1.3  # Rough token estimate
                output_tokens = 0
                if response_content:
                    output_tokens = len(response_content.split()) * 1.3

                total_tokens = input_tokens + output_tokens

                # Extract tool call information from response
                tool_calls_made = 0
                tool_call_details = []

                if hasattr(response, "messages") and response.messages:
                    for message in response.messages:
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            tool_calls_made += len(message.tool_calls)
                            for tool_call in message.tool_calls:
                                tool_info = {
                                    "type": getattr(tool_call, "type", "function"),
                                    "function_name": getattr(
                                        tool_call, "name", "unknown"
                                    ),
                                    "function_args": getattr(tool_call, "input", {}),
                                }
                                tool_call_details.append(tool_info)

                # Update performance stats
                stats = st.session_state.performance_stats
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

                # Store detailed debug metrics
                debug_entry = {
                    "timestamp": start_timestamp.strftime("%H:%M:%S"),
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "response_time": round(response_time, 3),
                    "input_tokens": round(input_tokens),
                    "output_tokens": round(output_tokens),
                    "total_tokens": round(total_tokens),
                    "tool_calls": tool_calls_made,
                    "tool_call_details": tool_call_details,
                    "response_type": "AgnoTeam",
                    "success": True,
                }

                # Keep only last 10 debug entries
                st.session_state.debug_metrics.append(debug_entry)
                if len(st.session_state.debug_metrics) > 10:
                    st.session_state.debug_metrics.pop(0)

                # Enhanced debug information
                if st.session_state.get("show_debug", False):
                    with st.expander("🔍 **Team Debug Info**", expanded=False):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("⏱️ Response Time", f"{response_time:.3f}s")
                            st.metric("🔢 Input Tokens", f"{round(input_tokens)}")

                        with col2:
                            st.metric("📝 Output Tokens", f"{round(output_tokens)}")
                            st.metric("📊 Total Tokens", f"{round(total_tokens)}")

                        with col3:
                            st.metric("🛠️ Tool Calls", tool_calls_made)
                            st.metric("📋 Response Type", "AgnoTeam")

                        st.write("**Team Response Details:**")

                        # Enhanced tool call display for team format
                        if tool_call_details:
                            st.write("**🛠️ Tool Calls Made by Team:**")
                            for i, tool_call in enumerate(tool_call_details, 1):
                                st.write(f"**Tool Call {i}:**")
                                if isinstance(tool_call, dict):
                                    st.write(
                                        f"  - Type: {tool_call.get('type', 'function')}"
                                    )
                                    st.write(
                                        f"  - Function: {tool_call.get('function_name', 'unknown')}"
                                    )
                                    args = tool_call.get("function_args", {})
                                    if isinstance(args, dict) and args:
                                        formatted_args = ", ".join(
                                            [f"{k}={v}" for k, v in args.items()]
                                        )
                                        st.write(f"  - Arguments: {formatted_args}")
                                    elif args:
                                        st.write(f"  - Arguments: {args}")
                                    else:
                                        st.write(f"  - Arguments: (none)")
                                else:
                                    st.write(f"  - Tool Call: {str(tool_call)}")
                                st.write("---")
                        else:
                            st.write("- No tool calls detected")

                        # Show team info
                        if st.session_state.team:
                            st.write("**🤝 Team Information:**")
                            st.write(f"  - Framework: agno")
                            st.write(
                                f"  - Team Name: {getattr(st.session_state.team, 'name', 'Unknown')}"
                            )
                            st.write(
                                f"  - Member Count: {len(getattr(st.session_state.team, 'members', []))}"
                            )

                            members = getattr(st.session_state.team, "members", [])
                            if members:
                                st.write("**👥 Team Members:**")
                                for member in members:
                                    member_name = getattr(member, "name", "Unknown")
                                    member_role = getattr(member, "role", "Unknown")
                                    member_tools = len(getattr(member, "tools", []))
                                    st.write(
                                        f"  - {member_name}: {member_role} ({member_tools} tools)"
                                    )

                # Display the response content
                if response_content:
                    st.markdown(response_content)
                    # Add assistant response to chat history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_content}
                    )
                else:
                    # Handle case where response might not have content
                    error_msg = "Team returned empty response"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time

                # Log failed request
                debug_entry = {
                    "timestamp": start_timestamp.strftime("%H:%M:%S"),
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "response_time": round(response_time, 3),
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "tool_calls": 0,
                    "response_type": "Error",
                    "success": False,
                    "error": str(e),
                }
                st.session_state.debug_metrics.append(debug_entry)
                if len(st.session_state.debug_metrics) > 10:
                    st.session_state.debug_metrics.pop(0)

                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)

                # Show enhanced error debug info
                if st.session_state.get("show_debug", False):
                    with st.expander("❌ **Error Debug Info**", expanded=True):
                        st.write(f"**Error Time:** {response_time:.3f}s")
                        st.write(f"**Error Type:** {type(e).__name__}")
                        st.write(f"**Error Message:** {str(e)}")

                        import traceback

                        st.code(traceback.format_exc())

                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

# Sidebar with team info and controls
with st.sidebar:
    # Theme section at the top of sidebar
    st.header("🎨 Theme")
    theme_icon = "🌙" if st.session_state.dark_theme else "☀️"
    theme_text = "Dark" if st.session_state.dark_theme else "Light"

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Current Theme:** {theme_text}")
    with col2:
        if st.button(
            theme_icon,
            key="sidebar_theme_toggle",
            help=f"Switch to {('Light' if st.session_state.dark_theme else 'Dark')} mode",
        ):
            st.session_state.dark_theme = not st.session_state.dark_theme
            st.rerun()

    st.header("Model Selection")

    # Ollama URL input
    new_ollama_url = st.text_input(
        "Ollama URL:",
        value=st.session_state.current_ollama_url,
        help="Enter the Ollama server URL (e.g., http://localhost:11434)",
    )

    # Button to fetch models
    if st.button("🔄 Fetch Available Models"):
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
            help="Choose an Ollama model to use for the team",
        )

        # Button to apply model selection
        if st.button("🚀 Apply Model Selection"):
            if (
                selected_model != st.session_state.current_model
                or new_ollama_url != st.session_state.current_ollama_url
            ):
                with st.spinner("Reinitializing team with new model..."):
                    try:
                        # Update session state
                        st.session_state.current_model = selected_model
                        st.session_state.current_ollama_url = new_ollama_url

                        # Reinitialize team
                        st.session_state.team = initialize_team(
                            selected_model, new_ollama_url
                        )

                        # Clear chat history for new model
                        st.session_state.messages = []

                        st.success(f"Team updated to use model: {selected_model}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to initialize team: {str(e)}")
            else:
                st.info("Model and URL are already current")
    else:
        st.info("Click 'Fetch Available Models' to see available models")

    st.header("Team Information")
    st.write(f"**Current Model:** {st.session_state.current_model}")
    st.write(f"**Current Ollama URL:** {st.session_state.current_ollama_url}")

    # Show remote mode indicator
    if hasattr(args, "remote") and args.remote:
        st.success("🌐 **Remote Mode:** Using remote Ollama server")
    else:
        st.info("🏠 **Local Mode:** Using local Ollama server")

    st.write(f"**User ID:** {USER_ID}")

    # Show team composition
    if st.session_state.team:
        st.write(f"**Team Framework:** agno")
        members = getattr(st.session_state.team, "members", [])
        st.write(f"**Team Members:** {len(members)}")

        if members:
            st.write("**Specialized Agents:**")
            for member in members:
                member_name = getattr(member, "name", "Unknown")
                member_role = getattr(member, "role", "Unknown")
                st.write(f"• **{member_name}**: {member_role}")

    st.header("Controls")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    # Semantic Memory Manager Controls
    st.header("🧠 Semantic Memory")

    # Memory reset button
    if st.button("Reset User Memory"):
        st.session_state.show_memory_confirmation = True

    # Confirmation dialog popup
    if st.session_state.show_memory_confirmation:
        st.markdown("---")
        st.markdown("### ⚠️ Confirm Memory Deletion")
        st.error(
            "**WARNING**: This will permanently delete ALL stored memories and "
            "personal information about you. This action CANNOT be undone!"
        )
        st.info(
            "💡 **Remember**: Your AI team's memories help create better, "
            "more personalized conversations over time."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_memory_confirmation = False
                st.rerun()

        with col2:
            if st.button(
                "🗑️ Yes, Delete All Memories", type="primary", use_container_width=True
            ):
                if st.session_state.team and hasattr(
                    st.session_state.team, "agno_memory"
                ):
                    try:
                        # Clear all user memories
                        st.session_state.team.agno_memory.clear_user_memories(
                            user_id=USER_ID
                        )
                        st.session_state.show_memory_confirmation = False
                        st.success("⚠️ All team memories have been cleared!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing memories: {str(e)}")
                else:
                    st.error("Memory system not available")

    if st.button("Show All Memories"):
        if st.session_state.team and hasattr(st.session_state.team, "agno_memory"):
            try:
                memories = st.session_state.team.agno_memory.get_user_memories(
                    user_id=USER_ID
                )
                if memories:
                    st.subheader("Stored Memories")
                    for i, memory in enumerate(memories, 1):
                        # UserMemory objects have direct attributes, not dictionary access
                        memory_content = getattr(memory, "memory", "No content")
                        with st.expander(f"Memory {i}: {memory_content[:50]}..."):
                            st.write(f"**Content:** {memory_content}")
                            st.write(
                                f"**Memory ID:** {getattr(memory, 'memory_id', 'N/A')}"
                            )
                            st.write(
                                f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                            )
                            st.write(f"**Input:** {getattr(memory, 'input', 'N/A')}")
                            topics = getattr(memory, "topics", [])
                            if topics:
                                st.write(f"**Topics:** {', '.join(topics)}")
                else:
                    st.info(
                        "No memories stored yet. Start chatting to create some memories!"
                    )
            except Exception as e:
                st.error(f"Error retrieving memories: {str(e)}")
        else:
            st.error("Memory system not available")

    # Memory Statistics
    if st.button("📊 Show Memory Statistics"):
        if st.session_state.team and hasattr(st.session_state.team, "agno_memory"):
            try:
                # Access the SemanticMemoryManager through the Memory object
                memory_manager = st.session_state.team.agno_memory.memory_manager
                if hasattr(memory_manager, "get_memory_stats"):
                    stats = memory_manager.get_memory_stats(
                        st.session_state.team.agno_memory.db, USER_ID
                    )

                    st.subheader("🧠 Semantic Memory Statistics")

                    # Display basic stats
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Memories", stats.get("total_memories", 0))
                        st.metric("Recent (24h)", stats.get("recent_memories_24h", 0))

                    with col2:
                        avg_length = stats.get("average_memory_length", 0)
                        st.metric(
                            "Avg Length",
                            f"{avg_length:.1f} chars" if avg_length else "N/A",
                        )
                        most_common = stats.get("most_common_topic", "None")
                        st.metric("Top Topic", most_common if most_common else "None")

                    # Topic distribution
                    topic_dist = stats.get("topic_distribution", {})
                    if topic_dist:
                        st.subheader("📈 Topic Distribution")
                        for topic, count in sorted(
                            topic_dist.items(), key=lambda x: x[1], reverse=True
                        ):
                            st.write(f"**{topic.title()}:** {count} memories")

                    # Show SemanticMemoryManager configuration
                    st.subheader("⚙️ Memory Configuration")
                    config = memory_manager.config
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(
                            f"**Similarity Threshold:** {config.similarity_threshold}"
                        )
                        st.write(
                            f"**Semantic Dedup:** {'✅' if config.enable_semantic_dedup else '❌'}"
                        )
                        st.write(
                            f"**Exact Dedup:** {'✅' if config.enable_exact_dedup else '❌'}"
                        )
                    with col2:
                        st.write(
                            f"**Topic Classification:** {'✅' if config.enable_topic_classification else '❌'}"
                        )
                        st.write(f"**Max Memory Length:** {config.max_memory_length}")
                        st.write(
                            f"**Debug Mode:** {'✅' if config.debug_mode else '❌'}"
                        )

                else:
                    st.info(
                        "Memory statistics not available - SemanticMemoryManager not found"
                    )
            except Exception as e:
                st.error(f"Error getting memory statistics: {str(e)}")
                import traceback

                st.code(traceback.format_exc())
        else:
            st.error("Memory system not available")

    # Memory Search
    st.subheader("🔍 Search Memories")
    search_query = st.text_input(
        "Search Query:",
        placeholder="Enter keywords to search your memories...",
        help="Search through your stored memories using semantic similarity",
    )

    if st.button("Search") and search_query:
        if st.session_state.team and hasattr(st.session_state.team, "agno_memory"):
            try:
                # Try different search methods to avoid the KeyError bug
                memories = None

                # First try the "agentic" method for semantic search
                try:
                    memories = st.session_state.team.agno_memory.search_user_memories(
                        user_id=USER_ID,
                        query=search_query,
                        retrieval_method="agentic",
                        limit=10,
                    )
                except Exception as search_error:
                    st.warning(f"Semantic search failed: {str(search_error)}")
                    # Fallback: get all memories and filter manually
                    try:
                        all_memories = (
                            st.session_state.team.agno_memory.get_user_memories(
                                user_id=USER_ID
                            )
                        )

                        if all_memories:
                            filtered_memories = []
                            search_terms = search_query.lower().split()

                            for memory in all_memories:
                                memory_content = getattr(memory, "memory", "").lower()
                                memory_topics = getattr(memory, "topics", [])
                                topic_text = " ".join(memory_topics).lower()

                                # Check if any search term appears in memory content or topics
                                if any(
                                    term in memory_content or term in topic_text
                                    for term in search_terms
                                ):
                                    filtered_memories.append(memory)

                            memories = filtered_memories[:10]
                        else:
                            memories = []

                    except Exception as fallback_error:
                        st.error(f"Fallback search also failed: {str(fallback_error)}")
                        memories = []

                if memories:
                    st.subheader(f"Search Results for: '{search_query}'")
                    for i, memory in enumerate(memories, 1):
                        memory_content = getattr(memory, "memory", "No content")
                        with st.expander(f"Result {i}: {memory_content[:50]}..."):
                            st.write(f"**Memory:** {memory_content}")
                            topics = getattr(memory, "topics", [])
                            if topics:
                                st.write(f"**Topics:** {', '.join(topics)}")
                            st.write(
                                f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                            )
                            st.write(
                                f"**Memory ID:** {getattr(memory, 'memory_id', 'N/A')}"
                            )
                else:
                    st.info("No matching memories found. Try different keywords.")
            except Exception as e:
                st.error(f"Error searching memories: {str(e)}")
                # Show detailed error for debugging
                import traceback

                st.code(traceback.format_exc())
        else:
            st.error("Memory system not available")

    st.header("Debug Info")
    # Debug mode toggle
    st.session_state.show_debug = st.checkbox(
        "Enable Debug Mode", value=st.session_state.get("show_debug", False)
    )

    if st.session_state.show_debug:
        # Performance Statistics
        st.subheader("📊 Performance Statistics")
        stats = st.session_state.performance_stats

        if stats["total_requests"] > 0:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Requests", stats["total_requests"])
                st.metric("Avg Response Time", f"{stats['average_response_time']:.3f}s")
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

        # Recent Debug Metrics
        st.subheader("🔍 Recent Request Details")
        if st.session_state.debug_metrics:
            for i, entry in enumerate(
                reversed(st.session_state.debug_metrics[-5:])
            ):  # Show last 5
                status_icon = "✅" if entry["success"] else "❌"
                tool_indicator = (
                    f" 🛠️{entry['tool_calls']}" if entry["tool_calls"] > 0 else ""
                )
                with st.expander(
                    f"{status_icon} {entry['timestamp']} - {entry['response_time']}s{tool_indicator}",
                    expanded=False,
                ):
                    st.write(f"**Prompt:** {entry['prompt']}")
                    st.write(f"**Response Time:** {entry['response_time']}s")
                    st.write(
                        f"**Tokens:** {entry['total_tokens']} (In: {entry['input_tokens']}, Out: {entry['output_tokens']})"
                    )
                    st.write(f"**Tool Calls:** {entry['tool_calls']}")
                    st.write(f"**Response Type:** {entry['response_type']}")

                    if not entry["success"] and "error" in entry:
                        st.error(f"**Error:** {entry['error']}")
        else:
            st.info("No debug metrics available yet.")

        # Clear debug data button
        if st.button("🗑️ Clear Debug Data"):
            st.session_state.debug_metrics = []
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
            st.success("Debug data cleared!")
            st.rerun()

# Initialize instructions display state
if "instructions_shown" not in st.session_state:
    st.session_state.instructions_shown = False

# Instructions for running - only show once
if not st.session_state.instructions_shown:
    st.markdown(
        """
    ---
    **Talk to the team!**
    
    Try these example queries:
    - "What do you remember about me?" (Memory Agent)
    - "What's the latest AI news?" (Web Research Agent)
    - "What's Tesla's stock price?" (Finance Agent)
    - "Calculate 15% of 250" (Calculator Agent)
    - "Remember that I love hiking, then search for hiking news" (Multiple agents)
    """
    )
    st.session_state.instructions_shown = True
