"""
Personal Agent Streamlit Web UI (Persag) - Unified Interface
============================================================

This module provides the main web-based user interface for the Personal Agent system,
built using Streamlit. It serves as a unified, comprehensive dashboard for interacting
with both a single AI personal assistant and a multi-agent team, featuring memory,
knowledge management, and advanced conversational capabilities.

The application allows users to dynamically switch between a single-agent mode for
direct interaction and a team-based mode that leverages multiple specialized agents
to accomplish complex tasks.

Key Features
-----------
🤖 **Dual-Mode Conversational AI Interface**
    - Real-time chat with a single agent (AgnoPersonalAgent) or a multi-agent team (PersonalAgentTeam).
    - Dynamic mode switching between single-agent and team-based interaction at runtime.
    - Streaming responses with real-time tool call visualization.
    - Support for multiple LLM models via Ollama.
    - Advanced debugging and performance metrics.

🧠 **Memory Management System**
    - Store, search, and manage personal facts and memories.
    - Semantic similarity search with configurable thresholds.
    - Topic-based categorization and organization.
    - Synchronization between local SQLite and graph-based storage.
    - Comprehensive memory statistics and analytics.

📚 **Knowledge Base Management**
    - Multi-format file upload support (PDF, DOCX, TXT, MD, HTML, etc.).
    - Direct text content ingestion with format selection.
    - Web content extraction from URLs.
    - Dual search capabilities: SQLite/LanceDB and RAG-based.
    - Advanced RAG query modes (naive, hybrid, local, global, mix, bypass).

⚙️ **System Configuration**
    - Dynamic agent/team mode selection.
    - Dynamic model selection and switching.
    - Ollama server configuration (local/remote).
    - RAG server location management.
    - Theme switching (light/dark mode).
    - Debug mode with detailed performance analytics.

🔧 **Advanced Features**
    - Real-time tool call monitoring and visualization.
    - Performance metrics tracking (response times, token usage).
    - Memory-knowledge synchronization status monitoring.
    - Comprehensive error handling and logging.
    - Session state management for a persistent user experience.
    - REST API integration on port 8001 with custom endpoints:
        * Standard endpoints: /api/v1/memory/*, /api/v1/knowledge/*, /api/v1/users/*, /api/v1/chat
        * Custom /api/v1/paga/restart endpoint for system reinitialization

Architecture
-----------
The application is built around three main components:

1. **AgnoPersonalAgent & PersonalAgentTeam**: Core conversational AI systems, supporting both single-agent and multi-agent team configurations.
2. **Streamlit Interface**: A multi-tab web UI with a unified chat interface and dedicated tabs for memory and knowledge management.
3. **Helper Classes**: StreamlitMemoryHelper and StreamlitKnowledgeHelper for abstracting data operations from the UI.

Technical Stack
--------------
- **Frontend**: Streamlit with custom CSS theming
- **AI Systems**: AgnoPersonalAgent and PersonalAgentTeam with tool-calling capabilities
- **Memory Storage**: SQLite with semantic search via embeddings
- **Knowledge Storage**: SQLite/LanceDB + RAG server integration
- **LLM Integration**: Ollama with support for multiple models
- **Visualization**: Altair charts for performance metrics

Usage
-----
Run the application with:
    ```bash
    streamlit run tools/paga_streamlit_agno.py [--remote] [--recreate] [--single] [--provider PROVIDER]
    ```

Command Line Arguments:
    --remote: Use remote Ollama URL instead of local.
    --recreate: Recreate the knowledge base and clear all memories.
    --single: Launch in single-agent mode (default is team mode).
    --provider: Set the LLM provider (ollama, lm-studio, or openai). Overrides PROVIDER environment variable.

Environment Variables:
    - AGNO_STORAGE_DIR: Directory for agent storage.
    - AGNO_KNOWLEDGE_DIR: Directory for knowledge files.
    - LLM_MODEL: Default language model to use.
    - OLLAMA_URL: Local Ollama server URL.
    - REMOTE_OLLAMA_URL: Remote Ollama server URL.
    - USER_ID: Current user identifier.

Session Management
-----------------
The application maintains a persistent session state across interactions, managing:
- Chat message history.
- Agent/Team configuration, mode, and initialization.
- Performance metrics and debug information.
- User preferences (theme, model selection).
- Memory and knowledge helper instances.

Author: Personal Agent Development Team
Version: v0.2.1
Last Revision: 2025-08-17
"""

# pylint: disable=c0413, c0301, c0415, w0718,

import logging
import os
import sys
import time
from pathlib import Path

import streamlit as st

# Set up logging
logger = logging.getLogger(__name__)

# Robust sys.path handling that avoids issues with __file__ being unreliable after Streamlit reloads
# Use a defensive approach: if we can already import personal_agent, don't modify sys.path
try:
    import personal_agent

    # Successfully imported, no need to modify sys.path
    logger.info("personal_agent module found, no sys.path modification needed.")
except ImportError:
    # If we can't import, try to add the src directory
    try:
        _current_file = Path(__file__).resolve()
        # Validate the path to avoid using incorrect __file__ from module reloads
        if "personal_agent" in str(_current_file):
            _src_path = str(_current_file.parent.parent.parent)
            if _src_path not in sys.path:
                sys.path.insert(0, _src_path)
    except Exception:
        # If anything fails, just skip it - the imports below will handle it
        pass

from personal_agent import __version__
from personal_agent.config import get_current_user_id
from personal_agent.config.runtime_config import get_config
from personal_agent.tools.global_state import update_global_state_from_streamlit
from personal_agent.tools.rest_api import start_rest_api
from personal_agent.tools.streamlit_config import (
    DEBUG_FLAG,
    EFFECTIVE_OLLAMA_URL,
    RECREATE_FLAG,
    SINGLE_FLAG,
    args,
)
from personal_agent.tools.streamlit_config import config as streamlit_config
from personal_agent.tools.streamlit_session import (
    SESSION_KEY_MESSAGES,
    initialize_session_state,
)
from personal_agent.tools.streamlit_tabs import (
    render_chat_tab,
    render_knowledge_tab,
    render_memory_tab,
    render_sidebar,
)
from personal_agent.tools.streamlit_ui_components import apply_custom_theme

# Apply dashboard-style layout but keep original page title/icon
st.set_page_config(
    page_title=f"Personal Agent Friendly Assistant {__version__}",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def add_paga_restart_endpoint(api_server):
    """Add a custom restart endpoint for paga_streamlit_agno that re-initializes agent/team.

    This endpoint emulates the functionality of switch-user.py for system restart:
    1. Stops LightRAG services before restart
    2. Clears global state
    3. Re-initializes agent/team with recreate=True
    4. Ensures Docker service consistency
    5. Updates global state with new configuration
    """
    import tempfile
    from datetime import datetime

    from flask import jsonify, request

    @api_server.app.route("/api/v1/paga/restart", methods=["POST"])
    def restart_paga_system():
        """Restart the paga system by re-initializing agent/team (emulates switch-user.py)."""
        try:
            logger.info("PAGA system restart requested via REST API")

            # Parse request data for optional parameters
            data = request.get_json() if request.is_json else {}
            restart_lightrag = data.get("restart_lightrag", True)  # Default to True

            # Create restart marker file to trigger page refresh
            marker_file = os.path.join(
                tempfile.gettempdir(), "personal_agent_restart_marker"
            )
            with open(marker_file, "w") as f:
                f.write(str(time.time()))

            # Import required modules
            from personal_agent.config.user_id_mgr import get_userid
            from personal_agent.core.docker_integration import (
                ensure_docker_user_consistency,
                stop_lightrag_services,
            )
            from personal_agent.tools.global_state import get_global_state

            # Get current user
            current_user = get_userid()
            logger.info(f"Current user: {current_user}")

            # Step 1: Stop LightRAG services BEFORE restart (matches switch-user.py line 163)
            if restart_lightrag:
                logger.info("Stopping LightRAG services before restart...")
                try:
                    success, message = stop_lightrag_services()
                    if success:
                        logger.info("LightRAG services stopped successfully.")
                    else:
                        logger.warning(
                            f"Could not stop all LightRAG services: {message}"
                        )
                except Exception as e:
                    logger.warning(f"Error stopping LightRAG services: {e}")

            # Step 2: Get current configuration from global state (matches switch-user.py line 228-231)
            global_state = get_global_state()
            current_mode = global_state.get(
                "agent_mode", st.session_state.get("agent_mode", "team")
            )
            current_model = global_state.get(
                "llm_model",
                st.session_state.get(
                    "current_model",
                    os.getenv(
                        "LLM_MODEL", "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:q8_0"
                    ),
                ),
            )
            current_ollama_url = global_state.get(
                "ollama_url", st.session_state.get("ollama_url", EFFECTIVE_OLLAMA_URL)
            )

            logger.info(
                f"Restart configuration: mode={current_mode}, model={current_model}"
            )

            # Step 3: Clear global state for clean restart (matches switch-user.py line 234)
            logger.info("Clearing global state for clean restart...")
            global_state.clear()

            # Step 4: Reinitialize agent/team with recreate=True (matches switch-user.py line 240-287)
            success = False
            message = ""
            restart_errors = []

            try:
                # Import required modules
                from personal_agent.tools.streamlit_agent_manager import (
                    create_team_wrapper,
                    initialize_agent,
                    initialize_team,
                )
                from personal_agent.tools.streamlit_helpers import (
                    StreamlitKnowledgeHelper,
                    StreamlitMemoryHelper,
                )

                if current_mode == "team":
                    logger.info("Reinitializing team with recreate=True...")
                    # Clear existing team from session state
                    if "team" in st.session_state:
                        del st.session_state["team"]
                    if "team_wrapper" in st.session_state:
                        del st.session_state["team_wrapper"]

                    # Re-initialize team with recreate=True (matches switch-user.py line 242)
                    # Note: initialize_team() now uses get_config() for all settings
                    team = initialize_team(recreate=True)

                    if team:
                        # Update session state
                        st.session_state["team"] = team
                        team_wrapper = create_team_wrapper(team)
                        st.session_state["team_wrapper"] = team_wrapper

                        # Update global state (matches switch-user.py line 244-247)
                        global_state.set("agent_mode", "team")
                        global_state.set("team", team)
                        global_state.set("llm_model", current_model)
                        global_state.set("ollama_url", current_ollama_url)

                        # Create helpers and update global state (matches switch-user.py line 249-254)
                        if hasattr(team, "members") and team.members:
                            knowledge_agent = team.members[0]
                            memory_helper = StreamlitMemoryHelper(knowledge_agent)
                            knowledge_helper = StreamlitKnowledgeHelper(knowledge_agent)
                        else:
                            memory_helper = StreamlitMemoryHelper(team_wrapper)
                            knowledge_helper = StreamlitKnowledgeHelper(team_wrapper)

                        st.session_state["memory_helper"] = memory_helper
                        st.session_state["knowledge_helper"] = knowledge_helper
                        global_state.set("memory_helper", memory_helper)
                        global_state.set("knowledge_helper", knowledge_helper)

                        success = True
                        message = "Team reinitialized successfully in team mode"
                        logger.info(message)
                    else:
                        message = "Failed to reinitialize team"
                        logger.error(message)
                        restart_errors.append(message)

                else:  # single agent mode
                    logger.info("Reinitializing agent with recreate=True...")
                    # Clear existing agent from session state
                    if "agent" in st.session_state:
                        del st.session_state["agent"]

                    # Re-initialize agent with recreate=True (matches switch-user.py line 267)
                    # Note: initialize_agent() now uses get_config() for all settings
                    agent = initialize_agent(recreate=True)

                    if agent:
                        # Update session state
                        st.session_state["agent"] = agent

                        # Update global state (matches switch-user.py line 269-272)
                        global_state.set("agent_mode", "single")
                        global_state.set("agent", agent)
                        global_state.set("llm_model", current_model)
                        global_state.set("ollama_url", current_ollama_url)

                        # Create helpers and update global state (matches switch-user.py line 274-277)
                        memory_helper = StreamlitMemoryHelper(agent)
                        knowledge_helper = StreamlitKnowledgeHelper(agent)
                        st.session_state["memory_helper"] = memory_helper
                        st.session_state["knowledge_helper"] = knowledge_helper
                        global_state.set("memory_helper", memory_helper)
                        global_state.set("knowledge_helper", knowledge_helper)

                        success = True
                        message = (
                            "Agent reinitialized successfully in single agent mode"
                        )
                        logger.info(message)
                    else:
                        message = "Failed to reinitialize agent"
                        logger.error(message)
                        restart_errors.append(message)

            except Exception as e:
                message = f"Error during reinitialization: {str(e)}"
                logger.error(message)
                restart_errors.append(message)
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")

            # Step 5: Ensure Docker service consistency (matches switch-user.py line 207-216)
            docker_result = None
            if restart_lightrag and success:
                logger.info("Ensuring Docker services are synchronized...")
                try:
                    docker_success, docker_message = ensure_docker_user_consistency(
                        user_id=current_user, auto_fix=True, force_restart=True
                    )
                    docker_result = {
                        "success": docker_success,
                        "message": docker_message,
                    }
                    if docker_success:
                        logger.info("Docker services synchronized successfully.")
                    else:
                        logger.error(f"Docker synchronization failed: {docker_message}")
                        restart_errors.append(f"Docker sync failed: {docker_message}")
                except Exception as e:
                    error_msg = f"Error ensuring Docker consistency: {str(e)}"
                    logger.error(error_msg)
                    docker_result = {"success": False, "message": error_msg}
                    restart_errors.append(error_msg)

            # Build response (matches switch-user.py structure)
            if success:
                response_data = {
                    "success": "True",
                    "message": message,
                    "mode": current_mode,
                    "model": current_model,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": current_user,
                }

                # Include Docker restart results
                if docker_result:
                    response_data["docker_sync"] = docker_result

                # Include any warnings/errors
                if restart_errors:
                    response_data["warnings"] = restart_errors

                return jsonify(response_data)
            else:
                response_data = {
                    "success": "False",
                    "error": message,
                    "errors": restart_errors,
                    "timestamp": datetime.now().isoformat(),
                }

                # Include Docker results even on failure
                if docker_result:
                    response_data["docker_sync"] = docker_result

                return jsonify(response_data), 500

        except Exception as e:
            logger.error(f"Error during PAGA system restart via API: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return (
                jsonify(
                    {
                        "success": "False",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                500,
            )

    logger.info("Added custom /api/v1/paga/restart endpoint")


def check_restart_marker_and_refresh():
    """Check for restart marker file and trigger page refresh if found."""
    import os
    import tempfile
    import time

    marker_file = os.path.join(tempfile.gettempdir(), "personal_agent_restart_marker")
    if os.path.exists(marker_file):
        try:
            with open(marker_file, "r") as f:
                timestamp_str = f.read().strip()
                marker_timestamp = float(timestamp_str)

            # Check if marker is recent (within last 30 seconds)
            current_time = time.time()
            if current_time - marker_timestamp < 30:
                # Remove the marker file
                os.remove(marker_file)
                # Trigger page refresh
                st.rerun()
        except (ValueError, OSError):
            # If there's an issue reading/deleting the file, just continue
            pass


def main():
    """Main function to run the Streamlit app."""
    # Check for restart marker and refresh if needed
    check_restart_marker_and_refresh()

    # Lazy initialization: Create default user if none exists
    userid_file = os.path.expanduser("~/.persagent/env.userid")
    if not os.path.exists(userid_file):
        default_user = os.getenv("USER", "user")
        logger.warning(f"No user configured, creating default: {default_user}")
        os.makedirs(os.path.dirname(userid_file), exist_ok=True)
        with open(userid_file, "w") as f:
            f.write(default_user)
        st.warning(
            f"⚠️ Created default user '{default_user}'. Please run `./first-run-setup.sh` or customize in Profile Management."
        )

    # Get and log current configuration
    config = get_config()
    logger.info(f"🔧 Starting with configuration: {config}")
    logger.info(f"   Provider: {config.provider}")
    logger.info(f"   Model: {config.model}")
    logger.info(f"   User: {config.user_id}")
    logger.info(f"   Mode: {config.agent_mode}")
    logger.info(f"   Base URL: {config.get_effective_base_url()}")

    initialize_session_state(RECREATE_FLAG, SINGLE_FLAG)
    apply_custom_theme()

    # Update global state with current session state for REST API access
    update_global_state_from_streamlit(st.session_state)

    # Initialize REST API server AFTER session state is fully initialized
    if "rest_api_server" not in st.session_state:
        try:
            # Start the REST API server with access to Streamlit session state
            api_server = start_rest_api(st.session_state, port=8001, host="0.0.0.0")
            st.session_state["rest_api_server"] = api_server

            # Add custom restart endpoint for paga_streamlit_agno
            add_paga_restart_endpoint(api_server)

            logger.info("REST API server initialized and started on port 8001")
        except Exception as e:
            logger.error(f"Failed to start REST API server: {e}")
            # Don't fail the entire app if REST API fails to start
            st.session_state["rest_api_server"] = None
    else:
        # Update the REST API server with current session state (in case it changed)
        api_server = st.session_state.get("rest_api_server")
        if api_server:
            api_server.set_streamlit_session(st.session_state)
        # Also update global state on every run
        update_global_state_from_streamlit(st.session_state)

    # Add power button to actual top banner using custom HTML/CSS
    st.markdown(
        """
    <style>
    .power-button-container {
        position: fixed;
        top: 10px;
        right: 20px;
        z-index: 999999;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 50%;
        padding: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .power-button {
        background: #ff4b4b;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .power-button:hover {
        background: #ff3333;
        transform: scale(1.05);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Streamlit UI
    st.title("🤖 Personal AI Friend with Memory")
    st.markdown(
        "*A friendly AI agent that remembers your conversations and learns about you*"
    )

    # Power off confirmation modal - full width
    if st.session_state.get("show_power_off_confirmation", False):
        # Create a prominent confirmation dialog
        st.markdown("---")
        st.error("⚠️ **SYSTEM SHUTDOWN CONFIRMATION**")
        st.warning("This will permanently shut down the Personal Agent application.")

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
                st.session_state["show_power_off_confirmation"] = False
                st.rerun()

        with col_confirm:
            if st.button(
                "🔴 CONFIRM SHUTDOWN",
                key="wide_confirm_power_off",
                type="primary",
                use_container_width=True,
            ):
                # Clear confirmation state
                st.session_state["show_power_off_confirmation"] = False

                # Show success notification
                st.toast("🎉 Shutting down system...", icon="🔴")
                time.sleep(2.0)  # 2 second delay

                # Graceful system shutdown - no browser closing attempts
                import threading

                def graceful_shutdown():
                    """Perform graceful shutdown of the system."""
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

    # Sidebar navigation (replaces top-level tabs)
    # Get user display name for sidebar (call dynamically, not static)
    current_user_id = get_current_user_id()
    try:
        from personal_agent.core.user_manager import UserManager

        user_manager = UserManager()
        user_details = user_manager.get_user_details(current_user_id)
        user_display_name = (
            user_details.get("user_name", current_user_id)
            if user_details
            else current_user_id
        )
    except Exception as e:
        logger.warning(f"Could not get user display name: {e}")
        user_display_name = current_user_id

    st.sidebar.title(f"🧠 {user_display_name}'s Personal Agent")
    selected_tab = st.sidebar.radio(
        "Navigation",
        ["💬 Chat", "🧠 Memory Manager", "📚 Knowledge Base"],
        index=0,
    )

    # Route content based on sidebar selection
    if selected_tab == "💬 Chat":
        render_chat_tab()
    elif selected_tab == "🧠 Memory Manager":
        render_memory_tab()
    elif selected_tab == "📚 Knowledge Base":
        render_knowledge_tab()

    # Append the original sidebar controls (theme/model/debug/etc.)
    render_sidebar()


if __name__ == "__main__":
    main()
