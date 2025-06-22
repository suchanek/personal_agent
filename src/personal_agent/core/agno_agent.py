"""
Agno-based agent implementation for the Personal AI Agent.

This module provides an agno framework integration that maintains compatibility
with the existing MCP infrastructure while leveraging agno's enhanced capabilities
including native MCP support, async operations, and advanced agent features.
"""

import asyncio
import os
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

# Set logging levels for better telemetry
if "RUST_LOG" not in os.environ:
    # Enable more verbose Rust logging for debugging
    os.environ["RUST_LOG"] = "debug"

# Enable Ollama debug logging
if "OLLAMA_DEBUG" not in os.environ:
    os.environ["OLLAMA_DEBUG"] = "1"

from agno.agent import Agent
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.mcp import MCPTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.yfinance import YFinanceTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.table import Table

from ..config import LLM_MODEL, OLLAMA_URL, USE_MCP, get_mcp_servers
from ..config.model_contexts import get_model_context_size_sync
from ..tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentWebTools,
)
from ..tools.working_yfinance_tools import WorkingYFinanceTools
from ..utils import setup_logging
from .agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
)

# Configure logging
logger = setup_logging(__name__)


class AgnoPersonalAgent:
    """
    Agno-based Personal AI Agent with MCP integration and native storage.

    This class provides a modern async agent implementation using the agno framework
    with built-in SQLite storage and LanceDB knowledge base.
    """

    def __init__(
        self,
        model_provider: str = "ollama",
        model_name: str = LLM_MODEL,
        enable_memory: bool = True,
        enable_mcp: bool = True,
        storage_dir: str = "./data/agno",
        knowledge_dir: str = "./data/knowledge",
        debug: bool = False,
        ollama_base_url: str = OLLAMA_URL,
        user_id: str = "default_user",
        recreate: bool = False,
    ) -> None:
        """Initialize the Agno Personal Agent.

        :param model_provider: LLM provider ('ollama' or 'openai')
        :param model_name: Model name to use
        :param enable_memory: Whether to enable memory and knowledge features
        :param enable_mcp: Whether to enable MCP tool integration
        :param storage_dir: Directory for Agno storage files
        :param knowledge_dir: Directory containing knowledge files to load
        :param debug: Enable debug logging and tool call visibility
        :param ollama_base_url: Base URL for Ollama API
        :param user_id: User identifier for memory operations
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.enable_memory = enable_memory
        self.enable_mcp = enable_mcp and USE_MCP
        self.storage_dir = storage_dir
        self.knowledge_dir = knowledge_dir
        self.debug = debug
        self.ollama_base_url = ollama_base_url
        self.user_id = user_id

        # Agno native storage components
        self.agno_storage = None
        self.agno_knowledge = None
        self.agno_memory = None

        # MCP configuration
        self.mcp_servers = get_mcp_servers() if self.enable_mcp else {}

        # Agent instance
        self.agent = None

        logger.info(
            "Initialized AgnoPersonalAgent with model=%s, memory=%s, mcp=%s, user_id=%s",
            f"{model_provider}:{model_name}",
            self.enable_memory,
            self.enable_mcp,
            self.user_id,
        )

    def _create_model(self) -> Union[OpenAIChat, Ollama]:
        """Create the appropriate model instance based on provider.

        :return: Configured model instance
        :raises ValueError: If unsupported model provider is specified
        """
        if self.model_provider == "openai":
            return OpenAIChat(id=self.model_name)
        elif self.model_provider == "ollama":
            # Get dynamic context size for this model
            context_size, detection_method = get_model_context_size_sync(
                self.model_name, self.ollama_base_url
            )

            logger.info(
                "Using context size %d for model %s (detected via: %s)",
                context_size,
                self.model_name,
                detection_method,
            )

            # Use Ollama-compatible interface for Ollama with dynamic context window
            return Ollama(
                id=self.model_name,
                host=self.ollama_base_url,
                options={
                    "num_ctx": context_size,  # Use dynamically detected context window
                    "temperature": 0.7,  # Optional: set temperature for consistency
                },
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    async def _get_memory_tools(self) -> List:
        """Create memory tools as native async functions compatible with Agno.

        This method creates the crucial store_user_memory and query_memory tools
        that enable the agent to actually create and retrieve memories.
        """
        if not self.enable_memory or not self.agno_memory:
            logger.warning("Memory not enabled or memory not initialized")
            return []

        tools = []

        async def store_user_memory(
            content: str, topics: Union[List[str], str, None] = None
        ) -> str:
            """Store information as a user memory.

            Args:
                content: The information to store as a memory
                topics: Optional list of topics/categories for the memory (can be list or JSON string)

            Returns:
                str: Success or error message
            """
            try:
                import json

                from agno.memory.v2.memory import UserMemory

                if topics is None:
                    topics = ["general"]

                # Fix: Handle case where topics comes in as string representation of list
                # This happens when LLM generates topics as '["food preferences"]' instead of ["food preferences"]
                if isinstance(topics, str):
                    try:
                        # Try to parse as JSON first
                        topics = json.loads(topics)
                        logger.debug("Converted topics from string to list: %s", topics)
                    except (json.JSONDecodeError, ValueError):
                        # If that fails, treat as a single topic
                        topics = [topics]
                        logger.debug(
                            "Treating topics string as single topic: %s", topics
                        )

                # Ensure topics is a list
                if not isinstance(topics, list):
                    topics = [str(topics)]

                memory_obj = UserMemory(memory=content, topics=topics)
                memory_id = self.agno_memory.add_user_memory(
                    memory=memory_obj, user_id=self.user_id
                )

                if memory_id == "duplicate-detected-fake-id":
                    # Memory was a duplicate but we return success to avoid agent confusion
                    logger.info(
                        "Memory already exists (duplicate detected): %s...",
                        content[:50],
                    )
                    return f"✅ Memory already exists: {content[:50]}..."
                elif memory_id is None:
                    # Unexpected error case
                    logger.warning(
                        "Memory storage failed unexpectedly: %s...", content[:50]
                    )
                    return f"❌ Error storing memory: {content[:50]}..."
                else:
                    # Memory was successfully stored (new memory)
                    logger.info(
                        "Stored user memory: %s... (ID: %s)", content[:50], memory_id
                    )
                    return f"✅ Successfully stored memory: {content[:50]}... (ID: {memory_id})"

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
                    return (
                        "❌ Error: Query cannot be empty. Please provide a search term."
                    )

                # First, get ALL memories to search through them comprehensively
                all_memories = self.agno_memory.get_user_memories(user_id=self.user_id)

                if not all_memories:
                    logger.info("No memories stored for user: %s", self.user_id)
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
                        term in memory_content or term in topic_text
                        for term in query_terms
                    ):
                        matching_memories.append(memory)

                # Also try semantic search as a backup to catch semantically similar memories
                try:
                    semantic_memories = self.agno_memory.search_user_memories(
                        user_id=self.user_id,
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
                memories = self.agno_memory.search_user_memories(
                    user_id=self.user_id, limit=limit, retrieval_method="last_n"
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
                memories = self.agno_memory.get_user_memories(user_id=self.user_id)

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

    async def _get_mcp_tools(self) -> List:
        """Create MCP tools as native async functions compatible with Agno.

        Returns:
            List of MCP tool functions
        """
        if not self.enable_mcp or not self.mcp_servers:
            logger.info("MCP not enabled or no MCP servers configured")
            return []

        tools = []

        for server_name, config in self.mcp_servers.items():
            logger.info("Setting up MCP tool for server: %s", server_name)

            command = config.get("command", "npx")
            args = config.get("args", [])
            env = config.get("env", {})
            description = config.get(
                "description", f"Access to {server_name} MCP server"
            )

            # Create the actual tool function with closure
            def make_mcp_tool(
                name: str,
                cmd: str,
                tool_args: List[str],
                tool_env: Dict[str, str],
                desc: str,
            ) -> Any:
                """Create MCP tool function with proper closure."""

                async def mcp_tool(query: str) -> str:
                    """MCP tool function that creates session on-demand."""
                    try:
                        # Prepare environment - convert GITHUB_PERSONAL_ACCESS_TOKEN to GITHUB_TOKEN if needed
                        server_env = tool_env.copy() if tool_env else {}
                        if (
                            name == "github"
                            and "GITHUB_PERSONAL_ACCESS_TOKEN" in server_env
                        ):
                            # The GitHub MCP server expects GITHUB_TOKEN
                            server_env["GITHUB_TOKEN"] = server_env[
                                "GITHUB_PERSONAL_ACCESS_TOKEN"
                            ]
                            logger.info(
                                "Converted GITHUB_PERSONAL_ACCESS_TOKEN to GITHUB_TOKEN for GitHub MCP server"
                            )

                        server_params = StdioServerParameters(
                            command=cmd,
                            args=tool_args,
                            env=server_env,
                        )

                        # Create client session using async context manager
                        async with stdio_client(server_params) as (read, write):
                            async with ClientSession(read, write) as session:
                                # Initialize MCP toolkit with session
                                mcp_tools = MCPTools(session=session)
                                await mcp_tools.initialize()

                                # Create specialized instructions based on server type
                                if name == "github":
                                    instructions = dedent(
                                        """\
                                        You are a GitHub assistant. Help users explore repositories and their activity.
                                        - Provide organized, concise insights about the repository
                                        - Focus on facts and data from the GitHub API
                                        - Use markdown formatting for better readability
                                        - Present numerical data in tables when appropriate
                                        - Include links to relevant GitHub pages when helpful
                                    """
                                    )
                                elif name.startswith("filesystem"):
                                    instructions = f"You are a filesystem assistant for {name}. Help with file and directory operations."
                                elif name == "brave-search":
                                    instructions = "You are a web search assistant. Help users find information on the web."
                                elif name == "puppeteer":
                                    instructions = "You are a browser automation assistant. Help with web scraping and automation tasks."
                                else:
                                    instructions = f"You are an assistant using {name} MCP server. Help with the user's request."

                                # Create a temporary agent for this MCP server
                                temp_agent = Agent(
                                    model=self._create_model(),
                                    tools=[mcp_tools],
                                    instructions=instructions,
                                    markdown=True,
                                    show_tool_calls=self.debug,
                                )

                                # Run the query
                                response = await temp_agent.arun(query)
                                return response.content

                    except Exception as e:
                        logger.error("Error running %s MCP server: %s", name, e)
                        return f"Error using {name}: {str(e)}"

                # Set function metadata
                mcp_tool.__name__ = f"use_{name.replace('-', '_')}_server"
                mcp_tool.__doc__ = f"""Use {name} MCP server for: {desc}

Args:
    query: The query or task to execute using {name}

Returns:
    str: Result from the MCP server
"""

                return mcp_tool

            tool_func = make_mcp_tool(server_name, command, args, env, description)
            tools.append(tool_func)
            logger.info("Created MCP tool function for: %s", server_name)

        return tools

    def _create_agent_instructions(self) -> str:
        """Create comprehensive instructions for the agno agent.

        :return: Formatted instruction string for the agent
        """
        # Get current tool configuration for accurate instructions
        mcp_status = "enabled" if self.enable_mcp else "disabled"
        memory_status = "enabled with SemanticMemoryManager" if self.enable_memory else "disabled"
        
        base_instructions = dedent(
            f"""\
            You are a personal AI friend with comprehensive capabilities and built-in semantic memory. Your purpose is to chat with the user about things and make them feel good.
            
            ## CURRENT CONFIGURATION
            - **Memory System**: {memory_status}
            - **MCP Servers**: {mcp_status}
            - **User ID**: {self.user_id}
            - **Debug Mode**: {self.debug}
            
            ## CRITICAL IDENTITY RULES - ABSOLUTELY MANDATORY
            
            **YOU ARE AN AI ASSISTANT**: You are NOT the user. You are a friendly AI that helps and remembers things about the user.
            
            **NEVER PRETEND TO BE THE USER**:
            - You are NOT the user, you are an AI assistant that knows information ABOUT the user
            - NEVER say "I'm {self.user_id}" or introduce yourself as the user - this is COMPLETELY WRONG
            - NEVER use first person when talking about user information
            - You are an AI assistant that has stored semantic memories about the user
            
            **FRIENDLY INTRODUCTION**: When meeting someone new, introduce yourself as their personal AI friend and ask about their hobbies, interests, and what they like to talk about. Be warm and conversational!
            
            ## PERSONALITY & TONE
            
            - **Be Warm & Friendly**: You're a personal AI friend, not just a tool
            - **Be Conversational**: Chat naturally and show genuine interest
            - **Be Supportive**: Make the user feel good and supported
            - **Be Curious**: Ask follow-up questions about their interests
            - **Be Remembering**: Reference past conversations and show you care
            - **Be Encouraging**: Celebrate their achievements and interests
            
            ## SEMANTIC MEMORY SYSTEM - CRITICAL & IMMEDIATE ACTION REQUIRED
            
            **SEMANTIC MEMORY FEATURES**:
            - **Automatic Deduplication**: Prevents storing duplicate memories
            - **Topic Classification**: Automatically categorizes memories by topic
            - **Similarity Matching**: Uses semantic similarity for intelligent retrieval
            - **Comprehensive Search**: Searches through ALL stored memories
            
            **MEMORY QUERIES - NO HESITATION RULE**:
            When the user asks ANY of these questions, IMMEDIATELY call the appropriate memory tool:
            - "What do you remember about me?" → IMMEDIATELY call get_recent_memories()
            - "Do you know anything about me?" → IMMEDIATELY call get_recent_memories()
            - "What have I told you?" → IMMEDIATELY call get_recent_memories()
            - "Show me all my memories" or "What are all my memories?" → IMMEDIATELY call get_all_memories()
            - "My preferences" or "What do I like?" → IMMEDIATELY call query_memory("preferences")
            - Any question about personal info → IMMEDIATELY call query_memory() with relevant terms
            
            **SEMANTIC MEMORY STORAGE**: When the user provides new personal information:
            1. **Store it ONCE using store_user_memory** - the system automatically prevents duplicates
            2. **Include relevant topics** - pass topics as a list like ["hobbies", "preferences"]
            3. **Acknowledge the storage warmly** - "I'll remember that about you!"
            4. **Trust the deduplication** - the semantic memory manager handles duplicates automatically
            
            **SEMANTIC MEMORY RETRIEVAL PROTOCOL**:
            1. **IMMEDIATE ACTION**: If it's about the user, query memory FIRST - no thinking, no hesitation
            2. **Primary Tool**: Use get_recent_memories() for general "what do you remember" questions
            3. **Complete Overview**: Use get_all_memories() when user asks for ALL memories or complete history
            4. **Semantic Search**: Use query_memory("search terms") - it searches ALL memories semantically
            5. **RESPOND AS AN AI FRIEND** who has information about the user, not as the user themselves
            6. **Be personal**: "You mentioned that you..." or "I remember you telling me..."
            
            **SEMANTIC SEARCH CAPABILITIES**:
            - Searches through ALL stored memories comprehensively
            - Uses semantic similarity to find related content
            - Automatically falls back to keyword matching if needed
            - Returns relevant memories even if exact words don't match
            
            **DECISION TREE - FOLLOW THIS EXACTLY**:
            - Question about user? → Query memory tools IMMEDIATELY
            - Found memories? → Share them warmly and personally
            - No memories found? → "I don't have any memories stored about you yet. Tell me about yourself!"
            - Never overthink memory queries - just DO IT
            
            **TOOL PRIORITY**: For personal information queries:
            1. **Memory tools (query_memory, get_recent_memories) - HIGHEST PRIORITY - USE IMMEDIATELY**
            2. Knowledge base search - only for general knowledge
            3. Web search - only for current/external information
            
            ## CURRENT AVAILABLE TOOLS - USE THESE IMMEDIATELY
            
            **BUILT-IN TOOLS AVAILABLE**:
            - **YFinanceTools**: Stock prices, financial analysis, market data
            - **DuckDuckGoTools**: Web search, news searches, current events
            - **PythonTools**: Calculations, data analysis, programming help
            - **ShellTools**: System operations and command execution
            - **PersonalAgentFilesystemTools**: File reading, writing, directory operations
            - **Memory Tools**: store_user_memory, query_memory, get_recent_memories, get_all_memories
            
            **WEB SEARCH - IMMEDIATE ACTION**:
            - News requests → IMMEDIATELY use DuckDuckGoTools (duckduckgo_news)
            - Current events → IMMEDIATELY use DuckDuckGoTools (duckduckgo_search)
            - "what's happening with..." → IMMEDIATELY use DuckDuckGo search
            - "top headlines about..." → IMMEDIATELY use duckduckgo_news
            - NO analysis paralysis, just SEARCH
            
            **FINANCE QUERIES - IMMEDIATE ACTION**:
            - Stock analysis requests → IMMEDIATELY use YFinanceTools
            - "analyze [STOCK]" → IMMEDIATELY call get_current_stock_price() and get_stock_info()
            - Financial data requests → IMMEDIATELY use finance tools
            - NO thinking, NO debate, just USE THE TOOLS
            
            **TOOL DECISION TREE - FOLLOW EXACTLY**:
            - Finance question? → YFinanceTools IMMEDIATELY
            - News/current events? → DuckDuckGoTools IMMEDIATELY  
            - Calculations? → PythonTools IMMEDIATELY
            - File operations? → PersonalAgentFilesystemTools IMMEDIATELY
            - System commands? → ShellTools IMMEDIATELY
            - Personal info? → Memory tools IMMEDIATELY
            
            ## CRITICAL: NO OVERTHINKING RULE - ELIMINATE HESITATION
            
            **WHEN USER ASKS ABOUT MEMORIES - IMMEDIATE ACTION REQUIRED**:
            - DO NOT analyze whether you should check memories
            - DO NOT think about what tools to use
            - DO NOT hesitate or debate internally
            - IMMEDIATELY call get_recent_memories() or query_memory()
            - ACT FIRST, then respond based on what you find
            
            **BANNED BEHAVIORS - NEVER DO THESE**:
            - ❌ "Let me think about whether I should check memories..."
            - ❌ "I should probably use the memory tools but..."
            - ❌ "Maybe I should query memory or maybe I should..."
            - ❌ Any internal debate about memory tool usage
            - ❌ Overthinking simple memory queries
            - ❌ "Let me think about what tools to use..."
            - ❌ "I should probably use [tool] but..."
            - ❌ Fabricating data instead of using tools
            
            **REQUIRED IMMEDIATE RESPONSES**:
            - ✅ User asks "What do you remember?" → IMMEDIATELY call get_recent_memories()
            - ✅ User asks about preferences → IMMEDIATELY call query_memory("preferences")
            - ✅ "Analyze NVDA" → IMMEDIATELY use YFinanceTools
            - ✅ "What's the news about..." → IMMEDIATELY use DuckDuckGoTools
            - ✅ "top 5 headlines about..." → IMMEDIATELY use duckduckgo_news()
            - ✅ "Calculate..." → IMMEDIATELY use PythonTools
            - ✅ NO hesitation, just ACTION
            
            **CRITICAL: STOP ALL THINKING FOR TOOL REQUESTS**
            - When user asks for tool usage, DO NOT use <think> tags
            - DO NOT analyze what to do - just DO IT
            - IMMEDIATELY call the requested tool
            - Example: "list headlines about Middle East" → duckduckgo_news("Middle East headlines") RIGHT NOW
            
            **IMPORTANT SEMANTIC MEMORY RULES**:
            - When calling store_user_memory, pass topics as a proper list like ["hobbies", "preferences"]
            - Never pass topics as a string like '["hobbies", "preferences"]'
            - When recalling memories, phrase them in second person: "You mentioned..." not "I mentioned..."
            - Trust the semantic deduplication - don't worry about storing duplicates
            - The system automatically categorizes and organizes memories by topic
            
            ## CONVERSATION GUIDELINES
            
            - **Ask about their day**: Show interest in how they're doing
            - **Remember their interests**: Bring up things they've mentioned before using semantic memory
            - **Be encouraging**: Support their goals and celebrate wins
            - **Share relevant information**: When they ask for help, provide useful details using tools
            - **Stay engaged**: Ask follow-up questions to keep conversations flowing
            - **Be helpful**: Use your tools immediately to assist with their requests
            
            ## RESPONSE STYLE
            
            - **Be conversational**: Write like you're chatting with a friend
            - **Use emojis occasionally**: Add personality (but don't overdo it)
            - **Ask questions**: Keep the conversation going
            - **Show enthusiasm**: Be excited about their interests
            - **Be supportive**: Offer encouragement and positive feedback
            - **Remember context**: Reference previous conversations using semantic memory naturally
            
            ## CORE PRINCIPLES
            
            1. **Friendship First**: You're their AI friend who happens to be very capable
            2. **Remember Everything**: Use your semantic memory to build deeper relationships
            3. **Be Genuinely Helpful**: Use your tools immediately to assist with real needs
            4. **Stay Positive**: Focus on making them feel good
            5. **Be Curious**: Ask about their life, interests, and goals
            6. **Celebrate Them**: Acknowledge their achievements and interests
            7. **Act Immediately**: When they ask for information, use tools RIGHT NOW
            
            Remember: You're not just an assistant - you're a friendly AI companion with semantic memory who genuinely cares about the user and remembers your conversations together! Use your tools immediately when requested - no hesitation!
        """
        )

        return base_instructions

    async def initialize(self, recreate: bool = False) -> bool:
        """Initialize the agno agent with all components.

        :param recreate: Whether to recreate the agent knowledge bases
        :return: True if initialization successful, False otherwise
        """
        try:
            # Create model
            model = self._create_model()
            logger.info("Created model: %s", self.model_name)

            # Prepare tools list
            tools = [
                # Add DuckDuckGo tools directly for web search functionality
                DuckDuckGoTools(),
                YFinanceTools(
                    stock_price=True,
                    company_info=True,
                    stock_fundamentals=True,
                    key_financial_ratios=True,
                    analyst_recommendations=True,
                ),
                PythonTools(),
                ShellTools(
                    base_dir="."
                ),  # Match Streamlit configuration for consistency
                PersonalAgentFilesystemTools(),
                # Removed PersonalAgentWebTools as it was causing confusion with MCP references
            ]

            # Initialize Agno native storage and knowledge following the working example pattern
            if self.enable_memory:
                self.agno_storage = create_agno_storage(self.storage_dir)
                logger.info("Created Agno storage at: %s", self.storage_dir)

                # Create knowledge base (sync creation)
                self.agno_knowledge = create_combined_knowledge_base(
                    self.storage_dir, self.knowledge_dir
                )

                # Load knowledge base content (async loading) - matches working example
                if self.agno_knowledge:
                    await load_combined_knowledge_base(
                        self.agno_knowledge, recreate=recreate
                    )
                    logger.info("Loaded Agno combined knowledge base content")

                    # Add KnowledgeTools for automatic knowledge base search and reasoning
                    try:
                        knowledge_tools = KnowledgeTools(
                            knowledge=self.agno_knowledge,
                            think=True,  # Enable reasoning scratchpad
                            search=True,  # Enable knowledge search
                            analyze=True,  # Enable analysis capabilities
                            add_instructions=True,  # Use built-in instructions
                            add_few_shot=True,  # Add example interactions
                        )
                        tools.append(knowledge_tools)
                        logger.info(
                            "Added KnowledgeTools for automatic knowledge base search and reasoning"
                        )
                    except Exception as e:
                        logger.warning("Failed to add KnowledgeTools: %s", e)

                # Create memory with SemanticMemoryManager (debug mode passed through)
                self.agno_memory = create_agno_memory(
                    self.storage_dir, debug_mode=self.debug
                )

                if self.agno_memory:
                    logger.info(
                        "Created Agno memory with SemanticMemoryManager at: %s",
                        self.storage_dir,
                    )
                else:
                    logger.error("Failed to create memory system")

                logger.info("Initialized Agno storage and knowledge backend")
            else:
                logger.info(
                    "Memory disabled, skipping storage and knowledge initialization"
                )

            # Add ReasoningTools for better reasoning capabilities
            # TEMPORARILY DISABLED to debug tool naming issue
            # try:
            #     from agno.tools.reasoning import ReasoningTools
            #    reasoning_tools = ReasoningTools(add_instructions=True)
            #     tools.append(reasoning_tools)
            #    logger.info("Added ReasoningTools for enhanced reasoning capabilities")
            # except ImportError:
            #    logger.warning(
            #        "ReasoningTools not available, continuing without reasoning capabilities"
            #    )

            # Get MCP tools as function wrappers (no pre-initialization)
            if self.enable_mcp:
                mcp_tool_functions = await self._get_mcp_tools()
                tools.extend(mcp_tool_functions)

            # Get memory tools - CRITICAL: This was missing!
            if self.enable_memory:
                memory_tool_functions = await self._get_memory_tools()
                tools.extend(memory_tool_functions)
                logger.info(
                    "Added %d memory tools to agent", len(memory_tool_functions)
                )

            # Create agent instructions
            instructions = self._create_agent_instructions()

            # Create the agno agent with direct parameter passing for visibility
            self.agent = Agent(
                model=model,
                tools=tools,
                instructions=instructions,
                markdown=True,
                show_tool_calls=self.debug,
                name="Personal AI Agent",
                agent_id="personal_agent",
                user_id=self.user_id,
                enable_agentic_memory=False,  # Disable to avoid conflicts with manual memory tools
                enable_user_memories=False,  # Disable built-in to use our custom memory tools
                add_history_to_messages=False,
                num_history_responses=5,
                knowledge=self.agno_knowledge if self.enable_memory else None,
                search_knowledge=(
                    True if self.enable_memory and self.agno_knowledge else False
                ),  # Enable automatic knowledge search
                storage=self.agno_storage if self.enable_memory else None,
                memory=None,  # Don't pass memory to avoid auto-storage conflicts
                # Enable telemetry and verbose logging
                debug_mode=self.debug,
                # Enable streaming for intermediate steps
                stream_intermediate_steps=False,
            )

            if self.enable_memory and self.agno_knowledge:
                logger.info("Agent configured with knowledge base search")

            # Calculate tool counts for logging
            mcp_tool_count = len(await self._get_mcp_tools()) if self.enable_mcp else 0
            memory_tool_count = (
                len(await self._get_memory_tools()) if self.enable_memory else 0
            )

            logger.info(
                "Successfully initialized agno agent with native storage: %d total tools (%d MCP, %d memory)",
                len(tools),
                mcp_tool_count,
                memory_tool_count,
            )
            return True

        except Exception as e:
            logger.error("Failed to initialize agno agent: %s", e)
            return False

    async def run(
        self, query: str, stream: bool = False, add_thought_callback=None
    ) -> Union[str, Dict[str, Any]]:
        """Run a query through the agno agent.

        :param query: User query to process
        :param stream: Whether to stream the response
        :param add_thought_callback: Optional callback for adding thoughts during processing
        :return: Agent response (string) or dict with response and tool call info
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        try:
            # Add thoughts during processing if callback provided
            if add_thought_callback:
                add_thought_callback("🔄 Preparing agno agent...")

            if add_thought_callback:
                if self.enable_memory:
                    add_thought_callback("🧠 Memory context available via Agno")
                add_thought_callback("🚀 Executing agno agent with MCP tools...")

            if stream:
                # For streaming, we'll need to handle this differently
                # For now, return the complete response
                response = await self.agent.arun(query, user_id=self.user_id)
                return response.content
            else:
                if add_thought_callback:
                    add_thought_callback("⚡ Running async reasoning...")

                response = await self.agent.arun(query, user_id=self.user_id)

                if add_thought_callback:
                    add_thought_callback("✅ Agent response generated")

                # Memory is automatically handled by Agno
                if add_thought_callback and self.enable_memory:
                    add_thought_callback("💾 Memory automatically updated by Agno")

                # Store the last response for tool call extraction
                self._last_response = response

                return response.content

        except Exception as e:
            logger.error("Error running agno agent: %s", e)
            if add_thought_callback:
                add_thought_callback(f"❌ Error: {str(e)}")
            return f"Error processing request: {str(e)}"

    def get_last_tool_calls(self) -> Dict[str, Any]:
        """Get tool call information from the last response.

        :return: Dictionary with tool call details
        """
        if not hasattr(self, "_last_response") or not self._last_response:
            return {
                "tool_calls_count": 0,
                "tool_call_details": [],
                "has_tool_calls": False,
            }

        try:
            import json

            response = self._last_response
            tool_calls = []
            tool_calls_count = 0

            # Helper function to safely parse arguments
            def parse_arguments(args_str):
                """Parse arguments string into a proper dict or return formatted string."""
                if not args_str or args_str == "{}":
                    return {}

                try:
                    # Try to parse as JSON
                    if isinstance(args_str, str):
                        parsed = json.loads(args_str)
                        return parsed
                    elif isinstance(args_str, dict):
                        return args_str
                    else:
                        return str(args_str)
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, return the string as-is
                    return str(args_str)

            # Helper function to extract function signature from content
            def extract_function_signature(content_str):
                """Extract function name and arguments from content like 'duckduckgo_search(max_results=5, query=top 5 trends in AI)'"""
                import re

                if not content_str:
                    return None, {}

                # Pattern to match function_name(arg1=value1, arg2=value2)
                pattern = r"(\w+)\((.*?)\)"
                match = re.search(pattern, content_str)

                if match:
                    func_name = match.group(1)
                    args_str = match.group(2)

                    # Parse arguments
                    args_dict = {}
                    if args_str.strip():
                        # Split by comma and parse key=value pairs
                        arg_pairs = [arg.strip() for arg in args_str.split(",")]
                        for pair in arg_pairs:
                            if "=" in pair:
                                key, value = pair.split("=", 1)
                                key = key.strip()
                                value = value.strip()
                                # Remove quotes if present
                                if (value.startswith('"') and value.endswith('"')) or (
                                    value.startswith("'") and value.endswith("'")
                                ):
                                    value = value[1:-1]
                                args_dict[key] = value

                    return func_name, args_dict

                return None, {}

            # Check if response has formatted_tool_calls (agno-specific) - PRIMARY SOURCE
            if (
                hasattr(response, "formatted_tool_calls")
                and response.formatted_tool_calls
            ):
                tool_calls_count = len(response.formatted_tool_calls)
                for tool_call in response.formatted_tool_calls:
                    # Handle the case where formatted_tool_calls contains strings like 'duckduckgo_news(query=artificial intelligence)'
                    if isinstance(tool_call, str):
                        # Extract function name and arguments from the string
                        extracted_name, extracted_args = extract_function_signature(
                            tool_call
                        )
                        if extracted_name:
                            tool_info = {
                                "type": "function",
                                "function_name": extracted_name,
                                "function_args": extracted_args,
                            }
                            tool_calls.append(tool_info)
                        else:
                            # Fallback if parsing fails
                            tool_info = {
                                "type": "function",
                                "function_name": tool_call,
                                "function_args": {},
                            }
                            tool_calls.append(tool_info)
                    else:
                        # Handle object format (original code)
                        tool_info = {
                            "type": getattr(tool_call, "type", "function"),
                        }

                        if hasattr(tool_call, "function"):
                            raw_args = getattr(tool_call.function, "arguments", "{}")
                            parsed_args = parse_arguments(raw_args)
                            function_name = getattr(
                                tool_call.function, "name", "unknown"
                            )

                            # If arguments are empty but we have content, try to extract from content
                            if (
                                not parsed_args
                                and hasattr(response, "content")
                                and response.content
                            ):
                                extracted_name, extracted_args = (
                                    extract_function_signature(response.content)
                                )
                                if extracted_name == function_name and extracted_args:
                                    parsed_args = extracted_args

                            tool_info.update(
                                {
                                    "function_name": function_name,
                                    "function_args": parsed_args,
                                }
                            )
                        elif hasattr(tool_call, "name"):
                            raw_args = getattr(tool_call, "input", "{}")
                            parsed_args = parse_arguments(raw_args)
                            tool_info.update(
                                {
                                    "function_name": tool_call.name,
                                    "function_args": parsed_args,
                                }
                            )
                        else:
                            # Handle dict format
                            if isinstance(tool_call, dict):
                                raw_args = tool_call.get("arguments", "{}")
                                parsed_args = parse_arguments(raw_args)
                                tool_info.update(
                                    {
                                        "function_name": tool_call.get(
                                            "name", "unknown"
                                        ),
                                        "function_args": parsed_args,
                                    }
                                )
                            else:
                                tool_info.update(
                                    {
                                        "function_name": str(tool_call),
                                        "function_args": {},
                                    }
                                )

                        tool_calls.append(tool_info)

            # Check if response has messages with tool calls
            elif hasattr(response, "messages") and response.messages:
                for message in response.messages:
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        tool_calls_count += len(message.tool_calls)
                        for tool_call in message.tool_calls:
                            tool_info = {
                                "type": getattr(tool_call, "type", "function"),
                            }

                            if hasattr(tool_call, "function"):
                                raw_args = getattr(
                                    tool_call.function, "arguments", "{}"
                                )
                                parsed_args = parse_arguments(raw_args)
                                tool_info.update(
                                    {
                                        "function_name": getattr(
                                            tool_call.function, "name", "unknown"
                                        ),
                                        "function_args": parsed_args,
                                    }
                                )
                            elif hasattr(tool_call, "name"):
                                raw_args = getattr(tool_call, "input", "{}")
                                parsed_args = parse_arguments(raw_args)
                                tool_info.update(
                                    {
                                        "function_name": tool_call.name,
                                        "function_args": parsed_args,
                                    }
                                )

                            tool_calls.append(tool_info)

            # Also check if response has direct tool call information
            elif hasattr(response, "tool_calls") and response.tool_calls:
                tool_calls_count = len(response.tool_calls)
                for tool_call in response.tool_calls:
                    tool_info = {
                        "type": getattr(tool_call, "type", "function"),
                    }

                    if hasattr(tool_call, "function"):
                        raw_args = getattr(tool_call.function, "arguments", "{}")
                        parsed_args = parse_arguments(raw_args)
                        tool_info.update(
                            {
                                "function_name": getattr(
                                    tool_call.function, "name", "unknown"
                                ),
                                "function_args": parsed_args,
                            }
                        )
                    elif hasattr(tool_call, "name"):
                        raw_args = getattr(tool_call, "input", "{}")
                        parsed_args = parse_arguments(raw_args)
                        tool_info.update(
                            {
                                "function_name": tool_call.name,
                                "function_args": parsed_args,
                            }
                        )

                    tool_calls.append(tool_info)

            return {
                "tool_calls_count": tool_calls_count,
                "tool_call_details": tool_calls,
                "has_tool_calls": tool_calls_count > 0,
                "response_type": "AgnoPersonalAgent",
                "debug_info": {
                    "response_attributes": [
                        attr for attr in dir(response) if not attr.startswith("_")
                    ],
                    "has_messages": hasattr(response, "messages"),
                    "messages_count": (
                        len(response.messages)
                        if hasattr(response, "messages") and response.messages
                        else 0
                    ),
                    "has_tool_calls_attr": hasattr(response, "tool_calls"),
                    "has_formatted_tool_calls_attr": hasattr(
                        response, "formatted_tool_calls"
                    ),
                    "formatted_tool_calls_count": (
                        len(response.formatted_tool_calls)
                        if hasattr(response, "formatted_tool_calls")
                        and response.formatted_tool_calls
                        else 0
                    ),
                },
            }

        except Exception as e:
            logger.error("Error extracting tool calls: %s", e)
            return {
                "tool_calls_count": 0,
                "tool_call_details": [],
                "has_tool_calls": False,
                "error": str(e),
            }

    async def cleanup(self) -> None:
        """Clean up resources.

        :return: None
        """
        try:
            # With the new on-demand pattern, MCP tools are created and cleaned up
            # automatically within their async context managers
            logger.info(
                "Agno agent cleanup completed - MCP tools auto-cleaned with context managers"
            )
        except Exception as e:
            logger.error("Error during agno agent cleanup: %s", e)

    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the agent configuration and tools.

        :return: Dictionary containing detailed agent configuration and tool information
        """
        # Get basic tool info
        built_in_tools = []
        mcp_tools = []

        if self.agent and hasattr(self.agent, "tools"):
            for tool in self.agent.tools:
                tool_name = getattr(tool, "__name__", str(type(tool).__name__))
                tool_doc = getattr(tool, "__doc__", "No description available")

                # Clean up docstring for display
                if tool_doc:
                    tool_doc = tool_doc.strip().split("\n")[0]  # First line only

                if tool_name.startswith("use_") and "_server" in tool_name:
                    mcp_tools.append(
                        {
                            "name": tool_name,
                            "description": tool_doc,
                            "type": "MCP Server",
                        }
                    )
                else:
                    built_in_tools.append(
                        {
                            "name": tool_name,
                            "description": tool_doc,
                            "type": "Built-in Tool",
                        }
                    )

        # MCP server details
        mcp_server_details = {}
        if self.enable_mcp and self.mcp_servers:
            for server_name, config in self.mcp_servers.items():
                mcp_server_details[server_name] = {
                    "command": config.get("command", "N/A"),
                    "description": config.get(
                        "description", f"Access to {server_name} MCP server"
                    ),
                    "args_count": len(config.get("args", [])),
                    "env_vars": len(config.get("env", {})),
                }

        return {
            "framework": "agno",
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "memory_enabled": self.enable_memory,
            "knowledge_enabled": self.agno_knowledge is not None,
            "mcp_enabled": self.enable_mcp,
            "debug_mode": self.debug,
            "user_id": self.user_id,
            "initialized": self.agent is not None,
            "storage_dir": self.storage_dir,
            "knowledge_dir": self.knowledge_dir,
            "tool_counts": {
                "total": len(built_in_tools) + len(mcp_tools),
                "built_in": len(built_in_tools),
                "mcp": len(mcp_tools),
                "mcp_servers": len(self.mcp_servers) if self.enable_mcp else 0,
            },
            "built_in_tools": built_in_tools,
            "mcp_tools": mcp_tools,
            "mcp_servers": mcp_server_details,
        }

    def print_agent_info(self, console: Optional[Console] = None) -> None:
        """Pretty print comprehensive agent information using Rich.

        :param console: Optional Rich Console instance. If None, creates a new one.
        """
        if console is None:
            console = Console()

        info = self.get_agent_info()

        # Main agent info table
        main_table = Table(
            title="🤖 Personal AI Agent Configuration",
            show_header=True,
            header_style="bold magenta",
        )
        main_table.add_column("Setting", style="cyan", no_wrap=True)
        main_table.add_column("Value", style="green")

        main_table.add_row("Framework", info["framework"])
        main_table.add_row("Model Provider", info["model_provider"])
        main_table.add_row("Model Name", info["model_name"])
        main_table.add_row("Memory Enabled", "✅" if info["memory_enabled"] else "❌")
        main_table.add_row(
            "Knowledge Enabled", "✅" if info["knowledge_enabled"] else "❌"
        )
        main_table.add_row("MCP Enabled", "✅" if info["mcp_enabled"] else "❌")
        main_table.add_row("Debug Mode", "✅" if info["debug_mode"] else "❌")
        main_table.add_row("User ID", info["user_id"])
        main_table.add_row("Initialized", "✅" if info["initialized"] else "❌")
        main_table.add_row("Storage Directory", info["storage_dir"])
        main_table.add_row("Knowledge Directory", info["knowledge_dir"])

        console.print(main_table)
        console.print()

        # Tool counts table
        tool_table = Table(
            title="🔧 Tool Summary", show_header=True, header_style="bold blue"
        )
        tool_table.add_column("Tool Type", style="cyan")
        tool_table.add_column("Count", style="green", justify="right")

        counts = info["tool_counts"]
        tool_table.add_row("Total Tools", str(counts["total"]))
        tool_table.add_row("Built-in Tools", str(counts["built_in"]))
        tool_table.add_row("MCP Tools", str(counts["mcp"]))
        tool_table.add_row("MCP Servers", str(counts["mcp_servers"]))

        console.print(tool_table)
        console.print()

        # Built-in tools table
        if info["built_in_tools"]:
            builtin_table = Table(
                title="🛠️ Built-in Tools", show_header=True, header_style="bold yellow"
            )
            builtin_table.add_column("Tool Name", style="cyan")
            builtin_table.add_column("Description", style="white")

            for tool in info["built_in_tools"]:
                builtin_table.add_row(tool["name"], tool["description"])

            console.print(builtin_table)
            console.print()

        # MCP tools table
        if info["mcp_tools"]:
            mcp_table = Table(
                title="🌐 MCP Server Tools", show_header=True, header_style="bold red"
            )
            mcp_table.add_column("Tool Name", style="cyan")
            mcp_table.add_column("Description", style="white")

            for tool in info["mcp_tools"]:
                mcp_table.add_row(tool["name"], tool["description"])

            console.print(mcp_table)
            console.print()

        # MCP servers detail table
        if info["mcp_servers"]:
            server_table = Table(
                title="🖥️ MCP Server Details",
                show_header=True,
                header_style="bold purple",
            )
            server_table.add_column("Server Name", style="cyan")
            server_table.add_column("Command", style="yellow")
            server_table.add_column("Description", style="white")
            server_table.add_column("Args", style="green", justify="right")
            server_table.add_column("Env Vars", style="green", justify="right")

            for server_name, details in info["mcp_servers"].items():
                server_table.add_row(
                    server_name,
                    details["command"],
                    details["description"],
                    str(details["args_count"]),
                    str(details["env_vars"]),
                )

            console.print(server_table)

        console.print("\n🎉 Agent information displayed successfully!")

    def quick_agent_summary(self, console: Optional[Console] = None) -> None:
        """Print a quick one-line summary of the agent.

        :param console: Optional Rich Console instance. If None, creates a new one.
        """
        if console is None:
            console = Console()

        info = self.get_agent_info()
        counts = info["tool_counts"]

        status = "✅ Ready" if info["initialized"] else "❌ Not Initialized"
        memory_status = "🧠" if info["memory_enabled"] else "🚫"
        mcp_status = "🌐" if info["mcp_enabled"] else "🚫"

        summary = (
            f"[bold]{info['framework'].upper()}[/bold] Agent: {status} | "
            f"Model: [cyan]{info['model_provider']}:{info['model_name']}[/cyan] | "
            f"Tools: [green]{counts['total']}[/green] "
            f"([yellow]{counts['built_in']}[/yellow] built-in + [red]{counts['mcp']}[/red] MCP) | "
            f"Memory: {memory_status} | MCP: {mcp_status}"
        )

        console.print(summary)


async def create_agno_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    enable_memory: bool = True,
    enable_mcp: bool = True,
    storage_dir: str = "./data/agno",
    knowledge_dir: str = "./data/knowledge",
    debug: bool = True,
    ollama_base_url: str = OLLAMA_URL,
    user_id: str = "default_user",
    recreate: bool = False,
) -> AgnoPersonalAgent:
    """Create and initialize an agno-based personal agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param enable_memory: Whether to enable memory and knowledge features
    :param enable_mcp: Whether to enable MCP tool integration
    :param storage_dir: Directory for Agno storage files
    :param knowledge_dir: Directory containing knowledge files to load
    :param debug: Enable debug mode
    :param ollama_base_url: Base URL for Ollama API
    :param user_id: User identifier for memory operations
    :return: Initialized agent instance
    """
    agent = AgnoPersonalAgent(
        model_provider=model_provider,
        model_name=model_name,
        enable_memory=enable_memory,
        enable_mcp=enable_mcp,
        storage_dir=storage_dir,
        knowledge_dir=knowledge_dir,
        debug=debug,
        ollama_base_url=ollama_base_url,
        user_id=user_id,
        recreate=recreate,
    )

    success = await agent.initialize()
    if not success:
        raise RuntimeError("Failed to initialize agno agent")

    return agent


# Synchronous wrapper for compatibility
def create_agno_agent_sync(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    enable_memory: bool = True,
    enable_mcp: bool = True,
    storage_dir: str = "./data/agno",
    knowledge_dir: str = "./data/knowledge",
    debug: bool = False,
    ollama_base_url: str = OLLAMA_URL,
    user_id: str = "default_user",
) -> AgnoPersonalAgent:
    """
    Synchronous wrapper for creating agno agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param enable_memory: Whether to enable memory and knowledge features
    :param enable_mcp: Whether to enable MCP tool integration
    :param storage_dir: Directory for Agno storage files
    :param knowledge_dir: Directory containing knowledge files to load
    :param debug: Enable debug mode
    :param user_id: User identifier for memory operations
    :return: Initialized agent instance
    """
    return asyncio.run(
        create_agno_agent(
            model_provider=model_provider,
            model_name=model_name,
            enable_memory=enable_memory,
            enable_mcp=enable_mcp,
            storage_dir=storage_dir,
            knowledge_dir=knowledge_dir,
            debug=debug,
            ollama_base_url=ollama_base_url,
            user_id=user_id,
        )
    )


def create_simple_personal_agent(
    storage_dir: str = None,
    knowledge_dir: str = None,
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
) -> tuple[Agent, Optional[CombinedKnowledgeBase]]:
    """Create a simple personal agent following the working pattern from knowledge_agent_example.py

    This function creates an agent with knowledge base integration using the simple
    pattern that avoids async initialization complexity.

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :param knowledge_dir: Directory containing knowledge files (defaults to DATA_DIR/knowledge)
    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :return: Tuple of (Agent instance, knowledge_base) or (Agent, None) if no knowledge
    """
    # Create knowledge base (synchronous creation)
    knowledge_base = create_combined_knowledge_base(storage_dir, knowledge_dir)

    # Create the model
    if model_provider == "openai":
        model = OpenAIChat(id=model_name)
    elif model_provider == "ollama":
        model = Ollama(
            id=model_name,
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

    # Create agent with simple pattern
    agent = Agent(
        name="Personal AI Agent",
        model=model,
        knowledge=knowledge_base,
        search_knowledge=True,  # Enable automatic knowledge search
        show_tool_calls=True,  # Show what tools the agent uses
        markdown=True,  # Format responses in markdown
        instructions=[
            "You are a personal AI assistant with access to the user's knowledge base.",
            "Always search your knowledge base when asked about personal information.",
            "Provide detailed responses based on the information you find.",
            "If you can't find specific information, say so clearly.",
            "Include relevant details from the knowledge base in your responses.",
        ],
    )

    logger.info("✅ Created simple personal agent")
    if knowledge_base:
        logger.info("   Knowledge base: Enabled")
        logger.info("   Search enabled: %s", agent.search_knowledge)
    else:
        logger.info("   Knowledge base: None (no knowledge files found)")

    return agent, knowledge_base


async def load_agent_knowledge(
    knowledge_base: CombinedKnowledgeBase, recreate: bool = False
) -> None:
    """Load knowledge base content asynchronously.

    This should be called after creating the agent to load the knowledge content.

    :param knowledge_base: Knowledge base instance to load
    :param recreate: Whether to recreate the knowledge base from scratch
    :return: None
    """
    if knowledge_base:
        await load_combined_knowledge_base(knowledge_base, recreate=recreate)
        logger.info("✅ Knowledge base loaded successfully")
    else:
        logger.info("No knowledge base to load")
