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

db_path = Path(AGNO_STORAGE_DIR) / "agent_memory.db"

# Initialize session state
if "agent" not in st.session_state:
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
                        """,
            model=Gemini(id="gemini-2.0-flash"),
            # model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
        ),
    )

    # Reset the memory for this example
    # memory.clear()

    # Create the agent
    st.session_state.agent = Agent(
        name="Personal AI Friend",
        model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
        user_id=USER_ID,  # Specify the user_id for memory management
        tools=[GoogleSearchTools()],
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
    st.write(f"**User ID:** {USER_ID}")
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

    if st.button("Show All Memories"):
        if "agent" in st.session_state:
            try:
                # Get all memories from the memory database
                # memories = st.session_state.agent.memory.db.get_all()
                # Get memories for a specific user
                memories = st.session_state.agent.memory.get_user_memories(
                    user_id=USER_ID
                )
                print(f"Memories: {memories}")
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
