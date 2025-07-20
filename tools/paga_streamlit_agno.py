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
    LIGHTRAG_URL,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent, create_agno_agent
from tools.streamlit_helpers import StreamlitKnowledgeHelper, StreamlitMemoryHelper

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
SESSION_KEY_RAG_SERVER_LOCATION = "rag_server_location"

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
    parser = argparse.ArgumentParser(description="Personal Agent Streamlit App")
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama URL instead of local"
    )
    parser.add_argument(
        "--recreate", action="store_true", help="Recreate the knowledge base and clear all memories"
    )
    return parser.parse_known_args()  # Use parse_known_args to ignore Streamlit's args


# Parse arguments and determine Ollama URL and recreate flag
args, unknown = parse_args()
EFFECTIVE_OLLAMA_URL = REMOTE_OLLAMA_URL if args.remote else OLLAMA_URL
RECREATE_FLAG = args.recreate

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
    if existing_agent and isinstance(existing_agent, AgnoPersonalAgent):
        # Update existing agent's configuration
        existing_agent.model_name = model_name
        existing_agent.ollama_base_url = ollama_url
        # Reinitialize with new settings
        await existing_agent.initialize()
        return existing_agent
    else:
        # Create new AgnoPersonalAgent using the factory
        return await create_agno_agent(
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


def render_chat_tab():
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
            with st.spinner("Thinking..."):
                start_time = time.time()
                start_timestamp = datetime.now()

                try:
                    agent = st.session_state[SESSION_KEY_AGENT]
                    if isinstance(agent, AgnoPersonalAgent):
                        response_content = asyncio.run(agent.run(prompt))
                    else:
                        response = agent.run(prompt)
                        response_content = (
                            response.content
                            if hasattr(response, "content")
                            else str(response)
                        )

                    end_time = time.time()
                    response_time = end_time - start_time

                    # Calculate token estimates
                    input_tokens = len(prompt.split()) * 1.3
                    output_tokens = (
                        len(response_content.split()) * 1.3 if response_content else 0
                    )
                    total_tokens = input_tokens + output_tokens

                    # Get tool call info from the last response object
                    last_response = agent._last_response
                    tool_calls = (
                        last_response.tool_calls
                        if last_response and hasattr(last_response, "tool_calls")
                        else []
                    )

                    tool_calls_made = len(tool_calls)
                    tool_call_details = []
                    if tool_calls:
                        for tool_call in tool_calls:
                            tool_call_details.append(
                                {
                                    "function_name": getattr(
                                        tool_call.function, "name", "Unknown"
                                    ),
                                    "function_args": getattr(
                                        tool_call.function, "arguments", {}
                                    ),
                                    "reasoning": getattr(tool_call, "reasoning", None),
                                }
                            )

                    response_metadata = (
                        getattr(last_response, "metadata", {}) if last_response else {}
                    )
                    response_type = "AgnoResponse"

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
                        "response_type": (
                            "AgnoPersonalAgent"
                            if isinstance(agent, AgnoPersonalAgent)
                            else "Unknown"
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

                    st.markdown(response_content)

                    # Store message with metadata for future reference
                    message_data = {
                        "role": "assistant",
                        "content": response_content,
                        "metadata": (
                            response_metadata
                            if response_type == "StructuredResponse"
                            else None
                        ),
                        "response_type": response_type,
                        "tool_calls": tool_calls_made,
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
    if fact_input := st.chat_input(
        "Enter a fact to store (e.g., I work at Google as a software engineer)"
    ):
        if fact_input.strip():
            topic_list = (
                None if selected_category == "automatic" else [selected_category]
            )
            success, message, memory_id, _ = memory_helper.add_memory(
                memory_text=fact_input.strip(),
                topics=topic_list,
                input_text="Direct fact storage",
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
    if search_query := st.chat_input("Enter keywords to search your memories"):
        search_results = memory_helper.search_memories(
            query=search_query,
            limit=search_limit,
            similarity_threshold=similarity_threshold,
        )
        if search_results:
            st.subheader(f"🔍 Search Results for: '{search_query}'")
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
                    if st.button(
                        f"🗑️ Delete Memory", key=f"delete_search_{memory.memory_id}"
                    ):
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
                    st.write(
                        f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                    )
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
    st.markdown("*Monitor synchronization between local SQLite and LightRAG graph memories*")
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
                st.success("✅ Memories are synchronized between local and graph systems")
            elif status == "out_of_sync":
                st.warning("⚠️ Memories may be out of sync between systems")
                if st.button("🔄 Sync Missing Memories", key="sync_missing_btn"):
                    # Sync any missing memories to graph
                    local_memories = memory_helper.get_all_memories()
                    synced_count = 0
                    for memory in local_memories:
                        try:
                            success, result = memory_helper.sync_memory_to_graph(
                                memory.memory, getattr(memory, 'topics', None)
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
            st.error(f"Error checking sync status: {sync_status.get('error', 'Unknown error')}")

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
            st.caption(f"**Path:** {AGNO_KNOWLEDGE_DIR}")

            if knowledge_helper.knowledge_manager:
                st.success("✅ Ready")
            else:
                st.warning("⚠️ Offline")
        with col2:
            st.markdown("**RAG**")

            # RAG Server Location Dropdown
            rag_location = st.selectbox(
                "RAG Server:",
                ["localhost", "tesla.local"],
                index=0 if st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] == "localhost" else 1,
                key="rag_server_dropdown"
            )

            # Check if location changed and show apply button
            location_changed = rag_location != st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]
            
            if location_changed:
                if st.button("🔄 Apply & Rescan", key="apply_rag_server", type="primary"):
                    # Update session state
                    st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] = rag_location
                    
                    # Determine the new RAG URL
                    if rag_location == "localhost":
                        new_rag_url = "http://localhost:9621"
                    else:  # tesla.local
                        new_rag_url = "http://tesla.local:9621"
                    
                    # Trigger rescan on the new server
                    with st.spinner(f"Switching to {rag_location} and triggering rescan..."):
                        try:
                            rescan_response = requests.post(f"{new_rag_url}/documents/scan", timeout=10)
                            if rescan_response.status_code == 200:
                                st.success(f"✅ Switched to {rag_location} and rescan initiated!")
                            else:
                                st.warning(f"⚠️ Switched to {rag_location} but rescan failed (status: {rescan_response.status_code})")
                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Failed to connect to {rag_location}: {str(e)}")
                    
                    # Force a rerun to update the status display
                    st.rerun()
            
            # Determine the RAG URL based on current session state
            if st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] == "localhost":
                rag_url = "http://localhost:9621"
            else:  # tesla.local
                rag_url = "http://tesla.local:9621"
            
            # Check RAG server status with detailed pipeline information
            try:
                # First check basic health
                health_response = requests.get(f"{rag_url}/health", timeout=3)
                if health_response.status_code == 200:
                    # Get pipeline status for more detailed information
                    try:
                        pipeline_response = requests.get(f"{rag_url}/documents/pipeline_status", timeout=3)
                        if pipeline_response.status_code == 200:
                            pipeline_data = pipeline_response.json()
                            
                            # Check if pipeline is processing
                            if pipeline_data.get("is_processing", False):
                                st.warning("🔄 Processing")
                                if pipeline_data.get("current_task"):
                                    st.caption(f"Task: {pipeline_data['current_task']}")
                            elif pipeline_data.get("queue_size", 0) > 0:
                                st.info(f"📋 Queued ({pipeline_data['queue_size']} items)")
                            else:
                                st.success("✅ Ready")
                                
                            # Show additional pipeline info if available
                            if pipeline_data.get("last_processed"):
                                st.caption(f"Last: {pipeline_data['last_processed']}")
                        else:
                            # Fallback to basic ready status if pipeline endpoint fails
                            st.success("✅ Ready")
                    except requests.exceptions.RequestException:
                        # Pipeline status failed, but health passed
                        st.success("✅ Ready")
                else:
                    st.error(f"❌ Error ({health_response.status_code})")
            except requests.exceptions.RequestException as e:
                st.warning("⚠️ Offline")
                st.caption(f"({st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]})" )
            
            # Show current server info
            if not location_changed:
                st.caption(f"Current: {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}")


def render_knowledge_tab():
    st.markdown("### Knowledge Base Search & Management")
    knowledge_helper = st.session_state[SESSION_KEY_KNOWLEDGE_HELPER]
    render_knowledge_status(knowledge_helper)

    # SQLite/LanceDB Knowledge Search Section
    st.markdown("---")
    st.subheader("🔍 SQLite/LanceDB Knowledge Search")
    st.markdown(
        "*Search through stored knowledge using the original sqlite and lancedb knowledge sources*"
    )
    knowledge_search_limit = st.number_input(
        "Max Results", 1, 50, 10, key="knowledge_search_limit"
    )
    if knowledge_search_query := st.chat_input(
        "Enter keywords to search the SQLite/LanceDB knowledge base"
    ):
        search_results = knowledge_helper.search_knowledge(
            query=knowledge_search_query, limit=knowledge_search_limit
        )
        if search_results:
            st.subheader(
                f"🔍 SQLite/LanceDB Knowledge Search Results for: '{knowledge_search_query}'"
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
    st.markdown("*Search through knowledge using direct RAG query with advanced options*")

    # Create a dictionary to hold the query parameters
    query_params = {}

    # Query mode
    query_params['mode'] = st.selectbox(
        "Select RAG Search Type:",
        ("naive", "hybrid", "local", "global", "mix", "bypass"),
        key="rag_search_type",
    )

    # Response type
    query_params['response_type'] = st.text_input(
        "Response Format:",
        "Multiple Paragraphs",
        key="rag_response_type",
        help="Examples: 'Single Paragraph', 'Bullet Points', 'JSON'"
    )

    # Top K
    query_params['top_k'] = st.slider(
        "Top K:",
        min_value=1,
        max_value=100,
        value=10,
        key="rag_top_k",
        help="Number of items to retrieve"
    )

    # Other boolean flags
    col1, col2, col3 = st.columns(3)
    with col1:
        query_params['only_need_context'] = st.checkbox("Context Only", key="rag_context_only")
    with col2:
        query_params['only_need_prompt'] = st.checkbox("Prompt Only", key="rag_prompt_only")
    with col3:
        query_params['stream'] = st.checkbox("Stream", key="rag_stream")

    if rag_search_query := st.chat_input(
        "Enter keywords to search the RAG knowledge base"
    ):
        # Pass the entire dictionary of parameters to the helper
        search_results = knowledge_helper.search_rag(
            query=rag_search_query, params=query_params
        )
        # Check if we have actual content (not just empty string or None)
        if search_results is not None and str(search_results).strip():
            st.subheader(
                f"🤖 RAG Knowledge Search Results for: '{rag_search_query}'"
            )
            st.markdown(search_results)
        elif search_results is not None:
            st.warning(f"Query returned empty response. Raw result: '{search_results}'")
        else:
            st.info("No matching knowledge found.")


def render_sidebar():
    with st.sidebar:
        st.header("🎨 Theme")
        is_dark = st.session_state.get(SESSION_KEY_DARK_THEME, False)
        theme_icon = "🌙" if is_dark else "☀️"
        theme_text = "Dark" if is_dark else "Light"
        if st.button(f"{theme_icon} {theme_text} Mode", key="sidebar_theme_toggle"):
            st.session_state[SESSION_KEY_DARK_THEME] = not st.session_state[
                SESSION_KEY_DARK_THEME
            ]
            st.rerun()

        st.header("👤 Current User")
        st.write(f"**🆔 {USER_ID}**")

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
                    with st.spinner("Reinitializing agent..."):
                        st.session_state[SESSION_KEY_CURRENT_MODEL] = selected_model
                        st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = (
                            new_ollama_url
                        )
                        st.session_state[SESSION_KEY_AGENT] = initialize_agent(
                            selected_model,
                            new_ollama_url,
                            st.session_state[SESSION_KEY_AGENT],
                        )
                        st.session_state[SESSION_KEY_MESSAGES] = []
                        st.success(f"Agent updated to use model: {selected_model}")
                        st.rerun()
                else:
                    st.info("Model and URL are already current")
        else:
            st.info("Click 'Fetch Available Models' to see available models")

        st.header("Agent Information")
        st.write(f"**Current Model:** {st.session_state[SESSION_KEY_CURRENT_MODEL]}")
        st.write(
            f"**Current Ollama URL:** {st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]}"
        )

        st.header("Controls")
        if st.button("Clear Chat History"):
            st.session_state[SESSION_KEY_MESSAGES] = []
            st.rerun()

        st.header("Debug Info")
        st.session_state[SESSION_KEY_SHOW_DEBUG] = st.checkbox(
            "Enable Debug Mode",
            value=st.session_state.get(SESSION_KEY_SHOW_DEBUG, False),
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
                PANDAS_AVAILABLE
                and len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 1
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
                                    st.write(
                                        f"**Tool {i}:** {tool_call.get('function_name', 'Unknown')}"
                                    )
                                    if tool_call.get("function_args"):
                                        st.json(tool_call["function_args"])
                                    if tool_call.get("reasoning"):
                                        st.write(
                                            f"**Reasoning:** {tool_call['reasoning']}"
                                        )
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