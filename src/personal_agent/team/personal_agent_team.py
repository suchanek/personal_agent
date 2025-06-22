"""
Personal Agent Team Coordinator

This module creates a team of specialized agents that work together,
following the pattern from examples/teams/reasoning_multi_purpose_team.py
"""

import asyncio
from textwrap import dedent
from typing import Any, Dict, List, Optional

from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.reasoning import ReasoningTools

from ..config import LLM_MODEL, OLLAMA_URL
from ..config.model_contexts import get_model_context_size_sync
from ..utils import setup_logging
from .specialized_agents import (
    create_calculator_agent,
    create_file_operations_agent,
    create_finance_agent,
    create_memory_agent,
    create_web_research_agent,
)

logger = setup_logging(__name__)


def _create_coordinator_model(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
) -> Any:
    """Create the model for the team coordinator.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :return: Configured model instance
    """
    if model_provider == "openai":
        return OpenAIChat(id=model_name)
    elif model_provider == "ollama":
        # Get dynamic context size for this model
        context_size, detection_method = get_model_context_size_sync(
            model_name, ollama_base_url
        )

        logger.info(
            "Team coordinator using context size %d for model %s (detected via: %s)",
            context_size,
            model_name,
            detection_method,
        )

        return Ollama(
            id=model_name,
            host=ollama_base_url,
            options={
                "num_ctx": context_size,
                "temperature": 0.7,
            },
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")


def create_personal_agent_team(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    storage_dir: str = "./data/agno",
    user_id: str = "default_user",
    debug: bool = False,
) -> Team:
    """Create a team of specialized personal agents.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param storage_dir: Directory for storage files
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: Configured team instance
    """
    logger.info("Creating Personal Agent Team with specialized agents")

    # Create specialized agents
    memory_agent = create_memory_agent(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        storage_dir=storage_dir,
        user_id=user_id,
        debug=debug,
    )

    web_research_agent = create_web_research_agent(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        debug=debug,
    )

    finance_agent = create_finance_agent(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        debug=debug,
    )

    calculator_agent = create_calculator_agent(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        debug=debug,
    )

    file_operations_agent = create_file_operations_agent(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        debug=debug,
    )

    # Create coordinator model
    coordinator_model = _create_coordinator_model(
        model_provider, model_name, ollama_base_url
    )

    # Create team instructions
    team_instructions = dedent(
        f"""\
        You are a team coordinator. Your job is to:
        1. Analyze the user's request
        2. Delegate to the appropriate team member
        3. Wait for their response
        4. Present the member's response to the user
        
        AVAILABLE TEAM MEMBERS:
        - member_id: "memory-agent" → Memory Agent (personal information, memories, user data)
        - member_id: "web-research-agent" → Web Research Agent (web searches, current events, news)
        - member_id: "finance-agent" → Finance Agent (stock prices, market data, financial information)
        - member_id: "calculator-agent" → Calculator Agent (math calculations, data analysis)
        - member_id: "file-operations-agent" → File Operations Agent (file operations, shell commands)
        
        ROUTING RULES:
        - Memory/personal questions → member_id: "memory-agent"
        - Web searches/news → member_id: "web-research-agent"
        - Financial/stock queries → member_id: "finance-agent"
        - Math/calculations → member_id: "calculator-agent"
        - File operations → member_id: "file-operations-agent"
        
        WORKFLOW:
        1. Use transfer_task_to_member with the exact member_id and clear task description
        2. Wait for the member's response
        3. Present the member's response directly to the user
        4. Do NOT show tool calls or technical details to the user
        """
    )

    # Create the team
    team = Team(
        name="Personal Agent Team",
        model=coordinator_model,
        mode="route",  # Use route mode - tools work, just need better response handling
        tools=[],  # No coordinator tools - let agno handle delegation automatically
        members=[
            memory_agent,
            web_research_agent,
            finance_agent,
            calculator_agent,
            file_operations_agent,
        ],
        instructions=team_instructions,
        markdown=True,
        show_tool_calls=False,  # Hide tool calls to get cleaner responses
        show_members_responses=True,  # Show individual agent responses
        enable_agentic_context=True,  # Enable context sharing between agents
        share_member_interactions=True,  # Share interactions between team members
    )

    logger.info(
        "Created Personal Agent Team with %d specialized agents", len(team.members)
    )
    return team


async def create_personal_agent_team_async(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    storage_dir: str = "./data/agno",
    user_id: str = "default_user",
    debug: bool = False,
) -> Team:
    """Async version of create_personal_agent_team.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param storage_dir: Directory for storage files
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: Configured team instance
    """
    # For now, just call the sync version since agent creation is sync
    return create_personal_agent_team(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        storage_dir=storage_dir,
        user_id=user_id,
        debug=debug,
    )


class PersonalAgentTeamWrapper:
    """Wrapper class to provide a similar interface to AgnoPersonalAgent for the team."""

    def __init__(
        self,
        model_provider: str = "ollama",
        model_name: str = LLM_MODEL,
        ollama_base_url: str = OLLAMA_URL,
        storage_dir: str = "./data/agno",
        user_id: str = "default_user",
        debug: bool = False,
    ):
        """Initialize the team wrapper.

        :param model_provider: LLM provider ('ollama' or 'openai')
        :param model_name: Model name to use
        :param ollama_base_url: Base URL for Ollama API
        :param storage_dir: Directory for storage files
        :param user_id: User identifier for memory operations
        :param debug: Enable debug mode
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.storage_dir = storage_dir
        self.user_id = user_id
        self.debug = debug
        self.team = None
        self._last_response = None
        self.agno_memory = None  # Expose memory system for Streamlit compatibility

    async def initialize(self) -> bool:
        """Initialize the team.

        :return: True if initialization successful
        """
        try:
            # Create the team
            self.team = create_personal_agent_team(
                model_provider=self.model_provider,
                model_name=self.model_name,
                ollama_base_url=self.ollama_base_url,
                storage_dir=self.storage_dir,
                user_id=self.user_id,
                debug=self.debug,
            )
            
            # Initialize memory system for Streamlit compatibility
            from ..core.agno_storage import create_agno_memory
            self.agno_memory = create_agno_memory(self.storage_dir, debug_mode=self.debug)
            
            logger.info("Personal Agent Team initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize Personal Agent Team: %s", e)
            return False

    async def run(self, query: str, stream: bool = False) -> str:
        """Run a query through the team.

        :param query: User query to process
        :param stream: Whether to stream the response (not implemented yet)
        :return: Team response
        """
        if not self.team:
            raise RuntimeError("Team not initialized. Call initialize() first.")

        try:
            # NOTE: Removed direct memory routing patch - now using route mode for proper routing
            # The team coordinator in route mode should preserve original user context
            logger.info("Running query through team coordinator: %s", query)
            
            # Use team coordination with route mode for all queries
            response = await self.team.arun(query, user_id=self.user_id)
            self._last_response = response
            return response.content
        except Exception as e:
            logger.error("Error running team query: %s", e)
            return f"Error processing request: {str(e)}"

    def get_last_tool_calls(self) -> Dict[str, Any]:
        """Get tool call information from the last response.

        :return: Dictionary with tool call details
        """
        if not self._last_response:
            return {
                "tool_calls_count": 0,
                "tool_call_details": [],
                "has_tool_calls": False,
            }

        try:
            # Extract tool calls from team response
            tool_calls = []
            tool_calls_count = 0

            # Check if response has tool calls or member responses
            if (
                hasattr(self._last_response, "messages")
                and self._last_response.messages
            ):
                for message in self._last_response.messages:
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        tool_calls_count += len(message.tool_calls)
                        for tool_call in message.tool_calls:
                            tool_info = {
                                "type": getattr(tool_call, "type", "function"),
                                "function_name": getattr(tool_call, "name", "unknown"),
                                "function_args": getattr(tool_call, "input", {}),
                            }
                            tool_calls.append(tool_info)

            return {
                "tool_calls_count": tool_calls_count,
                "tool_call_details": tool_calls,
                "has_tool_calls": tool_calls_count > 0,
                "response_type": "PersonalAgentTeam",
            }

        except Exception as e:
            logger.error("Error extracting tool calls from team response: %s", e)
            return {
                "tool_calls_count": 0,
                "tool_call_details": [],
                "has_tool_calls": False,
                "error": str(e),
            }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the team configuration.

        :return: Dictionary containing team information
        """
        if not self.team:
            return {
                "framework": "agno_team",
                "initialized": False,
                "error": "Team not initialized",
            }

        member_info = []
        for member in self.team.members:
            member_info.append(
                {
                    "name": getattr(member, "name", "Unknown"),
                    "role": getattr(member, "role", "Unknown"),
                    "tools": len(getattr(member, "tools", [])),
                }
            )

        return {
            "framework": "agno_team",
            "team_name": self.team.name,
            "team_mode": getattr(self.team, "mode", "unknown"),
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "user_id": self.user_id,
            "debug_mode": self.debug,
            "initialized": True,
            "member_count": len(self.team.members),
            "members": member_info,
            "coordinator_tools": len(getattr(self.team, "tools", [])),
        }

    async def cleanup(self) -> None:
        """Clean up team resources.

        :return: None
        """
        try:
            # Team cleanup is handled automatically by agno
            logger.info("Personal Agent Team cleanup completed")
        except Exception as e:
            logger.error("Error during team cleanup: %s", e)
