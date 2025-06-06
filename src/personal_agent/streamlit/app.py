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
        Configure Streamlit page settings with proper theme support.

        Sets up page title, icon, layout, and allows Streamlit's built-in
        theme system to handle light/dark mode switching.
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

    def apply_theme_aware_styling(self) -> None:
        """Apply theme-aware styling that respects Streamlit's built-in theme system"""
        # Apply theme-aware CSS that works with both light and dark themes
        theme_aware_css = """
        <style>
        /* Theme-aware styling using Streamlit's native theme variables */
        
        /* Fix selectbox dropdown to use proper theme colors */
        .stSelectbox > div[data-baseweb="select"] {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--secondary-background-color) !important;
        }
        
        .stSelectbox > div[data-baseweb="select"] > div {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
        }
        
        /* Dropdown menu options */
        [role="listbox"] {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--secondary-background-color) !important;
        }
        
        [role="option"] {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
        }
        
        [role="option"]:hover {
            background-color: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
        }
        
        /* Ensure all input elements follow theme */
        .stTextInput input, .stChatInput input {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--secondary-background-color) !important;
        }
        
        /* Chat input area */
        [data-testid="stChatInput"] {
            background-color: var(--background-color) !important;
        }
        
        [data-testid="stChatInput"] textarea {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--secondary-background-color) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--secondary-background-color) !important;
        }
        
        .stButton > button:hover {
            background-color: var(--primary-color) !important;
        }
        
        /* Chat messages */
        .stChatMessage {
            background-color: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--secondary-background-color) !important;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: var(--secondary-background-color) !important;
        }
        
        /* Main app container */
        .stApp {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
        }
        
        .main .block-container {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
        }
        </style>
        """

        st.markdown(theme_aware_css, unsafe_allow_html=True)

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
                logger.error("Agent initialization failed: %s", e)

    def run(self) -> None:
        """
        Main application entry point.

        This method orchestrates the entire application flow, from styling
        to agent initialization to rendering the main interface components.
        """
        # Apply theme-aware styling (respects Streamlit's built-in theme system)
        self.apply_theme_aware_styling()

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

            # Process with agent and display response with real-time tool calls
            with st.chat_message("assistant"):
                # Create containers for tool calls and response
                tool_calls_container = st.empty()
                response_container = st.empty()

                # Process agent response with streaming
                response = asyncio.run(
                    self.process_agent_response(
                        prompt, tool_calls_container, response_container
                    )
                )

            # Add assistant response to conversation
            self.session_manager.add_message("assistant", response)

            # Refresh the interface to show new messages
            st.rerun()

    async def process_agent_response(
        self, query: str, tool_calls_container, response_container
    ) -> str:
        """
        Process user query through the agno agent with real-time streaming.

        :param query: User's input message
        :param tool_calls_container: Streamlit container for displaying tool calls
        :param response_container: Streamlit container for displaying response
        :return: Agent's response content
        """
        try:
            agent = st.session_state.agent

            # Use session_id if available for conversation continuity
            session_id = st.session_state.get("session_id")

            # Run agent with streaming enabled to show tool calls in real-time
            response_text = ""

            try:
                # Create a status container for real-time agent thinking
                status_container = st.empty()

                # Use streaming with intermediate steps to see tool calls
                response_stream = await agent.arun(
                    message=query,
                    session_id=session_id,
                    stream=True,
                    stream_intermediate_steps=True,
                )

                # Process streaming response chunks
                async for response_chunk in response_stream:
                    # Show real-time status updates for all events
                    if hasattr(response_chunk, "event") and response_chunk.event:
                        event_name = response_chunk.event

                        # Display status based on event type
                        if event_name == "run_started":
                            with status_container.container():
                                st.info("🚀 Starting to process your request...")
                        elif event_name == "tool_call_started":
                            with status_container.container():
                                st.info("🔧 Using tools to help with your request...")
                        elif event_name == "reasoning_started":
                            with status_container.container():
                                st.info("🧠 Thinking through the problem...")
                        elif event_name == "reasoning_step":
                            if (
                                hasattr(response_chunk, "content")
                                and response_chunk.content
                            ):
                                with status_container.container():
                                    st.info(f"💭 {response_chunk.content}")
                        elif event_name == "tool_call_completed":
                            with status_container.container():
                                st.info("✅ Tool execution completed")

                    # Display tool calls if available
                    if response_chunk.tools and len(response_chunk.tools) > 0:
                        self.display_tool_calls_realtime(
                            tool_calls_container, response_chunk.tools
                        )

                    # Display response content as it streams (for any event with content)
                    if (
                        hasattr(response_chunk, "content")
                        and response_chunk.content is not None
                    ):
                        # Only accumulate content for RunResponse events for final response
                        if response_chunk.event == "RunResponse":
                            response_text += response_chunk.content
                            with response_container.container():
                                st.markdown(response_text)
                        else:
                            # For other events, show the content as status if it's text
                            content = response_chunk.content
                            if isinstance(content, str) and content.strip():
                                with status_container.container():
                                    st.info(f"💬 {content}")

                # Clear status when done
                status_container.empty()

                # Update session_id if it was generated
                if hasattr(agent, "run_response") and agent.run_response:
                    if (
                        hasattr(agent.run_response, "session_id")
                        and agent.run_response.session_id
                    ):
                        st.session_state.session_id = agent.run_response.session_id

                # Return the complete response text
                return (
                    response_text
                    or "I processed your request but didn't generate a text response."
                )

            except Exception as stream_error:
                logger.warning(
                    f"Streaming failed, falling back to standard processing: {stream_error}"
                )

                # Fallback to non-streaming
                with response_container.container():
                    st.info("🤔 Processing your request...")

                response = await agent.arun(message=query, session_id=session_id)

                # Update session_id if it was generated
                if hasattr(response, "session_id") and response.session_id:
                    st.session_state.session_id = response.session_id

                with response_container.container():
                    st.markdown(response.content)

                return response.content

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            logger.error("Error processing query '%s': %s", query, e)

            with response_container.container():
                st.error(f"❌ Error: {str(e)}")

            return error_msg

    def display_tool_calls_realtime(self, tool_calls_container, tools):
        """
        Display tool calls in real-time as they execute.

        :param tool_calls_container: Streamlit container for tool calls
        :param tools: List of tool execution objects
        """
        try:
            with tool_calls_container.container():
                for tool_call in tools:
                    tool_name = getattr(tool_call, "tool_name", "Unknown Tool")
                    tool_args = getattr(tool_call, "tool_args", {})
                    content = getattr(tool_call, "result", None) or getattr(
                        tool_call, "content", None
                    )

                    # Get execution time if available
                    execution_time_str = "Running..."
                    if hasattr(tool_call, "metrics") and tool_call.metrics:
                        if (
                            hasattr(tool_call.metrics, "time")
                            and tool_call.metrics.time is not None
                        ):
                            execution_time_str = f"{tool_call.metrics.time:.4f}s"
                    elif content:  # Tool has completed
                        execution_time_str = "Completed"

                    with st.expander(
                        f"🔧 {tool_name.replace('_', ' ').title()} ({execution_time_str})",
                        expanded=False,
                    ):
                        # Display tool arguments
                        if tool_args and tool_args != {"query": None}:
                            st.markdown("**Arguments:**")
                            if isinstance(tool_args, dict) and "query" in tool_args:
                                st.code(tool_args["query"], language="text")
                            try:
                                st.json(tool_args)
                            except Exception:
                                st.write(tool_args)

                        # Display tool results if available
                        if content:
                            st.markdown("**Results:**")
                            try:
                                if isinstance(content, (dict, list)):
                                    st.json(content)
                                else:
                                    st.markdown(str(content))
                            except Exception:
                                st.text(str(content))

        except Exception as e:
            logger.error(f"Error displaying tool calls: {str(e)}")
            with tool_calls_container.container():
                st.warning("⚠️ Error displaying tool execution details")


def main() -> None:
    """
    Main entry point for the Streamlit application.

    Creates and runs the PersonalAgentApp instance.
    """
    app = PersonalAgentApp()
    app.run()


if __name__ == "__main__":
    main()
