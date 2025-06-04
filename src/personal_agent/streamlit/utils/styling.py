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
    
    /* Global styling */
    .main > div {
        padding-top: 1rem;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: #1e293b;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: #64748b;
        font-style: italic;
        margin: 0;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.75rem;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
    }
    
    .stChatMessage[data-testid="chat-message-user"] {
        background-color: #f1f5f9;
        border-left: 4px solid #3b82f6;
    }
    
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #fefefe;
        border-left: 4px solid #10b981;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
        border: 1px solid #d1d5db;
        padding: 0.75rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        background-color: #ffffff;
        color: #374151;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: #9ca3af;
        background-color: #f9fafb;
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
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
        margin: 0.5rem 0;
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
        background-color: #f1f5f9;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 0.5rem 0;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 0.8rem;
        border-left: 3px solid #3b82f6;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 0.375rem;
        border: 1px solid #e2e8f0;
    }
    
    /* Chat input styling */
    .stChatInput > div > div > input {
        border-radius: 1.5rem;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
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
        color: #1f2937;
    }
    
    .metric-container .metric-label {
        font-size: 0.875rem;
        color: #6b7280;
        font-weight: 500;
    }
    
    /* Sidebar sections */
    .sidebar-section {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
    }
    
    .sidebar-section h3 {
        margin-top: 0;
        color: #374151;
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
