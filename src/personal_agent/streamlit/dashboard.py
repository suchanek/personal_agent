#!/usr/bin/env python3
"""
Memory & User Management Dashboard

A comprehensive Streamlit dashboard for managing memories, users, and Docker services
in the Personal Agent system.

Author: Personal Agent Development Team
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.streamlit.components.dashboard_memory_management import (
    memory_management_tab,
)
from personal_agent.streamlit.components.docker_services import docker_services_tab

# Import components
from personal_agent.streamlit.components.system_status import system_status_tab
from personal_agent.streamlit.components.user_management import user_management_tab

# Import utilities
from personal_agent.streamlit.utils.system_utils import check_dependencies, load_css

# Set page configuration
st.set_page_config(
    page_title="Personal Agent Management Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main dashboard application."""

    # Load custom CSS
    load_css()

    # Check dependencies
    check_dependencies()

    # Sidebar navigation
    st.sidebar.title("🧠 PersonalAgent Dashboard")

    # Navigation
    selected_tab = st.sidebar.radio(
        "Navigation",
        ["System Status", "User Management", "Memory Management", "Docker Services"],
    )

    # Display version information
    try:
        from personal_agent import __version__

        st.sidebar.caption(f"Personal Agent v{__version__}")
    except ImportError:
        st.sidebar.caption("Personal Agent")

    # Display current user
    try:
        from personal_agent.config.settings import get_userid

        st.sidebar.caption(f"Current User: {get_userid()}")
    except ImportError:
        st.sidebar.caption("Current User: Unknown")

    # Main content based on selected tab
    if selected_tab == "System Status":
        system_status_tab()
    elif selected_tab == "User Management":
        user_management_tab()
    elif selected_tab == "Memory Management":
        memory_management_tab()
    elif selected_tab == "Docker Services":
        docker_services_tab()


if __name__ == "__main__":
    main()
