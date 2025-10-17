"""
System Status Component

Displays system status information including:
- Memory usage statistics
- User information
- System health metrics
"""

import os
from datetime import datetime

import pandas as pd
import psutil
import streamlit as st


def system_status_tab():
    """Render the system status tab."""
    st.title("System Status")

    # Create columns for layout
    col1, col2 = st.columns(2)

    with col1:
        _render_system_info()
        _render_memory_stats()

    with col2:
        _render_user_info()


def _render_system_info():
    """Display system information."""
    st.subheader("System Information")

    # Get system information
    system_info = {
        "CPU Usage": f"{psutil.cpu_percent()}%",
        "Memory Usage": f"{psutil.virtual_memory().percent}%",
        "Disk Usage": f"{psutil.disk_usage('/').percent}%",
        "Python Version": os.popen("python --version").read().strip(),
        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Display as a table
    st.table(pd.DataFrame(list(system_info.items()), columns=["Metric", "Value"]))


def _render_memory_stats():
    """Display memory statistics using the same robust approach as paga_streamlit_agno.py."""
    st.subheader("Memory Statistics")

    try:
        # Try to get memory helper using the same approach as paga_streamlit_agno.py
        from personal_agent.streamlit.utils.agent_utils import get_agent_instance
        from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper

        # Get agent instance
        agent = get_agent_instance()
        if not agent:
            st.warning("⚠️ Agent not available - memory statistics unavailable")
            st.info("Memory system requires an initialized agent instance")
            return

        # Create memory helper
        memory_helper = StreamlitMemoryHelper(agent)

        # Get memory statistics using the helper (same as paga_streamlit_agno.py)
        stats = memory_helper.get_memory_stats()

        if "error" not in stats:
            # Format the statistics for display (same structure as paga_streamlit_agno.py)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Memories", stats.get("total_memories", 0))
            with col2:
                st.metric("Recent (24h)", stats.get("recent_memories_24h", 0))
            with col3:
                avg_length = stats.get("average_memory_length", 0)
                st.metric(
                    "Avg Length", f"{avg_length:.1f} chars" if avg_length else "N/A"
                )

            # Topic distribution (same as paga_streamlit_agno.py)
            topic_dist = stats.get("topic_distribution", {})
            if topic_dist:
                st.subheader("📈 Topic Distribution")
                for topic, count in sorted(
                    topic_dist.items(), key=lambda x: x[1], reverse=True
                ):
                    st.write(f"**{topic.title()}:** {count} memories")
            else:
                st.info("No topic distribution data available")
        else:
            st.error(f"❌ Error getting memory statistics: {stats['error']}")

    except ImportError as e:
        st.error(f"❌ Import error: {str(e)}")
        st.info("Required modules not available for memory statistics")
    except Exception as e:
        st.error(f"❌ Error processing memory statistics: {str(e)}")
        # Show fallback basic info
        st.info("Memory statistics temporarily unavailable")


def _render_user_info():
    """Display user information."""
    st.subheader("User Information")

    try:
        # This would be replaced with actual user data from your system
        # For now, using placeholder data
        from personal_agent.config.user_id_mgr import get_userid

        current_user_id = get_userid()
        user_info = {
            "Current User": current_user_id,
            "User Directory": f"//{current_user_id}",
            "User Config": "Default",
            "Last Login": "Today at 09:15",
        }

        st.table(pd.DataFrame(list(user_info.items()), columns=["Metric", "Value"]))

    except Exception as e:
        st.error(f"Error loading user information: {str(e)}")
