"""
Personal Agent Streamlit Web UI (PERSAG)
=======================================

A clean wrapper around the original PAGA app that moves the Chat/Memory/Knowledge
selector into the Streamlit sidebar (radio), removes top-level tabs, and
applies the dashboard-style page configuration (wide layout, expanded sidebar).

This script reuses the full functionality from the original implementation by
dynamically loading it and delegating to its render functions.

Run with:
    streamlit run tools/persag_app.py [--remote] [--recreate] [--debug]
"""

from pathlib import Path
import importlib.util
import sys
from typing import Any, Optional

import streamlit as st

# Page configuration to match the dashboard style
st.set_page_config(
    page_title="Personal AI Friend with Memory",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dynamically load the original application module to reuse all functionality
BASE_DIR = Path(__file__).parent
ORIGINAL_APP_PATH = BASE_DIR / "paga_streamlit_agno.py"

spec = importlib.util.spec_from_file_location("persag_base", str(ORIGINAL_APP_PATH))
persag_base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(persag_base)


def _inline_chat_input(placeholder: Optional[str] = None, *args: Any, **kwargs: Any) -> Optional[str]:
    """
    Inline replacement for st.chat_input to place an input field exactly where it is called,
    using a text input inside a small form with a submit button.

    Returns the submitted string (non-empty) when the form is submitted; otherwise None.
    """
    # Derive a stable key base from provided key or placeholder to avoid collisions
    provided_key = kwargs.get("key")
    key_base = provided_key or f"inline_{abs(hash(placeholder or ''))}"

    form_key = f"{key_base}_form"
    text_key = f"{key_base}_text"
    button_label = kwargs.get("label") or "Submit"

    with st.form(form_key):
        value = st.text_input(placeholder or "", key=text_key)
        submitted = st.form_submit_button(button_label)
    if submitted and value and value.strip():
        return value.strip()
    return None


def main():
    # Initialize session and theme using the original helpers
    persag_base.initialize_session_state()
    persag_base.apply_custom_theme()

    # Header
    st.title("🤖 Personal AI Friend with Memory")
    st.markdown(
        "*A friendly AI agent that remembers your conversations and learns about you*"
    )

    # Sidebar navigation (radio) replacing top-level tabs
    st.sidebar.title("🧠 PersonalAgent")
    selected = st.sidebar.radio(
        "Navigation",
        ["💬 Chat", "🧠 Memory Manager", "📚 Knowledge Base"],
        index=0,
    )

    # Main content routing
    if selected == "💬 Chat":
        # Use original chat input behavior (anchored), so do NOT patch here
        persag_base.render_chat_tab()
    elif selected == "🧠 Memory Manager":
        # Temporarily patch st.chat_input to render inline for memory tab only
        original_chat_input = st.chat_input
        st.chat_input = _inline_chat_input
        try:
            persag_base.render_memory_tab()
        finally:
            # Restore original chat_input to avoid side effects on other sections
            st.chat_input = original_chat_input
    elif selected == "📚 Knowledge Base":
        # Keep original behavior for knowledge tab (its chat_inputs are fine anchored or can be adjusted later)
        persag_base.render_knowledge_tab()

    # Append the original sidebar controls (theme/model/debug/etc.)
    persag_base.render_sidebar()


if __name__ == "__main__":
    main()