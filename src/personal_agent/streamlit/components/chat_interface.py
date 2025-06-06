"""
Chat interface components for Streamlit Personal AI Agent.

This module handles the main chat interface rendering including message display,
conversation history, tool call visualization, and agent status indicators.
"""

import logging
from typing import Any, Dict, List

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

    def render(self) -> None:
        """
        Render the complete chat interface.

        This method displays the header with status bar and chat history
        in a cohesive chat interface layout.
        """
        self.display_header()
        self.display_chat_history()

    def display_header(self) -> None:
        """
        Display the main header with branding, description, and status bar.

        Shows the application title, description, and agent status
        to match the Flask interface branding.
        """
        st.markdown("# 🤖 Personal AI Agent")
        st.markdown("*Powered by Agno Framework with Native Memory & MCP Tools*")

        # Display status bar in header area
        self.display_agent_status()

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
        Display a compact agent status bar at the top.

        Shows essential status information in a single line format.
        """
        if "agent" not in st.session_state or st.session_state.agent is None:
            st.error("🔴 Agent not initialized")
            return

        agent = st.session_state.agent

        # Create compact status indicators
        memory_icon = "🟢" if agent.memory else "🔴"
        knowledge_icon = "🟢" if agent.knowledge else "🔴"
        tools_count = len(agent.tools) if agent.tools else 0
        session_icon = "🟢" if st.session_state.get("session_id") else "🆕"

        # Display as a single info line with more detailed information
        st.info(
            f"**Status:** {memory_icon} Memory | {knowledge_icon} Knowledge | 🔧 {tools_count} Tools | {session_icon} Session"
        )

        # Add debug information if tools are available
        if hasattr(agent, "tools") and agent.tools:
            with st.expander("🔧 Available Tools", expanded=False):
                for tool in agent.tools:
                    tool_name = getattr(tool, "name", str(tool))
                    st.write(f"• {tool_name}")
        else:
            st.warning("⚠️ No tools detected in agent")

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
