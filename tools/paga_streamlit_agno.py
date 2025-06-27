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
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    USER_ID,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent


# Parse command line arguments
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Personal Agent Streamlit App")
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama URL instead of local"
    )
    return parser.parse_known_args()  # Use parse_known_args to ignore Streamlit's args


# Parse arguments and determine Ollama URL
args, unknown = parse_args()
EFFECTIVE_OLLAMA_URL = REMOTE_OLLAMA_URL if args.remote else OLLAMA_URL

db_path = Path(AGNO_STORAGE_DIR) / "agent_memory.db"


# Helper functions for direct SemanticMemoryManager access
def get_memory_manager_and_db():
    """Get direct access to memory manager and database."""
    if not hasattr(st.session_state, "agent"):
        return None, None

    agent = st.session_state.agent
    if not (hasattr(agent, "agno_memory") and agent.agno_memory):
        return None, None

    return agent.agno_memory.memory_manager, agent.agno_memory.db


def direct_search_memories(
    query: str, limit: int = 10, similarity_threshold: float = 0.3
):
    """Direct semantic search without agentic retrieval."""
    memory_manager, db = get_memory_manager_and_db()
    if not memory_manager or not db:
        return []

    try:
        results = memory_manager.search_memories(
            query=query,
            db=db,
            user_id=USER_ID,
            limit=limit,
            similarity_threshold=similarity_threshold,
            search_topics=True,
            topic_boost=0.5,
        )
        # Convert results to list of (UserMemory, score) tuples
        return results
    except Exception as e:
        st.error(f"Error in direct memory search: {e}")
        return []


def direct_get_all_memories():
    """Get all memories directly through SemanticMemoryManager."""
    memory_manager, db = get_memory_manager_and_db()
    if not memory_manager or not db:
        return []

    try:
        # Use the existing get_user_memories method from agno_memory
        agent = st.session_state.agent
        return agent.agno_memory.get_user_memories(user_id=USER_ID)
    except Exception as e:
        st.error(f"Error getting all memories: {e}")
        return []


def direct_add_memory(memory_text: str, topics: list = None, input_text: str = None):
    """Add memory directly through SemanticMemoryManager."""
    memory_manager, db = get_memory_manager_and_db()
    if not memory_manager or not db:
        return False, "Memory system not available", None

    try:
        return memory_manager.add_memory(
            memory_text=memory_text,
            db=db,
            user_id=USER_ID,
            topics=topics,
            input_text=input_text,
        )
    except Exception as e:
        return False, f"Error adding memory: {e}", None


def direct_clear_memories():
    """Clear all memories directly through SemanticMemoryManager."""
    memory_manager, db = get_memory_manager_and_db()
    if not memory_manager or not db:
        return False, "Memory system not available"

    try:
        return memory_manager.clear_memories(db=db, user_id=USER_ID)
    except Exception as e:
        return False, f"Error clearing memories: {e}"


def direct_get_memory_stats():
    """Get memory statistics directly through SemanticMemoryManager."""
    memory_manager, db = get_memory_manager_and_db()
    if not memory_manager or not db:
        return {"error": "Memory system not available"}

    try:
        return memory_manager.get_memory_stats(db, USER_ID)
    except Exception as e:
        return {"error": f"Error getting memory stats: {e}"}


def direct_delete_memory(memory_id: str):
    """Delete a specific memory directly through SemanticMemoryManager."""
    memory_manager, db = get_memory_manager_and_db()
    if not memory_manager or not db:
        return False, "Memory system not available"

    try:
        return memory_manager.delete_memory(memory_id, db, USER_ID)
    except Exception as e:
        return False, f"Error deleting memory: {e}"


def direct_update_memory(
    memory_id: str, memory_text: str, topics: list = None, input_text: str = None
):
    """Update a memory directly through SemanticMemoryManager."""
    memory_manager, db = get_memory_manager_and_db()
    if not memory_manager or not db:
        return False, "Memory system not available"

    try:
        return memory_manager.update_memory(
            memory_id=memory_id,
            memory_text=memory_text,
            db=db,
            user_id=USER_ID,
            topics=topics,
            input_text=input_text,
        )
    except Exception as e:
        return False, f"Error updating memory: {e}"


def direct_search_rag(query: str, mode: str = "naive"):
    """Direct search of the RAG KB"""
    agent = st.session_state.agent
    if not (hasattr(agent, "lightrag_knowledge")):
        return None

    # Use asyncio to run the async method with "naive" mode for correct results
    try:
        return asyncio.run(agent.query_knowledge_base(query, mode="naive"))
    except Exception as e:
        st.error(f"Error querying knowledge base: {e}")
        return None


# Helper functions for direct Knowledge Base access
def get_knowledge_manager():
    """Get direct access to knowledge manager."""
    if not hasattr(st.session_state, "agent"):
        return None

    agent = st.session_state.agent
    if not (hasattr(agent, "agno_knowledge") and agent.agno_knowledge):
        return None

    return agent.agno_knowledge


def direct_search_knowledge(query: str, limit: int = 10):
    """Direct knowledge base search."""
    knowledge_manager = get_knowledge_manager()
    if not knowledge_manager:
        return []

    try:
        # Use the knowledge manager's search functionality
        results = knowledge_manager.search(query=query, num_documents=limit)
        return results
    except Exception as e:
        st.error(f"Error in knowledge search: {e}")
        return []


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


async def initialize_agent_async(model_name, ollama_url, existing_agent=None):
    """Initialize AgnoPersonalAgent with proper async handling."""
    if existing_agent and isinstance(existing_agent, AgnoPersonalAgent):
        # Update existing agent's configuration
        existing_agent.model_name = model_name
        existing_agent.ollama_base_url = ollama_url
        # Reinitialize with new settings
        await existing_agent.initialize()
        return existing_agent
    else:
        # Create new AgnoPersonalAgent
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=model_name,
            ollama_base_url=ollama_url,
            user_id=USER_ID,
            debug=True,
            enable_memory=True,
            enable_mcp=False,  # Disable MCP to avoid conflicts with DuckDuckGo tools
            storage_dir=AGNO_STORAGE_DIR,
            knowledge_dir=AGNO_KNOWLEDGE_DIR,
        )
        await agent.initialize()
        return agent


def initialize_agent(model_name, ollama_url, existing_agent=None):
    """Sync wrapper for agent initialization."""
    return asyncio.run(initialize_agent_async(model_name, ollama_url, existing_agent))


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
        # Light theme CSS - minimal styling to avoid breaking interaction icons
        st.markdown(
            """
        <style>
        /* Light theme - only override essential elements, preserve interaction icons */
        .stApp {
            background-color: white !important;
            color: black !important;
        }
        
        .main .block-container {
            background-color: white !important;
            color: black !important;
        }
        
        .stSidebar {
            background-color: #f0f2f6 !important;
        }
        
        .stSidebar .stMarkdown {
            color: black !important;
        }
        
        /* Only target specific input elements to avoid breaking icons */
        .stTextInput > div > div > input {
            background-color: white !important;
            color: black !important;
            border: 1px solid #e0e0e0 !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #0066cc !important;
            box-shadow: 0 0 0 1px #0066cc !important;
        }
        
        /* Headers and main text only */
        h1, h2, h3, h4, h5, h6 {
            color: black !important;
        }
        
        /* Reset custom scrollbar to default */
        ::-webkit-scrollbar {
            width: unset;
        }
        
        ::-webkit-scrollbar-track {
            background: unset;
        }
        
        ::-webkit-scrollbar-thumb {
            background: unset;
            border-radius: unset;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: unset;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )


# Initialize session state variables
if "current_ollama_url" not in st.session_state:
    st.session_state.current_ollama_url = EFFECTIVE_OLLAMA_URL

if "current_model" not in st.session_state:
    st.session_state.current_model = LLM_MODEL

# Initialize theme state (start with softer default theme)
if "dark_theme" not in st.session_state:
    st.session_state.dark_theme = False

# Initialize agent
if "agent" not in st.session_state:
    st.session_state.agent = initialize_agent(
        st.session_state.current_model, st.session_state.current_ollama_url
    )

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize confirmation dialog state
if "show_memory_confirmation" not in st.session_state:
    st.session_state.show_memory_confirmation = False

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

# Apply theme before rendering UI
apply_custom_theme()

# Streamlit UI
theme_icon = "🌙" if st.session_state.dark_theme else "☀️"
theme_text = "Dark" if st.session_state.dark_theme else "Light"

# Create header with theme toggle
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🤖 Personal AI Friend with Memory")
    st.markdown(
        "*A friendly AI agent that remembers your conversations and learns about you*"
    )
with col2:
    # Theme toggle button
    if st.button(f"{theme_icon} {theme_text} Mode", key="theme_toggle"):
        st.session_state.dark_theme = not st.session_state.dark_theme
        st.rerun()

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["💬 Chat", "🧠 Memory Manager", "📚 Knowledge Base"])

with tab1:
    # Chat Tab Content
    st.markdown("### Have a conversation with your AI friend")

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

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Start timing
                start_time = time.time()
                start_timestamp = datetime.now()

                try:
                    # Handle async agent response
                    if isinstance(st.session_state.agent, AgnoPersonalAgent):
                        response_content = asyncio.run(
                            st.session_state.agent.run(prompt)
                        )
                    else:
                        # Fallback for other agent types
                        response = st.session_state.agent.run(prompt)
                        response_content = (
                            response.content
                            if hasattr(response, "content")
                            else str(response)
                        )

                    # End timing
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Calculate token estimates (rough approximation)
                    input_tokens = len(prompt.split()) * 1.3  # Rough token estimate
                    output_tokens = 0
                    if response_content:
                        output_tokens = len(response_content.split()) * 1.3

                    total_tokens = input_tokens + output_tokens

                    # For AgnoPersonalAgent, get tool call details from the agent
                    tool_call_info = st.session_state.agent.get_last_tool_calls()
                    tool_calls_made = tool_call_info.get("tool_calls_count", 0)
                    tool_call_details = tool_call_info.get("tool_call_details", [])

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
                        "response_type": (
                            "AgnoPersonalAgent"
                            if isinstance(st.session_state.agent, AgnoPersonalAgent)
                            else "Unknown"
                        ),
                        "success": True,
                    }

                    # Keep only last 10 debug entries
                    st.session_state.debug_metrics.append(debug_entry)
                    if len(st.session_state.debug_metrics) > 10:
                        st.session_state.debug_metrics.pop(0)

                    # Enhanced debug information
                    if st.session_state.get("show_debug", False):
                        with st.expander("🔍 **Detailed Debug Info**", expanded=False):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric("⏱️ Response Time", f"{response_time:.3f}s")
                                st.metric("🔢 Input Tokens", f"{round(input_tokens)}")

                            with col2:
                                st.metric("📝 Output Tokens", f"{round(output_tokens)}")
                                st.metric("📊 Total Tokens", f"{round(total_tokens)}")

                            with col3:
                                st.metric("🛠️ Tool Calls", tool_calls_made)
                                st.metric(
                                    "📋 Response Type",
                                    (
                                        "AgnoPersonalAgent"
                                        if isinstance(
                                            st.session_state.agent, AgnoPersonalAgent
                                        )
                                        else "Unknown"
                                    ),
                                )

                            st.write("**Response Object Details:**")

                            # Enhanced tool call display for new format
                            if tool_call_details:
                                st.write("**🛠️ Tool Calls Made:**")
                                for i, tool_call in enumerate(tool_call_details, 1):
                                    st.write(f"**Tool Call {i}:**")
                                    # Handle new dictionary format from get_last_tool_calls()
                                    if isinstance(tool_call, dict):
                                        st.write(
                                            f"  - Type: {tool_call.get('type', 'function')}"
                                        )
                                        st.write(
                                            f"  - Function: {tool_call.get('function_name', 'unknown')}"
                                        )
                                        args = tool_call.get("function_args", {})
                                        # Format arguments nicely
                                        if isinstance(args, dict) and args:
                                            formatted_args = ", ".join(
                                                [f"{k}={v}" for k, v in args.items()]
                                            )
                                            st.write(f"  - Arguments: {formatted_args}")
                                            st.write(
                                                f"  - ✅ Arguments parsed successfully"
                                            )
                                        elif args:
                                            st.write(f"  - Arguments: {args}")
                                            st.write(f"  - ✅ Arguments available")
                                        else:
                                            st.write(f"  - Arguments: (none)")
                                            st.write(f"  - ℹ️ No arguments required")
                                    # Handle legacy format for compatibility
                                    elif hasattr(tool_call, "function"):
                                        st.write(
                                            f"  - Function: {tool_call.function.name}"
                                        )
                                        st.write(
                                            f"  - Arguments: {tool_call.function.arguments}"
                                        )
                                    elif hasattr(tool_call, "name"):
                                        st.write(f"  - Tool: {tool_call.name}")
                                        if hasattr(tool_call, "input"):
                                            st.write(f"  - Input: {tool_call.input}")
                                    else:
                                        st.write(f"  - Tool Call: {str(tool_call)}")
                                    st.write("---")
                            else:
                                st.write("- No tool calls detected")

                            # Show debug info from get_last_tool_calls if available
                            if isinstance(st.session_state.agent, AgnoPersonalAgent):
                                debug_info = tool_call_info.get("debug_info", {})
                                if debug_info:
                                    st.write("**🔍 Tool Call Debug Info:**")
                                    st.write(
                                        f"  - Response has messages: {debug_info.get('has_messages', False)}"
                                    )
                                    st.write(
                                        f"  - Messages count: {debug_info.get('messages_count', 0)}"
                                    )
                                    st.write(
                                        f"  - Has tool_calls attr: {debug_info.get('has_tool_calls_attr', False)}"
                                    )
                                    response_attrs = debug_info.get(
                                        "response_attributes", []
                                    )
                                    if response_attrs:
                                        st.write(
                                            f"  - Response attributes: {response_attrs}"
                                        )

                            # For AgnoPersonalAgent, we only have response_content (string)
                            if isinstance(st.session_state.agent, AgnoPersonalAgent):
                                st.write("- Response format: String content")
                                if response_content:
                                    content_preview = (
                                        response_content[:200] + "..."
                                        if len(response_content) > 200
                                        else response_content
                                    )
                                    st.write(f"- Content preview: {content_preview}")
                            else:
                                # For other agent types that have response objects
                                if (
                                    "response" in locals()
                                    and hasattr(response, "messages")
                                    and response.messages
                                ):
                                    st.write(
                                        f"- Messages count: {len(response.messages)}"
                                    )
                                    st.write("**Message Details:**")
                                    for i, msg in enumerate(response.messages):
                                        st.write(f"**Message {i+1}:**")
                                        st.write(
                                            f"  - Role: {getattr(msg, 'role', 'Unknown')}"
                                        )
                                        if hasattr(msg, "content"):
                                            content_preview = (
                                                str(msg.content)[:200] + "..."
                                                if len(str(msg.content)) > 200
                                                else str(msg.content)
                                            )
                                            st.write(f"  - Content: {content_preview}")
                                        if (
                                            hasattr(msg, "tool_calls")
                                            and msg.tool_calls
                                        ):
                                            st.write(
                                                f"  - Tool calls: {len(msg.tool_calls)}"
                                            )

                                if (
                                    "response" in locals()
                                    and hasattr(response, "model")
                                    and response.model
                                ):
                                    st.write(f"- Model used: {response.model}")

                                # Show raw response attributes
                                if "response" in locals():
                                    st.write("**Available Response Attributes:**")
                                    response_attrs = [
                                        attr
                                        for attr in dir(response)
                                        if not attr.startswith("_")
                                    ]
                                    st.write(response_attrs)

                                    # Show full response object for deep debugging
                                    st.write("**Full Response Object (Advanced):**")
                                    st.code(str(response))
                                else:
                                    st.write(
                                        "- No response object available (AgnoPersonalAgent returns string)"
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
                        error_msg = "Agent returned empty response"
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

with tab2:
    # Memory Manager Tab Content
    st.markdown("### Comprehensive Memory Management")

    # Store New Facts Section
    st.markdown("---")
    st.subheader("📝 Store New Facts")
    st.markdown("*Add facts directly to memory without agent inference*")

    # Category selection
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

    # Chat input for fact storage - automatically clears after submission
    if fact_input := st.chat_input(
        "Enter a fact to store (e.g., I work at Google as a software engineer)"
    ):
        if fact_input.strip():
            # Use automatic classification if 'automatic' is selected
            topic_list = (
                None if selected_category == "automatic" else [selected_category]
            )
            success, message, memory_id = direct_add_memory(
                memory_text=fact_input.strip(),
                topics=topic_list,
                input_text="Direct fact storage",
            )

            if success:
                # More prominent success message with longer duration
                st.success("🎉 **Fact Successfully Stored!** 🎉")
                st.success("Your fact has been added to memory and is now searchable.")

                if memory_id:
                    st.info(
                        f"📂 **Category:** {selected_category} | **Memory ID:** {memory_id}"
                    )
                else:
                    st.info(f"📂 **Category:** {selected_category}")

                # Brief pause to show success message
                time.sleep(2)

                # Rerun to show the cleared input
                st.rerun()
            else:
                st.error(f"❌ Failed to store fact: {message}")

    # Search Memories Section
    st.markdown("---")
    st.subheader("🔍 Search Memories")
    st.markdown("*Search through stored memories using semantic similarity*")

    # Advanced search options
    col1, col2 = st.columns(2)
    with col1:
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Lower values return more results, higher values are more strict",
            key="memory_similarity_threshold",
        )
    with col2:
        search_limit = st.number_input(
            "Max Results",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum number of search results to return",
            key="memory_search_limit",
        )

    # Chat input for memory search - automatically clears after submission
    if search_query := st.chat_input(
        "Enter keywords to search your memories (e.g., work, hobbies, travel)"
    ):
        try:
            # Use direct semantic search (no agentic retrieval)
            search_results = direct_search_memories(
                query=search_query,
                limit=search_limit,
                similarity_threshold=similarity_threshold,
            )

            if search_results:
                st.subheader(f"🔍 Search Results for: '{search_query}'")
                st.info(
                    f"Found {len(search_results)} results with similarity ≥ {similarity_threshold}"
                )

                for i, (memory, score) in enumerate(search_results, 1):
                    memory_content = getattr(memory, "memory", "No content")
                    score_color = (
                        "🟢" if score >= 0.7 else "🟡" if score >= 0.5 else "🔴"
                    )

                    with st.expander(
                        f"{score_color} Result {i} (Score: {score:.3f}): {memory_content[:50]}..."
                    ):
                        st.write(f"**Memory:** {memory_content}")
                        st.write(f"**Similarity Score:** {score:.3f}")

                        topics = getattr(memory, "topics", [])
                        if topics:
                            st.write(f"**Topics:** {', '.join(topics)}")

                        st.write(
                            f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                        )
                        st.write(
                            f"**Memory ID:** {getattr(memory, 'memory_id', 'N/A')}"
                        )

                        # Add delete button for each memory
                        if st.button(
                            f"🗑️ Delete Memory", key=f"delete_search_{memory.memory_id}"
                        ):
                            success, message = direct_delete_memory(memory.memory_id)
                            if success:
                                st.success(f"Memory deleted: {message}")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete memory: {message}")
            else:
                st.info(
                    "No matching memories found. Try different keywords or lower the similarity threshold."
                )

        except Exception as e:
            st.error(f"Error searching memories: {str(e)}")

    # Browse All Memories Section
    st.markdown("---")
    st.subheader("📚 Browse All Memories")
    st.markdown("*View, edit, and manage all stored memories*")

    if st.button("📋 Load All Memories", key="load_all_memories_btn"):
        try:
            memories = direct_get_all_memories()
            if memories:
                st.info(f"Found {len(memories)} total memories")
                for i, memory in enumerate(memories, 1):
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

                        # Add delete button for each memory
                        if st.button(
                            f"🗑️ Delete", key=f"delete_browse_{memory.memory_id}"
                        ):
                            success, message = direct_delete_memory(memory.memory_id)
                            if success:
                                st.success(f"Memory deleted: {message}")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete memory: {message}")
            else:
                st.info("No memories stored yet. Start chatting or store some facts!")
        except Exception as e:
            st.error(f"Error retrieving memories: {str(e)}")

    # Memory Statistics Section
    st.markdown("---")
    st.subheader("📊 Memory Statistics")
    st.markdown("*Analytics and insights about your stored memories*")

    if st.button("📈 Show Statistics", key="show_stats_btn"):
        try:
            stats = direct_get_memory_stats()

            if "error" not in stats:
                # Display basic stats
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

                # Topic distribution
                topic_dist = stats.get("topic_distribution", {})
                if topic_dist:
                    st.subheader("📈 Topic Distribution")
                    for topic, count in sorted(
                        topic_dist.items(), key=lambda x: x[1], reverse=True
                    ):
                        st.write(f"**{topic.title()}:** {count} memories")

                # Most common topic
                most_common = stats.get("most_common_topic", "None")
                if most_common and most_common != "None":
                    st.info(f"🏆 Most common topic: **{most_common}**")
            else:
                st.error(f"Error getting statistics: {stats['error']}")
        except Exception as e:
            st.error(f"Error getting memory statistics: {str(e)}")

    # Memory Settings Section
    st.markdown("---")
    st.subheader("⚙️ Memory Settings")
    st.markdown("*Configure and manage memory system settings*")

    # Memory reset with confirmation
    if st.button("🗑️ Reset All Memories", key="reset_memories_btn"):
        st.session_state.show_memory_confirmation = True

    # Confirmation dialog
    if st.session_state.show_memory_confirmation:
        st.markdown("### ⚠️ Confirm Memory Deletion")
        st.error(
            "**WARNING**: This will permanently delete ALL stored memories and "
            "personal information. This action CANNOT be undone!"
        )
        st.info(
            "💡 **Remember**: Your AI friend's memories help create better, "
            "more personalized conversations over time."
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Cancel", use_container_width=True, key="cancel_reset"):
                st.session_state.show_memory_confirmation = False
                st.rerun()

        with col2:
            if st.button(
                "🗑️ Yes, Delete All",
                type="primary",
                use_container_width=True,
                key="confirm_reset",
            ):
                try:
                    success, message = direct_clear_memories()
                    st.session_state.show_memory_confirmation = False

                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")

                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing memories: {str(e)}")

    # Memory system configuration display
    try:
        if "agent" in st.session_state and hasattr(
            st.session_state.agent, "agno_memory"
        ):
            memory_manager = st.session_state.agent.agno_memory.memory_manager
            if hasattr(memory_manager, "config"):
                config = memory_manager.config
                st.subheader("🔧 Current Configuration")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Similarity Threshold:** {config.similarity_threshold}")
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
                    st.write(f"**Debug Mode:** {'✅' if config.debug_mode else '❌'}")
    except Exception as e:
        st.warning(f"Could not load memory configuration: {str(e)}")

with tab3:
    # Knowledge Base Tab Content
    st.markdown("### Knowledge Base Search & Management")

    # Search Knowledge Section
    st.markdown("---")
    st.subheader("🔍 Search Knowledge Base")
    st.markdown("*Search through stored knowledge using semantic similarity*")

    # Advanced search options for knowledge
    col1, col2 = st.columns(2)
    with col1:
        knowledge_search_limit = st.number_input(
            "Max Results",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum number of search results to return",
            key="knowledge_search_limit",
        )
    with col2:
        st.write("")  # Empty space for alignment

    # Chat input for knowledge search - automatically clears after submission
    if knowledge_search_query := st.chat_input(
        "Enter keywords to search the knowledge base (e.g., programming, science, history)"
    ):
        try:
            # Use direct RAG search
            search_results = direct_search_rag(query=knowledge_search_query)

            if search_results:
                st.subheader(
                    f"🔍 RAG Knowledge Search Results for: '{knowledge_search_query}'"
                )
                # Display the markdown results directly
                st.markdown(search_results)
            else:
                st.info("No matching knowledge found. Try different keywords.")

        except Exception as e:
            st.error(f"Error searching knowledge base: {str(e)}")

    # Knowledge Base Information
    st.markdown("---")
    st.subheader("📚 Knowledge Base Information")
    st.markdown("*Information about the knowledge base system*")

    knowledge_manager = get_knowledge_manager()
    if knowledge_manager:
        st.info("✅ Knowledge base is available and ready for searching")

        # Show knowledge base type and basic info
        kb_type = type(knowledge_manager).__name__
        st.write(f"**Knowledge Base Type:** {kb_type}")

        # Check if knowledge base exists
        if hasattr(knowledge_manager, "exists") and knowledge_manager.exists():
            st.success("📚 Knowledge base contains data and is ready for queries")
        else:
            st.warning("📭 Knowledge base appears to be empty or not loaded")
            st.info(
                "💡 **Tip:** Load some documents into your knowledge base to enable searching"
            )
    else:
        st.warning("⚠️ Knowledge base is not available")
        st.info(
            "💡 **Note:** Knowledge base functionality requires proper initialization"
        )


# Sidebar with agent info and controls
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

    # User ID section - prominently displayed
    st.header("👤 Current User")
    st.write(f"**🆔 {USER_ID}**")

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
            help="Choose an Ollama model to use for the agent",
        )

        # Button to apply model selection
        if st.button("🚀 Apply Model Selection"):
            if (
                selected_model != st.session_state.current_model
                or new_ollama_url != st.session_state.current_ollama_url
            ):
                with st.spinner("Reinitializing agent with new model..."):
                    try:
                        # Update session state
                        st.session_state.current_model = selected_model
                        st.session_state.current_ollama_url = new_ollama_url

                        # Reinitialize agent with existing agent to preserve memory
                        st.session_state.agent = initialize_agent(
                            selected_model, new_ollama_url, st.session_state.agent
                        )

                        # Clear chat history for new model
                        st.session_state.messages = []

                        st.success(f"Agent updated to use model: {selected_model}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to initialize agent: {str(e)}")
            else:
                st.info("Model and URL are already current")
    else:
        st.info("Click 'Fetch Available Models' to see available models")

    st.header("Agent Information")
    st.write(f"**Current Model:** {st.session_state.current_model}")
    st.write(f"**Current Ollama URL:** {st.session_state.current_ollama_url}")

    # Show remote mode indicator
    if hasattr(args, "remote") and args.remote:
        st.success("🌐 **Remote Mode:** Using remote Ollama server")
    else:
        st.info("🏠 **Local Mode:** Using local Ollama server")

    st.header("Controls")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

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

            # Performance chart
            if len(st.session_state.debug_metrics) > 1:
                st.subheader("📈 Response Time Trend")
                try:
                    import pandas as pd

                    df = pd.DataFrame(st.session_state.debug_metrics)
                    df = df[df["success"]]  # Only successful requests

                    if not df.empty and len(df) > 1:
                        # Create a simple line chart of response times
                        chart_data = df[["timestamp", "response_time"]].copy()
                        chart_data = chart_data.set_index("timestamp")

                        # Use altair for better chart control and avoid deprecation warnings
                        try:
                            import altair as alt

                            # Create altair chart with proper theme handling
                            chart = (
                                alt.Chart(chart_data.reset_index())
                                .mark_line(point=True)
                                .encode(
                                    x=alt.X("timestamp:O", title="Time"),
                                    y=alt.Y(
                                        "response_time:Q", title="Response Time (s)"
                                    ),
                                    tooltip=["timestamp:O", "response_time:Q"],
                                )
                                .properties(
                                    width=400, height=200, title="Response Time Trend"
                                )
                            )

                            st.altair_chart(chart, use_container_width=True)
                        except ImportError:
                            # Fallback to streamlit line chart if altair not available
                            st.line_chart(chart_data["response_time"])
                    else:
                        st.info(
                            "Need at least 2 successful requests to show trend chart"
                        )
                except Exception as e:
                    st.warning(
                        f"Chart rendering issue (this doesn't affect functionality): {str(e)}"
                    )
                    # Fallback: show data in table format
                    if st.session_state.debug_metrics:
                        recent_times = [
                            entry["response_time"]
                            for entry in st.session_state.debug_metrics[-5:]
                            if entry["success"]
                        ]
                        if recent_times:
                            st.write(
                                f"Recent response times: {', '.join([f'{t:.3f}s' for t in recent_times])}"
                            )
        else:
            st.info("No requests made yet. Start chatting to see performance stats!")

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

                    # Show tool call details if available
                    if (
                        entry.get("tool_call_details")
                        and len(entry["tool_call_details"]) > 0
                    ):
                        st.write("**🛠️ Tools Used:**")
                        for j, tool_call in enumerate(entry["tool_call_details"], 1):
                            if isinstance(tool_call, dict):
                                function_name = tool_call.get(
                                    "function_name", "unknown"
                                )
                                args = tool_call.get("function_args", {})
                                if isinstance(args, dict) and args:
                                    formatted_args = ", ".join(
                                        [f"{k}={v}" for k, v in args.items()]
                                    )
                                    st.write(
                                        f"  {j}. {function_name}({formatted_args})"
                                    )
                                else:
                                    st.write(f"  {j}. {function_name}()")
                            elif hasattr(tool_call, "function") and hasattr(
                                tool_call.function, "name"
                            ):
                                st.write(f"  {j}. {tool_call.function.name}")
                            elif hasattr(tool_call, "name"):
                                st.write(f"  {j}. {tool_call.name}")
                            else:
                                st.write(f"  {j}. {str(tool_call)[:50]}...")

                    if not entry["success"] and "error" in entry:
                        st.error(f"**Error:** {entry['error']}")
        else:
            st.info("No debug metrics available yet.")

        # Session Information
        st.subheader("🔧 Session Information")
        st.write("**Session State Keys:**")
        st.write(list(st.session_state.keys()))

        if st.session_state.messages:
            st.write("**Message Count:**", len(st.session_state.messages))

        # Show agent configuration
        if "agent" in st.session_state:
            st.write("**Agent Configuration:**")
            agent = st.session_state.agent

            # For AgnoPersonalAgent, use the built-in get_agent_info method
            if isinstance(agent, AgnoPersonalAgent):
                try:
                    agent_info = agent.get_agent_info()

                    # Display basic configuration
                    st.write(f"- Model: {agent_info['model_name']}")
                    st.write(f"- Provider: {agent_info['model_provider']}")
                    st.write(f"- Memory enabled: {agent_info['memory_enabled']}")
                    st.write(f"- Knowledge enabled: {agent_info['knowledge_enabled']}")
                    st.write(f"- MCP enabled: {agent_info['mcp_enabled']}")
                    st.write(f"- Debug mode: {agent_info['debug_mode']}")
                    st.write(f"- Initialized: {agent_info['initialized']}")

                    # Display tool counts
                    tool_counts = agent_info["tool_counts"]
                    st.write(
                        f"- Total tools: {tool_counts['total']} ({tool_counts['built_in']} built-in + {tool_counts['mcp']} MCP)"
                    )

                    # Display actual tool names
                    built_in_tools = [
                        tool["name"] for tool in agent_info["built_in_tools"]
                    ]
                    mcp_tools = [tool["name"] for tool in agent_info["mcp_tools"]]

                    if built_in_tools:
                        st.write(f"- Built-in tools: {built_in_tools}")
                    if mcp_tools:
                        st.write(f"- MCP tools: {mcp_tools}")

                except Exception as e:
                    st.write(f"- Error getting agent info: {str(e)}")
                    # Fallback to basic info
                    st.write(f"- Model: {agent.model_name}")
                    st.write(f"- Provider: {agent.model_provider}")
                    st.write(f"- Memory enabled: {agent.enable_memory}")
                    st.write(f"- MCP enabled: {agent.enable_mcp}")
                    st.write(f"- Debug mode: {agent.debug}")
            else:
                # Fallback for other agent types
                st.write(
                    f"- Tools: {[tool.__class__.__name__ for tool in agent.tools] if hasattr(agent, 'tools') and agent.tools else 'None'}"
                )
                st.write(
                    f"- Show tool calls: {getattr(agent, 'show_tool_calls', 'Not set')}"
                )
                st.write(
                    f"- Tool call limit: {getattr(agent, 'tool_call_limit', 'Not set')}"
                )
                st.write(f"- Debug mode: {getattr(agent, 'debug_mode', 'Not set')}")

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

# Instructions for running
if __name__ == "__main__":
    pass
