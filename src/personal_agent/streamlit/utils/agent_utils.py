"""
Agent Utilities for Streamlit

Manages AgnoPersonalAgent instances for the Streamlit dashboard.
"""

import asyncio
import streamlit as st
from typing import Optional

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)


@st.cache_resource
def get_agent_instance() -> Optional[AgnoPersonalAgent]:
    """
    Get or create a cached AgnoPersonalAgent instance for Streamlit.
    
    Returns:
        AgnoPersonalAgent instance or None if initialization fails
    """
    try:
        # Create agent with same configuration as CLI
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            user_id=USER_ID,
            debug=False,  # Disable debug for cleaner Streamlit output
            enable_memory=True,
            enable_mcp=True,
            storage_dir=AGNO_STORAGE_DIR,
        )
        
        # Initialize the agent synchronously
        # Note: We need to handle async initialization in Streamlit context
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is already running, we can't use asyncio.run()
            # This is a limitation in Streamlit - we'll need to handle this differently
            st.warning("Agent initialization requires async support. Some features may be limited.")
            return agent
        else:
            # Initialize the agent
            loop.run_until_complete(agent.initialize())
        
        return agent
        
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None


def get_agent_memory(agent: AgnoPersonalAgent):
    """
    Get the memory system from an agent instance.
    
    Args:
        agent: AgnoPersonalAgent instance
        
    Returns:
        Memory system instance or None
    """
    try:
        if hasattr(agent, 'agno_memory') and agent.agno_memory:
            return agent.agno_memory
        else:
            st.warning("Agent memory system not available")
            return None
    except Exception as e:
        st.error(f"Error accessing agent memory: {str(e)}")
        return None


async def initialize_agent_async() -> Optional[AgnoPersonalAgent]:
    """
    Asynchronously initialize an AgnoPersonalAgent instance.
    
    Returns:
        AgnoPersonalAgent instance or None if initialization fails
    """
    try:
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            user_id=USER_ID,
            debug=False,
            enable_memory=True,
            enable_mcp=True,
            storage_dir=AGNO_STORAGE_DIR,
        )
        
        await agent.initialize()
        return agent
        
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None


def check_agent_status(agent: Optional[AgnoPersonalAgent]) -> dict:
    """
    Check the status of an agent instance.
    
    Args:
        agent: AgnoPersonalAgent instance or None
        
    Returns:
        Dictionary with status information
    """
    if agent is None:
        return {
            "initialized": False,
            "memory_available": False,
            "error": "Agent not initialized"
        }
    
    try:
        memory_available = hasattr(agent, 'agno_memory') and agent.agno_memory is not None
        
        return {
            "initialized": True,
            "memory_available": memory_available,
            "user_id": getattr(agent, 'user_id', 'unknown'),
            "model": getattr(agent, 'model_name', 'unknown'),
            "storage_dir": str(getattr(agent, 'storage_dir', 'unknown'))
        }
        
    except Exception as e:
        return {
            "initialized": False,
            "memory_available": False,
            "error": str(e)
        }
