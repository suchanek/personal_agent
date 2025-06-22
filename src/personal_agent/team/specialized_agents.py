"""
Specialized Agents for Personal Agent Team

This module defines individual specialized agents that work together as a team.
Each agent has a specific role and set of tools, following the pattern from
examples/teams/reasoning_multi_purpose_team.py
"""

import asyncio
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.yfinance import YFinanceTools

from ..config import LLM_MODEL, OLLAMA_URL
from ..config.model_contexts import get_model_context_size_sync
from ..core.agno_storage import create_agno_memory
from ..tools.personal_agent_tools import PersonalAgentFilesystemTools
from ..utils import setup_logging

logger = setup_logging(__name__)


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


async def _create_memory_tools(
    storage_dir: str, user_id: str, debug: bool = False
) -> List:
    """Create memory tools for the memory agent.

    :param storage_dir: Directory for storage files
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: List of memory tool functions
    """
    # Create memory system
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)
    
    if not agno_memory:
        logger.error("Failed to create memory system")
        return []

    tools = []

    async def store_user_memory(
        content: str, topics: Union[List[str], str, None] = None
    ) -> str:
        """Store information as a user memory.

        Args:
            content: The information to store as a memory
            topics: Optional list of topics/categories for the memory

        Returns:
            str: Success or error message
        """
        try:
            import json
            from agno.memory.v2.memory import UserMemory

            if topics is None:
                topics = ["general"]

            # Handle case where topics comes in as string representation of list
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                    logger.debug("Converted topics from string to list: %s", topics)
                except (json.JSONDecodeError, ValueError):
                    topics = [topics]
                    logger.debug("Treating topics string as single topic: %s", topics)

            # Ensure topics is a list
            if not isinstance(topics, list):
                topics = [str(topics)]

            memory_obj = UserMemory(memory=content, topics=topics)
            memory_id = agno_memory.add_user_memory(memory=memory_obj, user_id=user_id)

            if memory_id == "duplicate-detected-fake-id":
                logger.info("Memory already exists (duplicate detected): %s...", content[:50])
                return f"✅ Memory already exists: {content[:50]}..."
            elif memory_id is None:
                logger.warning("Memory storage failed unexpectedly: %s...", content[:50])
                return f"❌ Error storing memory: {content[:50]}..."
            else:
                logger.info("Stored user memory: %s... (ID: %s)", content[:50], memory_id)
                return f"✅ Successfully stored memory: {content[:50]}... (ID: {memory_id})"

        except Exception as e:
            logger.error("Error storing user memory: %s", e)
            return f"❌ Error storing memory: {str(e)}"

    async def query_memory(query: str, limit: Union[int, None] = None) -> str:
        """Search user memories using semantic search.

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

            # Get all memories first
            all_memories = agno_memory.get_user_memories(user_id=user_id)

            if not all_memories:
                logger.info("No memories stored for user: %s", user_id)
                return "🔍 No memories found - you haven't shared any information with me yet!"

            # Search through all memories manually for comprehensive results
            query_terms = query.strip().lower().split()
            matching_memories = []

            for memory in all_memories:
                memory_content = getattr(memory, "memory", "").lower()
                memory_topics = getattr(memory, "topics", [])
                topic_text = " ".join(memory_topics).lower()

                # Check if any query term appears in memory content or topics
                if any(term in memory_content or term in topic_text for term in query_terms):
                    matching_memories.append(memory)

            # Also try semantic search using direct vector similarity (no inference)
            try:
                semantic_memories = agno_memory.search_user_memories(
                    user_id=user_id,
                    query=query.strip(),
                    retrieval_method="semantic",  # Use semantic instead of agentic to avoid inference
                    limit=20,
                )

                # Add semantic matches that aren't already in results
                for sem_memory in semantic_memories:
                    if sem_memory not in matching_memories:
                        matching_memories.append(sem_memory)

            except Exception as semantic_error:
                logger.warning("Semantic search failed, using manual search only: %s", semantic_error)

            if not matching_memories:
                logger.info("No matching memories found for query: %s", query)
                return f"🔍 No memories found for '{query}' (searched through {len(all_memories)} total memories). Try different keywords!"

            # Apply limit if specified
            if limit and len(matching_memories) > limit:
                display_memories = matching_memories[:limit]
                result_note = f"🧠 MEMORY RETRIEVAL (showing top {limit} of {len(matching_memories)} matches from {len(all_memories)} total memories)"
            else:
                display_memories = matching_memories
                result_note = f"🧠 MEMORY RETRIEVAL (found {len(matching_memories)} matches from {len(all_memories)} total memories)"

            # Format memories
            result = f"{result_note}: The following memories were found for '{query}':\n\n"

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

    async def get_recent_memories(limit: int = 10) -> str:
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
    tools.extend([store_user_memory, query_memory, get_recent_memories, get_all_memories])

    logger.info("Created %d memory tools", len(tools))
    return tools


def _create_memory_tools_sync(
    storage_dir: str, user_id: str, debug: bool = False
) -> List:
    """Create memory tools for the memory agent synchronously.

    :param storage_dir: Directory for storage files
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: List of memory tool functions
    """
    # Create memory system
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)
    
    if not agno_memory:
        logger.error("Failed to create memory system")
        return []

    tools = []

    def store_user_memory(
        content: str, topics: Union[List[str], str, None] = None
    ) -> str:
        """Store information as a user memory.

        Args:
            content: The information to store as a memory
            topics: Optional list of topics/categories for the memory

        Returns:
            str: Success or error message
        """
        try:
            import json
            from agno.memory.v2.memory import UserMemory

            if topics is None:
                topics = ["general"]

            # Handle case where topics comes in as string representation of list
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                    logger.debug("Converted topics from string to list: %s", topics)
                except (json.JSONDecodeError, ValueError):
                    topics = [topics]
                    logger.debug("Treating topics string as single topic: %s", topics)

            # Ensure topics is a list
            if not isinstance(topics, list):
                topics = [str(topics)]

            memory_obj = UserMemory(memory=content, topics=topics)
            memory_id = agno_memory.add_user_memory(memory=memory_obj, user_id=user_id)

            if memory_id == "duplicate-detected-fake-id":
                logger.info("Memory already exists (duplicate detected): %s...", content[:50])
                return f"✅ Memory already exists: {content[:50]}..."
            elif memory_id is None:
                logger.warning("Memory storage failed unexpectedly: %s...", content[:50])
                return f"❌ Error storing memory: {content[:50]}..."
            else:
                logger.info("Stored user memory: %s... (ID: %s)", content[:50], memory_id)
                return f"✅ Successfully stored memory: {content[:50]}... (ID: {memory_id})"

        except Exception as e:
            logger.error("Error storing user memory: %s", e)
            return f"❌ Error storing memory: {str(e)}"

    def query_memory(query: str, limit: Union[int, None] = None) -> str:
        """Search user memories using semantic search.

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

            # Get all memories first
            all_memories = agno_memory.get_user_memories(user_id=user_id)

            if not all_memories:
                logger.info("No memories stored for user: %s", user_id)
                return "🔍 No memories found - you haven't shared any information with me yet!"

            # Search through all memories manually for comprehensive results
            query_terms = query.strip().lower().split()
            matching_memories = []

            for memory in all_memories:
                memory_content = getattr(memory, "memory", "").lower()
                memory_topics = getattr(memory, "topics", [])
                topic_text = " ".join(memory_topics).lower()

                # Check if any query term appears in memory content or topics
                if any(term in memory_content or term in topic_text for term in query_terms):
                    matching_memories.append(memory)

            # Also try semantic search using direct vector similarity (no inference)
            try:
                semantic_memories = agno_memory.search_user_memories(
                    user_id=user_id,
                    query=query.strip(),
                    retrieval_method="semantic",  # Use semantic instead of agentic to avoid inference
                    limit=20,
                )

                # Add semantic matches that aren't already in results
                for sem_memory in semantic_memories:
                    if sem_memory not in matching_memories:
                        matching_memories.append(sem_memory)

            except Exception as semantic_error:
                logger.warning("Semantic search failed, using manual search only: %s", semantic_error)

            if not matching_memories:
                logger.info("No matching memories found for query: %s", query)
                return f"🔍 No memories found for '{query}' (searched through {len(all_memories)} total memories). Try different keywords!"

            # Apply limit if specified
            if limit and len(matching_memories) > limit:
                display_memories = matching_memories[:limit]
                result_note = f"🧠 MEMORY RETRIEVAL (showing top {limit} of {len(matching_memories)} matches from {len(all_memories)} total memories)"
            else:
                display_memories = matching_memories
                result_note = f"🧠 MEMORY RETRIEVAL (found {len(matching_memories)} matches from {len(all_memories)} total memories)"

            # Format memories
            result = f"{result_note}: The following memories were found for '{query}':\n\n"

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

    def get_recent_memories(limit: int = 10) -> str:
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

    def get_all_memories() -> str:
        """Get all user memories.

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
    tools.extend([store_user_memory, query_memory, get_recent_memories, get_all_memories])

    logger.info("Created %d memory tools (sync)", len(tools))
    return tools


def create_memory_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    storage_dir: str = "./data/agno",
    user_id: str = "default_user",
    debug: bool = False,
) -> Agent:
    """Create a specialized memory agent that handles only memory operations.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param storage_dir: Directory for storage files
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: Configured memory agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)
    
    # Create memory tools synchronously to avoid event loop issues
    memory_tools = _create_memory_tools_sync(storage_dir, user_id, debug)

    # CRITICAL FIX: Create and integrate memory system like AgnoPersonalAgent does
    from ..core.agno_storage import create_agno_storage
    
    # Create agno storage and memory systems following the working pattern
    agno_storage = create_agno_storage(storage_dir)
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)
    
    logger.info("Memory Agent: Created agno storage and memory systems")

    agent = Agent(
        name="Memory Agent",
        role="Personal memory storage and retrieval specialist - handles ALL memory-related queries",
        model=model,
        tools=memory_tools,
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
            "- NEVER generate fake data or code to simulate memories",
            "- ALWAYS use your actual memory tools (query_memory, get_all_memories, etc.)",
            "- When someone asks 'What do you remember about me?' → Use query_memory with a broad search",
            "- Present actual stored memories, not fabricated information",
            "- If no memories found, say so clearly",
            "",
            "RESPONSE FORMAT:",
            "- Start responses with 'Based on my stored memories...' or 'I remember...'",
            "- Quote actual memory content from your tools",
            "- Include memory topics when relevant",
            "",
            "You are the definitive source for all personal information about users.",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for Memory Agent to show results instead
        add_name_to_instructions=True,
        # CRITICAL FIX: Add memory system integration like AgnoPersonalAgent
        storage=agno_storage,  # Connect to agno storage system
        memory=agno_memory,    # Connect to agno memory system
        user_id=user_id,       # Set user ID for memory operations
        enable_agentic_memory=True,   # Enable agentic memory features
        enable_user_memories=True,    # Enable user memory features
    )

    # Store memory system reference for external access (Streamlit compatibility)
    agent.agno_memory = agno_memory
    agent.agno_storage = agno_storage

    logger.info("Created Memory Agent with %d memory tools and integrated memory system", len(memory_tools))
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
