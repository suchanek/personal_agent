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
    create_personal_memory_agent,
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
    logger.info("Creating Personal Agent Team - Coordinator as Memory Agent")

    # Create specialized agents (NO personal memory agent - coordinator handles memory)
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

    # Create memory system for direct access
    from ..core.agno_storage import create_agno_memory
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)

    # Get memory tools directly for the coordinator
    def get_memory_tools():
        """Get memory tools as native async functions for direct coordinator access."""
        tools = []

        async def store_user_memory(
            content: str, topics: Union[List[str], str, None] = None
        ) -> str:
            """Store information as a user memory."""
            try:
                import json
                from agno.memory.v2.memory import UserMemory

                if topics is None:
                    topics = ["general"]

                if isinstance(topics, str):
                    try:
                        topics = json.loads(topics)
                    except (json.JSONDecodeError, ValueError):
                        topics = [topics]

                if not isinstance(topics, list):
                    topics = [str(topics)]

                memory_obj = UserMemory(memory=content, topics=topics)
                memory_id = agno_memory.add_user_memory(
                    memory=memory_obj, user_id=user_id
                )

                if memory_id == "duplicate-detected-fake-id":
                    return f"✅ Memory already exists: {content[:50]}..."
                elif memory_id is None:
                    return f"❌ Error storing memory: {content[:50]}..."
                else:
                    return f"✅ Successfully stored memory: {content[:50]}... (ID: {memory_id})"

            except Exception as e:
                return f"❌ Error storing memory: {str(e)}"

        async def query_memory(query: str, limit: Union[int, None] = None) -> str:
            """Search user memories using semantic search."""
            try:
                if not query or not query.strip():
                    return "❌ Error: Query cannot be empty."

                all_memories = agno_memory.get_user_memories(user_id=user_id)
                if not all_memories:
                    return "🔍 No memories found - you haven't shared any information with me yet!"

                # Search through memories
                query_terms = query.strip().lower().split()
                matching_memories = []

                for memory in all_memories:
                    memory_content = getattr(memory, "memory", "").lower()
                    memory_topics = getattr(memory, "topics", [])
                    topic_text = " ".join(memory_topics).lower()

                    if any(
                        term in memory_content or term in topic_text
                        for term in query_terms
                    ):
                        matching_memories.append(memory)

                # Also try semantic search
                try:
                    semantic_memories = agno_memory.search_user_memories(
                        user_id=user_id,
                        query=query.strip(),
                        retrieval_method="agentic",
                        limit=20,
                    )
                    for sem_memory in semantic_memories:
                        if sem_memory not in matching_memories:
                            matching_memories.append(sem_memory)
                except Exception:
                    pass

                if not matching_memories:
                    return f"🔍 No memories found for '{query}' (searched through {len(all_memories)} total memories). Try different keywords!"

                if limit and len(matching_memories) > limit:
                    display_memories = matching_memories[:limit]
                    result_note = f"🧠 Found {len(matching_memories)} matches, showing top {limit}:"
                else:
                    display_memories = matching_memories
                    result_note = f"🧠 Found {len(matching_memories)} memories about '{query}':"

                result = f"{result_note}\n\n"
                for i, memory in enumerate(display_memories, 1):
                    result += f"{i}. {memory.memory}\n"
                    if memory.topics:
                        result += f"   Topics: {', '.join(memory.topics)}\n"
                    result += "\n"

                return result

            except Exception as e:
                return f"❌ Error searching memories: {str(e)}"

        async def get_recent_memories(limit: int = 10) -> str:
            """Get the most recent user memories."""
            try:
                memories = agno_memory.search_user_memories(
                    user_id=user_id, limit=limit, retrieval_method="last_n"
                )

                if not memories:
                    return "📝 No memories found - you haven't shared any information with me yet!"

                result = f"📝 Your most recent {len(memories)} memories:\n\n"
                for i, memory in enumerate(memories, 1):
                    result += f"{i}. {memory.memory}\n"
                    if memory.topics:
                        result += f"   Topics: {', '.join(memory.topics)}\n"
                    result += "\n"

                return result

            except Exception as e:
                return f"❌ Error getting recent memories: {str(e)}"

        # Set proper function names
        store_user_memory.__name__ = "store_user_memory"
        query_memory.__name__ = "query_memory"
        get_recent_memories.__name__ = "get_recent_memories"

        tools.extend([store_user_memory, query_memory, get_recent_memories])
        return tools

    # Get memory tools for coordinator (sync call)
    memory_tools = get_memory_tools()

    # Create team instructions - Coordinator IS the personal AI friend
    team_instructions = dedent(
        f"""\
        You are a warm, friendly personal AI assistant with memory capabilities and access to specialized team members.
        
        ## YOUR IDENTITY
        - You ARE the user's personal AI friend
        - You have direct access to memory tools to remember conversations
        - You can delegate specialized tasks to your team members
        - You should be conversational, warm, and genuinely interested in the user
        
        ## YOUR MEMORY TOOLS (use these directly):
        - store_user_memory(content, topics): Store new information about the user
        - query_memory(query): Search through stored memories about the user  
        - get_recent_memories(limit): Get the user's most recent memories
        
        ## YOUR TEAM MEMBERS (delegate specialized tasks):
        - "Web Research Agent": Web searches, current events, news
        - "Finance Agent": Stock prices, market data, financial information
        - "Calculator Agent": Math calculations, data analysis
        - "File Operations Agent": File operations, shell commands
        
        ## BEHAVIOR RULES:
        1. **Memory Operations ONLY**: EXECUTE memory functions directly, don't show code
           - "What do you remember about me?" → CALL get_recent_memories() and return results
           - "Do you know my preferences?" → CALL query_memory("preferences") and return results
           - "Remember that I..." → CALL store_user_memory(content, topics) and confirm
           - NEVER show function names or code tags - EXECUTE the functions
           - NEVER delegate memory tasks to team members
        
        2. **Math/Calculations**: ALWAYS delegate to Calculator Agent
           - "Calculate 15% of 250" → route to "Calculator Agent"
           - "What's 2+2?" → route to "Calculator Agent"
           - ANY mathematical operation → route to "Calculator Agent"
           - DO NOT use memory functions for calculations
        
        3. **Other Specialized Tasks**: Delegate to appropriate team members
           - Web searches → route to "Web Research Agent"
           - Finance queries → route to "Finance Agent"  
           - File operations → route to "File Operations Agent"
        
        4. **Complex Multi-Step Tasks**: Handle memory first, then delegate
           - For "Remember X, then search Y": 
             a) First CALL store_user_memory() to store X
             b) Then delegate search to appropriate team member
           - Always acknowledge memory storage before proceeding
        
        5. **General Conversation**: Respond directly as a friendly AI
           - Be warm, conversational, and supportive
           - Reference memories to personalize responses
           - Ask follow-up questions to show interest
        
        ## CRITICAL DELEGATION RULES:
        - MEMORY tasks: Handle directly with your tools
        - MATH tasks: Always delegate to Calculator Agent
        - WEB tasks: Always delegate to Web Research Agent
        - FINANCE tasks: Always delegate to Finance Agent
        - FILE tasks: Always delegate to File Operations Agent
        - DO NOT use memory functions for non-memory tasks
        """
    )

    # Create team with route mode for proper delegation
    team = Team(
        name="Personal Agent Team",
        mode="route",  # Enable routing to team members
        model=coordinator_model,
        tools=memory_tools,  # Give coordinator direct access to memory tools
        members=[
            web_research_agent,
            finance_agent,
            calculator_agent,
            file_operations_agent,
        ],
        instructions=team_instructions,
        markdown=True,
        show_tool_calls=debug,  # Only show tool calls in debug mode
        show_members_responses=False,  # Hide member responses for clean output
    )

    logger.info(
        "Created Personal Agent Team - Coordinator with memory + %d specialists", 
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
