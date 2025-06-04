"""
Chat interface components for Streamlit Personal AI Agent.

This module handles the main chat interface rendering including message display,
conversation history, tool call visualization, and agent status indicators.
"""

import logging
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class ChatInterface:
    """
    Handles the main chat interface rendering and interaction.

    This class manages the display of conversation history, message formatting,
    tool call visualization, and real-time agent status updates.
    """

    def __init__(self) -> None:
        """Initialize the chat interface component."""
        pass

    def render(self) -> None:
        """
        Render the complete chat interface.

        This method displays the header, chat history, and agent status
        in a cohesive chat interface layout.
        """
        self.display_header()
        self.display_chat_history()
        self.display_agent_status()

    def display_header(self) -> None:
        """
        Display the main header with branding and description.

        Shows the application title and description to match the
        Flask interface branding.
        """
        st.markdown("# 🤖 Personal AI Agent")
        st.markdown("*Powered by Agno Framework with Native Memory & MCP Tools*")
        st.markdown("---")

    def display_chat_history(self) -> None:
        """
        Display the complete conversation history.

        Renders all messages in the conversation with proper formatting,
        including user messages, assistant responses, and tool call information.
        """
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display welcome message if no conversation exists
        if not st.session_state.messages:
            self.display_welcome_message()
            return

        # Render each message in the conversation
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                self.render_message_content(message)

    def display_welcome_message(self) -> None:
        """
        Display a welcome message when no conversation exists.

        Shows helpful information about the agent's capabilities
        and example queries to get users started.
        """
        with st.chat_message("assistant"):
            st.markdown(
                """
            👋 **Welcome to your Personal AI Agent!**
            
            I'm powered by the Agno framework with native memory and MCP tools integration. 
            I can help you with:
            
            - 🧠 **Intelligent conversations** with persistent memory
            - 🔧 **Tool usage** including file operations, web search, and more
            - 📚 **Knowledge retrieval** from your personal knowledge base
            - 💭 **Complex reasoning** with step-by-step thinking
            
            **Try asking me:**
            - "What can you help me with?"
            - "Search for information about Python async programming"
            - "Help me organize my thoughts about a project"
            - "What do you remember from our previous conversations?"
            
            Just type your question below to get started! 🚀
            """
            )

    def render_message_content(self, message: Dict[str, Any]) -> None:
        """
        Render the content of a single message.

        :param message: Message dictionary containing content and metadata
        """
        # Display main message content
        st.markdown(message["content"])

        # Display timestamp if available
        if "timestamp" in message:
            timestamp = message["timestamp"]
            st.caption(f"*{timestamp}*")

        # Display tool calls if available
        if "tool_calls" in message and message["tool_calls"]:
            self.display_tool_calls(message["tool_calls"])

    def display_tool_calls(self, tool_calls: List[Dict]) -> None:
        """
        Display tool usage information in an expandable section.

        :param tool_calls: List of tool call dictionaries
        """
        with st.expander("🔧 Tool Usage", expanded=False):
            for i, tool_call in enumerate(tool_calls, 1):
                tool_name = tool_call.get("name", "Unknown Tool")

                st.markdown(f"**{i}. {tool_name}**")

                # Display tool arguments if available
                if tool_call.get("arguments"):
                    st.json(tool_call["arguments"])

                # Display tool result if available
                if tool_call.get("result"):
                    st.code(str(tool_call["result"]), language="text")

                if i < len(tool_calls):
                    st.divider()

    def display_agent_status(self) -> None:
        """
        Display agent connection and capability status.

        Shows real-time status of memory, knowledge base, tools,
        and other agent capabilities in a metrics layout.
        """
        if "agent" not in st.session_state or st.session_state.agent is None:
            st.warning("⚠️ Agent not initialized")
            return

        agent = st.session_state.agent

        # Create status metrics in columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            memory_status = "🟢 Active" if agent.memory else "🔴 Inactive"
            st.metric("Memory", memory_status)

        with col2:
            knowledge_status = "🟢 Connected" if agent.knowledge else "🔴 Disconnected"
            st.metric("Knowledge Base", knowledge_status)

        with col3:
            tools_count = len(agent.tools) if agent.tools else 0
            st.metric("Tools", f"{tools_count} available")

        with col4:
            session_status = (
                "🟢 Active" if st.session_state.get("session_id") else "🔴 New"
            )
            st.metric("Session", session_status)

    def display_thinking_process(self, thinking_text: str) -> None:
        """
        Display the agent's thinking process in real-time.

        :param thinking_text: The agent's current thinking content
        """
        with st.expander("🤔 Agent Thinking...", expanded=True):
            st.info(thinking_text)

    def display_error_message(self, error: str) -> None:
        """
        Display error messages in a consistent format.

        :param error: Error message to display
        """
        st.error(f"❌ **Error:** {error}")

    def display_success_message(self, message: str) -> None:
        """
        Display success messages in a consistent format.

        :param message: Success message to display
        """
        st.success(f"✅ **Success:** {message}")

    def clear_conversation_ui(self) -> None:
        """
        Clear the conversation with user confirmation.

        Provides a confirmation dialog before clearing the conversation
        to prevent accidental data loss.
        """
        if st.button("🗑️ Clear Conversation", type="secondary"):
            if len(st.session_state.get("messages", [])) > 0:
                # Show confirmation dialog
                if st.button("⚠️ Confirm Clear", type="primary"):
                    st.session_state.messages = []
                    st.session_state.session_id = None
                    st.rerun()
            else:
                st.info("No conversation to clear")


from ..utils.styling import create_metric_card, create_status_badge

logger = logging.getLogger(__name__)


class ChatInterface:
    """
    Handles the main chat interface rendering and interactions.

    This class manages the display of conversation history, agent status,
    tool usage information, and other chat-related UI components.
    """

    def __init__(self) -> None:
        """Initialize the chat interface component."""
        pass

    def render(self) -> None:
        """
        Render the complete chat interface.

        This method displays the header, chat history, agent status,
        and any additional interface elements.
        """
        self.render_header()
        self.display_chat_history()
        self.display_agent_status()

    def render_header(self) -> None:
        """Render the main header section."""
        st.markdown(
            """
        <div class="main-header">
            <h1>🤖 Personal AI Agent</h1>
            <p><em>Powered by Agno Framework with Native Memory & MCP Tools</em></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def display_chat_history(self) -> None:
        """
        Display the conversation history.

        Renders all messages in the conversation with proper formatting
        and includes tool usage information where applicable.
        """
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display welcome message if no conversation exists
        if not st.session_state.messages:
            self.display_welcome_message()
            return

        # Display each message in the conversation
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Display tool calls if available
                if "tool_calls" in message and message["tool_calls"]:
                    self.display_tool_calls(message["tool_calls"])

                # Display timestamp in small text
                if "timestamp" in message:
                    st.caption(f"*{message['timestamp']}*")

    def display_welcome_message(self) -> None:
        """Display a welcome message for new users."""
        with st.chat_message("assistant"):
            st.markdown(
                """
            👋 **Welcome to your Personal AI Agent!**
            
            I'm here to help you with:
            - **Research & Analysis** - Search the web and analyze information
            - **Memory & Context** - Remember our conversations and build knowledge
            - **Tool Integration** - Access various tools and services through MCP
            - **Document Processing** - Work with files and documents
            
            Feel free to ask me anything! I'll use my tools and memory to provide the best assistance possible.
            
            **Try asking:**
            - "What can you help me with?"
            - "Search for information about [topic]"
            - "Remember that I prefer [preference]"
            - "What tools do you have access to?"
            """
            )

    def display_tool_calls(self, tool_calls: List[Dict]) -> None:
        """
        Display tool usage information.

        :param tool_calls: List of tool call dictionaries
        """
        with st.expander("🔧 Tool Usage", expanded=False):
            for i, tool_call in enumerate(tool_calls, 1):
                tool_name = tool_call.get("name", "Unknown Tool")
                st.markdown(f"**{i}. {tool_name}**")

                # Display tool arguments if available
                if tool_call.get("arguments"):
                    st.code(str(tool_call["arguments"]), language="json")

                # Display tool output if available
                if tool_call.get("output"):
                    with st.expander(f"Output from {tool_name}", expanded=False):
                        st.text(str(tool_call["output"]))

                if i < len(tool_calls):
                    st.divider()

    def display_agent_status(self) -> None:
        """
        Display current agent connection and status information.

        Shows the status of memory, knowledge base, tools, and other
        agent components in a compact, informative layout.
        """
        if "agent" not in st.session_state or not st.session_state.agent:
            st.warning("⚠️ Agent not initialized")
            return

        agent = st.session_state.agent

        # Create status section
        st.markdown("### 📊 Agent Status")

        # Create three columns for status metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            memory_status = "🟢 Active" if agent.memory else "🔴 Inactive"
            st.markdown(
                create_metric_card("Memory", memory_status, "Conversation history"),
                unsafe_allow_html=True,
            )

        with col2:
            knowledge_status = "🟢 Connected" if agent.knowledge else "🔴 Disconnected"
            st.markdown(
                create_metric_card("Knowledge Base", knowledge_status, "Vector search"),
                unsafe_allow_html=True,
            )

        with col3:
            tools_count = len(agent.tools) if agent.tools else 0
            tools_status = f"{tools_count} tools"
            st.markdown(
                create_metric_card("MCP Tools", tools_status, "Available integrations"),
                unsafe_allow_html=True,
            )

        # Display session information
        if st.session_state.get("session_id"):
            st.info(f"📝 Session: `{st.session_state.session_id[:8]}...`")

        # Display conversation statistics
        message_count = len(st.session_state.messages)
        if message_count > 0:
            tool_calls_count = len(st.session_state.get("tool_calls_history", []))
            st.caption(
                f"💬 {message_count} messages • 🔧 {tool_calls_count} tool calls"
            )

    def display_thinking_indicator(self, thinking_text: str) -> None:
        """
        Display agent thinking process.

        :param thinking_text: Text showing what the agent is thinking about
        """
        with st.container():
            st.markdown(f"🤔 **Thinking:** {thinking_text}")

    def display_streaming_response(self, container, response_text: str) -> None:
        """
        Display streaming response in real-time.

        :param container: Streamlit container for the response
        :param response_text: Current response text
        """
        container.markdown(response_text)

    def clear_chat_history(self) -> None:
        """Clear the chat history and reset the conversation."""
        st.session_state.messages = []
        st.session_state.tool_calls_history = []
        st.session_state.session_id = None
        st.rerun()
