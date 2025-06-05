"""
Custom CSS styling for Streamlit Personal AI Agent interface.

This module provides custom styling to match the appearance and user experience
of the original Flask interface while leveraging Streamlit's native components.
"""

from typing import Any, Dict

import streamlit as st


def apply_custom_css() -> None:
    """
    Apply custom CSS styling to match Flask interface appearance.

    This function injects custom CSS to style the Streamlit interface
    with colors, layouts, and visual elements similar to the Flask version.
    """

    custom_css = """
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling - Light mode default */
    .main > div {
        padding-top: 1rem;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Header styling - Light mode */
    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 1px solid var(--border-color, #e2e8f0);
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: var(--text-primary, #1e293b);
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: var(--text-secondary, #64748b);
        font-style: italic;
        margin: 0;
    }

    /* Dark mode detection and variables */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --border-color: #475569;
            --chat-user-bg: #1e293b;
            --chat-assistant-bg: #0f172a;
            --button-bg: #334155;
            --button-hover-bg: #475569;
        }
        
        /* Force dark backgrounds for main content areas */
        .stApp > div:first-child,
        .main .block-container,
        .stChatMessage,
        .metric-container,
        .sidebar-section {
            background-color: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
        }
        
        /* Chat messages in dark mode */
        .stChatMessage[data-testid="chat-message-user"] {
            background-color: var(--chat-user-bg) !important;
            border-left: 4px solid #3b82f6;
            color: var(--text-primary) !important;
        }
        
        .stChatMessage[data-testid="chat-message-assistant"] {
            background-color: var(--chat-assistant-bg) !important;
            border-left: 4px solid #10b981;
            color: var(--text-primary) !important;
        }
        
        /* Buttons in dark mode */
        .stButton > button {
            background-color: var(--button-bg) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }
        
        .stButton > button:hover {
            background-color: var(--button-hover-bg) !important;
        }
        
        /* Input fields in dark mode */
        .stTextInput > div > div > input,
        .stChatInput > div > div > input {
            background-color: var(--bg-tertiary) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }
        
        /* Headers and text in dark mode */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
        }
        
        p, span, div {
            color: var(--text-primary) !important;
        }
        
        /* Sidebar in dark mode */
        .css-1d391kg {
            background-color: var(--bg-primary) !important;
            border-right: 1px solid var(--border-color) !important;
        }
        
        /* Expanders in dark mode */
        .streamlit-expanderHeader {
            background-color: var(--bg-tertiary) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-primary) !important;
        }
        
        /* Metrics in dark mode */
        .metric-container .metric-value {
            color: var(--text-primary) !important;
        }
        
        .metric-container .metric-label {
            color: var(--text-secondary) !important;
        }
    }
    
    /* Light mode variables (default) */
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
        --chat-user-bg: #f1f5f9;
        --chat-assistant-bg: #fefefe;
        --button-bg: #ffffff;
        --button-hover-bg: #f9fafb;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.75rem;
        border: 1px solid var(--border-color);
        background-color: var(--bg-secondary);
        color: var(--text-primary);
    }
    
    .stChatMessage[data-testid="chat-message-user"] {
        background-color: var(--chat-user-bg);
        border-left: 4px solid #3b82f6;
    }
    
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: var(--chat-assistant-bg);
        border-left: 4px solid #10b981;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
        border: 1px solid var(--border-color);
        padding: 0.75rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        background-color: var(--button-bg);
        color: var(--text-primary);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: var(--border-color);
        background-color: var(--button-hover-bg);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Primary button styling */
    .stButton > button[kind="primary"] {
        background-color: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #2563eb;
        border-color: #2563eb;
    }
    
    /* Status indicators */
    .metric-container {
        background-color: var(--bg-secondary);
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid var(--border-color);
        margin: 0.5rem 0;
        color: var(--text-primary);
    }
    
    /* Agent status */
    .status-connected {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-disconnected {
        color: #ef4444;
        font-weight: 600;
    }
    
    /* Tool calls styling */
    .tool-call {
        background-color: var(--bg-tertiary);
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 0.5rem 0;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 0.8rem;
        border-left: 3px solid #3b82f6;
        color: var(--text-primary);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--bg-tertiary);
        border-radius: 0.375rem;
        border: 1px solid var(--border-color);
        color: var(--text-primary);
    }
    
    /* Chat input styling */
    .stChatInput > div > div > input {
        border-radius: 1.5rem;
        border: 2px solid var(--border-color);
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }
    
    .stChatInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Loading spinner custom styling */
    .stSpinner {
        text-align: center;
        color: #3b82f6;
    }
    
    /* Metrics styling */
    .metric-container .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .metric-container .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    /* Sidebar sections */
    .sidebar-section {
        background-color: var(--bg-secondary);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
        color: var(--text-primary);
    }
    
    .sidebar-section h3 {
        margin-top: 0;
        color: var(--text-primary);
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* Success/Error styling */
    .stSuccess {
        background-color: #dcfce7;
        border-color: #16a34a;
        color: #166534;
    }
    
    .stError {
        background-color: #fef2f2;
        border-color: #dc2626;
        color: #991b1b;
    }
    
    .stWarning {
        background-color: #fefce8;
        border-color: #ca8a04;
        color: #92400e;
    }
    
    .stInfo {
        background-color: #eff6ff;
        border-color: #2563eb;
        color: #1e40af;
    }
    
    /* Custom scrollbar */
    .stChatMessageContainer {
        scrollbar-width: thin;
        scrollbar-color: #cbd5e1 #f1f5f9;
    }
    
    .stChatMessageContainer::-webkit-scrollbar {
        width: 6px;
    }
    
    .stChatMessageContainer::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 3px;
    }
    
    .stChatMessageContainer::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 3px;
    }
    
    .stChatMessageContainer::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)


def create_status_badge(status: str, label: str) -> str:
    """
    Create a status badge HTML element.

    :param status: Status text to display
    :param label: Label for the status
    :return: HTML string for the status badge
    """
    is_connected = "connected" in status.lower() or "active" in status.lower()
    color = "#10b981" if is_connected else "#ef4444"

    return f"""
    <div style="
        display: inline-block;
        background-color: {color};
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.25rem 0.25rem 0.25rem 0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    ">
        {label}: {status}
    </div>
    """


def create_metric_card(title: str, value: str, description: str = "") -> str:
    """
    Create a metric card HTML element.

    :param title: Metric title
    :param value: Metric value
    :param description: Optional description
    :return: HTML string for the metric card
    """
    return f"""
    <div class="metric-container">
        <div class="metric-label">{title}</div>
        <div class="metric-value">{value}</div>
        {f'<div style="font-size: 0.75rem; color: #9ca3af; margin-top: 0.25rem;">{description}</div>' if description else ''}
    </div>
    """
