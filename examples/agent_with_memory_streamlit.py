import sys
from pathlib import Path
from textwrap import dedent

import streamlit as st
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.manager import MemoryManager
from agno.memory.v2.memory import Memory
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.storage.sqlite import SqliteStorage

from agno.tools.googlesearch import GoogleSearchTools

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from the correct path
from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID

# Initialize session state
if "agent" not in st.session_state:
    # Set up storage and memory
    agent_storage = SqliteStorage(
        table_name="agent_sessions", db_file="/tmp/persistent_memory.db"
    )
    memory_db = SqliteMemoryDb(table_name="memory", db_file="/tmp/memory.db")

    memory = Memory(
        db=memory_db,
        memory_manager=MemoryManager(
            memory_capture_instructions="""\
                            Collect User's name,
                            Collect Information about user's passion and hobbies,
                            Collect Information about the users likes and dislikes,
                            Collect information about what the user is doing with their life right now
                        """,
            model=Gemini(id="gemini-2.0-flash"),
        ),
    )

    # Reset the memory for this example
    memory.clear()

    # Create the agent
    st.session_state.agent = Agent(
        name="Personal AI Friend",
        model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
        tools=[GoogleSearchTools()],
        add_history_to_messages=True,
        num_history_responses=3,
        add_datetime_to_instructions=True,
        markdown=True,
        memory=memory,
        enable_agentic_memory=True,
        instructions=dedent(
            """
            You are a personal AI friend of the user, your purpose is to chat with the user about things and make them feel good.
            First introduce yourself and ask for their name then, ask about themselves, their hobbies, what they like to do and what they like to talk about.
            If they ask for more information use Google Search tool to find latest information about things in the conversations.
            Store these memories for later recall.
            """
        ),
        debug_mode=True,
    )

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

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
    st.header("Agent Information")
    st.write(f"**Model:** {LLM_MODEL}")
    st.write(f"**Ollama URL:** {OLLAMA_URL}")
    st.write("**Features:**")
    st.write("- Memory storage")
    st.write("- Google Search")
    st.write("- Conversation history")

    st.header("Controls")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    if st.button("Reset Agent Memory"):
        if "agent" in st.session_state:
            st.session_state.agent.memory.clear()
            st.success("Agent memory cleared!")

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
    **To run this app:**
    ```bash
    streamlit run examples/agent_with_memory_streamlit.py
    ```
    """
    )
