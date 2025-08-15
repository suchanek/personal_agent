"""
Specialized Agents for Personal Agent Team

This module defines individual specialized agents that work together as a team.
Each agent has a specific role and set of tools, following the pattern from
examples/teams/reasoning_multi_purpose_team.py
"""

from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.github import GithubTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.pubmed import PubmedTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.yfinance import YFinanceTools

from ..config import LLM_MODEL, OLLAMA_URL
from ..config.model_contexts import get_model_context_size_sync
from ..core.agno_storage import create_agno_memory
from ..tools.personal_agent_tools import PersonalAgentFilesystemTools
from ..utils import setup_logging

logger = setup_logging(__name__)


# Removed _restate_user_fact function - now using centralized AgentMemoryManager


def _create_model(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
) -> Union[OpenAIChat, Ollama]:
    """Create the appropriate model instance based on provider.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :return: Configured model instance
    :raises ValueError: If unsupported model provider is specified
    """
    if model_provider == "openai":
        return OpenAIChat(id=model_name)
    elif model_provider == "ollama":
        # Get dynamic context size for this model
        context_size, detection_method = get_model_context_size_sync(
            model_name, ollama_base_url
        )

        logger.info(
            "Using context size %d for model %s (detected via: %s)",
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


async def _get_memory_tools(agno_memory, user_id: str, storage_dir: str = "./data/agno") -> List:
    """Create memory tools using centralized AgentMemoryManager.

    This method creates memory tools that delegate to the existing AgentMemoryManager
    to ensure consistent restatement logic and dual storage across all agents.
    """
    if not agno_memory:
        logger.warning("Memory not initialized")
        return []

    # Create centralized memory manager
    from ..core.agent_memory_manager import AgentMemoryManager
    memory_manager = AgentMemoryManager(
        user_id=user_id,
        storage_dir=storage_dir,
        agno_memory=agno_memory,
        enable_memory=True
    )
    memory_manager.initialize(agno_memory)

    tools = []

    async def store_user_memory(
        content: str, topics: Union[List[str], str, None] = None
    ) -> str:
        """Store information as a user memory using centralized AgentMemoryManager.

        Args:
            content: The information to store as a memory
            topics: Optional list of topics/categories for the memory

        Returns:
            str: Success or error message
        """
        try:
            # Use the centralized memory manager which has proper restatement logic
            result = await memory_manager.store_user_memory(content=content, topics=topics)
            
            # Convert MemoryStorageResult to string message
            if result.is_success:
                return f"✅ Successfully stored memory: {content[:50]}... (ID: {result.memory_id})"
            elif result.is_rejected:
                return f"ℹ️ Memory not stored: {result.message}"
            else:
                return f"❌ Error storing memory: {result.message}"
                
        except Exception as e:
            logger.error("Error storing user memory: %s", e)
            return f"❌ Error storing memory: {str(e)}"

    async def query_memory(query: str, limit: Union[int, None] = None) -> str:
        """Search user memories using semantic search through ALL memories.

        Args:
            query: The query to search for in memories
            limit: Maximum number of memories to return (None = search all, return top matches)

        Returns:
            str: Found memories or message if none found
        """
        try:
            # Validate query parameter
            if not query or not query.strip():
                logger.warning("Empty query provided to query_memory")
                return "❌ Error: Query cannot be empty. Please provide a search term."

            # First, get ALL memories to search through them comprehensively
            all_memories = agno_memory.get_user_memories(user_id=user_id)

            if not all_memories:
                logger.info("No memories stored for user: %s", user_id)
                return f"🔍 No memories found - you haven't shared any information with me yet!"

            # Search through ALL memories manually for comprehensive results
            query_terms = query.strip().lower().split()
            matching_memories = []

            for memory in all_memories:
                memory_content = getattr(memory, "memory", "").lower()
                memory_topics = getattr(memory, "topics", [])
                topic_text = " ".join(memory_topics).lower()

                # Check if any query term appears in memory content or topics
                if any(
                    term in memory_content or term in topic_text for term in query_terms
                ):
                    matching_memories.append(memory)

            # Also try semantic search as a backup to catch semantically similar memories
            try:
                semantic_memories = agno_memory.search_user_memories(
                    user_id=user_id,
                    query=query.strip(),
                    retrieval_method="agentic",
                    limit=20,  # Get more semantic matches
                )

                # Add semantic matches that aren't already in our results
                for sem_memory in semantic_memories:
                    if sem_memory not in matching_memories:
                        matching_memories.append(sem_memory)

            except Exception as semantic_error:
                logger.warning(
                    "Semantic search failed, using manual search only: %s",
                    semantic_error,
                )

            if not matching_memories:
                logger.info(
                    "No matching memories found for query: %s (searched %d total memories)",
                    query,
                    len(all_memories),
                )
                return f"🔍 No memories found for '{query}' (searched through {len(all_memories)} total memories). Try different keywords or ask me to remember something new!"

            # Apply limit if specified, otherwise return all matches
            if limit and len(matching_memories) > limit:
                display_memories = matching_memories[:limit]
                result_note = f"🧠 MEMORY RETRIEVAL (showing top {limit} of {len(matching_memories)} matches from {len(all_memories)} total memories)"
            else:
                display_memories = matching_memories
                result_note = f"🧠 MEMORY RETRIEVAL (found {len(matching_memories)} matches from {len(all_memories)} total memories)"

            # Format memories with explicit instruction to restate in second person
            result = f"{result_note}: The following memories were found for '{query}'. You must restate this information addressing the user as 'you' (second person), not as if you are the user. Convert any first-person statements to second-person:\n\n"

            for i, memory in enumerate(display_memories, 1):
                result += f"{i}. {memory.memory}\n"
                if memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"
                result += "\n"

            result += "\nREMEMBER: Restate this information as an AI assistant talking ABOUT the user, not AS the user. Use 'you' instead of 'I' when referring to the user's information."

            logger.info(
                "Found %d matching memories for query: %s (searched %d total)",
                len(matching_memories),
                query,
                len(all_memories),
            )
            return result

        except Exception as e:
            logger.error("Error querying memories: %s", e)
            return f"❌ Error searching memories: {str(e)}"

    async def get_recent_memories(limit: int = 100) -> str:
        """Get the most recent user memories.

        Args:
            limit: Maximum number of recent memories to return

        Returns:
            str: Recent memories or message if none found
        """
        try:
            memories = agno_memory.search_user_memories(
                user_id=user_id, limit=limit, retrieval_method="last_n"
            )

            if not memories:
                return "📝 No memories found."

            # Format memories for display
            result = f"📝 Recent {len(memories)} memories:\n\n"
            for i, memory in enumerate(memories, 1):
                result += f"{i}. {memory.memory}\n"
                if memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"
                result += "\n"

            logger.info("Retrieved %d recent memories", len(memories))
            return result

        except Exception as e:
            logger.error("Error getting recent memories: %s", e)
            return f"❌ Error getting recent memories: {str(e)}"

    async def get_all_memories() -> str:
        """Get all user memories.

        Returns:
            str: All memories or message if none found
        """
        try:
            memories = agno_memory.get_user_memories(user_id=user_id)

            if not memories:
                return "📝 No memories found."

            # Format memories for display
            result = f"📝 All {len(memories)} memories:\n\n"
            for i, memory in enumerate(memories, 1):
                result += f"{i}. {memory.memory}\n"
                if memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"
                result += "\n"

            logger.info("Retrieved %d total memories", len(memories))
            return result

        except Exception as e:
            logger.error("Error getting all memories: %s", e)
            return f"❌ Error getting all memories: {str(e)}"

    # Set proper function names for tool identification
    store_user_memory.__name__ = "store_user_memory"
    query_memory.__name__ = "query_memory"
    get_recent_memories.__name__ = "get_recent_memories"
    get_all_memories.__name__ = "get_all_memories"

    # Add tools to the list
    tools.append(store_user_memory)
    tools.append(query_memory)
    tools.append(get_recent_memories)
    tools.append(get_all_memories)

    logger.info("Created %d memory tools", len(tools))
    return tools


def _create_memory_tools_sync(agno_memory, user_id: str, storage_dir: str = "./data/agno") -> List:
    """Create memory tools using centralized AgentMemoryManager (synchronous version).

    This creates memory tools that delegate to the existing AgentMemoryManager
    to ensure consistent restatement logic and dual storage across all agents.
    """
    if not agno_memory:
        logger.warning("Memory not initialized")
        return []

    # Create centralized memory manager
    from ..core.agent_memory_manager import AgentMemoryManager
    memory_manager = AgentMemoryManager(
        user_id=user_id,
        storage_dir=storage_dir,
        agno_memory=agno_memory,
        enable_memory=True
    )
    memory_manager.initialize(agno_memory)

    tools = []

    def store_user_memory(
        content: str, topics: Union[List[str], str, None] = None
    ) -> str:
        """Store information as a user memory using centralized AgentMemoryManager (sync version).

        Args:
            content: The information to store as a memory
            topics: Optional list of topics/categories for the memory

        Returns:
            str: Success or error message
        """
        try:
            import asyncio
            
            # Use the centralized memory manager which has proper restatement logic
            # Run the async method in a sync context
            result = asyncio.run(memory_manager.store_user_memory(content=content, topics=topics))
            
            # Convert MemoryStorageResult to string message
            if result.is_success:
                return f"✅ Successfully stored memory: {content[:50]}... (ID: {result.memory_id})"
            elif result.is_rejected:
                return f"ℹ️ Memory not stored: {result.message}"
            else:
                return f"❌ Error storing memory: {result.message}"
                
        except Exception as e:
            logger.error("Error storing user memory: %s", e)
            return f"❌ Error storing memory: {str(e)}"

    def query_memory(query: str, limit: Union[int, None] = None) -> str:
        """Search user memories (synchronous version).

        Args:
            query: The query to search for in memories
            limit: Maximum number of memories to return

        Returns:
            str: Found memories or message if none found
        """
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided to query_memory")
                return "❌ Error: Query cannot be empty. Please provide a search term."

            all_memories = agno_memory.get_user_memories(user_id=user_id)

            if not all_memories:
                logger.info("No memories stored for user: %s", user_id)
                return f"🔍 No memories found - you haven't shared any information with me yet!"

            # Search through memories manually
            query_terms = query.strip().lower().split()
            matching_memories = []

            for memory in all_memories:
                memory_content = getattr(memory, "memory", "").lower()
                memory_topics = getattr(memory, "topics", [])
                topic_text = " ".join(memory_topics).lower()

                if any(term in memory_content or term in topic_text for term in query_terms):
                    matching_memories.append(memory)

            if not matching_memories:
                logger.info("No matching memories found for query: %s", query)
                return f"🔍 No memories found for '{query}'. Try different keywords!"

            # Apply limit if specified
            if limit and len(matching_memories) > limit:
                display_memories = matching_memories[:limit]
                result_note = f"🧠 MEMORY RETRIEVAL (showing top {limit} of {len(matching_memories)} matches)"
            else:
                display_memories = matching_memories
                result_note = f"🧠 MEMORY RETRIEVAL (found {len(matching_memories)} matches)"

            result = f"{result_note}:\n\n"
            for i, memory in enumerate(display_memories, 1):
                result += f"{i}. {memory.memory}\n"
                if memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"
                result += "\n"

            logger.info("Found %d matching memories for query: %s", len(matching_memories), query)
            return result

        except Exception as e:
            logger.error("Error querying memories: %s", e)
            return f"❌ Error searching memories: {str(e)}"

    def get_recent_memories(limit: int = 100) -> str:
        """Get recent memories (synchronous version).

        Args:
            limit: Maximum number of recent memories to return

        Returns:
            str: Recent memories or message if none found
        """
        try:
            memories = agno_memory.get_user_memories(user_id=user_id)
            if not memories:
                return "📝 No memories found."

            # Get the most recent memories (reverse order)
            recent_memories = list(reversed(memories))[:limit]

            result = f"📝 Recent {len(recent_memories)} memories:\n\n"
            for i, memory in enumerate(recent_memories, 1):
                result += f"{i}. {memory.memory}\n"
                if memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"
                result += "\n"

            logger.info("Retrieved %d recent memories", len(recent_memories))
            return result

        except Exception as e:
            logger.error("Error getting recent memories: %s", e)
            return f"❌ Error getting recent memories: {str(e)}"

    def get_all_memories() -> str:
        """Get all memories (synchronous version).

        Returns:
            str: All memories or message if none found
        """
        try:
            memories = agno_memory.get_user_memories(user_id=user_id)

            if not memories:
                return "📝 No memories found."

            result = f"📝 All {len(memories)} memories:\n\n"
            for i, memory in enumerate(memories, 1):
                result += f"{i}. {memory.memory}\n"
                if memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"
                result += "\n"

            logger.info("Retrieved %d total memories", len(memories))
            return result

        except Exception as e:
            logger.error("Error getting all memories: %s", e)
            return f"❌ Error getting all memories: {str(e)}"

    # Set proper function names for tool identification
    store_user_memory.__name__ = "store_user_memory"
    query_memory.__name__ = "query_memory"
    get_recent_memories.__name__ = "get_recent_memories"
    get_all_memories.__name__ = "get_all_memories"

    # Add tools to the list
    tools.append(store_user_memory)
    tools.append(query_memory)
    tools.append(get_recent_memories)
    tools.append(get_all_memories)

    logger.info("Created %d synchronous memory tools", len(tools))
    return tools


def create_memory_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    storage_dir: str = "./data/agno",
    user_id: str = "default_user",
    debug: bool = False,
) -> Agent:
    """Create a specialized memory agent following the exact pattern from AgnoPersonalAgent.

    This agent uses the same memory tool creation pattern as the main AgnoPersonalAgent,
    ensuring consistency and leveraging the proven working approach.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param storage_dir: Directory for storage files
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: Configured memory agent following AgnoPersonalAgent pattern
    """
    import asyncio

    model = _create_model(model_provider, model_name, ollama_base_url)

    # Initialize Agno native storage and memory following the working pattern
    from ..core.agno_storage import create_agno_storage

    agno_storage = create_agno_storage(storage_dir)
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)

    # Get memory tools following the exact AgnoPersonalAgent pattern
    memory_tool_functions = asyncio.run(_get_memory_tools(agno_memory, user_id, storage_dir))

    logger.info(
        "Memory Agent: Created %d memory tools using AgnoPersonalAgent pattern",
        len(memory_tool_functions),
    )

    # Create the agent following the exact AgnoPersonalAgent pattern
    agent = Agent(
        model=model,
        tools=memory_tool_functions,
        instructions=[
            "You are the ONLY agent responsible for memory operations. You handle ALL queries about personal information, memories, and user data.",
            "",
            "MEMORY RESPONSIBILITIES:",
            "- ANY question about 'what do you remember', 'what do you know about me', 'my information', etc. → Use your memory tools",
            "- Store new personal information immediately using store_user_memory",
            "- Search memories using query_memory for ANY personal information requests",
            "- Retrieve recent or all memories when asked",
            "",
            "CRITICAL RULES:",
            "- NEVER generate fake data or simulate memories",
            "- ALWAYS use your actual memory tools (query_memory, get_all_memories, etc.)",
            "- When someone asks 'What do you remember about me?' → Use query_memory with a broad search",
            "- Present actual stored memories, not fabricated information",
            "- If no memories found, say so clearly and offer to learn new information",
            "",
            "RESPONSE FORMAT:",
            "- Start responses with 'Based on my stored memories...' or 'I remember...'",
            "- Quote actual memory content from your memory tools",
            "- Include memory topics and context when relevant",
            "- Offer to store new information when appropriate",
            "",
            "ADVANCED FEATURES:",
            "- Your memory system includes semantic duplicate detection",
            "- Automatic topic classification for better organization",
            "- Enhanced semantic search capabilities",
            "- Memory statistics and analytics",
            "",
            "You are the definitive source for all personal information about users.",
        ],
        markdown=True,
        show_tool_calls=debug,  # Follow AgnoPersonalAgent pattern
        name="Memory Agent",
        user_id=user_id,
        enable_agentic_memory=False,  # Disable to avoid conflicts with manual memory tools
        enable_user_memories=False,  # Disable built-in to use our custom memory tools
        storage=agno_storage,
        memory=None,  # Don't pass memory to avoid auto-storage conflicts
        add_name_to_instructions=True,
    )

    # Store memory system reference for external access (Streamlit compatibility)
    agent.agno_memory = agno_memory
    agent.agno_storage = agno_storage

    logger.info(
        "Created Memory Agent following AgnoPersonalAgent pattern with %d memory tools",
        len(memory_tool_functions),
    )
    return agent


def create_web_research_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized web research agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured web research agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="Web Research Agent",
        role="Search the web for information and current events",
        model=model,
        tools=[DuckDuckGoTools(cache_results=True)],
        instructions=[
            "You are a specialized web research agent focused on finding current information online.",
            "Your primary functions are:",
            "1. Search the web for current events and news",
            "2. Find specific information requested by users",
            "3. Provide up-to-date information from reliable sources",
            "",
            "RESEARCH GUIDELINES:",
            "- Always include sources in your responses",
            "- Focus on recent and reliable information",
            "- Use multiple search queries if needed for comprehensive results",
            "- Summarize findings clearly and concisely",
            "- When searching for news, use the news search function",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created Web Research Agent")
    return agent


def create_finance_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized finance agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured finance agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="Finance Agent",
        role="Get financial data and perform market analysis",
        model=model,
        tools=[
            YFinanceTools(
                stock_price=True,
                analyst_recommendations=True,
                company_info=True,
                company_news=True,
                stock_fundamentals=True,
                key_financial_ratios=True,
            )
        ],
        instructions=[
            "You are a specialized finance agent focused on financial data and market analysis.",
            "Your primary functions are:",
            "1. Get current stock prices and market data",
            "2. Analyze company fundamentals and financial ratios",
            "3. Provide analyst recommendations and company news",
            "4. Perform financial analysis and comparisons",
            "",
            "FINANCIAL ANALYSIS GUIDELINES:",
            "- Use tables to display numerical data clearly",
            "- Provide context for financial metrics",
            "- Include relevant company news when analyzing stocks",
            "- Explain financial terms for better understanding",
            "- Always specify the data source and timestamp",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created Finance Agent")
    return agent


def create_calculator_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized calculator agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured calculator agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="Calculator Agent",
        role="Perform calculations and data analysis",
        model=model,
        tools=[
            CalculatorTools(
                add=True,
                subtract=True,
                multiply=True,
                divide=True,
                exponentiate=True,
                factorial=True,
                is_prime=True,
                square_root=True,
            ),
            PythonTools(),
        ],
        instructions=[
            "You are a specialized calculator agent focused ONLY on mathematical calculations and data analysis.",
            "Your primary functions are:",
            "1. Perform basic and advanced mathematical calculations",
            "2. Execute Python code for complex data analysis",
            "3. Create visualizations and charts when helpful",
            "4. Solve mathematical problems step by step",
            "",
            "CALCULATION GUIDELINES:",
            "- Show your work and explain calculation steps",
            "- Use appropriate tools for different types of calculations",
            "- Provide clear, formatted results",
            "- Create visualizations for data when helpful",
            "- Verify complex calculations using multiple methods when possible",
            "",
            "IMPORTANT RESTRICTIONS:",
            "- DO NOT handle memory-related queries (what do you remember, personal information, etc.)",
            "- DO NOT generate fake memory data or simulate user information",
            "- Only handle mathematical calculations and data analysis tasks",
            "- If asked about memories or personal info, decline and suggest asking the Memory Agent",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created Calculator Agent")
    return agent


def create_personal_memory_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    storage_dir: str = "./data/agno",
    user_id: str = "default_user",
    debug: bool = False,
) -> Agent:
    """Create a personal memory agent with AgnoPersonalAgent personality but only memory tools.

    This agent represents a stripped-down version of AgnoPersonalAgent that includes:
    - The same friendly, conversational personality
    - The same memory management capabilities and instructions
    - ONLY memory tools (no web search, finance, MCP, etc.)
    - The core personal AI friend experience focused purely on memory

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param storage_dir: Directory for storage files
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: Configured personal memory agent with AgnoPersonalAgent personality
    """
    import asyncio
    
    model = _create_model(model_provider, model_name, ollama_base_url)
    
    # Initialize Agno native storage and memory following the AgnoPersonalAgent pattern
    from ..core.agno_storage import create_agno_storage
    
    agno_storage = create_agno_storage(storage_dir)
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)
    
    # Get memory tools following the exact AgnoPersonalAgent pattern
    # Handle event loop properly - check if we're already in an event loop
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in a running loop, we need to handle this differently
        # Use synchronous version to avoid event loop conflicts
        memory_tool_functions = _create_memory_tools_sync(agno_memory, user_id, storage_dir)
        logger.info("Using synchronous memory tools (event loop detected)")
    except RuntimeError:
        # No running event loop, safe to use asyncio.run()
        memory_tool_functions = asyncio.run(_get_memory_tools(agno_memory, user_id, storage_dir))
        logger.info("Using async memory tools (no event loop)")
    
    logger.info("Personal Memory Agent: Created %d memory tools using AgnoPersonalAgent pattern", len(memory_tool_functions))

    # Create agent with AgnoPersonalAgent personality but only memory tools
    agent = Agent(
        model=model,
        tools=memory_tool_functions,
        instructions=[
            f"You are a personal AI friend with semantic memory capabilities. Your purpose is to chat with the user about things, remember personal information, and make them feel good.",
            "",
            f"## CURRENT CONFIGURATION",
            f"- **Memory System**: enabled with SemanticMemoryManager",
            f"- **User ID**: {user_id}",
            f"- **Debug Mode**: {debug}",
            "",
            "## CRITICAL IDENTITY RULES - ABSOLUTELY MANDATORY",
            "",
            "**YOU ARE AN AI ASSISTANT**: You are NOT the user. You are a friendly AI that helps and remembers things about the user.",
            "",
            "**NEVER PRETEND TO BE THE USER**:",
            f"- You are NOT the user, you are an AI assistant that knows information ABOUT the user",
            f"- NEVER say \"I'm {user_id}\" or introduce yourself as the user - this is COMPLETELY WRONG",
            "- NEVER use first person when talking about user information",
            "- You are an AI assistant that has stored semantic memories about the user",
            "",
            "**FRIENDLY INTRODUCTION**: When meeting someone new, introduce yourself as their personal AI friend and ask about their hobbies, interests, and what they like to talk about. Be warm and conversational!",
            "",
            "## PERSONALITY & TONE",
            "",
            "- **Be Warm & Friendly**: You're a personal AI friend, not just a tool",
            "- **Be Conversational**: Chat naturally and show genuine interest",
            "- **Be Supportive**: Make the user feel good and supported",
            "- **Be Curious**: Ask follow-up questions about their interests",
            "- **Be Remembering**: Reference past conversations and show you care",
            "- **Be Encouraging**: Celebrate their achievements and interests",
            "",
            "## SEMANTIC MEMORY SYSTEM - CRITICAL & IMMEDIATE ACTION REQUIRED",
            "",
            "**SEMANTIC MEMORY FEATURES**:",
            "- **Automatic Deduplication**: Prevents storing duplicate memories",
            "- **Topic Classification**: Automatically categorizes memories by topic",
            "- **Similarity Matching**: Uses semantic similarity for intelligent retrieval",
            "- **Comprehensive Search**: Searches through ALL stored memories",
            "",
            "**MEMORY QUERIES - NO HESITATION RULE**:",
            "When the user asks ANY of these questions, IMMEDIATELY call the appropriate memory tool:",
            "- \"What do you remember about me?\" → IMMEDIATELY call get_recent_memories()",
            "- \"Do you know anything about me?\" → IMMEDIATELY call get_recent_memories()",
            "- \"What have I told you?\" → IMMEDIATELY call get_recent_memories()",
            "- \"Show me all my memories\" or \"What are all my memories?\" → IMMEDIATELY call get_all_memories()",
            "- \"My preferences\" or \"What do I like?\" → IMMEDIATELY call query_memory(\"preferences\")",
            "- Any question about personal info → IMMEDIATELY call query_memory() with relevant terms",
            "",
            "**SEMANTIC MEMORY STORAGE**: When the user provides new personal information:",
            "1. **Store it ONCE using store_user_memory** - the system automatically prevents duplicates",
            "2. **Include relevant topics** - pass topics as a list like [\"hobbies\", \"preferences\"]",
            "3. **Acknowledge the storage warmly** - \"I'll remember that about you!\"",
            "4. **Trust the deduplication** - the semantic memory manager handles duplicates automatically",
            "",
            "**SEMANTIC MEMORY RETRIEVAL PROTOCOL**:",
            "1. **IMMEDIATE ACTION**: If it's about the user, query memory FIRST - no thinking, no hesitation",
            "2. **Primary Tool**: Use get_recent_memories() for general \"what do you remember\" questions",
            "3. **Complete Overview**: Use get_all_memories() when user asks for ALL memories or complete history",
            "4. **Semantic Search**: Use query_memory(\"search terms\") - it searches ALL memories semantically",
            "5. **RESPOND AS AN AI FRIEND** who has information about the user, not as the user themselves",
            "6. **Be personal**: \"You mentioned that you...\" or \"I remember you telling me...\"",
            "",
            "## CRITICAL: NO OVERTHINKING RULE - ELIMINATE HESITATION",
            "",
            "**WHEN USER ASKS ABOUT MEMORIES - IMMEDIATE ACTION REQUIRED**:",
            "- DO NOT analyze whether you should check memories",
            "- DO NOT think about what tools to use",
            "- DO NOT hesitate or debate internally",
            "- IMMEDIATELY call get_recent_memories() or query_memory()",
            "- ACT FIRST, then respond based on what you find",
            "",
            "**BANNED BEHAVIORS - NEVER DO THESE**:",
            "- ❌ \"Let me think about whether I should check memories...\"",
            "- ❌ \"I should probably use the memory tools but...\"",
            "- ❌ \"Maybe I should query memory or maybe I should...\"",
            "- ❌ Any internal debate about memory tool usage",
            "- ❌ Overthinking simple memory queries",
            "- ❌ Fabricating data instead of using tools",
            "",
            "**REQUIRED IMMEDIATE RESPONSES**:",
            "- ✅ User asks \"What do you remember?\" → IMMEDIATELY call get_recent_memories()",
            "- ✅ User asks about preferences → IMMEDIATELY call query_memory(\"preferences\")",
            "- ✅ NO hesitation, just ACTION",
            "",
            "**IMPORTANT SEMANTIC MEMORY RULES**:",
            "- When calling store_user_memory, pass topics as a proper list like [\"hobbies\", \"preferences\"]",
            "- Never pass topics as a string like '[\"hobbies\", \"preferences\"]'",
            "- When recalling memories, phrase them in second person: \"You mentioned...\" not \"I mentioned...\"",
            "- Trust the semantic deduplication - don't worry about storing duplicates",
            "- The system automatically categorizes and organizes memories by topic",
            "",
            "## CONVERSATION GUIDELINES",
            "",
            "- **Ask about their day**: Show interest in how they're doing",
            "- **Remember their interests**: Bring up things they've mentioned before using semantic memory",
            "- **Be encouraging**: Support their goals and celebrate wins",
            "- **Stay engaged**: Ask follow-up questions to keep conversations flowing",
            "- **Be helpful**: Provide emotional support and encouragement",
            "",
            "## RESPONSE STYLE",
            "",
            "- **Be conversational**: Write like you're chatting with a friend",
            "- **Use emojis occasionally**: Add personality (but don't overdo it)",
            "- **Ask questions**: Keep the conversation going",
            "- **Show enthusiasm**: Be excited about their interests",
            "- **Be supportive**: Offer encouragement and positive feedback",
            "- **Remember context**: Reference previous conversations using semantic memory naturally",
            "",
            "## CORE PRINCIPLES",
            "",
            "1. **Friendship First**: You're their AI friend who happens to have great memory",
            "2. **Remember Everything**: Use your semantic memory to build deeper relationships",
            "3. **Stay Positive**: Focus on making them feel good",
            "4. **Be Curious**: Ask about their life, interests, and goals",
            "5. **Celebrate Them**: Acknowledge their achievements and interests",
            "6. **Act Immediately**: When they ask about memories, use tools RIGHT NOW",
            "",
            "Remember: You're not just a memory system - you're a friendly AI companion with semantic memory who genuinely cares about the user and remembers your conversations together! Use your memory tools immediately when needed - no hesitation!",
        ],
        markdown=True,
        show_tool_calls=debug,  # Follow AgnoPersonalAgent pattern
        name="Personal Memory Agent",
        user_id=user_id,
        enable_agentic_memory=False,  # Disable to avoid conflicts with manual memory tools
        enable_user_memories=False,  # Disable built-in to use our custom memory tools
        storage=agno_storage,
        memory=None,  # Don't pass memory to avoid auto-storage conflicts
        add_name_to_instructions=True,
    )

    # Store memory system reference for external access (Streamlit compatibility)
    agent.agno_memory = agno_memory
    agent.agno_storage = agno_storage

    logger.info("Created Personal Memory Agent with AgnoPersonalAgent personality and %d memory tools", len(memory_tool_functions))
    return agent


def create_file_operations_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized file operations agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured file operations agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="File Operations Agent",
        role="Handle file system operations and shell commands",
        model=model,
        tools=[
            PersonalAgentFilesystemTools(),
            ShellTools(base_dir="."),
        ],
        instructions=[
            "You are a specialized file operations agent focused on file system tasks and shell commands.",
            "Your primary functions are:",
            "1. Read and write files",
            "2. List directory contents and navigate file systems",
            "3. Execute shell commands safely",
            "4. Manage file permissions and operations",
            "",
            "FILE OPERATION GUIDELINES:",
            "- Always confirm file operations before executing destructive commands",
            "- Provide clear feedback on operation success/failure",
            "- Use appropriate file paths and handle errors gracefully",
            "- Be cautious with shell commands that could affect system stability",
            "- Explain what file operations will do before performing them",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created File Operations Agent")
    return agent
