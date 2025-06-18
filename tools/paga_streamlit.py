import json
import sys
from pathlib import Path
from textwrap import dedent

import requests
import streamlit as st
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.manager import MemoryManager
from agno.memory.v2.memory import Memory
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.storage.sqlite import SqliteStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.googlesearch import GoogleSearchTools

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from the correct path
from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID

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


def initialize_agent(model_name, ollama_url):
    """Initialize or reinitialize the agent with the specified model and URL."""
    # Set up storage and memory
    agent_storage = SqliteStorage(
        table_name="agent_sessions", db_file="/tmp/persistent_memory.db"
    )
    memory_db = SqliteMemoryDb(table_name="personal_agent_memory", db_file=str(db_path))

    memory = Memory(
        db=memory_db,
        memory_manager=MemoryManager(
            memory_capture_instructions="""\
                            Collect User's name,
                            Collect Information about user's passion and hobbies,
                            Collect Information about the users likes and dislikes,
                            Collect information about what the user is doing with their life right now
                            Collect information about what matters to the user
                            Collect information about the life events that had impact on them
                        """,
            # model=Gemini(id="gemini-2.0-flash"),
            model=Ollama(
                id=model_name,
                host=ollama_url,
                options={
                    "num_ctx": 131072,  # Use full context window capacity
                    "temperature": 0.7,
                },
            ),
        ),
    )

    # Create the agent
    return Agent(
        name="Personal AI Friend",
        model=Ollama(
            id=model_name,
            host=ollama_url,
            options={
                "num_ctx": 8192,  # Use full context window capacity
                "temperature": 0.7,
            },
        ),
        user_id=USER_ID,  # Specify the user_id for memory management
        tools=[GoogleSearchTools(), DuckDuckGoTools()],
        add_history_to_messages=True,
        num_history_responses=3,
        add_datetime_to_instructions=True,
        markdown=True,
        memory=memory,
        enable_agentic_memory=True,
        enable_user_memories=True,
        instructions=dedent(
            f"""
            You are a personal AI friend of the user, your purpose is to chat with the user about things and make them feel good.
            The user you are talking to is: {USER_ID}
            First introduce yourself and greet them by their user ID, then ask about themselves, their hobbies, what they like to do and what they like to talk about.
            If they ask for more information use Google Search tool to find latest information about things in the conversations.
            Store these memories for later recall.
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
            try:
                response = st.session_state.agent.run(prompt)
                st.markdown(response.content)

                # Add assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": response.content}
                )

            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
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

                        # Reinitialize agent
                        st.session_state.agent = initialize_agent(
                            selected_model, new_ollama_url
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
    st.write("**Features:**")
    st.write("- Memory storage")
    st.write("- Google Search")
    st.write("- Conversation history")
    st.write("- Dynamic model selection")

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
                # memories = st.session_state.agent.memory.db.get_all()
                # Get memories for a specific user
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

    st.header("Debug Info")
    if st.checkbox("Show Debug Mode"):
        st.write("**Session State Keys:**")
        st.write(list(st.session_state.keys()))

        if st.session_state.messages:
            st.write("**Message Count:**", len(st.session_state.messages))

# Instructions for running
if __name__ == "__main__":
    st.markdown(
        """
    ---
    **Talk to the agent!**
    
    """
    )
