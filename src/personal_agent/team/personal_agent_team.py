"""
Personal Agent Team Coordinator

This module creates a team of specialized agents that work together,
following the pattern from examples/teams/reasoning_multi_purpose_team.py
"""

import asyncio
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.reasoning import ReasoningTools

from ..config import LLM_MODEL, OLLAMA_URL, AGNO_KNOWLEDGE_DIR, AGNO_STORAGE_DIR
from ..config.model_contexts import get_model_context_size_sync
from ..utils import setup_logging
from .specialized_agents import (
    create_calculator_agent,
    create_file_operations_agent,
    create_finance_agent,
    create_knowledge_memory_agent,
    create_pubmed_agent,
    create_web_research_agent,
    create_writer_agent,
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
                "temperature": 0.3,  # Lower temperature for more consistent function execution
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")


def create_personal_agent_team(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    storage_dir: str = AGNO_STORAGE_DIR,
    user_id: str = "test_user",
    debug: bool = True,
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
    logger.info("Creating Personal Agent Team - Coordinator with Knowledge Agent")

    # Create specialized agents
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

    pubmed_agent = create_pubmed_agent(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        debug=debug,
    )

    writer_agent = create_writer_agent(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        debug=debug,
    )

    # Create knowledge/memory agent using PersonalAgnoAgent
    knowledge_agent = create_knowledge_memory_agent(
        model_provider=model_provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
        storage_dir=storage_dir,
        knowledge_dir=AGNO_KNOWLEDGE_DIR,
        user_id=user_id,
        debug=debug,
    )


    # Create coordinator model
    coordinator_model = _create_coordinator_model(
        model_provider, model_name, ollama_base_url
    )

    # Create team instructions - Coordinator routes to specialized agents
    team_instructions = dedent(
        f"""\
        You are a team coordinator that routes requests to specialized team members.
        
        ## YOUR ROLE
        - Route user requests to the appropriate team member
        - Provide brief context when delegating
        - Coordinate responses from multiple agents when needed
        - Be warm and friendly while ensuring users get expert help
        
        ## TEAM MEMBERS (delegate to these agents):
        - "Knowledge Agent": Personal information, memories, user data, knowledge queries
        - "Web Research Agent": Web searches, current events, news
        - "Finance Agent": Stock prices, market data, financial information
        - "Calculator Agent": Math calculations, data analysis
        - "File Operations Agent": File operations, shell commands
        - "PubMed Research Agent": Biomedical literature, scientific papers, medical research
        - "Writer Agent": Writing, editing, content creation, document formatting
        
        ## ROUTING RULES:
        1. **Memory/Knowledge Tasks**: ALWAYS route to "Knowledge Agent"
           - "What do you remember about me?" → route to "Knowledge Agent"
           - "Do you know my preferences?" → route to "Knowledge Agent"
           - "Remember that I..." → route to "Knowledge Agent"
           - ANY personal information queries → route to "Knowledge Agent"
           - Knowledge base questions → route to "Knowledge Agent"
        
        2. **Math/Calculations**: ALWAYS route to "Calculator Agent"
           - "Calculate 15% of 250" → route to "Calculator Agent"
           - "What's 2+2?" → route to "Calculator Agent"
           - ANY mathematical operation → route to "Calculator Agent"
        
        3. **Web Research**: ALWAYS route to "Web Research Agent"
           - Web searches → route to "Web Research Agent"
           - Current events → route to "Web Research Agent"
           - News queries → route to "Web Research Agent"
        
        4. **Finance**: ALWAYS route to "Finance Agent"
           - Stock prices → route to "Finance Agent"
           - Market data → route to "Finance Agent"
           - Financial information → route to "Finance Agent"
        
        5. **File Operations**: ALWAYS route to "File Operations Agent"
            - File operations → route to "File Operations Agent"
            - Shell commands → route to "File Operations Agent"
        
        6. **PubMed Research**: ALWAYS route to "PubMed Research Agent"
            - Medical research queries → route to "PubMed Research Agent"
            - Scientific literature searches → route to "PubMed Research Agent"
            - Biomedical information → route to "PubMed Research Agent"
            - Research paper searches → route to "PubMed Research Agent"
        
        7. **Writing Tasks**: ALWAYS route to "Writer Agent"
            - "Write an article about..." → route to "Writer Agent"
            - "Edit this text..." → route to "Writer Agent"
            - "Create a document..." → route to "Writer Agent"
            - "Proofread this..." → route to "Writer Agent"
            - ANY writing, editing, or content creation tasks → route to "Writer Agent"
        
        ## COORDINATION PRINCIPLES:
        - Be a helpful coordinator who ensures users get expert help
        - Provide brief, friendly context when routing requests
        - For complex multi-step tasks, coordinate between multiple agents
        - Always route to the most appropriate specialist
        - Don't try to handle specialized tasks yourself - delegate them
        """
    )

    # Create team with route mode for proper delegation
    team = Team(
        name="Personal Agent Team",
        mode="route",  # Enable routing to team members
        model=coordinator_model,
        tools=[],  # Coordinator has no tools - only routes to specialists
        members=[
            knowledge_agent,  # New PersonalAgnoAgent for memory/knowledge
            web_research_agent,
            finance_agent,
            calculator_agent,
            file_operations_agent,
            pubmed_agent,
            writer_agent,
        ],
        instructions=team_instructions,
        markdown=True,
        show_tool_calls=debug,  # Only show tool calls in debug mode
        show_members_responses=False,  # Hide member responses for clean output
    )

    logger.info(
        "Created Personal Agent Team - Coordinator routes to %d specialists including Knowledge Agent",
        len(team.members)
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
            # Get the memory system from the knowledge agent for compatibility
            if hasattr(self.team, 'members') and len(self.team.members) > 0:
                # The first member should be the knowledge agent (PersonalAgnoAgent)
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, 'agno_memory'):
                    self.agno_memory = knowledge_agent.agno_memory
                else:
                    # Fallback: create memory system directly
                    from ..core.agno_storage import create_agno_memory
                    self.agno_memory = create_agno_memory(self.storage_dir, debug_mode=self.debug)
            else:
                # Fallback: create memory system directly
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
