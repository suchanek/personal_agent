"""
Web interface package for the Personal AI Agent.

Note: LangChain interface.py and smolagents smol_interface.py have been archived to legacy_frameworks/
Current system uses the Agno framework with agno_main.py for web interfaces.
"""

# Note: Legacy interfaces have been archived
# from .interface import create_app, register_routes  # Archived to legacy_frameworks/langchain/
# from .smol_interface import create_app as create_smol_app  # Archived to legacy_frameworks/smolagents/


# Placeholder functions for compatibility
def create_app():
    """Legacy function - interfaces archived to legacy_frameworks/"""
    raise NotImplementedError("Legacy interfaces archived. Use agno_main.py instead.")


def register_routes():
    """Legacy function - interfaces archived to legacy_frameworks/"""
    raise NotImplementedError("Legacy interfaces archived. Use agno_main.py instead.")


__all__ = ["create_app", "register_routes"]
