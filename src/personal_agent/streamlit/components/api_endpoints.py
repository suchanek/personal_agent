"""
API Endpoints Component

Displays REST API endpoints organized by category with their methods, paths, and descriptions.
Similar to LightRAG server display format.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time


def api_endpoints_tab():
    """Render the API endpoints tab."""
    st.title("🛠️ API Endpoints")

    # API Server Status
    _render_api_server_status()

    st.markdown("---")

    # API Endpoints by Category
    _render_api_endpoints()


def _render_api_server_status():
    """Display API server status information."""
    st.subheader("🔗 API Server Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Server URL - get actual port from global state
        try:
            from personal_agent.tools.global_state import get_global_state
            global_state = get_global_state()
            api_port = global_state.get("rest_api_port", 8002)
            api_host = global_state.get("rest_api_host", "localhost")
            api_url = f"http://{api_host}:{api_port}"
        except:
            api_url = "http://localhost:8002"  # fallback
        st.metric("Server URL", api_url)

    with col2:
        # Server Status
        try:
            response = requests.get(f"{api_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                if status == "healthy":
                    st.metric("Status", "🟢 Healthy")
                else:
                    st.metric("Status", "🟡 Unhealthy")
            else:
                st.metric("Status", "🔴 Offline")
        except:
            st.metric("Status", "🔴 Offline")

    with col3:
        # API Version
        try:
            response = requests.get(f"{api_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                version = status_data.get("version", "unknown")
                st.metric("Version", version)
        except:
            st.metric("Version", "unknown")

    # Additional status details
    try:
        response = requests.get(f"{api_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            checks = status_data.get("checks", {})

            st.markdown("**System Checks:**")
            check_cols = st.columns(4)
            with check_cols[0]:
                streamlit_status = "✅" if checks.get("streamlit_connected") else "❌"
                st.write(f"Streamlit: {streamlit_status}")
            with check_cols[1]:
                agent_status = "✅" if checks.get("agent_available") else "❌"
                st.write(f"Agent: {agent_status}")
            with check_cols[2]:
                memory_status = "✅" if checks.get("memory_available") else "❌"
                st.write(f"Memory: {memory_status}")
            with check_cols[3]:
                knowledge_status = "✅" if checks.get("knowledge_available") else "❌"
                st.write(f"Knowledge: {knowledge_status}")
    except:
        st.warning("Unable to retrieve detailed status information")


def _get_api_base_url():
    """Get the actual API base URL from global state."""
    try:
        from personal_agent.tools.global_state import get_global_state
        global_state = get_global_state()
        api_port = global_state.get("rest_api_port", 8002)
        api_host = global_state.get("rest_api_host", "localhost")
        return f"http://{api_host}:{api_port}"
    except:
        return "http://localhost:8002"  # fallback


def _render_api_endpoints():
    """Display API endpoints organized by category."""

    # Memory Endpoints
    st.subheader("🧠 Memory Endpoints")
    memory_endpoints = [
        {
            "Method": "POST",
            "Path": "/api/v1/memory/store",
            "Description": "Store text content as memory",
            "Parameters": "content (required), topics (optional)"
        },
        {
            "Method": "POST",
            "Path": "/api/v1/memory/store-url",
            "Description": "Extract and store URL content as memory",
            "Parameters": "url (required), title (optional), topics (optional)"
        },
        {
            "Method": "GET",
            "Path": "/api/v1/memory/search",
            "Description": "Search existing memories",
            "Parameters": "q (required), limit (optional), similarity_threshold (optional)"
        },
        {
            "Method": "GET",
            "Path": "/api/v1/memory/list",
            "Description": "List all memories",
            "Parameters": "limit (optional)"
        },
        {
            "Method": "DELETE",
            "Path": "/api/v1/memory/{memory_id}",
            "Description": "Delete specific memory",
            "Parameters": "memory_id (path parameter)"
        },
        {
            "Method": "GET",
            "Path": "/api/v1/memory/stats",
            "Description": "Get memory statistics",
            "Parameters": "None"
        }
    ]

    memory_df = pd.DataFrame(memory_endpoints)
    st.dataframe(memory_df, use_container_width=True)

    # Knowledge Endpoints
    st.subheader("📚 Knowledge Endpoints")
    knowledge_endpoints = [
        {
            "Method": "POST",
            "Path": "/api/v1/knowledge/store-text",
            "Description": "Store text in knowledge base",
            "Parameters": "content (required), title (required), file_type (optional)"
        },
        {
            "Method": "POST",
            "Path": "/api/v1/knowledge/store-url",
            "Description": "Extract and store URL content in knowledge base",
            "Parameters": "url (required), title (optional)"
        },
        {
            "Method": "GET",
            "Path": "/api/v1/knowledge/search",
            "Description": "Search knowledge base",
            "Parameters": "q (required), mode (optional), limit (optional)"
        },
        {
            "Method": "GET",
            "Path": "/api/v1/knowledge/status",
            "Description": "Get knowledge base status",
            "Parameters": "None"
        }
    ]

    knowledge_df = pd.DataFrame(knowledge_endpoints)
    st.dataframe(knowledge_df, use_container_width=True)

    # User Endpoints
    st.subheader("👥 User Endpoints")
    user_endpoints = [
        {
            "Method": "GET",
            "Path": "/api/v1/users",
            "Description": "List all users",
            "Parameters": "None"
        },
        {
            "Method": "POST",
            "Path": "/api/v1/users/switch",
            "Description": "Switch to a different user (includes system restart)",
            "Parameters": "user_id (required), restart_containers (optional), restart_system (optional)"
        }
    ]

    user_df = pd.DataFrame(user_endpoints)
    st.dataframe(user_df, use_container_width=True)

    # System Endpoints
    st.subheader("⚙️ System Endpoints")
    system_endpoints = [
        {
            "Method": "GET",
            "Path": "/api/v1/health",
            "Description": "Health check",
            "Parameters": "None"
        },
        {
            "Method": "GET",
            "Path": "/api/v1/status",
            "Description": "System status",
            "Parameters": "None"
        },
        {
            "Method": "GET",
            "Path": "/api/v1/discovery",
            "Description": "API server discovery and endpoint information",
            "Parameters": "None"
        },
        {
            "Method": "POST",
            "Path": "/api/v1/system/restart",
            "Description": "Restart the system",
            "Parameters": "None"
        }
    ]

    system_df = pd.DataFrame(system_endpoints)
    st.dataframe(system_df, use_container_width=True)

    # API Documentation Links
    st.markdown("---")
    st.subheader("📖 API Documentation")

    col1, col2 = st.columns(2)

    with col1:
        # Get actual base URL from global state
        try:
            from personal_agent.tools.global_state import get_global_state
            global_state = get_global_state()
            api_port = global_state.get("rest_api_port", 8002)
            api_host = global_state.get("rest_api_host", "localhost")
            base_url = f"http://{api_host}:{api_port}"
        except:
            base_url = "http://localhost:8002"  # fallback
        st.markdown(f"**Base URL:** `{base_url}`")
        st.markdown("**API Version:** v1")

    with col2:
        if st.button("🔄 Refresh Status", key="refresh_api_status"):
            st.rerun()

    # Usage Examples
    st.markdown("---")
    st.subheader("💡 Usage Examples")

    base_url = _get_api_base_url()

    with st.expander("Store Memory Example"):
        st.code(f"""
# Store memory
curl -X POST {base_url}/api/v1/memory/store \\
  -H "Content-Type: application/json" \\
  -d '{{"content": "I work at Google", "topics": ["work"]}}'
        """, language="bash")

    with st.expander("Search Memories Example"):
        st.code(f"""
# Search memories
curl "{base_url}/api/v1/memory/search?q=work&limit=5"
        """, language="bash")

    with st.expander("Store Knowledge from URL Example"):
        st.code(f"""
# Store knowledge from URL
curl -X POST {base_url}/api/v1/knowledge/store-url \\
  -H "Content-Type: application/json" \\
  -d '{{"url": "https://example.com", "title": "Example"}}'
        """, language="bash")

    with st.expander("Switch User Example"):
        st.code(f"""
# Switch user
curl -X POST {base_url}/api/v1/users/switch \\
  -H "Content-Type: application/json" \\
  -d '{{"user_id": "user123", "restart_containers": true}}'
        """, language="bash")

    with st.expander("API Discovery Example"):
        st.code(f"""
# Get API server information and all endpoints
curl "{base_url}/api/v1/discovery"
        """, language="bash")
