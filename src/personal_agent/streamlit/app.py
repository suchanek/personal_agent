"""
Streamlit interface for Personal AI Agent using agno framework.

This module provides a Streamlit-based web interface that replaces the Flask implementation
while maintaining all functionality including real-time thought streaming, memory management,
and MCP tools integration.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import nest_asyncio
import streamlit as st

# Add the src directory to sys.path to enable imports when run directly
repo_root = Path(__file__).parent.parent.parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from personal_agent.agno_main import initialize_agno_system
    from personal_agent.streamlit.components.agent_info import AgentInfo
    from personal_agent.streamlit.components.chat_interface import ChatInterface
    from personal_agent.streamlit.components.sidebar import Sidebar
    from personal_agent.streamlit.utils.session_manager import SessionManager
    from personal_agent.streamlit.utils.styling import apply_custom_css
except ImportError:
    # Fallback for relative imports
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
        Configure Streamlit page settings with dark theme support.

        Sets up page title, icon, layout, and dark theme configuration
        to provide a modern dark mode experience.
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

    def apply_dark_theme(self) -> None:
        """
        Apply enhanced dark theme support.

        This method adds dark theme support by leveraging CSS media queries
        and forcing dark mode styling for better visibility.
        """
        # Check if dark theme is enabled (default to True)
        dark_theme_enabled = st.session_state.get("dark_theme", True)

        if dark_theme_enabled:
            # Enhanced dark theme CSS that works with Streamlit's system
            dark_theme_css = """
            <style>
            /* Force dark theme by default and respond to system preferences */
            :root {
                color-scheme: dark;
            }
            
            /* Dark theme variables - ensure these override defaults */
            :root, [data-theme="dark"] {
                --bg-primary: #0f172a !important;
                --bg-secondary: #1e293b !important;
                --bg-tertiary: #334155 !important;
                --text-primary: #f1f5f9 !important;
                --text-secondary: #cbd5e1 !important;
                --border-color: #475569 !important;
                --chat-user-bg: #1e293b !important;
                --chat-assistant-bg: #0f172a !important;
                --button-bg: #334155 !important;
                --button-hover-bg: #475569 !important;
            }
            
            /* Force dark backgrounds for Streamlit components */
            .stApp {
                background-color: var(--bg-primary) !important;
                color: var(--text-primary) !important;
            }
            
            .main .block-container {
                background-color: var(--bg-primary) !important;
                color: var(--text-primary) !important;
            }
            
            /* Enhanced dark mode for all components */
            .stChatMessage {
                background-color: var(--bg-secondary) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
            }
            
            .stButton > button {
                background-color: var(--button-bg) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
            }
            
            .stTextInput input, .stChatInput input, .stSelectbox select {
                background-color: var(--bg-tertiary) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
            }
            
            /* Sidebar dark theme */
            .css-1d391kg, section[data-testid="stSidebar"] {
                background-color: var(--bg-secondary) !important;
            }
            
            /* Text elements */
            h1, h2, h3, h4, h5, h6, p, span, div, label {
                color: var(--text-primary) !important;
            }
            
            /* Metric containers */
            .metric-container {
                background-color: var(--bg-secondary) !important;
                border: 1px solid var(--border-color) !important;
            }
            
            /* System preference detection */
            @media (prefers-color-scheme: dark) {
                .stApp {
                    background-color: var(--bg-primary) !important;
                }
            }
            </style>
            """
        else:
            # Light theme CSS (minimal, rely on Streamlit defaults)
            dark_theme_css = """
            <style>
            :root {
                color-scheme: light;
            }
            
            .stApp {
                background-color: #ffffff !important;
                color: #000000 !important;
            }
            
            .main .block-container {
                background-color: #ffffff !important;
                color: #000000 !important;
            }
            </style>
            """

        st.markdown(dark_theme_css, unsafe_allow_html=True)

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
        # Apply theme styling (respects user preference)
        self.apply_dark_theme()

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
