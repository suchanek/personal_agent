"""
Streamlit interface for Personal AI Agent using agno framework.

This module provides a Streamlit-based web interface that replaces the Flask implementation
while maintaining all functionality including real-time thought streaming, memory management,
and MCP tools integration.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import nest_asyncio
import streamlit as st

from ..agno_main import initialize_agno_system
from .components.agent_info import AgentInfo
from .components.chat_interface import ChatInterface
from .components.sidebar import Sidebar
from .utils.session_manager import SessionManager
from .utils.styling import apply_custom_css

# Enable nested async loops for Streamlit compatibility
nest_asyncio.apply()

logger = logging.getLogger(__name__)


class PersonalAgentApp:
    """
    Main Streamlit application for Personal AI Agent.

    This class orchestrates the entire Streamlit interface, managing the chat interface,
    sidebar controls, agent initialization, and user interactions.
    """

    def __init__(self) -> None:
        """Initialize the Streamlit application with all required components."""
        self.setup_page_config()
        self.session_manager = SessionManager()
        self.chat_interface = ChatInterface()
        self.sidebar = Sidebar()
        self.agent_info = AgentInfo()

    def setup_page_config(self) -> None:
        """
        Configure Streamlit page settings.

        Sets up page title, icon, layout, and other configuration options
        to match the branding and functionality of the Flask interface.
        """
        st.set_page_config(
            page_title="Personal AI Agent",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                "About": "Personal AI Agent - Powered by Agno Framework with Native Memory & MCP Tools"
            },
        )

    async def initialize_agent(self) -> None:
        """
        Initialize the agno agent if not already done.

        This method ensures the agent is only initialized once per session
        and handles any initialization errors gracefully.
        """
        if "agent" not in st.session_state or st.session_state.agent is None:
            try:
                with st.spinner("🔄 Initializing AI Agent..."):
                    st.session_state.agent = await initialize_agno_system()
                    st.session_state.messages = []
                    st.session_state.session_id = None
                    logger.info("Agent initialized successfully in Streamlit")
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")
                logger.error(f"Agent initialization failed: {e}")

    def run(self) -> None:
        """
        Main application entry point.

        This method orchestrates the entire application flow, from styling
        to agent initialization to rendering the main interface components.
        """
        # Apply custom styling to match Flask interface appearance
        apply_custom_css()

        # Initialize agent asynchronously
        asyncio.run(self.initialize_agent())

        # Only proceed if agent is properly initialized
        if "agent" not in st.session_state or st.session_state.agent is None:
            st.error("Agent initialization failed. Please refresh the page.")
            return

        # Main layout with chat interface and sidebar
        col1, col2 = st.columns([3, 1])

        with col1:
            self.chat_interface.render()

        with col2:
            self.sidebar.render()

        # Handle new messages and interactions
        self.handle_chat_interaction()

    def handle_chat_interaction(self) -> None:
        """
        Process new chat messages and user interactions.

        This method handles the main chat input, processes user messages
        through the agno agent, and manages the conversation flow.
        """
        # Chat input at the bottom of the interface
        if prompt := st.chat_input("💬 Ask me anything..."):
            # Add user message to conversation
            self.session_manager.add_message("user", prompt)

            # Process with agent and display response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    response = asyncio.run(self.process_agent_response(prompt))

            # Add assistant response to conversation
            self.session_manager.add_message("assistant", response)

            # Refresh the interface to show new messages
            st.rerun()

    async def process_agent_response(self, query: str) -> str:
        """
        Process user query through the agno agent.

        :param query: User's input message
        :return: Agent's response content
        """
        try:
            agent = st.session_state.agent

            # Use session_id if available for conversation continuity
            session_id = st.session_state.get("session_id")

            # Run agent with query
            response = await agent.arun(message=query, session_id=session_id)

            # Update session_id if it was generated
            if hasattr(response, "session_id") and response.session_id:
                st.session_state.session_id = response.session_id

            return response.content

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            logger.error(f"Error processing query '{query}': {e}")
            st.error(error_msg)
            return error_msg


def main() -> None:
    """
    Main entry point for the Streamlit application.

    Creates and runs the PersonalAgentApp instance.
    """
    app = PersonalAgentApp()
    app.run()


if __name__ == "__main__":
    main()
