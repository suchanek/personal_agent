"""
Agno-powered Personal AI Agent core.

This module implements a production-ready personal agent built directly on
agno.agent.Agent with a robust, lazy-initialized runtime and a unified approach
to storage, knowledge, semantic memory, tools, and instructions while retaining
backward compatibility with existing integrations.

Highlights:
- Lazy, thread-safe initialization with asyncio.Lock; eager initialization
  is available via factory helpers.
- Pluggable LLM backends (Ollama/OpenAI) managed through a model manager.
- Per-user storage path resolution with configurable defaults and overrides.
- Knowledge system:
  * Combined knowledge base creation and asynchronous loading.
  * Optional LightRAG integration and a coordinator for unified knowledge queries.
- Memory system:
  * SemanticMemoryManager-backed agent memory with LightRAG endpoints.
  * Public methods for storing, restating, seeding, checking, and clearing memories.
- Tools:
  * Curated built-ins (Google Search, Calculator, YFinance, Python, Shell, filesystem).
  * Consolidated KnowledgeTools and PersagMemoryTools when memory is enabled.
  * Optional MCP server tool integration controlled by configuration.
- Instructions:
  * Dynamic instruction assembly via an instruction manager and rich introspection.

Public entry points (selected):
- AgnoPersonalAgent: async initialize and run flows, memory and knowledge helpers,
  detailed agent info and pretty-printing, and cleanup routines.
- Factories: create_with_init() (class method) and create_agno_agent() (function)
  for eager, fully-initialized agent instances.
- Convenience: create_simple_personal_agent() for a synchronous pattern and
  load_agent_knowledge() for async knowledge loading.

Initialization order of operations:
1) Create Agno storage
2) Create combined knowledge base
3) Asynchronously load knowledge
4) Create semantic memory
5) Initialize managers (model, instructions, memory, knowledge, tools)
6) Assemble tools
7) Build instructions
8) Wire Agent fields (model, tools, instructions, storage/knowledge/memory)

This module is part of personal_agent.core and coordinates with the model,
instruction, memory, knowledge, and tool managers as well as storage and
knowledge-coordination utilities.

Author: Eric G. Suchanek, PhD
Last revision: 2025-08-14 20:09:59
"""

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import aiohttp
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools
from agno.tools.dalle import DalleTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.pubmed import PubmedTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.yfinance import YFinanceTools
from agno.utils.pprint import pprint_run_response
from rich.console import Console
from rich.table import Table

from ..config import get_mcp_servers
from ..config.runtime_config import get_config
from ..config.settings import (
    LOG_LEVEL,
    SHOW_SPLASH_SCREEN,
)
from ..tools.knowledge_tools import KnowledgeTools

# PersagMemoryTools is no longer used - memory functions are now standalone
# from ..tools.persag_memory_tools import PersagMemoryTools
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
from .user_manager import UserManager

# Configure logging
logger = setup_logging(__name__, level=LOG_LEVEL)


class AgnoPersonalAgent(Agent):
    """
    Refactored Agno-based Personal AI Agent that inherits directly from Agent.

    This class uses the proven initialization pattern from the working team
    implementation while maintaining backward compatibility with existing code.
    """

    def __init__(
        self,
        model: Optional[Any] = None,  # Accept pre-created model
        enable_memory: Optional[bool] = None,
        enable_mcp: Optional[bool] = None,
        debug: Optional[bool] = None,
        user_id: Optional[str] = None,
        recreate: Optional[bool] = None,
        instruction_level: Optional[InstructionLevel] = None,
        seed: Optional[int] = None,
        alltools: Optional[bool] = None,
        initialize_agent: Optional[bool] = False,
        stream: Optional[bool] = False,
        use_remote: Optional[bool] = None,
        **kwargs,  # Accept additional kwargs for backward compatibility
    ) -> None:
        """Initialize the Agno Personal Agent.

        This constructor is designed to be lightweight. It pulls configuration
        from the centralized `PersonalAgentConfig` singleton but allows for
        overrides via parameters, which is useful for testing.

        Args:
            model: Optional pre-created model instance.
            enable_memory: Override central config for enabling memory.
            enable_mcp: Override central config for enabling MCP.
            debug: Override central config for debug mode.
            user_id: Override central config for the user ID.
            recreate: Override central config for recreating knowledge bases.
            instruction_level: Override central config for instruction sophistication.
            seed: Override central config for model reproducibility.
            alltools: Override central config for enabling all tools.
            initialize_agent: Force immediate initialization.
            stream: Set the default streaming behavior.
            use_remote: Override central config for using remote endpoints.
            **kwargs: Additional keyword arguments for the base Agent class.
        """
        # Get the centralized configuration singleton
        config = get_config()

        # Set properties, using constructor arguments as overrides, otherwise use central config
        self.user_id = user_id if user_id is not None else config.user_id
        self.model_provider = config.provider
        self.model_name = config.model
        self.enable_memory = (
            enable_memory if enable_memory is not None else config.enable_memory
        )
        self.use_remote = use_remote if use_remote is not None else config.use_remote
        self.debug = debug if debug is not None else config.debug_mode
        self.recreate = recreate if recreate is not None else False
        self.seed = seed if seed is not None else config.seed
        self.alltools = alltools if alltools is not None else True
        self.instruction_level = (
            instruction_level
            if instruction_level is not None
            else InstructionLevel.CONCISE
        )
        self.enable_mcp = enable_mcp if enable_mcp is not None else config.use_mcp

        user_manager = UserManager()
        self.user_details = user_manager.get_user_details(self.user_id)
        self.delta_year = self.user_details.get("delta_year", 0)
        self.cognitive_state = self.user_details.get("cognitive_state", 100)

        # Lazy initialization flag
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        self._force_init = initialize_agent

        # Set up storage paths from central config
        self.storage_dir = config.user_storage_dir
        self.knowledge_dir = config.user_knowledge_dir

        # Initialize component managers (will be set in _do_initialization())
        self.model_manager: Optional[AgentModelManager] = None
        self.instruction_manager: Optional[AgentInstructionManager] = None
        self.memory_manager: Optional[AgentMemoryManager] = None
        self.knowledge_manager: Optional[AgentKnowledgeManager] = None
        self.tool_manager: Optional[AgentToolManager] = None

        # Initialize separate tool classes
        self.knowledge_tools = None
        self.memory_tools = None

        # Storage components (will be set in _do_initialization())
        self.agno_storage = None
        self.agno_knowledge = None
        self.lightrag_knowledge = None
        self.lightrag_knowledge_enabled = False
        self.agno_memory = None
        self.knowledge_coordinator = None
        self.knowledge_ingestion_tools = None
        self.semantic_knowledge_ingestion_tools = None

        # Legacy compatibility fields
        self._last_response = None
        self._collected_tool_calls = []
        self.mcp_servers = get_mcp_servers() if self.enable_mcp else {}

        # Create the initial model to pass to super().__init__()
        # This ensures the base Agent class is initialized with a valid model
        # that respects the central configuration.
        if model is not None:
            initial_model = model
        else:
            # Use the new config-aware model creation (class method, no instantiation needed)
            initial_model = AgentModelManager.create_model_from_config()

        # Initialize base Agent with proper model to prevent OpenAI default
        super().__init__(
            name="Personal-Agent",
            model=initial_model,  # Set proper model immediately
            tools=[],  # Will be updated in _do_initialization()
            instructions=[],  # Will be updated in _do_initialization()
            markdown=True,
            show_tool_calls=self.debug,
            agent_id="personal-agent",  # Use hyphen to match team expectations
            user_id=self.user_id,
            enable_agentic_memory=False,  # Disable to avoid conflicts
            enable_user_memories=False,  # Use our custom tools instead
            add_history_to_messages=True,
            num_history_responses=3,
            debug_mode=self.debug,
            stream_intermediate_steps=True,
            stream=stream,
            **kwargs,
        )

        logger.info(
            "Created AgnoPersonalAgent with model=%s, memory=%s, user_id=%s (lazy initialization=%s)",
            f"{self.model_provider}:{self.model_name}",
            self.enable_memory,
            self.user_id,
            not self._force_init,
        )

        # Force initialization if requested
        if self._force_init:
            logger.debug(
                "Force initialization requested - initializing agent synchronously"
            )
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                # If we're in a running loop, we can't use asyncio.run()
                logger.warning(
                    "Event loop detected - agent will initialize on first use"
                )
            except RuntimeError:
                # No running event loop, safe to initialize now
                try:
                    asyncio.run(self.initialize())
                    logger.warning(
                        "Agent initialized synchronously with %d tools",
                        len(self.tools) if self.tools else 0,
                    )
                except RuntimeError as e:
                    logger.error("Failed to force initialize agent: %s", e)
                    raise e

    async def _ensure_initialized(self) -> None:
        """Ensure the agent is initialized, performing lazy initialization if needed."""
        if self._initialized:
            return

        async with self._initialization_lock:
            # Double-check pattern to avoid race conditions
            if self._initialized:
                return

            logger.info("🚀 Performing lazy initialization of AgnoPersonalAgent")
            success = await self._do_initialization(self.recreate)
            if not success:
                raise RuntimeError("Failed to initialize AgnoPersonalAgent")
            self._initialized = True
            logger.info("✅ Lazy initialization completed successfully")

    async def initialize(self, recreate: bool = False) -> bool:
        """Initialize the agent.

        Args:
            recreate: Whether to recreate the agent knowledge bases

        Returns:
            True if initialization successful, False otherwise
        """
        logger.info(
            "🚀 AgnoPersonalAgent.initialize() called with recreate=%s",
            recreate,
        )

        # Update recreate flag if different from constructor
        if recreate != self.recreate:
            self.recreate = recreate

        try:
            await self._ensure_initialized()
            return True
        except Exception as e:
            logger.error("Failed to initialize AgnoPersonalAgent: %s", e, exc_info=True)
            return False

    async def _do_initialization(self, recreate: bool = False) -> bool:
        """Perform the actual initialization work.

        Args:
            recreate: Whether to recreate the agent knowledge bases

        Returns:
            True if initialization successful, False otherwise
        """
        logger.debug(
            "🚀 AgnoPersonalAgent._do_initialization() called with recreate=%s",
            recreate,
        )
        config = get_config()

        try:
            # 1. Create Agno storage (CRITICAL: Must be done first)
            self.agno_storage = create_agno_storage(self.storage_dir)
            logger.debug("Created Agno storage at: %s", self.storage_dir)

            # 2. Create combined knowledge base (CRITICAL: Must be done before loading)
            self.agno_knowledge = create_combined_knowledge_base(
                self.storage_dir, self.knowledge_dir, self.agno_storage
            )

            # 3. Load knowledge base content (CRITICAL: Must be async)
            if self.agno_knowledge:
                await load_combined_knowledge_base(
                    self.agno_knowledge, recreate=recreate
                )
                logger.debug("Loaded Agno combined knowledge base content")

            # 4. Create memory with SemanticMemoryManager (CRITICAL: Must be done after storage)
            self.agno_memory = create_agno_memory(
                self.storage_dir, debug_mode=self.debug
            )

            if self.agno_memory:
                logger.debug(
                    "Created Agno memory with SemanticMemoryManager at: %s",
                    self.storage_dir,
                )
            else:
                logger.error("Failed to create memory system")
                return False

            # 5. Initialize managers (CRITICAL: Must be done after agno_memory creation)
            # Get config to pass required parameters to AgentModelManager
            self.model_manager = AgentModelManager(
                model_provider=config.provider,
                model_name=config.model,
                ollama_base_url=config.get_effective_ollama_url(),
                seed=self.seed,
            )
            self.instruction_manager = AgentInstructionManager(
                self.instruction_level,
                self.user_id,
                self.enable_memory,
                self.enable_mcp,
                self.mcp_servers,
            )

            self.memory_manager = AgentMemoryManager(
                self.user_id,
                self.storage_dir,
                self.agno_memory,
                config.lightrag_url,  # Use central config
                config.lightrag_memory_url,  # Use central config
                self.enable_memory,
            )

            # Initialize the memory manager with the created agno_memory
            self.memory_manager.initialize(self.agno_memory)

            self.knowledge_manager = AgentKnowledgeManager(
                self.user_id,
                self.storage_dir,
                config.lightrag_url,  # Use central config
                config.lightrag_memory_url,  # Use central config
            )

            self.tool_manager = AgentToolManager(self.user_id, self.storage_dir)

            # 6. Create tool instances (CRITICAL: Must be done after managers)
            if self.enable_memory:
                self.knowledge_tools = KnowledgeTools(
                    self.knowledge_manager, self.agno_knowledge
                )
                # PersagMemoryTools is no longer used - memory functions are now standalone
                self.memory_tools = None

            # 7. Create the model from the central config
            model = self.model_manager.create_model_from_config()
            logger.debug("Created model: %s", config.model)
            # we are using a subset for now
            tools = [
                self.store_user_memory,
                self.query_memory,
                self.get_all_memories,
                self.list_all_memories,
                self.update_memory,
            ]

            # Add built-in tools if alltools is enabled
            if self.alltools:
                all_tools = [
                    DuckDuckGoTools(),
                    # CalculatorTools(enable_all=True),
                    YFinanceTools(
                        stock_price=True,
                        company_info=True,
                        stock_fundamentals=True,
                        key_financial_ratios=True,
                        analyst_recommendations=True,
                    ),
                    PythonTools(
                        base_dir="/tmp",
                        run_code=True,
                        list_files=True,
                        run_files=True,
                        read_files=True,
                        uv_pip_install=True,
                    ),
                    ShellTools(base_dir=Path(config.home_dir)),
                    PersonalAgentFilesystemTools(),
                    PubmedTools(),
                ]
                tools.extend(all_tools)
                logger.info(f"Added {len(all_tools)} built-in tools")
            else:
                logger.info("alltools=False, only memory tools will be available")

            # ALWAYS add memory tools if memory is enabled, regardless of alltools setting
            if self.enable_memory:
                if self.knowledge_tools:
                    knowledge_tools = [
                        self.knowledge_tools,  # Now contains all knowledge functionality
                    ]
                    tools.extend(knowledge_tools)
                    logger.debug(
                        "Added KnowledgeTools (memory functions are now standalone methods)"
                    )
                else:
                    logger.warning(
                        "Memory enabled but knowledge tools not properly initialized"
                    )
            else:
                logger.warning("Memory disabled - no memory tools added")

            # 9. Create instructions using the AgentInstructionManager
            # For LM Studio, use minimal instructions to avoid context issues
            if config.provider == "lm-studio":
                # Use minimal instructions for LM Studio to avoid context window issues
                instructions = [
                    "You are a helpful AI assistant.",
                    "Be direct and helpful in your responses.",
                    "Use tools when needed for calculations or information.",
                ]
                logger.info(
                    "Using minimal instructions for LM Studio to avoid context issues"
                )
            else:
                instructions = self.instruction_manager.create_instructions()
                logger.info(
                    "Generated dynamic instructions using AgentInstructionManager with level: %s",
                    self.instruction_level.name,
                )

            # 10. Update the Agent's components (KEY: Update inherited Agent properties)
            self.model = model
            self.tools = tools
            self.instructions = instructions

            # Update Agent's storage components
            if self.enable_memory:
                self.storage = self.agno_storage
                self.knowledge = self.agno_knowledge
                self.memory = self.agno_memory
                self.search_knowledge = True

            # Create Knowledge Coordinator
            if self.enable_memory:
                self.knowledge_coordinator = create_knowledge_coordinator(
                    agno_knowledge=self.agno_knowledge,
                    lightrag_url=config.lightrag_url,  # Use central config
                    debug=config.debug_mode,  # Use central config
                )
                logger.debug(
                    "Created Knowledge Coordinator for unified knowledge queries"
                )

            logger.info(
                "Successfully initialized AgnoPersonalAgent with %d tools",
                len(tools),
            )

            # Display splash screen if enabled
            if SHOW_SPLASH_SCREEN:
                import importlib.metadata

                agent_info = self.get_agent_info()
                agent_version = importlib.metadata.version("personal-agent")
                display_splash_screen(agent_info, agent_version)

            return True

        except Exception as e:
            logger.error("Failed to initialize AgnoPersonalAgent: %s", e, exc_info=True)
            return False

    async def run(
        self, query: str, stream: bool = True, add_thought_callback=None, **kwargs
    ) -> Union[Iterator[RunResponse], str]:
        """Run a query through the agent following the proper RunResponse pattern.

        This method follows the proper pattern for handling RunResponse as shown in the
        agno documentation example. When stream=True, it returns an Iterator[RunResponse].
        When stream=False, it collects the response and returns a string.

        Args:
            query: User query to process.
            stream: Whether to return streaming Iterator[RunResponse] or collected string.
            add_thought_callback: Optional callback for adding thoughts.

        Returns:
            Iterator[RunResponse] when stream=True, str when stream=False.
        """
        await self._ensure_initialized()

        if add_thought_callback:
            add_thought_callback("🚀 Executing agent...")

        # Use the proper pattern: call super().run() with stream parameter
        run_result = super().run(query, user_id=self.user_id, stream=stream, **kwargs)

        if stream:
            # Return the stream directly for proper RunResponse handling
            return run_result
        else:
            # Collect all chunks from the stream for backward compatibility
            content_parts = []
            self._collected_tool_calls = []

            # Handle both iterator and single response cases
            try:
                # Try to iterate over the result
                for chunk in run_result:  # Use regular for loop, not async for
                    # Store the last response for tool call extraction
                    self._last_response = chunk

                    # Collect content from chunks
                    if hasattr(chunk, "content") and chunk.content:
                        content_parts.append(chunk.content)
            except TypeError:
                # Single response case - not iterable
                self._last_response = run_result
                if hasattr(run_result, "content") and run_result.content:
                    content_parts.append(run_result.content)

            # Join all content parts
            content = "".join(content_parts)

            # Extract tool calls from the final run_response using the proper pattern
            if self.run_response and self.run_response.messages:
                for message in self.run_response.messages:
                    if message.role == "assistant" and message.tool_calls:
                        self._collected_tool_calls.extend(message.tool_calls)
                        if self.debug:
                            logger.debug(f"Tool calls found: {message.tool_calls}")

            if add_thought_callback:
                add_thought_callback("✅ Agent execution complete.")

            # Validate and return content
            validated_content = self._validate_response_content(content, query)
            return validated_content

    def get_last_tool_calls(self) -> List[Any]:
        """Get tool calls from the last agent run.

        Returns:
            List of ToolExecution objects from the most recent run.
        """
        return self._collected_tool_calls

    def print_run_response(
        self,
        run_response: Union[Iterator[RunResponse], RunResponse],
        markdown: bool = True,
        show_time: bool = True,
    ) -> None:
        """Print a run response using agno's pprint_run_response function.

        This method provides easy access to the agno pprint functionality for
        displaying run responses with proper formatting, including metrics
        per message and tool calls as shown in the example pattern.

        Args:
            run_response: The RunResponse or Iterator[RunResponse] to print
            markdown: Whether to format output as markdown
            show_time: Whether to show timing information
        """
        pprint_run_response(run_response, markdown=markdown, show_time=show_time)

    def print_run_response_with_metrics(self) -> None:
        """Print the last run response with detailed metrics per message.

        This method implements the pattern shown in the task description for
        printing metrics per message, including tool calls and message content.
        """
        if not self.run_response or not self.run_response.messages:
            logger.warning("No run response available to print metrics for")
            return

        print("=" * 60)
        print("RUN RESPONSE METRICS")
        print("=" * 60)

        # Print metrics per message
        for message in self.run_response.messages:
            if message.role == "assistant":
                if message.content:
                    print(f"Message: {message.content}")
                elif message.tool_calls:
                    print(f"Tool calls: {message.tool_calls}")
                print("---" * 5, "Metrics", "---" * 5)
                if hasattr(message, "metrics") and message.metrics:
                    from pprint import pprint

                    pprint(message.metrics)
                else:
                    print("No metrics available for this message")
                print("---" * 20)

    def _validate_response_content(self, content: str, query: str) -> str:
        """Validate and potentially fix response content.

        Args:
            content: The raw content from the agent response
            query: The original user query

        Returns:
            Validated and potentially fixed content
        """
        import re

        if not content or not content.strip():
            logger.warning(f"Empty response for query: {query[:50]}...")

            # Try to extract from response object attributes if available
            if self._last_response:
                for attr in ["text", "message", "output", "result"]:
                    if hasattr(self._last_response, attr):
                        alt_content = getattr(self._last_response, attr)
                        if alt_content and str(alt_content).strip():
                            logger.debug(f"Recovered content from {attr} attribute")
                            return str(alt_content)

            # Generate a simple fallback based on query
            if any(greeting in query.lower() for greeting in ["hello", "hi", "hey"]):
                return f"Hello {self.user_id}!"
            else:
                return "I'm here to help! What would you like to know?"

        return content

    async def store_user_memory(
        self, content: str = "", topics: Union[List[str], str, None] = None
    ) -> MemoryStorageResult:
        """Store information as a user memory in both local SQLite and LightRAG graph systems.

        This method delegates to the standalone memory function.

        Args:
            content: The information to store as a memory
            topics: Optional list of topics/categories for the memory (None = auto-classify)

        Returns:
            MemoryStorageResult: Structured result with detailed status information
        """
        from ..tools.memory_functions import store_user_memory

        return await store_user_memory(self, content, topics)

    async def query_memory(self, query: str, limit: Union[int, None] = None) -> str:
        """Search user memories using semantic search.

        This method delegates to the standalone memory function.

        Args:
            query: The query to search for in memories
            limit: Maximum number of memories to return

        Returns:
            str: Found memories or message if none found
        """
        from ..tools.memory_functions import query_memory

        return await query_memory(self, query, limit)

    async def list_all_memories(self) -> str:
        """List all memories in a simple, user-friendly format.

        This method delegates to the standalone memory function.

        Returns:
            str: Simplified list of all memories
        """
        from ..tools.memory_functions import list_all_memories

        return await list_all_memories(self)

    async def get_all_memories(self) -> str:
        """Get all user memories with full details.

        This method delegates to the standalone memory function.

        Returns:
            str: Formatted string of all memories
        """
        from ..tools.memory_functions import get_all_memories

        return await get_all_memories(self)

    async def update_memory(
        self, memory_id: str, content: str, topics: Union[List[str], str, None] = None
    ) -> str:
        """Update an existing memory.

        This method delegates to the standalone memory function.

        Args:
            memory_id: ID of the memory to update
            content: New memory content
            topics: Optional list of topics/categories for the memory

        Returns:
            str: Success or error message
        """
        from ..tools.memory_functions import update_memory

        return await update_memory(self, memory_id, content, topics)

    async def delete_memory(self, memory_id: str) -> str:
        """Delete a memory from both SQLite and LightRAG systems.

        This method delegates to the standalone memory function.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            str: Success or error message
        """
        from ..tools.memory_functions import delete_memory

        return await delete_memory(self, memory_id)

    async def get_recent_memories(self, limit: int = 10) -> str:
        """Get recent memories sorted by date.

        This method delegates to the standalone memory function.

        Args:
            limit: Maximum number of memories to return

        Returns:
            str: Formatted string of recent memories
        """
        from ..tools.memory_functions import get_recent_memories

        return await get_recent_memories(self, limit)

    async def get_memory_stats(self) -> str:
        """Get memory statistics including counts and topics.

        This method delegates to the standalone memory function.

        Returns:
            str: Formatted string with memory statistics
        """
        from ..tools.memory_functions import get_memory_stats

        return await get_memory_stats(self)

    async def get_memories_by_topic(
        self, topics: Union[List[str], str, None] = None, limit: Union[int, None] = None
    ) -> str:
        """Get memories filtered by topic.

        This method delegates to the standalone memory function.

        Args:
            topics: Topic or list of topics to filter memories by
            limit: Maximum number of memories to return

        Returns:
            str: Formatted string of memories matching the topics
        """
        from ..tools.memory_functions import get_memories_by_topic

        return await get_memories_by_topic(self, topics, limit)

    async def delete_memories_by_topic(self, topics: Union[List[str], str]) -> str:
        """Delete all memories associated with specific topics.

        This method delegates to the standalone memory function.

        Args:
            topics: Topic or list of topics to delete memories for

        Returns:
            str: Success or error message
        """
        from ..tools.memory_functions import delete_memories_by_topic

        return await delete_memories_by_topic(self, topics)

    async def get_memory_graph_labels(self) -> str:
        """Get the list of all entity and relation labels from the memory graph.

        This method delegates to the standalone memory function.

        Returns:
            str: Formatted string with entity and relation labels
        """
        from ..tools.memory_functions import get_memory_graph_labels

        return await get_memory_graph_labels(self)

    async def clear_all_memories(self) -> str:
        """Clear all memories from both SQLite and LightRAG systems.

        This method delegates to the standalone memory function.

        Returns:
            str: Success or error message
        """
        from ..tools.memory_functions import clear_all_memories

        return await clear_all_memories(self)

    async def get_graph_entity_count(self) -> int:
        """Get the count of entities/documents in the LightRAG memory graph.

        This method delegates to the standalone memory function.

        Returns:
            int: Number of entities/documents in the graph
        """
        from ..tools.memory_functions import get_graph_entity_count

        return await get_graph_entity_count(self)

    async def query_lightrag_knowledge_direct(
        self, query: str, params: dict = None, url: str = None
    ) -> str:
        """Directly query the LightRAG knowledge base and return the raw response.

        Args:
            query: The query string to search in the knowledge base
            params: A dictionary of query parameters (mode, response_type, top_k, etc.)
            url: The base URL of the LightRAG server. Defaults to the one in the config.

        Returns:
            String with query results exactly as LightRAG returns them
        """
        config = get_config()
        if url is None:
            url = config.lightrag_url

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
            final_url = f"{url}/query"

            logger.debug(
                f"Querying LightRAG at {final_url} with params: {query_params}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    final_url, json=query_params, timeout=60
                ) as response:
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

    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the agent configuration and tools.

        Returns:
            Dictionary containing detailed agent configuration and tool information
        """
        config = get_config()

        # Get basic tool info
        built_in_tools = []
        mcp_tools = []

        if hasattr(self, "tools") and self.tools:
            for tool in self.tools:
                # Get tool name - try multiple approaches for different tool types
                tool_name = None

                # Try common name attributes
                for name_attr in ["name", "__name__", "_name"]:
                    if hasattr(tool, name_attr):
                        tool_name = getattr(tool, name_attr)
                        if tool_name:
                            break

                # Fallback to class name
                if not tool_name:
                    tool_name = str(type(tool).__name__)

                # Get tool description
                tool_doc = getattr(tool, "__doc__", "No description available")

                # Clean up docstring for display
                if tool_doc:
                    tool_doc = tool_doc.strip().split("\n")[0]  # First line only

                # Classify tool type
                if tool_name.startswith("use_") and "_server" in tool_name:
                    mcp_tools.append(
                        {
                            "name": tool_name,
                            "description": tool_doc,
                            "type": "MCP Server",
                        }
                    )
                else:
                    # Determine if it's a built-in agno tool or custom tool
                    tool_type = "Built-in Tool"
                    if any(
                        keyword in tool_name.lower()
                        for keyword in ["memory", "knowledge", "ingestion"]
                    ):
                        tool_type = "Memory/Knowledge Tool"
                    elif "Tools" in tool_name:
                        tool_type = "Built-in Tool"

                    built_in_tools.append(
                        {
                            "name": tool_name,
                            "description": tool_doc,
                            "type": tool_type,
                        }
                    )

        knowledge_enabled = config.enable_memory and (
            self.agno_knowledge is not None or not self._initialized
        )

        return {
            "framework": "agno",
            "model_provider": config.provider,
            "model_name": config.model,
            "memory_enabled": config.enable_memory,
            "knowledge_enabled": knowledge_enabled,
            "lightrag_knowledge_enabled": self.lightrag_knowledge_enabled,
            "mcp_enabled": config.use_mcp,
            "debug_mode": config.debug_mode,
            "user_id": config.user_id,
            "initialized": self._initialized,
            "storage_dir": config.user_storage_dir,
            "knowledge_dir": config.user_knowledge_dir,
            "ollama_base_url": config.get_effective_ollama_url(),
            "lightrag_url": config.lightrag_url,
            "lightrag_memory_url": config.lightrag_memory_url,
            "tool_counts": {
                "total": len(built_in_tools) + len(mcp_tools),
                "built_in": len(built_in_tools),
                "mcp": len(mcp_tools),
                "mcp_servers": len(self.mcp_servers) if self.enable_mcp else 0,
            },
            "built_in_tools": built_in_tools,
            "mcp_tools": mcp_tools,
            "mcp_servers": {},  # Simplified for now
        }

    def print_agent_info(self, console: Optional[Console] = None) -> None:
        """Pretty print comprehensive agent information using Rich.

        Args:
            console: Optional Rich Console instance. If None, creates a new one.
        """
        if console is None:
            console = Console()

        info = self.get_agent_info()
        config = get_config()

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
        main_table.add_row("Debug Mode", str(info["debug_mode"]))
        main_table.add_row("User ID", info["user_id"])
        main_table.add_row("User Data Directory", config.user_data_dir)
        main_table.add_row("Storage Directory", info["storage_dir"])
        main_table.add_row("Knowledge Directory", info["knowledge_dir"])
        main_table.add_row("Total Tools", str(info["tool_counts"]["total"]))

        console.print(main_table)

        # Service Endpoints table
        endpoints_table = Table(
            title="🔌 Service Endpoints",
            show_header=True,
            header_style="bold magenta",
        )
        endpoints_table.add_column("Service", style="cyan")
        endpoints_table.add_column("URL", style="green")

        endpoints_table.add_row("Ollama", info["ollama_base_url"])
        endpoints_table.add_row("LightRAG Knowledge", info["lightrag_url"])
        endpoints_table.add_row("LightRAG Memory", info["lightrag_memory_url"])

        console.print(endpoints_table)

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

    async def cleanup(self) -> None:
        """Clean up resources when the agent is being shut down.

        This method is called during application shutdown to properly
        clean up any resources, connections, or background tasks.
        """
        try:
            logger.debug("Cleaning up AgnoPersonalAgent resources...")

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

            logger.debug("AgnoPersonalAgent cleanup completed successfully")

        except Exception as e:
            logger.warning("Error during AgnoPersonalAgent cleanup: %s", e)

    def sync_cleanup(self) -> None:
        """Synchronous cleanup method for compatibility.

        This method provides a synchronous interface to cleanup for cases
        where async cleanup cannot be used.
        """
        try:
            logger.debug("Running synchronous cleanup...")

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

            logger.debug("Synchronous cleanup completed successfully")

        except Exception as e:
            logger.warning("Error during synchronous cleanup: %s", e)

    @classmethod
    async def create_with_init(
        cls, **kwargs
    ) -> "AgnoPersonalAgent":
        """Create and fully initialize an AgnoPersonalAgent.

        This is an async factory method that creates the agent and immediately
        initializes it, which is useful when you need the agent to be ready
        to use immediately.

        Args:
            **kwargs: Configuration overrides for the agent constructor.

        Returns:
            Fully initialized AgnoPersonalAgent instance
        """
        # Create the agent instance, passing any overrides
        agent = cls(initialize_agent=False, **kwargs)

        # Now initialize it
        await agent._ensure_initialized()

        return agent

    # Legacy property for backward compatibility
    @property
    def agent(self):
        """Backward compatibility property - returns self since we ARE the agent now."""
        return self


def create_simple_personal_agent(
    storage_dir: str = None,
    knowledge_dir: str = None,
    model_provider: str = None,
    model_name: str = None,
):
    """Create a simple personal agent following the working pattern from knowledge_agent_example.py

    This function creates an agent with knowledge base integration using the simple
    pattern that avoids async initialization complexity.

    Args:
        storage_dir: Override for the storage directory.
        knowledge_dir: Override for the knowledge directory.
        model_provider: Override for the model provider.
        model_name: Override for the model name.

    Returns:
        Tuple of (Agent instance, knowledge_base) or (Agent, None) if no knowledge
    """
    from agno.knowledge.combined import CombinedKnowledgeBase

    config = get_config()

    # Use overrides or fall back to central config
    final_storage_dir = storage_dir or config.user_storage_dir
    final_knowledge_dir = knowledge_dir or config.user_knowledge_dir
    final_provider = model_provider or config.provider
    final_model_name = model_name or config.model

    # Create knowledge base (synchronous creation)
    knowledge_base = create_combined_knowledge_base(
        final_storage_dir, final_knowledge_dir
    )

    # Always use AgentModelManager to ensure consistent model creation
    model_manager = AgentModelManager(
        model_provider=final_provider,
        model_name=final_model_name,
    )
    model = model_manager.create_model()

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

    logger.debug("✅ Created simple personal agent")
    if knowledge_base:
        logger.debug("   Knowledge base: Enabled")
        logger.debug("   Search enabled: %s", agent.search_knowledge)
    else:
        logger.debug("   Knowledge base: None (no knowledge files found)")

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
        logger.debug("✅ Knowledge base loaded successfully")
    else:
        logger.debug("No knowledge base to load")


async def create_agno_agent(**kwargs) -> AgnoPersonalAgent:
    """Create and fully initialize an agno-based personal agent.

    This function creates an AgnoPersonalAgent and performs complete initialization,
    ensuring the agent is ready to use immediately upon return.

    Args:
        **kwargs: Configuration overrides for the agent constructor.

    Returns:
        Fully initialized AgnoPersonalAgent instance
    """
    logger.debug(
        "create_agno_agent() called - creating and initializing agent with proper init"
    )

    # Use the create_with_init class method to ensure proper initialization
    return await AgnoPersonalAgent.create_with_init(**kwargs)
