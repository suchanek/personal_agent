"""
Personal Agent Team Module

This module provides specialized agents that work together as a team,
following the reasoning_multi_purpose_team.py pattern from agno examples.
"""

from .basic_memory_agent import create_basic_memory_agent
from .personal_agent_team import (
    create_personal_agent_team,
    create_personal_agent_team_async,
    PersonalAgentTeamWrapper,
)
from .reasoning_team import (
    create_ollama_model,
    create_model,
    create_openai_model,
    create_memory_agent,
    create_team,
    cleanup_team,
    main,
    cli_main,
)
from .specialized_agents import (
    create_web_research_agent,
    create_finance_agent,
    create_calculator_agent,
    create_file_operations_agent,
    create_pubmed_agent,
    create_knowledge_memory_agent,
)

__all__ = [
    # Basic memory agent
    "create_basic_memory_agent",
    
    # Personal agent team functions
    "create_personal_agent_team",
    "create_personal_agent_team_async",
    "PersonalAgentTeamWrapper",
    
    # Reasoning team functions
    "create_ollama_model",
    "create_model",
    "create_openai_model",
    "create_memory_agent",
    "create_team",
    "cleanup_team",
    "main",
    "cli_main",
    
    # Specialized agents
    "create_web_research_agent",
    "create_finance_agent",
    "create_calculator_agent",
    "create_file_operations_agent",
    "create_pubmed_agent",
    "create_knowledge_memory_agent",
]
