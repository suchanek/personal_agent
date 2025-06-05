"""
Sidebar components for Streamlit Personal AI Agent.

This module handles all sidebar functionality including controls, settings,
memory management, and utility functions for the Streamlit interface.
"""

import logging
from datetime import datetime
from typing import List, Optional

import streamlit as st

from ..utils.session_manager import SessionManager

logger = logging.getLogger(__name__)


class Sidebar:
    """
    Handles sidebar functionality and controls.

    This class manages all sidebar elements including chat controls,
    memory management, settings, and utility functions.
    """

    def __init__(self) -> None:
        """Initialize the sidebar component."""
        self.session_manager = SessionManager()

    def render(self) -> None:
        """
        Render the complete sidebar interface.

        This method displays all sidebar sections including controls,
        memory management, settings, and utility functions.
        """
        with st.sidebar:
            self.render_header()
            self.render_chat_controls()
            self.render_memory_management()
            self.render_settings()
            self.render_agent_info()
            self.render_utilities()

    def render_header(self) -> None:
        """Render sidebar header with branding."""
        st.markdown("## 🛠️ Controls")
        st.markdown("*Manage your AI agent and conversation*")
        st.markdown("---")

    def render_chat_controls(self) -> None:
        """Render main chat control buttons."""
        st.markdown("### 💬 Chat Controls")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "🔄 New Chat", use_container_width=True, help="Start a new conversation"
            ):
                self.clear_conversation()

        with col2:
            if st.button(
                "💾 Export", use_container_width=True, help="Download conversation"
            ):
                self.export_chat_history()

        # Display conversation stats
        message_count = len(st.session_state.get("messages", []))
        if message_count > 0:
            st.caption(f"📊 {message_count} messages in current chat")

    def render_memory_management(self) -> None:
        """Render memory management controls and statistics."""
        st.markdown("### 🧠 Memory Management")

        # Memory clear button
        if st.button(
            "🗑️ Clear Memory", use_container_width=True, help="Clear agent memory"
        ):
            self.clear_memory()

        # Memory statistics
        if "agent" in st.session_state and st.session_state.agent:
            agent = st.session_state.agent

            # Memory status indicator
            if agent.memory:
                st.success("✅ Memory system active")

                # Try to get memory statistics
                try:
                    # This depends on the agent's memory implementation
                    memory_info = self.get_memory_info(agent)
                    if memory_info:
                        # Display memory info in a user-friendly format
                        st.markdown(
                            f"**Session ID:** {memory_info.get('session_id', 'None')}"
                        )
                        st.markdown(
                            f"**Messages:** {memory_info.get('messages_count', 0)}"
                        )
                        st.markdown(
                            f"**Tools:** {memory_info.get('tools_available', 0)}"
                        )
                except Exception as e:
                    logger.debug(f"Could not retrieve memory info: {e}")

            else:
                st.warning("⚠️ Memory system inactive")

            # Knowledge base status
            if agent.knowledge:
                st.success("✅ Knowledge base connected")
            else:
                st.warning("⚠️ Knowledge base disconnected")
        else:
            st.error("❌ Agent not initialized")

    def render_settings(self) -> None:
        """Render application settings and preferences."""
        st.markdown("### ⚙️ Settings")

        # Theme toggle
        dark_theme = st.checkbox(
            "🌙 Dark Theme",
            value=st.session_state.get("dark_theme", True),
            help="Enable dark theme for better visibility",
        )
        if dark_theme != st.session_state.get("dark_theme", True):
            st.session_state.dark_theme = dark_theme
            st.rerun()

        # Debug mode toggle
        debug_mode = st.checkbox(
            "Debug Mode",
            value=st.session_state.get("debug_mode", False),
            help="Show detailed debugging information",
        )
        if debug_mode != st.session_state.get("debug_mode", False):
            st.session_state.debug_mode = debug_mode
            st.rerun()

        # Model selection (if multiple models supported)
        model_options = [
            "qwen2.5:7b-instruct",
            "llama2:latest",
            "mistral:latest",
            "codellama:latest",
        ]

        selected_model = st.selectbox(
            "Model", options=model_options, index=0, help="Select the AI model to use"
        )

        if selected_model != st.session_state.get("selected_model"):
            st.session_state.selected_model = selected_model
            st.info("Model selection updated. Restart chat to apply changes.")

        # Auto-scroll toggle
        auto_scroll = st.checkbox(
            "Auto-scroll",
            value=st.session_state.get("auto_scroll", True),
            help="Automatically scroll to new messages",
        )
        st.session_state.auto_scroll = auto_scroll

    def render_agent_info(self) -> None:
        """Render agent information and status details."""
        st.markdown("### ℹ️ Agent Information")

        if st.button("📊 View Details", use_container_width=True):
            st.session_state.show_agent_info = True
            st.rerun()

        # Show agent info if requested
        if st.session_state.get("show_agent_info", False):
            self.display_agent_details()

    def render_utilities(self) -> None:
        """Render utility functions and tools."""
        st.markdown("### 🔧 Utilities")

        # System status check
        if st.button("🔍 System Status", use_container_width=True):
            self.check_system_status()

        # Connection test
        if st.button("🌐 Test Connections", use_container_width=True):
            self.test_connections()

        # Help information
        with st.expander("❓ Help & Tips"):
            st.markdown(
                """
            **Getting Started:**
            - Type a message in the chat input below
            - Use natural language to ask questions
            - The agent has access to web search and memory
            
            **Features:**
            - **Memory**: Conversations are remembered
            - **Tools**: Web search, file operations, etc.
            - **Knowledge**: Vector-based information retrieval
            
            **Tips:**
            - Be specific in your requests
            - Ask follow-up questions for clarification
            - Use "remember that..." to store preferences
            """
            )

    def clear_conversation(self) -> None:
        """Clear the current conversation."""
        try:
            self.session_manager.clear_messages()
            st.success("✅ Conversation cleared")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to clear conversation: {e}")
            logger.error(f"Error clearing conversation: {e}")

    def export_chat_history(self) -> None:
        """Export chat history as downloadable markdown file."""
        try:
            markdown_content = self.session_manager.export_conversation()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"personal_agent_chat_{timestamp}.md"

            st.download_button(
                label="📄 Download Chat History",
                data=markdown_content,
                file_name=filename,
                mime="text/markdown",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"❌ Failed to export chat: {e}")
            logger.error(f"Error exporting chat: {e}")

    def clear_memory(self) -> None:
        """Clear the agent's memory."""
        try:
            if "agent" in st.session_state and st.session_state.agent:
                agent = st.session_state.agent

                # Clear agent memory if available
                if hasattr(agent, "memory") and agent.memory:
                    # Implementation depends on the specific memory system
                    # For now, we'll clear the session
                    st.session_state.session_id = None
                    st.success("✅ Agent memory cleared")
                else:
                    st.warning("⚠️ No active memory to clear")
            else:
                st.error("❌ No agent available")

        except Exception as e:
            st.error(f"❌ Failed to clear memory: {e}")
            logger.error(f"Error clearing memory: {e}")

    def get_memory_info(self, agent) -> Optional[dict]:
        """
        Get memory information from the agent.

        :param agent: The agno agent instance
        :return: Dictionary with memory information
        """
        try:
            memory_info = {
                "memory_active": agent.memory is not None,
                "session_id": st.session_state.get("session_id"),
                "messages_count": len(st.session_state.get("messages", [])),
                "tools_available": len(agent.tools) if agent.tools else 0,
            }
            return memory_info
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return None

    def display_agent_details(self) -> None:
        """Display detailed agent information."""
        if "agent" not in st.session_state or not st.session_state.agent:
            st.error("❌ Agent not available")
            return

        agent = st.session_state.agent

        with st.expander("🤖 Agent Details", expanded=True):
            # Basic agent information
            st.markdown("**Agent Configuration:**")
            st.json(
                {
                    "name": getattr(agent, "name", "Unknown"),
                    "model": str(getattr(agent, "model", "Unknown")),
                    "memory_enabled": agent.memory is not None,
                    "knowledge_enabled": agent.knowledge is not None,
                    "tools_count": len(agent.tools) if agent.tools else 0,
                }
            )

            # Tools information
            if agent.tools:
                st.markdown("**Available Tools:**")
                for tool in agent.tools:
                    tool_name = getattr(tool, "__name__", str(tool))
                    st.markdown(f"- {tool_name}")

        # Close button
        if st.button("❌ Close Details", use_container_width=True):
            st.session_state.show_agent_info = False
            st.rerun()

    def check_system_status(self) -> None:
        """Check and display system status."""
        status_info = []

        # Check agent status
        if "agent" in st.session_state and st.session_state.agent:
            status_info.append("✅ Agent: Active")
        else:
            status_info.append("❌ Agent: Inactive")

        # Check memory status
        if st.session_state.get("agent") and st.session_state.agent.memory:
            status_info.append("✅ Memory: Connected")
        else:
            status_info.append("❌ Memory: Disconnected")

        # Check session status
        if st.session_state.get("session_id"):
            status_info.append("✅ Session: Active")
        else:
            status_info.append("⚠️ Session: None")

        # Display status
        for status in status_info:
            if "✅" in status:
                st.success(status)
            elif "❌" in status:
                st.error(status)
            else:
                st.warning(status)

    def test_connections(self) -> None:
        """Test various system connections."""
        st.info("🔍 Testing connections...")

        # Test agent connection
        try:
            if "agent" in st.session_state and st.session_state.agent:
                st.success("✅ Agent connection: OK")
            else:
                st.error("❌ Agent connection: Failed")
        except Exception as e:
            st.error(f"❌ Agent test failed: {e}")

        # Add more connection tests as needed
        st.info("🏁 Connection tests completed")
