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
    streamlit run tools/paga_streamlit_agno.py [--remote] [--recreate] [--single]
    ```

Command Line Arguments:
    --remote: Use remote Ollama URL instead of local.
    --recreate: Recreate the knowledge base and clear all memories.
    --single: Launch in single-agent mode (default is team mode).

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

# sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent import __version__
from personal_agent.config import (
    get_current_user_id,
)
from personal_agent.tools.global_state import update_global_state_from_streamlit
from personal_agent.tools.rest_api import start_rest_api
from personal_agent.tools.streamlit_config import (
    args,
    DEBUG_FLAG,
    EFFECTIVE_OLLAMA_URL,
    RECREATE_FLAG,
    SINGLE_FLAG,
)
from personal_agent.tools.streamlit_session import (
    SESSION_KEY_MESSAGES,
    initialize_session_state,
)
from personal_agent.tools.streamlit_tabs import (
    render_chat_tab,
    render_memory_tab,
    render_knowledge_tab,
    render_sidebar,
)
from personal_agent.tools.streamlit_ui_components import (
    apply_custom_theme,
)

# Apply dashboard-style layout but keep original page title/icon
st.set_page_config(
    page_title=f"Personal Agent Friendly Assistant {__version__}",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

USER_ID = get_current_user_id()


def main():
    """Main function to run the Streamlit app."""
    initialize_session_state(args, EFFECTIVE_OLLAMA_URL, RECREATE_FLAG, DEBUG_FLAG, SINGLE_FLAG, USER_ID)
    apply_custom_theme()

    # Update global state with current session state for REST API access
    update_global_state_from_streamlit(st.session_state)
    
    # Initialize REST API server AFTER session state is fully initialized
    if "rest_api_server" not in st.session_state:
        try:
            # Start the REST API server with access to Streamlit session state
            api_server = start_rest_api(st.session_state, port=8001, host="0.0.0.0")
            st.session_state["rest_api_server"] = api_server
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
    st.sidebar.title(f"🧠 {USER_ID}'s Personal Agent")
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
