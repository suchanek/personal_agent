"""
Agent information display components for Streamlit Personal AI Agent.

This module handles detailed agent information display including capabilities,
model information, configuration details, and system status.
"""

import logging
from typing import Any, Dict, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class AgentInfo:
    """
    Handles agent information display and status reporting.

    This class manages the display of detailed agent information including
    model details, capabilities, configuration, and performance metrics.
    """

    def __init__(self) -> None:
        """Initialize the agent info component."""
        self.logger = logging.getLogger(__name__)

    def render(self) -> None:
        """
        Render the agent information interface.

        This method displays comprehensive agent information
        when requested by the user.
        """
        if st.session_state.get("show_agent_info", False):
            self.display_agent_info_modal()

    def display_agent_info_modal(self) -> None:
        """
        Display detailed agent information in a modal-style interface.

        Shows comprehensive information about the agent's configuration,
        capabilities, and current status.
        """
        st.markdown("## 🤖 Agent Information")

        if "agent" not in st.session_state or st.session_state.agent is None:
            st.warning("Agent not initialized")
            return

        agent = st.session_state.agent

        # Create tabs for different information categories
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Overview", "Capabilities", "Configuration", "Performance"]
        )

        with tab1:
            self.display_overview(agent)

        with tab2:
            self.display_capabilities(agent)

        with tab3:
            self.display_configuration(agent)

        with tab4:
            self.display_performance_metrics(agent)

        # Close button
        if st.button("✖️ Close", type="secondary"):
            st.session_state.show_agent_info = False
            st.rerun()

    def display_overview(self, agent) -> None:
        """
        Display agent overview information.

        :param agent: The agno agent instance
        """
        st.markdown("### 📋 Overview")

        # Basic information
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Agent Name", getattr(agent, "name", "Personal AI Agent"))
            st.metric("Model", getattr(agent.model, "id", "Unknown"))
            st.metric("Session ID", st.session_state.get("session_id", "None"))

        with col2:
            memory_status = "Active" if agent.memory else "Inactive"
            st.metric("Memory", memory_status)

            knowledge_status = "Connected" if agent.knowledge else "Disconnected"
            st.metric("Knowledge Base", knowledge_status)

            tools_count = len(agent.tools) if agent.tools else 0
            st.metric("Tools Available", tools_count)

        # Description
        if hasattr(agent, "description") and agent.description:
            st.markdown("**Description:**")
            st.info(agent.description)

    def display_capabilities(self, agent) -> None:
        """
        Display agent capabilities and features.

        :param agent: The agno agent instance
        """
        st.markdown("### 🚀 Capabilities")

        capabilities = []

        # Memory capabilities
        if agent.memory:
            capabilities.append(
                {
                    "name": "🧠 Persistent Memory",
                    "status": "✅ Active",
                    "description": "Maintains conversation history and context across sessions",
                }
            )
        else:
            capabilities.append(
                {
                    "name": "🧠 Memory",
                    "status": "❌ Inactive",
                    "description": "Memory system not configured",
                }
            )

        # Knowledge base capabilities
        if agent.knowledge:
            capabilities.append(
                {
                    "name": "📚 Knowledge Base",
                    "status": "✅ Connected",
                    "description": "Access to vector database for information retrieval",
                }
            )
        else:
            capabilities.append(
                {
                    "name": "📚 Knowledge Base",
                    "status": "❌ Disconnected",
                    "description": "No knowledge base configured",
                }
            )

        # Tool capabilities
        if agent.tools:
            capabilities.append(
                {
                    "name": f"🔧 MCP Tools ({len(agent.tools)})",
                    "status": "✅ Available",
                    "description": f"Access to {len(agent.tools)} external tools and services",
                }
            )
        else:
            capabilities.append(
                {
                    "name": "🔧 Tools",
                    "status": "❌ None",
                    "description": "No tools configured",
                }
            )

        # Additional capabilities
        capabilities.extend(
            [
                {
                    "name": "💭 Reasoning",
                    "status": "✅ Enabled",
                    "description": "Advanced reasoning and step-by-step thinking",
                },
                {
                    "name": "📝 Markdown Support",
                    "status": "✅ Enabled",
                    "description": "Rich text formatting in responses",
                },
                {
                    "name": "🔄 Async Processing",
                    "status": "✅ Enabled",
                    "description": "Non-blocking asynchronous operations",
                },
            ]
        )

        # Display capabilities
        for cap in capabilities:
            with st.expander(f"{cap['name']} - {cap['status']}", expanded=False):
                st.write(cap["description"])

    def display_configuration(self, agent) -> None:
        """
        Display agent configuration details.

        :param agent: The agno agent instance
        """
        st.markdown("### ⚙️ Configuration")

        config_data = {}

        # Model configuration
        if hasattr(agent, "model"):
            model_config = {
                "ID": getattr(agent.model, "id", "Unknown"),
                "Provider": getattr(agent.model, "provider", "Unknown"),
                "Temperature": getattr(agent.model, "temperature", "Not set"),
                "Max Tokens": getattr(agent.model, "max_tokens", "Not set"),
            }
            config_data["Model"] = model_config

        # Memory configuration
        if agent.memory:
            memory_config = {
                "Type": type(agent.memory).__name__,
                "Enabled": True,
            }
            config_data["Memory"] = memory_config
        else:
            config_data["Memory"] = {"Enabled": False}

        # Knowledge configuration
        if agent.knowledge:
            knowledge_config = {
                "Type": type(agent.knowledge).__name__,
                "Enabled": True,
            }
            config_data["Knowledge"] = knowledge_config
        else:
            config_data["Knowledge"] = {"Enabled": False}

        # Tools configuration
        if agent.tools:
            tools_config = {
                "Count": len(agent.tools),
                "Types": [type(tool).__name__ for tool in agent.tools],
            }
            config_data["Tools"] = tools_config
        else:
            config_data["Tools"] = {"Count": 0}

        # Session configuration
        session_config = {
            "Debug Mode": st.session_state.get("debug_mode", False),
            "Show Tool Calls": st.session_state.get("show_tool_calls", True),
            "Show Thinking": st.session_state.get("show_thinking", False),
            "Messages Count": len(st.session_state.get("messages", [])),
        }
        config_data["Session"] = session_config

        # Display configuration
        for section, data in config_data.items():
            with st.expander(f"📋 {section}", expanded=False):
                if isinstance(data, dict):
                    for key, value in data.items():
                        st.write(f"**{key}:** {value}")
                else:
                    st.write(str(data))

    def display_performance_metrics(self, agent) -> None:
        """
        Display agent performance metrics and statistics.

        :param agent: The agno agent instance
        """
        st.markdown("### 📊 Performance Metrics")

        # Conversation metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            message_count = len(st.session_state.get("messages", []))
            st.metric("Total Messages", message_count)

        with col2:
            tool_calls = st.session_state.get("tool_calls_history", [])
            st.metric("Tool Calls", len(tool_calls))

        with col3:
            last_response_time = st.session_state.get("last_response_time")
            response_time_display = (
                f"{last_response_time:.2f}s" if last_response_time else "N/A"
            )
            st.metric("Last Response Time", response_time_display)

        # Memory usage (if available)
        if agent.memory:
            st.markdown("#### 🧠 Memory Usage")
            try:
                # This would depend on the specific memory implementation
                st.info("Memory usage details would be displayed here")
            except Exception as e:
                st.error(f"Could not retrieve memory usage: {e}")

        # Tool usage statistics
        if st.session_state.get("tool_calls_history"):
            st.markdown("#### 🔧 Tool Usage Statistics")
            tool_calls = st.session_state.get("tool_calls_history", [])

            if tool_calls:
                # Count tool usage
                tool_counts = {}
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name", "Unknown")
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

                # Display as chart
                if tool_counts:
                    st.bar_chart(tool_counts)
                else:
                    st.info("No tool usage data available")
            else:
                st.info("No tools have been used yet")

        # System resource usage
        st.markdown("#### 💻 System Resources")
        try:
            import psutil

            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            col1, col2 = st.columns(2)
            with col1:
                st.metric("CPU Usage", f"{cpu_percent:.1f}%")
            with col2:
                st.metric("Memory Usage", f"{memory_percent:.1f}%")

        except ImportError:
            st.info("System resource monitoring not available (psutil not installed)")
        except Exception as e:
            st.error(f"Could not retrieve system metrics: {e}")

    def get_agent_summary(self, agent) -> Dict[str, Any]:
        """
        Get a summary of agent information for quick display.

        :param agent: The agno agent instance
        :return: Dictionary containing agent summary information
        """
        summary = {
            "name": getattr(agent, "name", "Personal AI Agent"),
            "model": getattr(agent.model, "id", "Unknown"),
            "memory_enabled": agent.memory is not None,
            "knowledge_enabled": agent.knowledge is not None,
            "tools_count": len(agent.tools) if agent.tools else 0,
            "session_id": st.session_state.get("session_id"),
            "messages_count": len(st.session_state.get("messages", [])),
        }

        return summary
