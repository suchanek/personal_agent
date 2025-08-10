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
    get_userid,
)


@st.cache_resource(ttl=300)  # Cache for 5 minutes, then refresh
def get_agent_instance() -> Optional[AgnoPersonalAgent]:
    """
    Get or create a cached AgnoPersonalAgent instance for Streamlit using the same pattern as paga_streamlit_agno.py.
    
    Returns:
        AgnoPersonalAgent instance or None if initialization fails
    """
    try:
        # Import the create_agno_agent function (same as paga_streamlit_agno.py)
        from personal_agent.core.agno_agent import create_agno_agent
        
        # Import knowledge directory setting
        from personal_agent.config import AGNO_KNOWLEDGE_DIR
        
        # Use asyncio.run to properly initialize the agent (same pattern as paga_streamlit_agno.py)
        agent = asyncio.run(create_agno_agent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            user_id=get_userid(),
            debug=False,  # Disable debug for cleaner Streamlit output
            enable_memory=True,
            enable_mcp=True,
            storage_dir=AGNO_STORAGE_DIR,
            knowledge_dir=AGNO_KNOWLEDGE_DIR,
            recreate=False,
        ))
        
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
            user_id=get_userid(),
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
    Check the status of an agent instance, accounting for lazy initialization.
    
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
        # Check if agent is initialized (accounting for lazy initialization)
        is_initialized = getattr(agent, '_initialized', False)
        
        # For lazy initialization, trigger initialization if needed to get accurate status
        if not is_initialized and hasattr(agent, '_ensure_initialized'):
            try:
                # Trigger lazy initialization to get accurate memory status
                asyncio.run(agent._ensure_initialized())
                is_initialized = getattr(agent, '_initialized', False)
            except Exception as init_e:
                return {
                    "initialized": False,
                    "memory_available": False,
                    "error": f"Initialization failed: {str(init_e)}"
                }
        
        # Check memory availability after ensuring initialization
        memory_available = hasattr(agent, 'agno_memory') and agent.agno_memory is not None
        
        return {
            "initialized": is_initialized,
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
