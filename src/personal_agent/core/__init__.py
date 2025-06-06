"""Core package for Personal Agent."""

# Note: agent.py, smol_agent.py, memory.py, multi_agent_system.py have been archived to legacy_frameworks/
# Current system uses agno_agent.py with the Agno framework

from .mcp_client import SimpleMCPClient

__all__ = [
    "SimpleMCPClient",
]
