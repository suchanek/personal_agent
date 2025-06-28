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

sys.path.insert(0, str(Path(__file__).parent.parent))
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
from tools.streamlit_helpers import StreamlitMemoryHelper, StreamlitKnowledgeHelper

# Constants for session state keys
SESSION_KEY_MESSAGES = "messages"
SESSION_KEY_AGENT = "agent"
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

# Optional imports
try:
    import pandas as pd
    import altair as alt
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

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

    if SESSION_KEY_AGENT not in st.session_state:
        st.session_state[SESSION_KEY_AGENT] = initialize_agent(
            st.session_state[SESSION_KEY_CURRENT_MODEL], st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]
        )

    if SESSION_KEY_MEMORY_HELPER not in st.session_state:
        st.session_state[SESSION_KEY_MEMORY_HELPER] = StreamlitMemoryHelper(st.session_state[SESSION_KEY_AGENT])

    if SESSION_KEY_KNOWLEDGE_HELPER not in st.session_state:
        st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = StreamlitKnowledgeHelper(st.session_state[SESSION_KEY_AGENT])

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


def render_chat_tab():
    st.markdown("### Have a conversation with your AI friend")

    for message in st.session_state[SESSION_KEY_MESSAGES]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to talk about?"):
        st.session_state[SESSION_KEY_MESSAGES].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                start_time = time.time()
                start_timestamp = datetime.now()

                try:
                    agent = st.session_state[SESSION_KEY_AGENT]
                    if isinstance(agent, AgnoPersonalAgent):
                        response_content = asyncio.run(agent.run(prompt))
                    else:
                        response = agent.run(prompt)
                        response_content = response.content if hasattr(response, "content") else str(response)

                    end_time = time.time()
                    response_time = end_time - start_time

                    # Calculate token estimates
                    input_tokens = len(prompt.split()) * 1.3
                    output_tokens = len(response_content.split()) * 1.3 if response_content else 0
                    total_tokens = input_tokens + output_tokens

                    # Get tool call info
                    tool_call_info = agent.get_last_tool_calls()
                    tool_calls_made = tool_call_info.get("tool_calls_count", 0)
                    tool_call_details = tool_call_info.get("tool_call_details", [])

                    # Update performance stats
                    stats = st.session_state[SESSION_KEY_PERFORMANCE_STATS]
                    stats["total_requests"] += 1
                    stats["total_response_time"] += response_time
                    stats["average_response_time"] = stats["total_response_time"] / stats["total_requests"]
                    stats["total_tokens"] += total_tokens
                    stats["average_tokens"] = stats["total_tokens"] / stats["total_requests"]
                    stats["fastest_response"] = min(stats["fastest_response"], response_time)
                    stats["slowest_response"] = max(stats["slowest_response"], response_time)
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
                        "response_type": "AgnoPersonalAgent" if isinstance(agent, AgnoPersonalAgent) else "Unknown",
                        "success": True,
                    }
                    st.session_state[SESSION_KEY_DEBUG_METRICS].append(debug_entry)
                    if len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 10:
                        st.session_state[SESSION_KEY_DEBUG_METRICS].pop(0)

                    # Display debug info if enabled
                    if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
                        with st.expander("🔍 **Detailed Debug Info**", expanded=False):
                            # ... (Detailed debug UI from original file)
                            pass

                    st.markdown(response_content)
                    st.session_state[SESSION_KEY_MESSAGES].append({"role": "assistant", "content": response_content})

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state[SESSION_KEY_MESSAGES].append({"role": "assistant", "content": error_msg})

                    # Log failed request
                    debug_entry = {
                        "timestamp": start_timestamp.strftime("%H:%M:%S"),
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "response_time": round(response_time, 3),
                        "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "tool_calls": 0,
                        "response_type": "Error", "success": False, "error": str(e),
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


def render_memory_tab():
    st.markdown("### Comprehensive Memory Management")
    memory_helper = st.session_state[SESSION_KEY_MEMORY_HELPER]

    # Store New Facts Section
    st.markdown("---")
    st.subheader("📝 Store New Facts")
    st.markdown("*Add facts directly to memory without agent inference*")
    categories = ["automatic", "personal", "work", "education", "hobbies", "preferences", "goals", "health", "family", "travel", "technology", "other"]
    selected_category = st.selectbox("Category:", categories, key="fact_category")
    if fact_input := st.chat_input("Enter a fact to store (e.g., I work at Google as a software engineer)"):
        if fact_input.strip():
            topic_list = None if selected_category == "automatic" else [selected_category]
            success, message, memory_id = memory_helper.add_memory(
                memory_text=fact_input.strip(), topics=topic_list, input_text="Direct fact storage"
            )
            if success:
                st.success("🎉 **Fact Successfully Stored!** 🎉")
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"❌ Failed to store fact: {message}")

    # Search Memories Section
    st.markdown("---")
    st.subheader("🔍 Search Memories")
    st.markdown("*Search through stored memories using semantic similarity*")
    col1, col2 = st.columns(2)
    with col1:
        similarity_threshold = st.slider("Similarity Threshold", 0.1, 1.0, 0.3, 0.1, key="memory_similarity_threshold")
    with col2:
        search_limit = st.number_input("Max Results", 1, 50, 10, key="memory_search_limit")
    if search_query := st.chat_input("Enter keywords to search your memories"):
        search_results = memory_helper.search_memories(query=search_query, limit=search_limit, similarity_threshold=similarity_threshold)
        if search_results:
            st.subheader(f"🔍 Search Results for: '{search_query}'")
            for i, (memory, score) in enumerate(search_results, 1):
                with st.expander(f"Result {i} (Score: {score:.3f}): {memory.memory[:50]}..."):
                    st.write(f"**Memory:** {memory.memory}")
                    st.write(f"**Similarity Score:** {score:.3f}")
                    topics = getattr(memory, "topics", [])
                    if topics:
                        st.write(f"**Topics:** {', '.join(topics)}")
                    st.write(f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}")
                    st.write(f"**Memory ID:** {getattr(memory, 'memory_id', 'N/A')}")
                    if st.button(f"🗑️ Delete Memory", key=f"delete_search_{memory.memory_id}"):
                        success, message = memory_helper.delete_memory(memory.memory_id)
                        if success:
                            st.success(f"Memory deleted: {message}")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete memory: {message}")
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
                    st.write(f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}")
                    st.write(f"**Input:** {getattr(memory, 'input', 'N/A')}")
                    topics = getattr(memory, "topics", [])
                    if topics:
                        st.write(f"**Topics:** {', '.join(topics)}")
                    if st.button(f"🗑️ Delete", key=f"delete_browse_{memory.memory_id}"):
                        success, message = memory_helper.delete_memory(memory.memory_id)
                        if success:
                            st.success(f"Memory deleted: {message}")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete memory: {message}")
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
                st.metric("Avg Length", f"{avg_length:.1f} chars" if avg_length else "N/A")
            topic_dist = stats.get("topic_distribution", {})
            if topic_dist:
                st.subheader("📈 Topic Distribution")
                for topic, count in sorted(topic_dist.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"**{topic.title()}:** {count} memories")
        else:
            st.error(f"Error getting statistics: {stats['error']}")

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


def render_knowledge_tab():
    st.markdown("### Knowledge Base Search & Management")
    knowledge_helper = st.session_state[SESSION_KEY_KNOWLEDGE_HELPER]

    # SQLite/LanceDB Knowledge Search Section
    st.markdown("---")
    st.subheader("🔍 SQLite/LanceDB Knowledge Search")
    st.markdown("*Search through stored knowledge using the original sqlite and lancedb knowledge sources*")
    knowledge_search_limit = st.number_input("Max Results", 1, 50, 10, key="knowledge_search_limit")
    if knowledge_search_query := st.chat_input("Enter keywords to search the SQLite/LanceDB knowledge base"):
        search_results = knowledge_helper.search_knowledge(query=knowledge_search_query, limit=knowledge_search_limit)
        if search_results:
            st.subheader(f"🔍 SQLite/LanceDB Knowledge Search Results for: '{knowledge_search_query}'")
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

                with st.expander(f"📚 Result {i}: {title if title != 'Untitled' else content[:50]}..."):
                    st.write(f"**Title:** {title}")
                    st.write(f"**Content:** {content}")
                    st.write(f"**Source:** {source}")
                    st.write(f"**Knowledge ID:** {knowledge_id}")
        else:
            st.info("No matching knowledge found.")

    # RAG Knowledge Search Section
    st.markdown("---")
    st.subheader("🤖 RAG Knowledge Search")
    st.markdown("*Search through knowledge using direct RAG query*")
    if rag_search_query := st.chat_input("Enter keywords to search the RAG knowledge base"):
        search_results = knowledge_helper.search_rag(query=rag_search_query)
        if search_results:
            st.subheader(f"🤖 RAG Knowledge Search Results for: '{rag_search_query}'")
            st.markdown(search_results)
        else:
            st.info("No matching knowledge found.")

    # Knowledge Base Information
    st.markdown("---")
    st.subheader("📚 Knowledge Base Information")
    st.markdown("*Information about both knowledge base systems*")
    st.markdown("#### SQLite/LanceDB Knowledge Base")
    if knowledge_helper.knowledge_manager:
        st.info("✅ SQLite/LanceDB knowledge base is available and ready for searching")
    else:
        st.warning("⚠️ SQLite/LanceDB knowledge base is not available")
    st.markdown("#### RAG Knowledge Base")
    agent = st.session_state[SESSION_KEY_AGENT]
    if hasattr(agent, "lightrag_knowledge"):
        st.info("✅ RAG knowledge base is available and ready for searching")
    else:
        st.warning("⚠️ RAG knowledge base is not available")


def render_sidebar():
    with st.sidebar:
        st.header("🎨 Theme")
        is_dark = st.session_state.get(SESSION_KEY_DARK_THEME, False)
        theme_icon = "🌙" if is_dark else "☀️"
        theme_text = "Dark" if is_dark else "Light"
        if st.button(f"{theme_icon} {theme_text} Mode", key="sidebar_theme_toggle"):
            st.session_state[SESSION_KEY_DARK_THEME] = not st.session_state[SESSION_KEY_DARK_THEME]
            st.rerun()

        st.header("👤 Current User")
        st.write(f"**🆔 {USER_ID}**")

        st.header("Model Selection")
        new_ollama_url = st.text_input("Ollama URL:", value=st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL])
        if st.button("🔄 Fetch Available Models"):
            with st.spinner("Fetching models..."):
                available_models = get_ollama_models(new_ollama_url)
                if available_models:
                    st.session_state[SESSION_KEY_AVAILABLE_MODELS] = available_models
                    st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = new_ollama_url
                    st.success(f"Found {len(available_models)} models!")
                else:
                    st.error("No models found or connection failed")

        if SESSION_KEY_AVAILABLE_MODELS in st.session_state and st.session_state[SESSION_KEY_AVAILABLE_MODELS]:
            current_model_index = 0
            if st.session_state[SESSION_KEY_CURRENT_MODEL] in st.session_state[SESSION_KEY_AVAILABLE_MODELS]:
                current_model_index = st.session_state[SESSION_KEY_AVAILABLE_MODELS].index(st.session_state[SESSION_KEY_CURRENT_MODEL])
            selected_model = st.selectbox("Select Model:", st.session_state[SESSION_KEY_AVAILABLE_MODELS], index=current_model_index)
            if st.button("🚀 Apply Model Selection"):
                if selected_model != st.session_state[SESSION_KEY_CURRENT_MODEL] or new_ollama_url != st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]:
                    with st.spinner("Reinitializing agent..."):
                        st.session_state[SESSION_KEY_CURRENT_MODEL] = selected_model
                        st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = new_ollama_url
                        st.session_state[SESSION_KEY_AGENT] = initialize_agent(selected_model, new_ollama_url, st.session_state[SESSION_KEY_AGENT])
                        st.session_state[SESSION_KEY_MESSAGES] = []
                        st.success(f"Agent updated to use model: {selected_model}")
                        st.rerun()
                else:
                    st.info("Model and URL are already current")
        else:
            st.info("Click 'Fetch Available Models' to see available models")

        st.header("Agent Information")
        st.write(f"**Current Model:** {st.session_state[SESSION_KEY_CURRENT_MODEL]}")
        st.write(f"**Current Ollama URL:** {st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]}")
        if hasattr(args, "remote") and args.remote:
            st.success("🌐 **Remote Mode:** Using remote Ollama server")
        else:
            st.info("🏠 **Local Mode:** Using local Ollama server")

        st.header("Controls")
        if st.button("Clear Chat History"):
            st.session_state[SESSION_KEY_MESSAGES] = []
            st.rerun()

        st.header("Debug Info")
        st.session_state[SESSION_KEY_SHOW_DEBUG] = st.checkbox("Enable Debug Mode", value=st.session_state.get(SESSION_KEY_SHOW_DEBUG, False))
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG):
            st.subheader("📊 Performance Statistics")
            stats = st.session_state[SESSION_KEY_PERFORMANCE_STATS]
            if stats["total_requests"] > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Requests", stats["total_requests"])
                    st.metric("Avg Response Time", f"{stats['average_response_time']:.3f}s")
                    st.metric("Fastest Response", f"{stats['fastest_response']:.3f}s" if stats["fastest_response"] != float("inf") else "N/A")
                with col2:
                    st.metric("Total Tool Calls", stats["tool_calls_count"])
                    st.metric("Avg Tokens/Request", f"{stats['average_tokens']:.0f}")
                    st.metric("Slowest Response", f"{stats['slowest_response']:.3f}s")
            else:
                st.info("No requests made yet.")

            if PANDAS_AVAILABLE and len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 1:
                st.subheader("📈 Response Time Trend")
                df = pd.DataFrame(st.session_state[SESSION_KEY_DEBUG_METRICS])
                df = df[df["success"]]
                if not df.empty and len(df) > 1:
                    chart_data = df[["timestamp", "response_time"]].copy().set_index("timestamp")
                    chart = alt.Chart(chart_data.reset_index()).mark_line(point=True).encode(
                        x=alt.X("timestamp:O", title="Time"),
                        y=alt.Y("response_time:Q", title="Response Time (s)"),
                        tooltip=["timestamp:O", "response_time:Q"]
                    ).properties(title="Response Time Trend")
                    st.altair_chart(chart, use_container_width=True)

            st.subheader("🔍 Recent Request Details")
            if st.session_state[SESSION_KEY_DEBUG_METRICS]:
                for entry in reversed(st.session_state[SESSION_KEY_DEBUG_METRICS][-5:]):
                    with st.expander(f"{'✅' if entry['success'] else '❌'} {entry['timestamp']} - {entry['response_time']}s"):
                        st.write(f"**Prompt:** {entry['prompt']}")
                        # ... (display other debug details)
            else:
                st.info("No debug metrics available yet.")


def main():
    """Main function to run the Streamlit app."""
    initialize_session_state()
    apply_custom_theme()

    # Streamlit UI
    is_dark = st.session_state.get(SESSION_KEY_DARK_THEME, False)
    theme_icon = "🌙" if is_dark else "☀️"
    theme_text = "Dark" if is_dark else "Light"

    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🤖 Personal AI Friend with Memory")
        st.markdown("*A friendly AI agent that remembers your conversations and learns about you*")
    with col2:
        if st.button(f"{theme_icon} {theme_text} Mode", key="theme_toggle"):
            st.session_state[SESSION_KEY_DARK_THEME] = not st.session_state[SESSION_KEY_DARK_THEME]
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["💬 Chat", "🧠 Memory Manager", "📚 Knowledge Base"])

    with tab1:
        render_chat_tab()

    with tab2:
        render_memory_tab()

    with tab3:
        render_knowledge_tab()

    render_sidebar()


if __name__ == "__main__":
    main()
