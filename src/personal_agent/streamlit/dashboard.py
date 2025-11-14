#!/usr/bin/env python3
"""
Memory & User Management Dashboard

A comprehensive Streamlit dashboard for managing memories and users
in the Personal Agent system.

Author: Personal Agent Development Team
"""

import logging
import os
import sys
import time
from pathlib import Path

import streamlit as st

# Set up logging
logger = logging.getLogger(__name__)

# Add project root to path for imports
from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.streamlit.components.api_endpoints import api_endpoints_tab
from personal_agent.streamlit.components.dashboard_memory_management import (
    memory_management_tab,
)

# Import components
from personal_agent.streamlit.components.system_status import system_status_tab
from personal_agent.streamlit.components.user_management import user_management_tab
from personal_agent.streamlit.utils.agent_utils import get_agent_instance

# Import utilities
from personal_agent.streamlit.utils.system_utils import check_dependencies, load_css

# Import REST API components
from personal_agent.tools.global_state import (
    get_global_state,
    update_global_state_from_streamlit,
)
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
    
    # Check if a user switch just completed and auto-refresh
    if st.session_state.get("user_switch_success", False):
        # Clear the user manager cache to force fresh data
        try:
            from personal_agent.streamlit.utils.user_utils import get_user_manager
            get_user_manager.clear()
        except Exception:
            pass
        # The flag will be cleared when sidebar displays the success message

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
                global_state.set(
                    "agent_mode", "single"
                )  # Assuming single agent mode for dashboard

                # Create and store memory/knowledge helpers
                from personal_agent.tools.streamlit_helpers import (
                    StreamlitKnowledgeHelper,
                    StreamlitMemoryHelper,
                )

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
        # Clear cached user info if a user switch is detected
        if "last_displayed_user" not in st.session_state:
            st.session_state.last_displayed_user = None
            
        current_user_id = None
        
        # Method 1: ALWAYS read current_user.json FIRST for most up-to-date info (this is what gets updated on switch)
        try:
            import json
            from pathlib import Path
            current_user_file = Path.home() / ".persagent" / "current_user.json"
            if current_user_file.exists():
                with open(current_user_file) as f:
                    user_data = json.load(f)
                    current_user_id = user_data.get("user_id", "Unknown")
        except Exception:
            pass
            
        # Method 2: Try direct user_id_mgr import
        if not current_user_id or current_user_id == "Unknown":
            try:
                from personal_agent.config.user_id_mgr import get_userid
                current_user_id = get_userid()
            except ImportError:
                pass
        
        # Method 3: Try agent status system
        if not current_user_id or current_user_id == "Unknown":
            try:
                from personal_agent.streamlit.utils.agent_utils import check_agent_status
                agent = get_agent_instance()
                if agent:
                    status = check_agent_status(agent)
                    current_user_id = status.get("user_id", "Unknown")
            except Exception:
                pass
                
        # Method 4: Final fallback to environment variable
        if not current_user_id or current_user_id == "Unknown":
            import os
            current_user_id = os.getenv("USER_ID", "Unknown")
        
        # Display current user with refresh detection
        if current_user_id != st.session_state.last_displayed_user:
            # User has changed, clear any cached user manager
            try:
                from personal_agent.streamlit.utils.user_utils import get_user_manager
                get_user_manager.clear()
            except Exception:
                pass
            st.session_state.last_displayed_user = current_user_id

        # Get user details to show the display name
        if current_user_id != "Unknown":
            from personal_agent.streamlit.utils.user_utils import get_user_details
            user_details = get_user_details(current_user_id)
            if user_details and user_details.get("user_name"):
                display_name = user_details["user_name"]
                # Display with refresh indicator if user recently switched
                if st.session_state.get('user_switch_success', False):
                    st.sidebar.success(f"✅ **{display_name}** ({current_user_id})")
                    # Clear the success flag after displaying
                    st.session_state.user_switch_success = False
                else:
                    st.sidebar.info(f"**{display_name}** ({current_user_id})")
            else:
                if st.session_state.get('user_switch_success', False):
                    st.sidebar.success(f"✅ **{current_user_id}**")
                    st.session_state.user_switch_success = False
                else:
                    st.sidebar.info(f"**{current_user_id}**")
        else:
            st.sidebar.info(f"**{current_user_id}**")

    except Exception as e:
        # Final fallback to environment variable
        import os

        user_id = os.getenv("USER_ID", "Unknown")
        st.sidebar.info(f"**{user_id}**")
        st.sidebar.caption(f"⚠️ User detection error: {str(e)}")

    # Sidebar navigation
    st.sidebar.title("🧠 PersonalAgent Dashboard")

    # Navigation
    # Initialize selected tab in session state if not exists
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "System Status"

    selected_tab = st.sidebar.radio(
        "Navigation",
        ["System Status", "User Management", "Memory Management", "API Endpoints"],
        index=[
            "System Status",
            "User Management",
            "Memory Management",
            "API Endpoints",
        ].index(st.session_state.selected_tab),
        key="tab_selection",
    )

    # Update session state when tab changes
    if selected_tab != st.session_state.selected_tab:
        st.session_state.selected_tab = selected_tab

    # Display version information
    try:
        from personal_agent import __version__

        st.sidebar.caption(f"Personal Agent v{__version__}")
    except ImportError:
        st.sidebar.caption("Personal Agent")

    # System control buttons at the bottom of the sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("🚨 System Control")
    
    # Add refresh button above power off
    if st.sidebar.button("🔄 Refresh Dashboard", use_container_width=True, help="Refresh current user and system status", key="sidebar_refresh_btn"):
        # Clear all cached data
        try:
            from personal_agent.streamlit.utils.user_utils import get_user_manager
            get_user_manager.clear()
        except Exception:
            pass
        
        # Clear session state flags
        if "last_displayed_user" in st.session_state:
            del st.session_state.last_displayed_user
        if "user_switch_success" in st.session_state:
            del st.session_state.user_switch_success
            
        st.rerun()

    # Power off button
    if st.sidebar.button(
        "🔴 Power Off System",
        key="sidebar_power_off_btn",
        type="primary",
        use_container_width=True,
    ):
        # Show confirmation dialog
        st.session_state[SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION] = True
        st.rerun()

    # Power off confirmation modal - full width
    if st.session_state.get(SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION, False):
        # Clear the main pane and show only the shutdown confirmation
        st.markdown("---")
        st.error("⚠️ **SYSTEM SHUTDOWN CONFIRMATION**")
        st.warning(
            "This will permanently shut down the Personal Agent Management Dashboard."
        )

        # Create wider columns for better button layout
        col_spacer1, col_cancel, col_spacer2, col_confirm, col_spacer3 = st.columns(
            [1, 2, 1, 2, 1]
        )

        with col_cancel:
            if st.button(
                "❌ Cancel Shutdown",
                key="wide_cancel_power_off",
                use_container_width=True,
            ):
                st.session_state[SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION] = False
                st.rerun()

        with col_confirm:
            if st.button(
                "🔴 CONFIRM SHUTDOWN",
                key="wide_confirm_power_off",
                type="primary",
                use_container_width=True,
            ):
                # Clear confirmation state
                st.session_state[SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION] = False

                # Show success notification
                st.toast("🎉 Shutting down system...", icon="🔴")

                # Import required modules for shutdown
                import logging
                import threading
                import time

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
    elif selected_tab == "API Endpoints":
        api_endpoints_tab()


if __name__ == "__main__":
    main()
