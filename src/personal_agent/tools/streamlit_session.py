"""
Streamlit Session State Management
===================================

This module handles all session state initialization and management for the
Personal Agent Streamlit application.

It centralizes session state keys and initialization logic to keep the main
application file clean and maintainable.
"""

import os
import streamlit as st

# Constants for session state keys
SESSION_KEY_MESSAGES = "messages"
SESSION_KEY_AGENT = "agent"
SESSION_KEY_TEAM = "team"
SESSION_KEY_AGENT_MODE = "agent_mode"  # "single" or "team"
SESSION_KEY_DARK_THEME = "dark_theme"
SESSION_KEY_CURRENT_MODEL = "current_model"
SESSION_KEY_CURRENT_OLLAMA_URL = "current_ollama_url"
SESSION_KEY_AVAILABLE_MODELS = "available_models"
SESSION_KEY_SHOW_MEMORY_CONFIRMATION = "show_memory_confirmation"
SESSION_KEY_DEBUG_METRICS = "debug_metrics"
SESSION_KEY_PERFORMANCE_STATS = "performance_stats"
SESSION_KEY_SHOW_DEBUG = "show_debug"
SESSION_KEY_MEMORY_HELPER = "memory_helper"
SESSION_KEY_KNOWLEDGE_HELPER = "knowledge_helper"
SESSION_KEY_RAG_SERVER_LOCATION = "rag_server_location"
SESSION_KEY_DELETE_CONFIRMATIONS = "delete_confirmations"
SESSION_KEY_SHOW_POWER_OFF_CONFIRMATION = "show_power_off_confirmation"


def initialize_session_state(args, EFFECTIVE_OLLAMA_URL, RECREATE_FLAG, DEBUG_FLAG, SINGLE_FLAG, USER_ID):
    """Initialize all session state variables."""
    # Import here to avoid circular imports
    from personal_agent.config import (
        LLM_MODEL,
        REMOTE_LMSTUDIO_URL,
    )
    from personal_agent.tools.streamlit_helpers import (
        StreamlitKnowledgeHelper,
        StreamlitMemoryHelper,
    )
    # These will be imported later when the modules are created
    # from personal_agent.tools.streamlit_agent_manager import (
    #     initialize_agent,
    #     initialize_team,
    # )

    if SESSION_KEY_CURRENT_OLLAMA_URL not in st.session_state:
        # SIMPLIFIED: Just use the appropriate URL based on provider and --remote flag
        provider = os.getenv("PROVIDER", "ollama")
        if provider == "lm-studio":
            if args.remote:
                url = REMOTE_LMSTUDIO_URL
                # Remove /v1 suffix if present since we add it in the model manager
                if url.endswith("/v1"):
                    url = url[:-3]
            else:
                url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234")
            st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = url
        else:
            # For Ollama and other providers, use EFFECTIVE_OLLAMA_URL which already respects --remote
            st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = EFFECTIVE_OLLAMA_URL

    if SESSION_KEY_CURRENT_MODEL not in st.session_state:
        # Use provider-specific default model instead of hardcoded fallback
        provider = os.getenv("PROVIDER", "ollama")
        from personal_agent.config import get_provider_default_model
        default_model = get_provider_default_model(provider)
        st.session_state[SESSION_KEY_CURRENT_MODEL] = default_model

    if SESSION_KEY_DARK_THEME not in st.session_state:
        st.session_state[SESSION_KEY_DARK_THEME] = False

    # Initialize agent mode - use --single flag if provided, otherwise default to team mode
    if SESSION_KEY_AGENT_MODE not in st.session_state:
        st.session_state[SESSION_KEY_AGENT_MODE] = "single" if SINGLE_FLAG else "team"

    # Initialize based on mode - FORCE initialization to ensure REST API can detect systems
    if st.session_state[SESSION_KEY_AGENT_MODE] == "team":
        # Team mode initialization
        if SESSION_KEY_TEAM not in st.session_state:
            with st.spinner("Initializing AI Team..."):
                # Import here to avoid circular imports
                from personal_agent.tools.streamlit_agent_manager import initialize_team
                st.session_state[SESSION_KEY_TEAM] = initialize_team(
                    st.session_state[SESSION_KEY_CURRENT_MODEL],
                    st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL],
                    recreate=RECREATE_FLAG,
                )

        # Create memory helper using the knowledge agent directly
        if SESSION_KEY_MEMORY_HELPER not in st.session_state:
            team = st.session_state[SESSION_KEY_TEAM]
            if team and hasattr(team, "members") and team.members:
                knowledge_agent = team.members[0]  # First member is the knowledge agent
                st.session_state[SESSION_KEY_MEMORY_HELPER] = StreamlitMemoryHelper(
                    knowledge_agent
                )
            else:
                # Fallback: create with team object if available
                if team:
                    st.session_state[SESSION_KEY_MEMORY_HELPER] = StreamlitMemoryHelper(
                        team
                    )

        if SESSION_KEY_KNOWLEDGE_HELPER not in st.session_state:
            # For team mode, pass the knowledge agent (first team member) to the knowledge helper
            team = st.session_state[SESSION_KEY_TEAM]
            if team and hasattr(team, "members") and team.members:
                knowledge_agent = team.members[0]  # First member is the knowledge agent
                st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                    StreamlitKnowledgeHelper(knowledge_agent)
                )
            else:
                # Fallback: create with team object if available
                if team:
                    st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                        StreamlitKnowledgeHelper(team)
                    )
    else:
        # Single agent mode initialization (default)
        if SESSION_KEY_AGENT not in st.session_state:
            with st.spinner("Initializing AI Agent..."):
                # Import here to avoid circular imports
                from personal_agent.tools.streamlit_agent_manager import initialize_agent
                st.session_state[SESSION_KEY_AGENT] = initialize_agent(
                    st.session_state[SESSION_KEY_CURRENT_MODEL],
                    st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL],
                    recreate=RECREATE_FLAG,
                )

        if SESSION_KEY_MEMORY_HELPER not in st.session_state:
            agent = st.session_state[SESSION_KEY_AGENT]
            if agent:
                st.session_state[SESSION_KEY_MEMORY_HELPER] = StreamlitMemoryHelper(
                    agent
                )

        if SESSION_KEY_KNOWLEDGE_HELPER not in st.session_state:
            agent = st.session_state[SESSION_KEY_AGENT]
            if agent:
                st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = StreamlitKnowledgeHelper(
                    agent
                )

    if SESSION_KEY_MESSAGES not in st.session_state:
        st.session_state[SESSION_KEY_MESSAGES] = []

    if SESSION_KEY_SHOW_MEMORY_CONFIRMATION not in st.session_state:
        st.session_state[SESSION_KEY_SHOW_MEMORY_CONFIRMATION] = False

    if SESSION_KEY_DEBUG_METRICS not in st.session_state:
        st.session_state[SESSION_KEY_DEBUG_METRICS] = []

    if SESSION_KEY_PERFORMANCE_STATS not in st.session_state:
        st.session_state[SESSION_KEY_PERFORMANCE_STATS] = {
            "total_requests": 0,
            "total_response_time": 0,
            "average_response_time": 0,
            "total_tokens": 0,
            "average_tokens": 0,
            "fastest_response": float("inf"),
            "slowest_response": 0,
            "tool_calls_count": 0,
            "memory_operations": 0,
        }

    if SESSION_KEY_RAG_SERVER_LOCATION not in st.session_state:
        st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] = "localhost"

    if SESSION_KEY_DELETE_CONFIRMATIONS not in st.session_state:
        st.session_state[SESSION_KEY_DELETE_CONFIRMATIONS] = {}

    # Initialize debug mode based on command line flag
    if SESSION_KEY_SHOW_DEBUG not in st.session_state:
        st.session_state[SESSION_KEY_SHOW_DEBUG] = DEBUG_FLAG
