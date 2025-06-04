"""
Session state management utilities for Streamlit Personal AI Agent.

This module handles all session state operations including message history,
agent state, and user preferences persistence across Streamlit interactions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages Streamlit session state for the Personal AI Agent.

    This class provides a centralized way to handle session state variables,
    message history, and user preferences in the Streamlit application.
    """

    def __init__(self) -> None:
        """Initialize session state with default values."""
        self.initialize_session_state()

    def initialize_session_state(self) -> None:
        """
        Initialize all required session state variables with default values.

        This method ensures all necessary session variables exist and have
        appropriate default values when the application starts.
        """
        defaults = {
            "messages": [],
            "session_id": None,
            "agent": None,
            "debug_mode": False,
            "show_agent_info": False,
            "memory_stats": {},
            "last_response_time": None,
            "tool_calls_history": [],
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
                logger.debug(f"Initialized session state key: {key}")

    def add_message(
        self, role: str, content: str, tool_calls: Optional[List[Dict]] = None
    ) -> None:
        """
        Add a message to the conversation history.

        :param role: Message role ('user' or 'assistant')
        :param content: Message content text
        :param tool_calls: Optional list of tool calls made during response
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if tool_calls:
            message["tool_calls"] = tool_calls
            # Also track tool calls separately for analysis
            st.session_state.tool_calls_history.extend(tool_calls)

        st.session_state.messages.append(message)
        logger.debug(f"Added {role} message with {len(content)} characters")

    def clear_messages(self) -> None:
        """Clear all messages from the conversation history."""
        st.session_state.messages = []
        st.session_state.tool_calls_history = []
        st.session_state.session_id = None
        logger.info("Cleared conversation history")

    def get_messages(self) -> List[Dict]:
        """
        Get all messages from the conversation history.

        :return: List of message dictionaries
        """
        return st.session_state.messages

    def get_conversation_length(self) -> int:
        """
        Get the total number of messages in the conversation.

        :return: Number of messages
        """
        return len(st.session_state.messages)

    def export_conversation(self) -> str:
        """
        Export the current conversation as markdown text.

        :return: Formatted markdown string of the conversation
        """
        if not st.session_state.messages:
            return "# Empty Conversation\n\nNo messages to export."

        markdown_content = "# Personal AI Agent Conversation\n\n"
        markdown_content += (
            f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        for i, message in enumerate(st.session_state.messages, 1):
            role = message["role"].title()
            content = message["content"]
            timestamp = message.get("timestamp", "Unknown")

            markdown_content += f"## {i}. {role}\n"
            markdown_content += f"**Time:** {timestamp}\n\n"
            markdown_content += f"{content}\n\n"

            # Include tool calls if present
            if "tool_calls" in message and message["tool_calls"]:
                markdown_content += "**Tools Used:**\n"
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call.get("name", "Unknown")
                    markdown_content += f"- {tool_name}\n"
                markdown_content += "\n"

        return markdown_content

    def update_memory_stats(self, agent) -> None:
        """
        Update memory statistics from the agent.

        :param agent: The agno agent instance
        """
        try:
            stats = {
                "memory_enabled": agent.memory is not None,
                "knowledge_enabled": agent.knowledge is not None,
                "tools_count": len(agent.tools) if agent.tools else 0,
                "session_active": st.session_state.session_id is not None,
                "messages_count": len(st.session_state.messages),
                "last_updated": datetime.now().isoformat(),
            }
            st.session_state.memory_stats = stats
            logger.debug("Updated memory statistics")
        except Exception as e:
            logger.error(f"Failed to update memory stats: {e}")
