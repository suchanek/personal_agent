"""
Refactored Agno-based agent implementation for the Personal AI Agent.

This module provides a cleaner implementation of the AgnoPersonalAgent
that inherits directly from agno.agent.Agent and uses the proven initialization
pattern from the working team implementation.
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import aiohttp
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
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
    get_userid,
)
from ..tools.knowledge_ingestion_tools import KnowledgeIngestionTools
from ..tools.knowledge_tools import KnowledgeTools
from ..tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentSystemTools,
)
from ..tools.refactored_memory_tools import AgnoMemoryTools
from ..tools.semantic_knowledge_ingestion_tools import SemanticKnowledgeIngestionTools
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


@dataclass
class AgnoPersonalAgentConfig:
    """Configuration data for AgnoPersonalAgent."""

    model_provider: str = "ollama"
    model_name: str = LLM_MODEL
    enable_memory: bool = True
    storage_dir: str = AGNO_STORAGE_DIR
    knowledge_dir: str = AGNO_KNOWLEDGE_DIR
    debug: bool = False
    ollama_base_url: str = OLLAMA_URL
    user_id: str = None
    recreate: bool = False
    seed: Optional[int] = None


def create_ollama_model(model_name: str = LLM_MODEL) -> Any:
    """Create an Ollama model using AgentModelManager."""
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url=OLLAMA_URL,
        seed=None,
    )
    return model_manager.create_model()


class AgnoPersonalAgent(Agent):
    """
    Refactored Agno-based Personal AI Agent that inherits directly from Agent.

    This class uses the proven initialization pattern from the working team
    implementation while maintaining backward compatibility with existing code.
    """

    def __init__(
        self,
        model_provider: str = "ollama",
        model_name: str = LLM_MODEL,
        enable_memory: bool = True,
        enable_mcp: bool = True,  # Simplified: disable MCP by default
        storage_dir: str = AGNO_STORAGE_DIR,
        knowledge_dir: str = AGNO_KNOWLEDGE_DIR,
        debug: bool = False,
        ollama_base_url: str = OLLAMA_URL,
        user_id: str = None,
        recreate: bool = False,
        instruction_level: InstructionLevel = InstructionLevel.STANDARD,
        seed: Optional[int] = None,
        alltools: Optional[bool] = True,
        **kwargs,  # Accept additional kwargs for backward compatibility
    ) -> None:
        """Initialize the Agno Personal Agent.

        Args:
            model_provider: LLM provider ('ollama' or 'openai')
            model_name: Model name to use
            enable_memory: Whether to enable memory and knowledge features
            enable_mcp: Whether to enable MCP tool integration (simplified)
            storage_dir: Directory for Agno storage files
            knowledge_dir: Directory containing knowledge files to load
            debug: Enable debug logging and tool call visibility
            ollama_base_url: Base URL for Ollama API
            user_id: User identifier for memory operations
            recreate: Whether to recreate knowledge bases
            instruction_level: The sophistication level for agent instructions (kept for compatibility)
            seed: Optional seed for model reproducibility
        """
        # Store configuration
        self.config = AgnoPersonalAgentConfig(
            model_provider=model_provider,
            model_name=model_name,
            enable_memory=enable_memory,
            storage_dir=storage_dir,
            knowledge_dir=knowledge_dir,
            debug=debug,
            ollama_base_url=ollama_base_url,
            user_id=user_id,
            recreate=recreate,
            seed=seed,
        )

        # Legacy compatibility fields
        self.model_provider = model_provider
        self.model_name = model_name
        self.enable_memory = enable_memory
        self.enable_mcp = (
            enable_mcp and USE_MCP
        )  # Keep for compatibility but simplified
        self.debug = debug
        self.ollama_base_url = ollama_base_url
        self.user_id = user_id
        self.recreate = recreate
        self.instruction_level = instruction_level
        self.seed = seed
        self.alltools = alltools

        # Lazy initialization flag
        self._initialized = False
        self._initialization_lock = asyncio.Lock()

        # Set user_id with fallback
        if user_id is None:
            user_id = get_userid()
        self.user_id = user_id

        # Set up storage paths
        self._setup_storage_paths(storage_dir, knowledge_dir, user_id)

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

        # Initialize base Agent with minimal setup - will be updated in _do_initialization()
        super().__init__(
            name="Personal AI Agent",
            model=None,  # Will be set in _do_initialization()
            tools=[],  # Will be set in _do_initialization()
            instructions=[],  # Will be set in _do_initialization()
            markdown=True,
            show_tool_calls=debug,
            agent_id="personal-agent",  # Use hyphen to match team expectations
            user_id=user_id,
            enable_agentic_memory=False,  # Disable to avoid conflicts
            enable_user_memories=False,  # Use our custom tools instead
            add_history_to_messages=True,
            num_history_responses=3,
            debug_mode=debug,
            stream_intermediate_steps=True,
            stream=True,
        )

        logger.info(
            "Created AgnoPersonalAgent with model=%s, memory=%s, user_id=%s (lazy initialization)",
            f"{model_provider}:{model_name}",
            self.enable_memory,
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
        if user_id != get_userid():
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

        # Update config with resolved paths
        self.config.storage_dir = self.storage_dir
        self.config.knowledge_dir = self.knowledge_dir

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
        """Initialize the agent using the proven create_memory_agent() pattern.

        DEPRECATED: This method is kept for backward compatibility.
        Initialization now happens automatically when needed.

        Args:
            recreate: Whether to recreate the agent knowledge bases

        Returns:
            True if initialization successful, False otherwise
        """
        logger.info(
            "🚀 AgnoPersonalAgent.initialize() called with recreate=%s (deprecated - use constructor directly)",
            recreate,
        )

        # Update recreate flag if different from constructor
        if recreate != self.recreate:
            self.recreate = recreate
            self.config.recreate = recreate

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
        logger.info(
            "🚀 AgnoPersonalAgent._do_initialization() called with recreate=%s",
            recreate,
        )

        try:
            # 1. Create Agno storage (CRITICAL: Must be done first)
            self.agno_storage = create_agno_storage(self.storage_dir)
            logger.info("Created Agno storage at: %s", self.storage_dir)

            # 2. Create combined knowledge base (CRITICAL: Must be done before loading)
            self.agno_knowledge = create_combined_knowledge_base(
                self.storage_dir, self.knowledge_dir, self.agno_storage
            )

            # 3. Load knowledge base content (CRITICAL: Must be async)
            if self.agno_knowledge:
                await load_combined_knowledge_base(
                    self.agno_knowledge, recreate=recreate
                )
                logger.info("Loaded Agno combined knowledge base content")

            # 4. Create memory with SemanticMemoryManager (CRITICAL: Must be done after storage)
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
                return False

            # 5. Initialize managers (CRITICAL: Must be done after agno_memory creation)
            self.model_manager = AgentModelManager(
                self.model_provider, self.model_name, self.ollama_base_url, self.seed
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
                LIGHTRAG_URL,
                LIGHTRAG_MEMORY_URL,
                self.enable_memory,
            )

            # Initialize the memory manager with the created agno_memory
            self.memory_manager.initialize(self.agno_memory)

            self.knowledge_manager = AgentKnowledgeManager(
                self.user_id, self.storage_dir, LIGHTRAG_URL, LIGHTRAG_MEMORY_URL
            )

            self.tool_manager = AgentToolManager(self.user_id, self.storage_dir)

            # 6. Create tool instances (CRITICAL: Must be done after managers)
            if self.enable_memory:
                self.knowledge_tools = KnowledgeTools(self.knowledge_manager)
                self.knowledge_ingestion_tools = KnowledgeIngestionTools()
                self.semantic_knowledge_ingestion_tools = (
                    SemanticKnowledgeIngestionTools()
                )
                self.memory_tools = AgnoMemoryTools(self.memory_manager)

            # 7. Create the model
            model = self.model_manager.create_model()
            logger.info("Created model: %s", self.model_name)
            tools = []
            # 8. Prepare tools list - MEMORY AGENT ONLY: Just memory and knowledge tools
            if self.alltools:
                tools = (
                    [  # Add GoogleSearch tools directly for web search functionality
                        GoogleSearchTools(),
                        CalculatorTools(
                            enable_all=True
                        ),  # Add calculator tools for mathematical operations
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
                        ShellTools(
                            base_dir="~"
                        ),  # Match Streamlit configuration for consistency
                        PersonalAgentFilesystemTools(),
                    ]
                )

            if self.enable_memory:
                tools.extend(
                    [
                        self.knowledge_tools,
                        self.knowledge_ingestion_tools,
                        self.semantic_knowledge_ingestion_tools,
                        self.memory_tools,
                    ]
                )
                logger.info(
                    "Added KnowledgeTools, KnowledgeIngestionTools, SemanticKnowledgeIngestionTools, and AgnoMemoryTools to memory agent"
                )
            else:
                logger.warning("Memory disabled - memory agent will have no tools!")

            # 9. Create instructions using the AgentInstructionManager
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

    # Keep ALL existing methods for backward compatibility

    async def aprint_response(
        self, query: str, stream: bool = True, show_tool_calls: bool = None
    ) -> None:
        """Print agent response with streaming support (for CLI).

        Args:
            query: User query to process
            stream: Whether to stream the response
            show_tool_calls: Whether to show tool calls (uses agent's setting if None)
        """
        # Ensure agent is initialized before running
        await self._ensure_initialized()

        # Use the inherited Agent's aprint_response method
        await super().aprint_response(
            query,
            stream=stream,
            show_tool_calls=(
                show_tool_calls if show_tool_calls is not None else self.debug
            ),
        )

    async def run(
        self, query: str, stream: bool = False, add_thought_callback=None
    ) -> str:
        """Run a query through the agent.

        Args:
            query: User query to process
            stream: Whether to stream the response (parameter kept for compatibility)
            add_thought_callback: Optional callback for adding thoughts during processing

        Returns:
            Agent's final string response

        Raises:
            RuntimeError: If agent initialization fails
        """
        # Ensure agent is initialized before running
        await self._ensure_initialized()

        try:
            if add_thought_callback:
                add_thought_callback("🚀 Executing agent...")

            # Use the inherited Agent's arun method
            response_stream = await self.arun(query, user_id=self.user_id)

            # Initialize variables
            self._collected_tool_calls = []
            final_content = ""

            # Handle both streaming and direct responses
            if hasattr(response_stream, "__aiter__"):
                # Streaming response - collect all chunks
                chunks = []
                async for chunk in response_stream:
                    chunks.append(chunk)

                    # Collect tool calls from streaming events
                    if hasattr(chunk, "event") and chunk.event == "ToolCallCompleted":
                        if hasattr(chunk, "tool"):
                            self._collected_tool_calls.append(chunk.tool)

                # Process final response from chunks
                if chunks:
                    final_response = chunks[-1]
                    final_content = getattr(final_response, "content", "")

                    # If no content in final chunk, try to extract from all chunks
                    if not final_content or not final_content.strip():
                        for i, chunk in enumerate(reversed(chunks)):
                            chunk_content = getattr(chunk, "content", "")
                            if chunk_content and chunk_content.strip():
                                final_content = chunk_content
                                break

                    self._last_response = final_response
                else:
                    logger.warning("No chunks received from streaming response")
                    self._last_response = None
            else:
                # Direct response object
                self._last_response = response_stream
                final_content = getattr(
                    response_stream, "content", str(response_stream)
                )

            # Validate and clean content
            final_content = self._validate_response_content(final_content, query)

            # SmolLM2 cleanup if needed
            if is_smollm2_model(self.model_name) and final_content:
                final_content = extract_content_from_smollm2_response(final_content)

            if add_thought_callback:
                add_thought_callback("✅ Agent execution complete.")

            return (
                final_content.strip()
                if final_content
                else "I apologize, but I didn't generate a proper response. Could you please try again?"
            )

        except Exception as e:
            logger.error("Error running agent: %s", e, exc_info=True)
            if add_thought_callback:
                add_thought_callback(f"❌ Error: {str(e)}")
            return f"Error processing request: {str(e)}"

    def get_last_tool_calls(self) -> List[Any]:
        """Get tool calls from the last agent run.

        Returns:
            List of ToolExecution objects from the most recent run
        """
        return getattr(self, "_collected_tool_calls", [])

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
                            logger.info(f"Recovered content from {attr} attribute")
                            return str(alt_content)

            # Generate a simple fallback based on query
            if any(greeting in query.lower() for greeting in ["hello", "hi", "hey"]):
                return f"Hello {self.user_id}!"
            else:
                return "I'm here to help! What would you like to know?"

        # Check for common SmolLM2 issues
        if is_smollm2_model(self.model_name):
            # Remove any XML artifacts that might remain
            cleaned_content = re.sub(r"<[^>]+>", "", content).strip()

            # If still empty after cleanup
            if not cleaned_content:
                # Generate a simple fallback based on query
                if any(
                    greeting in query.lower() for greeting in ["hello", "hi", "hey"]
                ):
                    return f"Hello {self.user_id}!"
                else:
                    return "I'm here to help! What would you like to know?"

            return cleaned_content

        return content

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
        await self._ensure_initialized()
        return await self.memory_manager.store_user_memory(content, topics)

    async def _restate_user_fact(self, content: str) -> str:
        """Restate a user fact from first-person to third-person.

        Delegates to the memory_manager for processing.

        Args:
            content: The original fact from the user

        Returns:
            The restated fact
        """
        if not self.memory_manager:
            raise RuntimeError(
                "Memory manager not initialized. Call initialize() first."
            )
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
        if not self.memory_manager:
            raise RuntimeError(
                "Memory manager not initialized. Call initialize() first."
            )
        return await self.memory_manager.seed_entity_in_graph(entity_name, entity_type)

    async def check_entity_exists(self, entity_name: str) -> bool:
        """Check if entity exists in the graph.

        Delegates to the memory_manager for processing.

        Args:
            entity_name: Name of the entity to check

        Returns:
            True if entity exists
        """
        if not self.memory_manager:
            raise RuntimeError(
                "Memory manager not initialized. Call initialize() first."
            )
        return await self.memory_manager.check_entity_exists(entity_name)

    async def clear_all_memories(self) -> str:
        """Clear all memories from both SQLite and LightRAG systems.

        Delegates to the memory_manager for processing.

        Returns:
            str: Success or error message
        """
        if not self.memory_manager:
            raise RuntimeError(
                "Memory manager not initialized. Call initialize() first."
            )
        return await self.memory_manager.clear_all_memories()

    async def query_lightrag_knowledge_direct(
        self, query: str, params: dict = None, url: str = LIGHTRAG_URL
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
        # Get basic tool info
        built_in_tools = []
        mcp_tools = []

        if hasattr(self, "tools") and self.tools:
            for tool in self.tools:
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

        # For lazy initialization, knowledge is enabled if memory is enabled
        # (since knowledge is part of the memory system)
        knowledge_enabled = self.enable_memory and (
            self.agno_knowledge is not None or not self._initialized
        )

        return {
            "framework": "agno",
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "memory_enabled": self.enable_memory,
            "knowledge_enabled": knowledge_enabled,
            "lightrag_knowledge_enabled": self.lightrag_knowledge_enabled,
            "mcp_enabled": self.enable_mcp,
            "debug_mode": self.debug,
            "user_id": self.user_id,
            "initialized": self._initialized,
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

    async def cleanup(self) -> None:
        """Clean up resources when the agent is being shut down.

        This method is called during application shutdown to properly
        clean up any resources, connections, or background tasks.
        """
        try:
            logger.info("Cleaning up AgnoPersonalAgent resources...")

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

    # Legacy property for backward compatibility
    @property
    def agent(self):
        """Backward compatibility property - returns self since we ARE the agent now."""
        return self


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
        from agno.models.ollama.tools import OllamaTools

        model = OllamaTools(id=model_name)
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
    enable_mcp: bool = False,  # Simplified: disable MCP by default
    storage_dir: str = AGNO_STORAGE_DIR,
    knowledge_dir: str = AGNO_KNOWLEDGE_DIR,
    debug: bool = False,
    ollama_base_url: str = OLLAMA_URL,
    user_id: str = None,
    recreate: bool = False,
    instruction_level: InstructionLevel = InstructionLevel.EXPLICIT,
) -> AgnoPersonalAgent:
    """Create an agno-based personal agent.

    DEPRECATED: Use AgnoPersonalAgent() constructor directly.
    This function is kept for backward compatibility.

    Args:
        model_provider: LLM provider ('ollama' or 'openai')
        model_name: Model name to use
        enable_memory: Whether to enable memory and knowledge features
        enable_mcp: Whether to enable MCP tool integration (simplified)
        storage_dir: Directory for Agno storage files
        knowledge_dir: Directory containing knowledge files to load
        debug: Enable debug mode
        ollama_base_url: Base URL for Ollama API
        user_id: User identifier for memory operations
        recreate: Whether to recreate knowledge bases
        instruction_level: The sophistication level for agent instructions

    Returns:
        Agent instance (initialization happens automatically on first use)
    """
    logger.info(
        "create_agno_agent() called (deprecated - use AgnoPersonalAgent() constructor directly)"
    )

    # Set user_id with fallback
    if user_id is None:
        user_id = get_userid()

    # Just create the agent - initialization happens automatically when needed
    return AgnoPersonalAgent(
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
