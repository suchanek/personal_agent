"""
Import redirect for streamlit_helpers.

This file redirects imports to the updated version in src/personal_agent/tools/streamlit_helpers.py
which contains the fixed memory deletion functionality.
"""

# Import from the updated location with fixed memory deletion
from personal_agent.tools.streamlit_helpers import StreamlitKnowledgeHelper, StreamlitMemoryHelper

__all__ = ['StreamlitKnowledgeHelper', 'StreamlitMemoryHelper']