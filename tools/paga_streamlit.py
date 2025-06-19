import json
import sys
import time
from pathlib import Path
from textwrap import dedent
from datetime import datetime

import requests
import streamlit as st
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.storage.sqlite import SqliteStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.yfinance import YFinanceTools

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from the correct path
from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID
from personal_agent.core.semantic_memory_manager import SemanticMemoryManager, SemanticMemoryManagerConfig

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


def initialize_agent(model_name, ollama_url, existing_agent=None):
    """Initialize or reinitialize the agent with the specified model and URL."""
    # Set up storage and memory (reuse existing if available)
    if existing_agent and hasattr(existing_agent, 'memory') and existing_agent.memory:
        # Reuse existing memory to preserve stored memories
        memory = existing_agent.memory
        # Update the memory manager's model to use the new model
        if hasattr(memory, 'memory_manager') and memory.memory_manager:
            memory.memory_manager.model = Ollama(
                id=model_name,
                host=ollama_url,
                options={
                    "num_ctx": 8192,
                    "temperature": 0.7,
                },
            )
    else:
        # Create new memory for first-time initialization
        agent_storage = SqliteStorage(
            table_name="agent_sessions", db_file="/tmp/persistent_memory.db"
        )
        memory_db = SqliteMemoryDb(table_name="personal_agent_memory", db_file=str(db_path))

        # Create semantic memory manager configuration
        semantic_config = SemanticMemoryManagerConfig(
            similarity_threshold=0.8,
            enable_semantic_dedup=True,
            enable_exact_dedup=True,
            enable_topic_classification=True,
            debug_mode=True,
        )
        
        # Create semantic memory manager (LLM-free, but with model attribute for compatibility)
        semantic_memory_manager = SemanticMemoryManager(
            model=Ollama(
                id=model_name,
                host=ollama_url,
                options={
                    "num_ctx": 8192,
                    "temperature": 0.7,
                },
            ),
            config=semantic_config
        )
        
        # Memory class with custom memory manager (no model parameter needed)
        memory = Memory(
            db=memory_db,
            memory_manager=semantic_memory_manager,
        )

    # If we have an existing agent, update its properties instead of creating new
    if existing_agent:
        # Update the main model
        existing_agent.model = Ollama(
            id=model_name,
            host=ollama_url,
            options={
                "num_ctx": 8192,
                "temperature": 0.7,
            },
        )
        # Update memory reference
        existing_agent.memory = memory
        return existing_agent
    else:
        # Create new agent for first-time initialization
        return Agent(
            name="Personal AI Friend",
            model=Ollama(
                id=model_name,
                host=ollama_url,
                options={
                    "num_ctx": 8192,
                    "temperature": 0.7,
                },
            ),
            user_id=USER_ID,
            tools=[GoogleSearchTools(), DuckDuckGoTools(), YFinanceTools()],
            add_history_to_messages=False,
            num_history_responses=3,
            add_datetime_to_instructions=True,
            markdown=True,
            memory=memory,
            enable_agentic_memory=True,
            enable_user_memories=True,
            show_tool_calls=True,
            tool_call_limit=5,
            instructions=dedent(
                f"""
                You are a personal AI friend of the user, your purpose is to chat with the user about things and make them feel good.
                The user you are talking to is: {USER_ID}
                First introduce yourself and greet them by their user ID, then ask about themselves, their hobbies, what they like to do and what they like to talk about.
                
                When users ask for current information, news, or search queries, use the available search tools:
                - Use DuckDuckGoTools for news searches and general web searches
                - Use GoogleSearchTools for comprehensive web searches
                
                - Always execute tool calls properly and provide the results to the user in a conversational manner.
                - Store these memories for later recall.
                - Only store a memory ONCE
                - Do not duplicate memories
                
                IMPORTANT: When calling memory functions, always pass topics as a proper list like ["topic1", "topic2"], 
                never as a string like '["topic1", "topic2"]'.
                """
            ),
            debug_mode=True,
        )


# Initialize session state variables
if "current_ollama_url" not in st.session_state:
    st.session_state.current_ollama_url = OLLAMA_URL

if "current_model" not in st.session_state:
    st.session_state.current_model = LLM_MODEL

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
        "fastest_response": float('inf'),
        "slowest_response": 0,
        "tool_calls_count": 0,
        "memory_operations": 0
    }

# Streamlit UI
st.title("🤖 Personal AI Friend with Memory")
st.markdown(
    "*A friendly AI agent that remembers your conversations and learns about you*"
)

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
                response = st.session_state.agent.run(prompt)
                
                # End timing
                end_time = time.time()
                response_time = end_time - start_time
                
                # Calculate token estimates (rough approximation)
                input_tokens = len(prompt.split()) * 1.3  # Rough token estimate
                output_tokens = 0
                if hasattr(response, "content") and response.content:
                    output_tokens = len(response.content.split()) * 1.3
                
                total_tokens = input_tokens + output_tokens
                
                # Count tool calls - check multiple possible attributes
                tool_calls_made = 0
                tool_call_details = []
                
                # Check various possible tool call attributes
                if hasattr(response, "tool_calls") and response.tool_calls:
                    tool_calls_made = len(response.tool_calls)
                    tool_call_details = response.tool_calls
                elif hasattr(response, "messages") and response.messages:
                    # Check if tool calls are in messages
                    for msg in response.messages:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            tool_calls_made += len(msg.tool_calls)
                            tool_call_details.extend(msg.tool_calls)
                        elif hasattr(msg, "content") and isinstance(msg.content, list):
                            # Check for tool calls in message content
                            for content_item in msg.content:
                                if hasattr(content_item, "type") and content_item.type == "tool_use":
                                    tool_calls_made += 1
                                    tool_call_details.append(content_item)
                
                # Update performance stats
                stats = st.session_state.performance_stats
                stats["total_requests"] += 1
                stats["total_response_time"] += response_time
                stats["average_response_time"] = stats["total_response_time"] / stats["total_requests"]
                stats["total_tokens"] += total_tokens
                stats["average_tokens"] = stats["total_tokens"] / stats["total_requests"]
                stats["fastest_response"] = min(stats["fastest_response"], response_time)
                stats["slowest_response"] = max(stats["slowest_response"], response_time)
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
                    "response_type": str(type(response).__name__),
                    "success": True
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
                            st.metric("📋 Response Type", str(type(response).__name__))
                        
                        st.write("**Response Object Details:**")
                        
                        # Enhanced tool call display
                        if tool_call_details:
                            st.write("**🛠️ Tool Calls Made:**")
                            for i, tool_call in enumerate(tool_call_details, 1):
                                st.write(f"**Tool Call {i}:**")
                                if hasattr(tool_call, 'function'):
                                    st.write(f"  - Function: {tool_call.function.name}")
                                    st.write(f"  - Arguments: {tool_call.function.arguments}")
                                elif hasattr(tool_call, 'name'):
                                    st.write(f"  - Tool: {tool_call.name}")
                                    if hasattr(tool_call, 'input'):
                                        st.write(f"  - Input: {tool_call.input}")
                                else:
                                    st.write(f"  - Tool Call: {str(tool_call)}")
                                st.write("---")
                        else:
                            st.write("- No tool calls detected")
                        
                        if hasattr(response, "messages") and response.messages:
                            st.write(f"- Messages count: {len(response.messages)}")
                            st.write("**Message Details:**")
                            for i, msg in enumerate(response.messages):
                                st.write(f"**Message {i+1}:**")
                                st.write(f"  - Role: {getattr(msg, 'role', 'Unknown')}")
                                if hasattr(msg, 'content'):
                                    content_preview = str(msg.content)[:200] + "..." if len(str(msg.content)) > 200 else str(msg.content)
                                    st.write(f"  - Content: {content_preview}")
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    st.write(f"  - Tool calls: {len(msg.tool_calls)}")
                        
                        if hasattr(response, "model") and response.model:
                            st.write(f"- Model used: {response.model}")
                        
                        # Show raw response attributes
                        st.write("**Available Response Attributes:**")
                        response_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
                        st.write(response_attrs)
                        
                        # Show full response object for deep debugging
                        st.write("**Full Response Object (Advanced):**")
                        st.code(str(response))

                # Display the response content
                if hasattr(response, "content") and response.content:
                    st.markdown(response.content)
                    # Add assistant response to chat history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response.content}
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
                    "error": str(e)
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

# Sidebar with agent info and controls
with st.sidebar:
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
    st.write(f"**User ID:** {USER_ID}")

    st.header("Controls")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

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
            "💡 **Remember**: Your AI friend's memories help create better, "
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
                if "agent" in st.session_state:
                    st.session_state.agent.memory.clear()
                    st.session_state.show_memory_confirmation = False
                    st.success("⚠️ All agent memories have been cleared!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("No agent found in session state")

    if st.button("Show All Memories"):
        if "agent" in st.session_state:
            try:
                # Get all memories from the memory database
                memories = st.session_state.agent.memory.get_user_memories(
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

    # Semantic Memory Manager Controls
    st.header("🧠 Semantic Memory")
    
    # Memory Statistics
    if st.button("📊 Show Memory Statistics"):
        if "agent" in st.session_state and hasattr(st.session_state.agent, 'memory'):
            try:
                # Get semantic memory manager from the agent's memory
                memory_manager = st.session_state.agent.memory.memory_manager
                if hasattr(memory_manager, 'get_memory_stats'):
                    stats = memory_manager.get_memory_stats(
                        st.session_state.agent.memory.db, USER_ID
                    )
                    
                    st.subheader("Memory Statistics")
                    
                    # Display basic stats
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Memories", stats.get("total_memories", 0))
                        st.metric("Recent (24h)", stats.get("recent_memories_24h", 0))
                    
                    with col2:
                        avg_length = stats.get("average_memory_length", 0)
                        st.metric("Avg Length", f"{avg_length:.1f} chars" if avg_length else "N/A")
                        most_common = stats.get("most_common_topic", "None")
                        st.metric("Top Topic", most_common if most_common else "None")
                    
                    # Topic distribution
                    topic_dist = stats.get("topic_distribution", {})
                    if topic_dist:
                        st.subheader("📈 Topic Distribution")
                        for topic, count in sorted(topic_dist.items(), key=lambda x: x[1], reverse=True):
                            st.write(f"**{topic.title()}:** {count} memories")
                    
                else:
                    st.info("Memory statistics not available with current memory manager")
            except Exception as e:
                st.error(f"Error getting memory statistics: {str(e)}")
    
    # Memory Search
    st.subheader("🔍 Search Memories")
    search_query = st.text_input(
        "Search Query:",
        placeholder="Enter keywords to search your memories...",
        help="Search through your stored memories using semantic similarity"
    )
    
    if st.button("Search") and search_query:
        if "agent" in st.session_state and hasattr(st.session_state.agent, 'memory'):
            try:
                memory_manager = st.session_state.agent.memory.memory_manager
                if hasattr(memory_manager, 'search_memories'):
                    results = memory_manager.search_memories(
                        search_query,
                        st.session_state.agent.memory.db,
                        USER_ID,
                        limit=5,
                        similarity_threshold=0.3
                    )
                    
                    if results:
                        st.subheader(f"Search Results for: '{search_query}'")
                        for i, (memory, similarity) in enumerate(results, 1):
                            with st.expander(f"Result {i} (Similarity: {similarity:.2f})"):
                                st.write(f"**Memory:** {memory.memory}")
                                if memory.topics:
                                    st.write(f"**Topics:** {', '.join(memory.topics)}")
                                st.write(f"**Last Updated:** {memory.last_updated}")
                    else:
                        st.info("No matching memories found. Try different keywords.")
                else:
                    st.info("Memory search not available with current memory manager")
            except Exception as e:
                st.error(f"Error searching memories: {str(e)}")

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
                st.metric("Fastest Response", f"{stats['fastest_response']:.3f}s" if stats['fastest_response'] != float('inf') else "N/A")
                
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
                    df = df[df['success'] == True]  # Only successful requests
                    
                    if not df.empty and len(df) > 1:
                        # Create a simple line chart of response times
                        chart_data = df[['timestamp', 'response_time']].copy()
                        chart_data = chart_data.set_index('timestamp')
                        
                        # Use altair for better chart control and avoid deprecation warnings
                        try:
                            import altair as alt
                            
                            # Create altair chart with proper theme handling
                            chart = alt.Chart(chart_data.reset_index()).mark_line(point=True).encode(
                                x=alt.X('timestamp:O', title='Time'),
                                y=alt.Y('response_time:Q', title='Response Time (s)'),
                                tooltip=['timestamp:O', 'response_time:Q']
                            ).properties(
                                width=400,
                                height=200,
                                title='Response Time Trend'
                            )
                            
                            st.altair_chart(chart, use_container_width=True)
                        except ImportError:
                            # Fallback to streamlit line chart if altair not available
                            st.line_chart(chart_data['response_time'])
                    else:
                        st.info("Need at least 2 successful requests to show trend chart")
                except Exception as e:
                    st.warning(f"Chart rendering issue (this doesn't affect functionality): {str(e)}")
                    # Fallback: show data in table format
                    if st.session_state.debug_metrics:
                        recent_times = [entry['response_time'] for entry in st.session_state.debug_metrics[-5:] if entry['success']]
                        if recent_times:
                            st.write(f"Recent response times: {', '.join([f'{t:.3f}s' for t in recent_times])}")
        else:
            st.info("No requests made yet. Start chatting to see performance stats!")
        
        # Recent Debug Metrics
        st.subheader("🔍 Recent Request Details")
        if st.session_state.debug_metrics:
            for i, entry in enumerate(reversed(st.session_state.debug_metrics[-5:])):  # Show last 5
                status_icon = "✅" if entry['success'] else "❌"
                tool_indicator = f" 🛠️{entry['tool_calls']}" if entry['tool_calls'] > 0 else ""
                with st.expander(f"{status_icon} {entry['timestamp']} - {entry['response_time']}s{tool_indicator}", expanded=False):
                    st.write(f"**Prompt:** {entry['prompt']}")
                    st.write(f"**Response Time:** {entry['response_time']}s")
                    st.write(f"**Tokens:** {entry['total_tokens']} (In: {entry['input_tokens']}, Out: {entry['output_tokens']})")
                    st.write(f"**Tool Calls:** {entry['tool_calls']}")
                    st.write(f"**Response Type:** {entry['response_type']}")
                    
                    # Show tool call details if available
                    if entry.get('tool_call_details') and len(entry['tool_call_details']) > 0:
                        st.write("**🛠️ Tools Used:**")
                        for j, tool_call in enumerate(entry['tool_call_details'], 1):
                            if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                                st.write(f"  {j}. {tool_call.function.name}")
                            elif hasattr(tool_call, 'name'):
                                st.write(f"  {j}. {tool_call.name}")
                            else:
                                st.write(f"  {j}. {str(tool_call)[:50]}...")
                    
                    if not entry['success'] and 'error' in entry:
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
            st.write(
                f"- Tools: {[tool.__class__.__name__ for tool in agent.tools] if agent.tools else 'None'}"
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
                "fastest_response": float('inf'),
                "slowest_response": 0,
                "tool_calls_count": 0,
                "memory_operations": 0
            }
            st.success("Debug data cleared!")
            st.rerun()

# Instructions for running
if __name__ == "__main__":
    st.markdown(
        """
    ---
    **Talk to the agent!**
    
    """
    )
