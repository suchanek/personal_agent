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

# Constants for session state keys
SESSION_KEY_DARK_THEME = "dark_theme"

# Set page configuration
st.set_page_config(
    page_title="Personal Agent Management Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_theme():
    """Apply custom CSS for theme switching."""
    is_dark_theme = st.session_state.get(SESSION_KEY_DARK_THEME, False)

    if is_dark_theme:
        # Apply dark theme styling
        css_file = "tools/dark_theme.css"
        try:
            with open(css_file) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            # Fallback: try relative to project root
            try:
                project_root = Path(__file__).parent.parent.parent.parent
                css_file_path = project_root / "tools" / "dark_theme.css"
                with open(css_file_path) as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
            except FileNotFoundError:
                st.warning("Dark theme CSS file not found")
    # Light mode: use default Streamlit styling (no additional CSS needed)


def initialize_session_state():
    """Initialize session state variables."""
    if SESSION_KEY_DARK_THEME not in st.session_state:
        st.session_state[SESSION_KEY_DARK_THEME] = False


def main():
    """Main dashboard application."""
    
    # Initialize session state
    initialize_session_state()
    
    # Apply theme
    apply_custom_theme()

    # Load custom CSS with theme awareness
    load_css(st.session_state.get(SESSION_KEY_DARK_THEME, False))

    # Check dependencies
    check_dependencies()

    # Theme toggle in sidebar
    st.sidebar.header("🎨 Theme")
    dark_mode = st.sidebar.toggle(
        "Dark Mode", value=st.session_state.get(SESSION_KEY_DARK_THEME, False)
    )

    if dark_mode != st.session_state.get(SESSION_KEY_DARK_THEME, False):
        st.session_state[SESSION_KEY_DARK_THEME] = dark_mode
        st.rerun()

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

    # Display current user using the agent status system
    try:
        from personal_agent.streamlit.utils.agent_utils import get_agent_instance, check_agent_status
        
        agent = get_agent_instance()
        if agent:
            status = check_agent_status(agent)
            user_id = status.get("user_id", "Unknown")
            st.sidebar.caption(f"Current User: {user_id}")
        else:
            # Fallback to direct user_id_mgr import if no agent
            try:
                from personal_agent.config.user_id_mgr import get_userid
                st.sidebar.caption(f"Current User: {get_userid()}")
            except ImportError:
                # Final fallback to environment variable
                import os
                user_id = os.getenv("USER_ID", "Unknown")
                st.sidebar.caption(f"Current User: {user_id}")
    except Exception as e:
        # Final fallback to environment variable
        import os
        user_id = os.getenv("USER_ID", "Unknown")
        st.sidebar.caption(f"Current User: {user_id}")
        st.sidebar.caption(f"⚠️ User detection error: {str(e)}")

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
