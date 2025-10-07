#!/usr/bin/env python3
"""
Memory & User Management Dashboard

A comprehensive Streamlit dashboard for managing memories, users, and Docker services
in the Personal Agent system.

Author: Personal Agent Development Team
"""

import os
import sys
import time
import logging
from pathlib import Path

import streamlit as st

# Set up logging
logger = logging.getLogger(__name__)

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
from personal_agent.streamlit.components.api_endpoints import api_endpoints_tab

# Import utilities
from personal_agent.streamlit.utils.system_utils import check_dependencies, load_css
from personal_agent.streamlit.utils.agent_utils import get_agent_instance

# Import REST API components
from personal_agent.tools.global_state import update_global_state_from_streamlit, get_global_state
from personal_agent.tools.rest_api import start_rest_api

# Constants for session state keys
SESSION_KEY_DARK_THEME = "dark_theme"
SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION = "show_power_off_confirmation"

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

    # Add power button CSS styling
    power_button_css = """
    <style>
    /* Power button styling */
    .stButton > button[key="sidebar_power_off_btn"] {
        background: #ff4b4b !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[key="sidebar_power_off_btn"]:hover {
        background: #ff3333 !important;
        transform: scale(1.02) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
    }
    
    /* Confirmation dialog styling */
    .stButton > button[key="wide_confirm_power_off"] {
        background: #ff4b4b !important;
        color: white !important;
        font-weight: bold !important;
        border: 2px solid #ff3333 !important;
    }
    
    .stButton > button[key="wide_cancel_power_off"] {
        background: #f0f2f6 !important;
        color: #262730 !important;
        border: 2px solid #d1d5db !important;
    }
    
    .stButton > button[key="wide_cancel_power_off"]:hover {
        background: #e5e7eb !important;
        border-color: #9ca3af !important;
    }
    </style>
    """
    st.markdown(power_button_css, unsafe_allow_html=True)

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

    # Initialize agent and update global state ONCE
    if "agent_initialized" not in st.session_state:
        try:
            # Get cached agent instance (will be created only once due to @st.cache_resource)
            agent = get_agent_instance()
            if agent:
                # Update global state with the agent
                global_state = get_global_state()
                global_state.set("agent", agent)
                global_state.set("agent_mode", "single")  # Assuming single agent mode for dashboard

                # Create and store memory/knowledge helpers
                from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper, StreamlitKnowledgeHelper
                memory_helper = StreamlitMemoryHelper(agent)
                knowledge_helper = StreamlitKnowledgeHelper(agent)
                global_state.set("memory_helper", memory_helper)
                global_state.set("knowledge_helper", knowledge_helper)

                st.session_state["agent_initialized"] = True
        except Exception as e:
            st.error(f"Failed to initialize agent: {str(e)}")
            st.session_state["agent_initialized"] = False

    # Update global state with current session state for REST API access
    update_global_state_from_streamlit(st.session_state)

    # Initialize REST API server AFTER session state is fully initialized
    if "rest_api_server" not in st.session_state:
        try:
            # Start the REST API server with access to Streamlit session state
            api_server = start_rest_api(st.session_state, port=8002, host="0.0.0.0")
            st.session_state["rest_api_server"] = api_server
            # Note: No logging import needed as this is handled in rest_api.py
        except Exception as e:
            # Don't fail the entire app if REST API fails to start
            st.session_state["rest_api_server"] = None
    else:
        # Update the REST API server with current session state (in case it changed)
        api_server = st.session_state.get("rest_api_server")
        if api_server:
            api_server.set_streamlit_session(st.session_state)
        # Also update global state on every run
        update_global_state_from_streamlit(st.session_state)

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

    # Display current user prominently near the top
    st.sidebar.header("👤 Current User")
    try:
        from personal_agent.streamlit.utils.agent_utils import check_agent_status
        from personal_agent.streamlit.utils.user_utils import get_user_details

        agent = get_agent_instance()
        if agent:
            status = check_agent_status(agent)
            user_id = status.get("user_id", "Unknown")
        else:
            # Fallback to direct user_id_mgr import if no agent
            try:
                from personal_agent.config.user_id_mgr import get_userid
                user_id = get_userid()
            except ImportError:
                # Final fallback to environment variable
                import os
                user_id = os.getenv("USER_ID", "Unknown")

        # Get user details to show the display name
        if user_id != "Unknown":
            user_details = get_user_details(user_id)
            if user_details and user_details.get("user_name"):
                display_name = user_details["user_name"]
                st.sidebar.info(f"**{display_name}** ({user_id})")
            else:
                st.sidebar.info(f"**{user_id}**")
        else:
            st.sidebar.info(f"**{user_id}**")

    except Exception as e:
        # Final fallback to environment variable
        import os
        user_id = os.getenv("USER_ID", "Unknown")
        st.sidebar.info(f"**{user_id}**")
        st.sidebar.caption(f"⚠️ User detection error: {str(e)}")

    # Sidebar navigation
    st.sidebar.title("🧠 PersonalAgent Dashboard")

    # Navigation
    selected_tab = st.sidebar.radio(
        "Navigation",
        ["System Status", "User Management", "Memory Management", "Docker Services", "API Endpoints"],
    )

    # Display version information
    try:
        from personal_agent import __version__

        st.sidebar.caption(f"Personal Agent v{__version__}")
    except ImportError:
        st.sidebar.caption("Personal Agent")

    # System control buttons at the bottom of the sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("🚨 System Control")

    # Power off button
    if st.sidebar.button("🔴 Power Off System", key="sidebar_power_off_btn", type="primary", use_container_width=True):
        # Show confirmation dialog
        st.session_state[SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION] = True
        st.rerun()

    # Power off confirmation modal - full width
    if st.session_state.get(SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION, False):
        # Clear the main pane and show only the shutdown confirmation
        st.markdown("---")
        st.error("⚠️ **SYSTEM SHUTDOWN CONFIRMATION**")
        st.warning("This will permanently shut down the Personal Agent Management Dashboard.")
        
        # Create wider columns for better button layout
        col_spacer1, col_cancel, col_spacer2, col_confirm, col_spacer3 = st.columns([1, 2, 1, 2, 1])
        
        with col_cancel:
            if st.button("❌ Cancel Shutdown", key="wide_cancel_power_off", use_container_width=True):
                st.session_state[SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION] = False
                st.rerun()
        
        with col_confirm:
            if st.button("🔴 CONFIRM SHUTDOWN", key="wide_confirm_power_off", type="primary", use_container_width=True):
                # Clear confirmation state
                st.session_state[SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION] = False

                # Show success notification
                st.toast("🎉 Shutting down system...", icon="🔴")
                
                # Import required modules for shutdown
                import time
                import threading
                import logging

                # Set up logging
                logger = logging.getLogger(__name__)

                # Graceful system shutdown - no browser closing attempts
                def graceful_shutdown():
                    """Perform graceful shutdown of the system."""
                    import os  # Import os within the function scope
                    try:
                        # Give time for the UI to show the shutdown message
                        time.sleep(3)

                        # Log shutdown
                        logger.info("🔴 SHUTDOWN: Initiating graceful shutdown...")

                        # Force exit the Python process
                        os._exit(0)

                    except Exception as e:
                        logger.error(f"🔴 SHUTDOWN ERROR: {e}")
                        # Force exit as fallback
                        os._exit(1)

                # Start shutdown in a separate thread
                shutdown_thread = threading.Thread(target=graceful_shutdown)
                shutdown_thread.daemon = True
                shutdown_thread.start()

                # Stop Streamlit execution
                st.stop()
        
        st.markdown("---")
        
        # Don't show any other content when shutdown confirmation is active
        return

    # Main content based on selected tab (only shown when not in shutdown confirmation)
    if selected_tab == "System Status":
        system_status_tab()
    elif selected_tab == "User Management":
        user_management_tab()
    elif selected_tab == "Memory Management":
        memory_management_tab()
    elif selected_tab == "Docker Services":
        docker_services_tab()
    elif selected_tab == "API Endpoints":
        api_endpoints_tab()


if __name__ == "__main__":
    main()
