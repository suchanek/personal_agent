"""
Streamlit interface package for Personal AI Agent.

This package provides a Streamlit-based web interface that replaces the Flask
implementation while maintaining all functionality including real-time thought
streaming, memory management, and MCP tools integration.

The Streamlit interface offers:
- Modern, responsive web UI
- Real-time conversation updates
- Interactive controls and settings
- Memory and knowledge base management
- Tool usage visualization
- Agent performance monitoring

Usage:
    Run the Streamlit app:
    ```bash
    streamlit run src/personal_agent/streamlit/main.py
    ```

    Or use the entry point:
    ```bash
    personal-agent-streamlit
    ```
"""

from .app import PersonalAgentApp, main
from .main import main as streamlit_main

__all__ = ["PersonalAgentApp", "main", "streamlit_main"]
