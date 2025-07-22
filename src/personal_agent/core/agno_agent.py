"""
Refactored Agno-based agent implementation for the Personal AI Agent.

This module provides a cleaner, more modular implementation of the AgnoPersonalAgent
that leverages specialized manager classes for different responsibilities:
- AgentModelManager: Handles model creation and configuration
- AgentInstructionManager: Manages instruction creation and customization
- AgentMemoryManager: Handles memory operations including storage and retrieval
- AgentKnowledgeManager: Manages knowledge base operations
- AgentToolManager: Handles tool registration and execution
"""

import asyncio
import os
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.python import PythonTools
from agno.tools.yfinance import YFinanceTools
from rich.console import Console
from rich.table import Table

from ..config import get_mcp_servers
from ..config.settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    DATA_DIR,
    LIGHTRAG_MEMORY_URL,
    LIGHTRAG_URL,
    LLM_MODEL,
    LOG_LEVEL,
    OLLAMA_URL,
    SHOW_SPLASH_SCREEN,
    STORAGE_BACKEND,
    USE_MCP,
    USER_ID,
)
from ..tools.knowledge_ingestion_tools import KnowledgeIngestionTools
from ..tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentSystemTools,
)
from ..utils import setup_logging
from ..utils.splash_screen import display_splash_screen
from .agent_instruction_manager import AgentInstructionManager, InstructionLevel
from .agent_knowledge_manager import AgentKnowledgeManager
from .agent_memory_manager import AgentMemoryManager
from .agent_model_manager import AgentModelManager
from .agent_tool_manager import AgentToolManager
from .agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
    load_lightrag_knowledge_base,
)
from .docker_integration import ensure_docker_user_consistency
from .knowledge_coordinator import create_knowledge_coordinator
from .semantic_memory_manager import MemoryStorageResult, MemoryStorageStatus

# Configure logging
logger = setup_logging(__name__, level=LOG_LEVEL)


class AgnoPersonalAgent:
    """
    Refactored Agno-based Personal AI Agent with MCP integration and native storage.

    This class coordinates the different components of the agent system,
    delegating specific responsibilities to specialized manager classes.
    """

    def __init__(
        self,
        model_provider: str = "ollama",
        model_name: str = LLM_MODEL,
        enable_memory: bool = True,
        enable_mcp: bool = True,
        storage_dir: str = AGNO_STORAGE_DIR,
        knowledge_dir: str = AGNO_KNOWLEDGE_DIR,
        debug: bool = False,
        ollama_base_url: str = OLLAMA_URL,
        user_id: str = USER_ID,
        recreate: bool = False,
        instruction_level: InstructionLevel = InstructionLevel.STANDARD,
        seed: Optional[int] = None,
    ) -> None:
        """Initialize the Agno Personal Agent.

        Args:
            model_provider: LLM provider ('ollama' or 'openai')
            model_name: Model name to use
            enable_memory: Whether to enable memory and knowledge features
            enable_mcp: Whether to enable MCP tool integration
            storage_dir: Directory for Agno storage files
            knowledge_dir: Directory containing knowledge files to load
            debug: Enable debug logging and tool call visibility
            ollama_base_url: Base URL for Ollama API
            user_id: User identifier for memory operations
            recreate: Whether to recreate knowledge bases
            instruction_level: The sophistication level for agent instructions
            seed: Optional seed for model reproducibility
        """
        # Basic configuration
        self.model_provider = model_provider
        self.model_name = model_name
        self.enable_memory = enable_memory
        self.enable_mcp = enable_mcp and USE_MCP
        self.debug = debug
        self.ollama_base_url = ollama_base_url
        self.user_id = user_id
        self.recreate = recreate
        self.instruction_level = instruction_level
        self.seed = seed

        # Set up storage paths
        self._setup_storage_paths(storage_dir, knowledge_dir, user_id)

        # MCP configuration
        self.mcp_servers = get_mcp_servers() if self.enable_mcp else {}

        # Initialize component managers
        self.model_manager: AgentModelManager = AgentModelManager(
            model_provider, model_name, ollama_base_url, seed
        )

        self.instruction_manager: AgentInstructionManager = AgentInstructionManager(
            instruction_level, user_id, enable_memory, self.enable_mcp, self.mcp_servers
        )

        self.memory_manager: AgentMemoryManager = AgentMemoryManager(
            user_id,
            self.storage_dir,
            None,  # agno_memory will be set during initialization
            LIGHTRAG_URL,
            LIGHTRAG_MEMORY_URL,
            enable_memory,
        )

        self.knowledge_manager: AgentKnowledgeManager = AgentKnowledgeManager(
            user_id, self.storage_dir, LIGHTRAG_URL, LIGHTRAG_MEMORY_URL
        )

        self.tool_manager: AgentToolManager = AgentToolManager(
            user_id, self.storage_dir
        )

        # Storage components
        self.agno_storage = None
        self.agno_knowledge = None
        self.lightrag_knowledge = None
        self.lightrag_knowledge_enabled = False
        self.agno_memory = None
        self.knowledge_coordinator = None

        # Agent instance
        self.agent = None
        self._last_response = None

        logger.info(
            "Initialized AgnoPersonalAgent with model=%s, memory=%s, mcp=%s, user_id=%s",
            f"{model_provider}:{model_name}",
            self.enable_memory,
            self.enable_mcp,
            self.user_id,
        )

    def _setup_storage_paths(
        self, storage_dir: str, knowledge_dir: str, user_id: str
    ) -> None:
        """Set up storage paths based on user ID.

        Args:
            storage_dir: Default storage directory
            knowledge_dir: Default knowledge directory
            user_id: User identifier
        """
        # If user_id differs from default, create user-specific paths
        if user_id != USER_ID:
            # Replace the default user ID in the paths with the custom user ID
            self.storage_dir = os.path.expandvars(
                f"{DATA_DIR}/{STORAGE_BACKEND}/{user_id}"
            )
            self.knowledge_dir = os.path.expandvars(
                f"{DATA_DIR}/{STORAGE_BACKEND}/{user_id}/knowledge"
            )
        else:
            self.storage_dir = storage_dir
            self.knowledge_dir = knowledge_dir

    async def initialize(self, recreate: bool = False) -> bool:
        """Initialize the agno agent with all components.

        Args:
            recreate: Whether to recreate the agent knowledge bases

        Returns:
            True if initialization successful, False otherwise
        """
        logger.info(
            "🚀 AgnoPersonalAgent.initialize() called with recreate=%s", recreate
        )

        # CRITICAL: Synchronize the agent's user_id with the persistent user setting
        try:
            from ..config import get_current_user_id
            from .user_manager import UserManager

            user_manager = UserManager()
            persistent_user_id = (
                get_current_user_id()
            )  # This is loaded from env.userid at startup

            if self.user_id != persistent_user_id:
                logger.warning(
                    "Agent initialized with user '%s', but persistent user is '%s'. Switching context...",
                    self.user_id,
                    persistent_user_id,
                )
                # This is a formal user switch. Update the persistent user file.
                switch_result = user_manager.switch_user(
                    self.user_id, restart_lightrag=True, update_global_config=True
                )
                if not switch_result.get(
                    "success"
                ) and "Already logged in" not in switch_result.get("error", ""):
                    raise RuntimeError(
                        f"Failed to switch user context to '{self.user_id}': {switch_result.get('error')}"
                    )
                else:
                    logger.info(
                        "Successfully switched user context to '%s'", self.user_id
                    )

        except Exception as e:
            logger.error("🚨 Critical error during user context synchronization: %s", e)
            # This is a critical step, so we raise an exception if it fails.
            raise RuntimeError(f"User context synchronization failed: {e}") from e

        # CRITICAL: Ensure user is registered in the user registry
        logger.info("📝 Ensuring user %s is registered in user registry", self.user_id)
        try:
            from .user_registry import UserRegistry

            user_registry = UserRegistry()
            user_registry.ensure_current_user_registered()
            logger.info("✅ User registration check completed")
        except Exception as e:
            logger.warning("⚠️ User registry check failed: %s", e)
            # Don't fail initialization for user registry issues

        # CRITICAL: Ensure Docker USER_ID consistency with smart restart capability
        logger.info("🔍 Checking Docker USER_ID consistency for user: %s", self.user_id)
        try:
            ready_to_proceed, consistency_message = ensure_docker_user_consistency(
                user_id=self.user_id, auto_fix=True, force_restart=False
            )

            if ready_to_proceed:
                logger.info(
                    "✅ Docker consistency check passed: %s", consistency_message
                )
            else:
                logger.error(
                    "❌ Docker consistency check failed: %s", consistency_message
                )
                raise RuntimeError(
                    f"Docker USER_ID consistency check failed: {consistency_message}"
                )

        except Exception as e:
            logger.error("🚨 Critical error during Docker consistency check: %s", e)
            # Don't fail initialization for Docker consistency issues in case Docker is not available
            logger.warning(
                "⚠️ Continuing initialization despite Docker consistency check failure"
            )

        try:
            # Create model using the model manager
            model = self.model_manager.create_model()
            logger.info("Created model: %s", self.model_name)

            # Prepare tools list
            tools = [
                # Add GoogleSearch tools directly for web search functionality
                GoogleSearchTools(),
                YFinanceTools(
                    stock_price=True,
                    company_info=True,
                    stock_fundamentals=True,
                    key_financial_ratios=True,
                    analyst_recommendations=True,
                ),
                PythonTools(),
                PersonalAgentFilesystemTools(),  # @todo: modify to pass a proper starting dir
                PersonalAgentSystemTools(),
                KnowledgeIngestionTools(),  # Add knowledge ingestion capabilities
                CalculatorTools(enable_all=True),
            ]

            # Initialize Agno native storage and knowledge following the working example pattern
            if self.enable_memory:
                self.agno_storage = create_agno_storage(self.storage_dir)
                logger.info("Created Agno storage at: %s", self.storage_dir)

                # Create knowledge base (sync creation)
                self.agno_knowledge = create_combined_knowledge_base(
                    self.storage_dir, self.knowledge_dir, self.agno_storage
                )

                # Load knowledge base content (async loading) - matches working example
                if self.agno_knowledge:
                    await load_combined_knowledge_base(
                        self.agno_knowledge, recreate=recreate
                    )
                    logger.info("Loaded Agno combined knowledge base content")

                # Create memory with SemanticMemoryManager (debug mode passed through)
                self.agno_memory = create_agno_memory(
                    self.storage_dir, debug_mode=self.debug
                )

                if self.agno_memory:
                    # Initialize the memory manager with the created agno_memory
                    self.memory_manager.initialize(self.agno_memory)
                    logger.info(
                        "Created Agno memory with SemanticMemoryManager at: %s",
                        self.storage_dir,
                    )
                else:
                    logger.error("Failed to create memory system")

                # Add Lightrag knowledge if enabled
                if self.enable_memory:
                    try:
                        self.lightrag_knowledge = await load_lightrag_knowledge_base()
                        self.lightrag_knowledge_enabled = (
                            self.lightrag_knowledge is not None
                        )
                        logger.info("Loaded Lightrag knowledge base metadata")
                    except Exception as e:
                        logger.warning("Failed to load Lightrag knowledge base: %s", e)
                        self.lightrag_knowledge = None
                        self.lightrag_knowledge_enabled = False

                # Create Knowledge Coordinator
                self.knowledge_coordinator = create_knowledge_coordinator(
                    agno_knowledge=self.agno_knowledge,
                    lightrag_url=LIGHTRAG_URL,
                    debug=self.debug,
                )
                logger.info(
                    "Created Knowledge Coordinator for unified knowledge queries"
                )

                # If recreate is True, clear all memories AFTER memory system is initialized
                if recreate and self.enable_memory:
                    logger.info(
                        "Recreate flag is True, clearing all memories after memory system initialization"
                    )
                    clear_result = await self.memory_manager.clear_all_memories()
                    logger.info("Memory clear result: %s", clear_result)

                logger.info("Initialized Agno storage and knowledge backend")
            else:
                logger.info(
                    "Memory disabled, skipping storage and knowledge initialization"
                )

            # Get MCP tools as function wrappers (no pre-initialization)
            mcp_tool_functions = []
            if self.enable_mcp:
                mcp_tool_functions = await self._get_mcp_tools()
                tools.extend(mcp_tool_functions)
                logger.info("Added %d MCP tools to agent", len(mcp_tool_functions))

            # Get memory tools from the memory manager
            memory_tool_functions = []
            if self.enable_memory:
                memory_tool_functions = await self.memory_manager.get_memory_tools()
                tools.extend(memory_tool_functions)
                logger.info(
                    "Added %d memory tools to agent", len(memory_tool_functions)
                )

            # Create the agno agent with direct parameter passing for visibility
            self.agent = Agent(
                model=model,
                tools=tools,
                instructions=self.instruction_manager.create_instructions(),
                markdown=True,
                show_tool_calls=self.debug,
                name="Personal AI Agent",
                agent_id="personal_agent",
                user_id=self.user_id,
                enable_agentic_memory=False,  # Disable agno's native memory to avoid saving everything!
                enable_user_memories=True,  # Enable agno's native memory
                add_history_to_messages=True,  # Add conversation history to context
                num_history_responses=3,
                knowledge=self.agno_knowledge if self.enable_memory else None,
                search_knowledge=(
                    True if self.enable_memory and self.agno_knowledge else False
                ),  # Enable automatic knowledge search
                storage=(self.agno_storage if self.enable_memory else None),
                memory=(
                    self.agno_memory if self.enable_memory else None
                ),  # Don't pass memory to avoid auto-storage conflicts
                # Enable telemetry and verbose logging
                debug_mode=self.debug,
                # Enable streaming for intermediate steps
                stream_intermediate_steps=True,  # Required for aprint_response to work correctly
                stream=True,
            )

            if self.enable_memory and self.agno_knowledge:
                logger.info("Agent configured with knowledge base search")

            # Calculate tool counts for logging using already-created tool lists
            mcp_tool_count = len(mcp_tool_functions)
            memory_tool_count = len(memory_tool_functions)

            logger.info(
                "Successfully initialized agno agent with native storage: %d total tools (%d MCP, %d memory)",
                len(tools),
                mcp_tool_count,
                memory_tool_count,
            )

            # Display splash screen if enabled
            if SHOW_SPLASH_SCREEN:
                import importlib.metadata

                agent_info = self.get_agent_info()
                agent_version = importlib.metadata.version("personal-agent")
                display_splash_screen(agent_info, agent_version)

            return True

        except Exception as e:
            logger.error("Failed to initialize agno agent: %s", e)
            return False

    async def run(
        self, query: str, stream: bool = False, add_thought_callback=None
    ) -> Union[str, Dict[str, Any]]:
        """Run a query through the agno agent, allowing for native tool execution.

        Args:
            query: User query to process
            stream: Whether to stream the response
            add_thought_callback: Optional callback for adding thoughts during processing

        Returns:
            Agent's final string response or response dictionary

        Raises:
            RuntimeError: If agent is not initialized
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        try:
            if add_thought_callback:
                add_thought_callback("🚀 Executing agno agent...")

            # The agent will handle the full tool-use loop internally
            # Since the agent is configured with stream=True, arun returns an async generator
            response_generator = await self.agent.arun(query, user_id=self.user_id)

            # Check if we got a generator (streaming) or a direct response
            if hasattr(response_generator, "__aiter__"):
                # It's an async generator, consume it to get the final response
                # Following the working example pattern from github_agent_streamlit.py
                final_response = None
                response_content = ""
                all_tools_used = []

                async for chunk in response_generator:
                    # Look for individual tool in chunk (singular, like the working example)
                    if hasattr(chunk, "tool") and chunk.tool:
                        all_tools_used.append(chunk.tool)
                        logger.debug(
                            f"Found tool in chunk: {getattr(chunk.tool, 'name', 'Unknown')}"
                        )

                    # Look for content in RunResponse events (like the working example)
                    if (
                        hasattr(chunk, "event")
                        and chunk.event == "RunResponse"
                        and hasattr(chunk, "content")
                        and chunk.content is not None
                    ):
                        response_content += chunk.content

                    # Keep track of the last chunk
                    final_response = chunk

                # Create a response object with collected tools
                if final_response:
                    # Create a simple object to hold tools for compatibility
                    class ResponseWithTools:
                        def __init__(self, original_response, tools):
                            self.tool_calls = (
                                tools  # Store as tool_calls for compatibility
                            )
                            self.tools = tools  # Also store as tools
                            # Copy other attributes from original response
                            for attr in dir(original_response):
                                if not attr.startswith("_") and attr not in [
                                    "tool_calls",
                                    "tools",
                                ]:
                                    try:
                                        setattr(
                                            self, attr, getattr(original_response, attr)
                                        )
                                    except:
                                        pass

                    if all_tools_used:
                        final_response = ResponseWithTools(
                            final_response, all_tools_used
                        )
                    else:
                        # Ensure we have empty tool_calls for consistency
                        if not hasattr(final_response, "tool_calls"):
                            final_response.tool_calls = []

                # Store the final response for tool call inspection
                self._last_response = final_response

                # Use tool_manager to analyze tool calls if needed
                if all_tools_used:
                    logger.debug(
                        f"Agent used {len(all_tools_used)} tools in this response"
                    )

                if add_thought_callback:
                    add_thought_callback("✅ Agent execution complete.")

                return response_content
            else:
                # It's a direct response object
                self._last_response = response_generator

                # Use tool_manager to analyze tool calls if needed
                if (
                    hasattr(response_generator, "tool_calls")
                    and response_generator.tool_calls
                ):
                    logger.debug(
                        f"Agent used {len(response_generator.tool_calls)} tools in this response"
                    )

                if add_thought_callback:
                    add_thought_callback("✅ Agent execution complete.")

                return (
                    response_generator.content
                    if hasattr(response_generator, "content")
                    else str(response_generator)
                )

        except Exception as e:
            logger.error("Error running agno agent: %s", e)
            if add_thought_callback:
                add_thought_callback(f"❌ Error: {str(e)}")
            return f"Error processing request: {str(e)}"

    async def store_user_memory(
        self, content: str = "", topics: Union[List[str], str, None] = None
    ) -> MemoryStorageResult:
        """Store information as a user memory in both local SQLite and LightRAG graph systems.

        This is a public method that delegates to the memory_manager.

        Args:
            content: The information to store as a memory
            topics: Optional list of topics/categories for the memory (None = auto-classify)

        Returns:
            MemoryStorageResult: Structured result with detailed status information
        """
        return await self.memory_manager.store_user_memory(content, topics)

    async def _restate_user_fact(self, content: str) -> str:
        """Restate a user fact from first-person to third-person.

        Delegates to the memory_manager for processing.

        Args:
            content: The original fact from the user

        Returns:
            The restated fact
        """
        return self.memory_manager.restate_user_fact(content)

    async def seed_entity_in_graph(self, entity_name: str, entity_type: str) -> bool:
        """Seed an entity into the graph by creating and uploading a physical file.

        Delegates to the memory_manager for processing.

        Args:
            entity_name: Name of the entity to create
            entity_type: Type of the entity

        Returns:
            True if entity was successfully seeded
        """
        return await self.memory_manager.seed_entity_in_graph(entity_name, entity_type)

    async def check_entity_exists(self, entity_name: str) -> bool:
        """Check if entity exists in the graph.

        Delegates to the memory_manager for processing.

        Args:
            entity_name: Name of the entity to check

        Returns:
            True if entity exists
        """
        return await self.memory_manager.check_entity_exists(entity_name)

    async def clear_all_memories(self) -> str:
        """Clear all memories from both SQLite and LightRAG systems.

        Delegates to the memory_manager for processing.

        Returns:
            str: Success or error message
        """
        return await self.memory_manager.clear_all_memories()

    async def query_lightrag_knowledge_direct(
        self, query: str, params: dict = None
    ) -> str:
        """Directly query the LightRAG knowledge base and return the raw response.

        Args:
            query: The query string to search in the knowledge base
            params: A dictionary of query parameters (mode, response_type, top_k, etc.)

        Returns:
            String with query results exactly as LightRAG returns them
        """
        if not query or not query.strip():
            return "❌ Error: Query cannot be empty"

        # Use default parameters if none provided
        if params is None:
            params = {}

        # Set up the query parameters with defaults
        query_params = {
            "query": query.strip(),
            "mode": params.get("mode", "global"),
            "response_type": params.get("response_type", "Multiple Paragraphs"),
            "top_k": params.get("top_k", 10),
            "only_need_context": params.get("only_need_context", False),
            "only_need_prompt": params.get("only_need_prompt", False),
            "stream": params.get("stream", False),
        }

        # Add optional parameters if provided
        if "max_token_for_text_unit" in params:
            query_params["max_token_for_text_unit"] = params["max_token_for_text_unit"]
        if "max_token_for_global_context" in params:
            query_params["max_token_for_global_context"] = params[
                "max_token_for_global_context"
            ]
        if "max_token_for_local_context" in params:
            query_params["max_token_for_local_context"] = params[
                "max_token_for_local_context"
            ]
        if "conversation_history" in params:
            query_params["conversation_history"] = params["conversation_history"]
        if "history_turns" in params:
            query_params["history_turns"] = params["history_turns"]
        if "ids" in params:
            query_params["ids"] = params["ids"]

        try:
            # Use the correct LightRAG URL and endpoint
            from ..config.settings import LIGHTRAG_URL

            url = f"{LIGHTRAG_URL}/query"

            logger.debug(f"Querying LightRAG at {url} with params: {query_params}")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=query_params, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Extract the response content
                        if isinstance(result, dict):
                            content = result.get(
                                "response", result.get("content", str(result))
                            )
                        else:
                            content = str(result)

                        if content and content.strip():
                            logger.info(f"LightRAG query successful: {query[:50]}...")
                            return content
                        else:
                            return f"🔍 No relevant knowledge found for '{query}'. Try different keywords or add more knowledge to your base."
                    else:
                        error_text = await response.text()
                        logger.warning(
                            f"LightRAG query failed with status {response.status}: {error_text}"
                        )
                        return f"❌ Error querying knowledge base (status {response.status}): {error_text}"

        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to LightRAG server: {e}")
            return f"❌ Error connecting to knowledge base server: {str(e)}"
        except Exception as e:
            logger.error(f"Error querying LightRAG knowledge base: {e}")
            return f"❌ Error querying knowledge base: {str(e)}"

    async def _get_mcp_tools(self) -> List:
        """Create MCP tools as native async functions compatible with Agno.

        Returns:
            List of MCP tool functions
        """
        logger.info(
            "_get_mcp_tools called - enable_mcp: %s, mcp_servers: %s",
            self.enable_mcp,
            self.mcp_servers,
        )

        if not self.enable_mcp:
            logger.info("MCP disabled - enable_mcp is False")
            return []

        if not self.mcp_servers:
            logger.info(
                "No MCP servers configured - mcp_servers is empty: %s", self.mcp_servers
            )
            return []

        # This method is complex and specific to MCP integration
        # For now, we'll keep the original implementation
        # In the future, this could be moved to the tool_manager
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

                from textwrap import dedent

                from agno.tools.mcp import MCPTools
                from mcp import ClientSession, StdioServerParameters
                from mcp.client.stdio import stdio_client

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
                                    model=self.model_manager.create_model(),
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

    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the agent configuration and tools.

        Returns:
            Dictionary containing detailed agent configuration and tool information
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
            "lightrag_knowledge_enabled": self.lightrag_knowledge_enabled,
            "mcp_enabled": self.enable_mcp,
            "debug_mode": self.debug,
            "user_id": self.user_id,
            "initialized": self.agent is not None,
            "storage_dir": self.storage_dir,
            "knowledge_dir": self.knowledge_dir,
            "lightrag_url": LIGHTRAG_URL,
            "lightrag_memory_url": LIGHTRAG_MEMORY_URL,
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

        Args:
            console: Optional Rich Console instance. If None, creates a new one.
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
        main_table.add_row("Model Provider", f"{info['model_provider']}")
        main_table.add_row("Model Name", info["model_name"])
        main_table.add_row("Memory Enabled", str(info["memory_enabled"]))
        main_table.add_row("Knowledge Enabled", str(info["knowledge_enabled"]))
        main_table.add_row(
            "LightRAG Knowledge", str(info["lightrag_knowledge_enabled"])
        )
        main_table.add_row("MCP Enabled", str(info["mcp_enabled"]))
        main_table.add_row("Debug Mode", str(info["debug_mode"]))
        main_table.add_row("User ID", info["user_id"])
        main_table.add_row("Storage Directory", info["storage_dir"])
        main_table.add_row("Knowledge Directory", info["knowledge_dir"])
        main_table.add_row("Total Tools", str(info["tool_counts"]["total"]))

        console.print(main_table)

        # Tools table
        tools_table = Table(
            title="🛠️ Available Tools",
            show_header=True,
            header_style="bold magenta",
        )
        tools_table.add_column("Name", style="cyan")
        tools_table.add_column("Type", style="yellow")
        tools_table.add_column("Description", style="green")

        # Add built-in tools
        for tool in info["built_in_tools"]:
            tools_table.add_row(
                tool["name"], tool["type"], tool.get("description", "No description")
            )

        # Add MCP tools
        for tool in info["mcp_tools"]:
            tools_table.add_row(
                tool["name"], tool["type"], tool.get("description", "No description")
            )

        console.print(tools_table)

        # MCP servers table if enabled
        if info["mcp_enabled"] and info["mcp_servers"]:
            mcp_table = Table(
                title="🔌 MCP Servers",
                show_header=True,
                header_style="bold magenta",
            )
            mcp_table.add_column("Server Name", style="cyan")
            mcp_table.add_column("Command", style="yellow")
            mcp_table.add_column("Description", style="green")
            mcp_table.add_column("Args Count", style="blue")
            mcp_table.add_column("Env Vars", style="blue")

            for server_name, server_info in info["mcp_servers"].items():
                mcp_table.add_row(
                    server_name,
                    server_info["command"],
                    server_info["description"],
                    str(server_info["args_count"]),
                    str(server_info["env_vars"]),
                )

            console.print(mcp_table)

    async def cleanup(self) -> None:
        """Clean up resources when the agent is being shut down.

        This method is called during application shutdown to properly
        clean up any resources, connections, or background tasks.
        """
        try:
            logger.info("Cleaning up AgnoPersonalAgent resources...")

            # Clean up agent resources
            if self.agent:
                # Clear the agent reference
                self.agent = None
                logger.debug("Cleared agent reference")

            # Clean up storage references
            if self.agno_storage:
                self.agno_storage = None
                logger.debug("Cleared storage reference")

            if self.agno_knowledge:
                self.agno_knowledge = None
                logger.debug("Cleared knowledge reference")

            if self.agno_memory:
                self.agno_memory = None
                logger.debug("Cleared memory reference")

            if self.knowledge_coordinator:
                self.knowledge_coordinator = None
                logger.debug("Cleared knowledge coordinator reference")

            # Clean up manager references safely
            if self.model_manager:
                self.model_manager = None
                logger.debug("Cleared model manager reference")

            if self.instruction_manager:
                self.instruction_manager = None
                logger.debug("Cleared instruction manager reference")

            if self.memory_manager:
                self.memory_manager = None
                logger.debug("Cleared memory manager reference")

            if self.knowledge_manager:
                self.knowledge_manager = None
                logger.debug("Cleared knowledge manager reference")

            if self.tool_manager:
                self.tool_manager = None
                logger.debug("Cleared tool manager reference")

            logger.info("AgnoPersonalAgent cleanup completed successfully")

        except Exception as e:
            logger.warning("Error during AgnoPersonalAgent cleanup: %s", e)

    def sync_cleanup(self) -> None:
        """Synchronous cleanup method for compatibility.

        This method provides a synchronous interface to cleanup for cases
        where async cleanup cannot be used.
        """
        try:
            logger.info("Running synchronous cleanup...")

            # Clean up agent resources without async calls
            if self.agent:
                self.agent = None
                logger.debug("Cleared agent reference")

            # Clean up storage references
            if self.agno_storage:
                self.agno_storage = None
                logger.debug("Cleared storage reference")

            if self.agno_knowledge:
                self.agno_knowledge = None
                logger.debug("Cleared knowledge reference")

            if self.agno_memory:
                self.agno_memory = None
                logger.debug("Cleared memory reference")

            if self.knowledge_coordinator:
                self.knowledge_coordinator = None
                logger.debug("Cleared knowledge coordinator reference")

            # Clean up manager references
            self.model_manager = None
            self.instruction_manager = None
            self.memory_manager = None
            self.knowledge_manager = None
            self.tool_manager = None

            logger.info("Synchronous cleanup completed successfully")

        except Exception as e:
            logger.warning("Error during synchronous cleanup: %s", e)


def create_simple_personal_agent(
    storage_dir: str = None,
    knowledge_dir: str = None,
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
):
    """Create a simple personal agent following the working pattern from knowledge_agent_example.py

    This function creates an agent with knowledge base integration using the simple
    pattern that avoids async initialization complexity.

    Args:
        storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
        knowledge_dir: Directory containing knowledge files (defaults to DATA_DIR/knowledge)
        model_provider: LLM provider ('ollama' or 'openai')
        model_name: Model name to use

    Returns:
        Tuple of (Agent instance, knowledge_base) or (Agent, None) if no knowledge
    """
    from agno.knowledge.combined import CombinedKnowledgeBase

    # Create knowledge base (synchronous creation)
    knowledge_base = create_combined_knowledge_base(storage_dir, knowledge_dir)

    # Create the model
    if model_provider == "openai":
        model = OpenAIChat(id=model_name)
    elif model_provider == "ollama":
        model = Ollama(id=model_name)
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


async def load_agent_knowledge(knowledge_base, recreate: bool = False) -> None:
    """Load knowledge base content asynchronously.

    This should be called after creating the agent to load the knowledge content.

    Args:
        knowledge_base: Knowledge base instance to load
        recreate: Whether to recreate the knowledge base from scratch

    Returns:
        None
    """
    if knowledge_base:
        await load_combined_knowledge_base(knowledge_base, recreate=recreate)
        logger.info("✅ Knowledge base loaded successfully")
    else:
        logger.info("No knowledge base to load")


async def create_agno_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    enable_memory: bool = True,
    enable_mcp: bool = True,
    storage_dir: str = AGNO_STORAGE_DIR,
    knowledge_dir: str = AGNO_KNOWLEDGE_DIR,
    debug: bool = False,
    ollama_base_url: str = OLLAMA_URL,
    user_id: str = USER_ID,
    recreate: bool = False,
    instruction_level: InstructionLevel = InstructionLevel.STANDARD,
) -> AgnoPersonalAgent:
    """Create and initialize an agno-based personal agent.

    Args:
        model_provider: LLM provider ('ollama' or 'openai')
        model_name: Model name to use
        enable_memory: Whether to enable memory and knowledge features
        enable_mcp: Whether to enable MCP tool integration
        storage_dir: Directory for Agno storage files
        knowledge_dir: Directory containing knowledge files to load
        debug: Enable debug mode
        ollama_base_url: Base URL for Ollama API
        user_id: User identifier for memory operations
        recreate: Whether to recreate knowledge bases
        instruction_level: The sophistication level for agent instructions

    Returns:
        Initialized agent instance
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
        instruction_level=instruction_level,
    )

    success = await agent.initialize(recreate=recreate)
    if not success:
        raise RuntimeError("Failed to initialize agno agent")

    return agent
