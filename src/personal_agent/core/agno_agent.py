"""
Agno-based agent implementation for the Personal AI Agent.

This module provides an agno framework integration that maintains compatibility
with the existing MCP infrastructure while leveraging agno's enhanced capabilities
including native MCP support, async operations, and advanced agent features.
"""

# pylint disable=C0413

import asyncio
import os
import re
from pathlib import Path
from tempfile import gettempdir
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

# Enable Ollama debug logging
if "OLLAMA_DEBUG" not in os.environ:
    os.environ["OLLAMA_DEBUG"] = "1"

from agno.agent import Agent
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.manager import MemoryManager
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama, OllamaTools
from agno.models.openai import OpenAIChat
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.table import Table

from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.mcp import MCPTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.yfinance import YFinanceTools

from ..config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USE_MCP,
    USER_ID,
    get_mcp_servers,
)
from ..config.rate_limiting import get_duckduckgo_rate_limits
from ..tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentWebTools,
)
from ..tools.rate_limited_duckduckgo import RateLimitedDuckDuckGoTools
from ..utils import setup_logging
from .agent_instructions import create_agent_instructions
from .agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
)
from .anti_duplicate_memory import AntiDuplicateMemory

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

    def _create_model(self) -> Union[OpenAIChat, Ollama]:
        """Create the appropriate model instance based on provider.

        :return: Configured model instance
        :raises ValueError: If unsupported model provider is specified
        """
        if self.model_provider == "openai":
            return OpenAIChat(id=self.model_name)
        elif self.model_provider == "ollama":
            return Ollama(
                id=self.model_name,
                host=self.ollama_base_url,
                # Simplified configuration - use options dict for model parameters
                options={
                    "temperature": 0.7,
                    "num_predict": 2048,  # max_tokens equivalent
                    "top_p": 0.9,
                    "num_ctx": 4096,  # context window
                },
                # Connection and reliability settings
                timeout=60.0,  # Request timeout (seconds)
                keep_alive="5m",  # Keep model loaded for 5 minutes
                # Client configuration
                client_params={
                    "verify": False,  # Skip SSL verification for local Ollama
                    "timeout": 60,  # Client-level timeout
                },
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

        return None

    async def initialize(
        self, recreate: bool = False, complexity_level: int = 4
    ) -> bool:
        """Initialize the agno agent with all components.

        :param recreate: Whether to recreate the agent knowledge bases
        :param complexity_level: Instruction complexity level (0=minimal, 4=full)
        :return: True if initialization successful, False otherwise
        """
        # Memory layer

        db_path = Path(AGNO_STORAGE_DIR) / "agent_memory.db"
        memory_db = SqliteMemoryDb(
            table_name="personal_agent_memory", db_file=str(db_path)
        )

        self.agno_memory = Memory(
            db=memory_db,
            memory_manager=MemoryManager(
                memory_capture_instructions="""\
                            Collect User's name,
                            Collect Information about user's passion and hobbies,
                            Collect Information about the users likes and dislikes,
                            Collect information about what the user is doing with their life right now
                            Collect information about what matters to the user
                        """,
                # model=Gemini(id="gemini-2.0-flash"),
                model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
            ),
        )
        # Agno native storage components
        self.agno_storage = create_agno_storage(self.storage_dir)
        self.agno_knowledge = create_combined_knowledge_base(self.storage_dir)

        # MCP configuration
        self.mcp_servers = get_mcp_servers() if self.enable_mcp else {}

        # Agent instance
        self.agent = Agent(
            name="Personal AI Friend",
            model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
            user_id=USER_ID,  # Specify the user_id for memory management
            tools=[GoogleSearchTools(), YFinanceTools()],
            add_history_to_messages=True,
            num_history_responses=3,
            add_datetime_to_instructions=True,
            markdown=True,
            memory=self.agno_memory,
            knowledge=self.agno_knowledge,
            enable_agentic_memory=True,
            enable_user_memories=True,
            instructions=dedent(
                f"""
            You are a personal AI friend of the user, your purpose is to chat with the user about things and make them feel good.
            The user you are talking to is: {USER_ID}
            First introduce yourself and greet them by their user ID, then ask about themselves, their hobbies, what they like to do and what they like to talk about.
            If they ask for more information use Google Search tool to find latest information about things in the conversations.
            Store these memories for later recall.
            """
            ),
            debug_mode=True,
        )

        if self.agno_knowledge:
            load_agent_knowledge(self.agno_knowledge, recreate=recreate)

        logger.info(
            "Initialized AgnoPersonalAgent with model=%s, memory=%s, mcp=%s, user_id=%s",
            f"{self.model_provider}:{self.model_name}",
            self.enable_memory,
            self.enable_mcp,
            self.user_id,
        )

        return self.agent

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


# end of class


# backup original class
class _AgnoPersonalAgent:
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
        self.agno_storage = create_agno_storage(self.storage_dir)
        self.agno_knowledge = create_combined_knowledge_base()
        self.agno_memory = create_agno_memory(self.storage_dir)

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
            return Ollama(
                id=self.model_name,
                host=self.ollama_base_url,
                # Simplified configuration - use options dict for model parameters
                options={
                    "temperature": 0.7,
                    "num_predict": 2048,  # max_tokens equivalent
                    "top_p": 0.9,
                    "num_ctx": 4096,  # context window
                },
                # Connection and reliability settings
                timeout=60.0,  # Request timeout (seconds)
                keep_alive="5m",  # Keep model loaded for 5 minutes
                # Client configuration
                client_params={
                    "verify": False,  # Skip SSL verification for local Ollama
                    "timeout": 60,  # Client-level timeout
                },
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def _clean_response(self, response_content: str) -> str:
        """Remove thinking tags and other unwanted formatting from response.

        This method cleans up responses that may contain thinking tags or other
        internal reasoning artifacts that shouldn't be shown to users.

        :param response_content: Raw response content from the model
        :return: Cleaned response content
        """
        if not response_content:
            return response_content

        # Remove <thinking>...</thinking> blocks (case insensitive, multiline)
        cleaned = re.sub(
            r"<thinking>.*?</thinking>",
            "",
            response_content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove <think>...</think> blocks (case insensitive, multiline)
        cleaned = re.sub(
            r"<think>.*?</think>",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove any orphaned thinking/think tags
        cleaned = re.sub(r"</?thinking>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)

        # Clean up excessive whitespace that might be left behind
        cleaned = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned)
        cleaned = re.sub(r"^\s+|\s+$", "", cleaned)  # Strip leading/trailing whitespace

        return cleaned

    async def _get_memory_tools(self) -> List:
        """Create memory tools as native async functions compatible with Agno.

        This method creates the crucial store_user_memory and query_memory tools
        that enable the agent to actually create and retrieve memories.
        """
        if not self.enable_memory or not self.agno_memory:
            logger.warning("Memory not enabled or memory not initialized")
            return []

        tools = []

        async def store_user_memory(content: str, topics: List[str] = None) -> str:
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
                    topics = ["user_memory", "general"]

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
                # Ensure that the "user_memory" topic is present
                if "user_memory" not in topics:
                    topics.append("user_memory")

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

        async def query_memory(query: str, limit: int = 5000) -> str:
            """Search user memories using semantic search.

            Args:
                query: The query to search for in memories
                limit: Maximum number of memories to return

            Returns:
                str: Found memories or message if none found
            """
            try:
                memories = self.agno_memory.search_user_memories(
                    user_id=self.user_id,
                    query=query,
                    retrieval_method="agentic",
                    limit=limit,
                )

                if not memories:
                    logger.info("No memories found for query: %s", query)
                    return f"🔍 No memories found for: {query}"

                # Format memories for display
                result = f"🧠 Found {len(memories)} memories for '{query}':\n\n"
                for i, memory in enumerate(memories, 1):
                    result += f"{i}. {memory.memory}\n"
                    if memory.topics:
                        result += f"   Topics: {', '.join(memory.topics)}\n"
                    result += "\n"

                logger.info("Found %d memories for query: %s", len(memories), query)
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

        async def retrieve_memory(
            query: str = None,
            user_id: str = None,
            n_memories: int = None,
            topic: str = None,
        ) -> str:
            """Retrieve memories with flexible filtering options.

            Args:
                query: Optional search query for semantic search
                user_id: User ID (defaults to current user)
                n_memories: Optional limit on number of memories
                topic: Optional topic filter

            Returns:
                str: Formatted list of matching memories
            """
            try:
                # Use current user if not specified
                target_user_id = user_id or self.user_id

                # Validate parameters
                if n_memories is not None and n_memories <= 0:
                    return "❌ Error: n_memories must be greater than 0"

                # Call the retrieve_memory method from AntiDuplicateMemory
                memories = self.agno_memory.retrieve_memory(
                    user_id=target_user_id,
                    query=query,
                    n_memories=n_memories,
                    topic=topic,
                )

                if not memories:
                    # Create descriptive message based on parameters
                    filters = []
                    if query:
                        filters.append(f"query '{query}'")
                    if topic:
                        filters.append(f"topic '{topic}'")
                    if n_memories:
                        filters.append(f"limit {n_memories}")

                    filter_desc = " with " + ", ".join(filters) if filters else ""
                    return f"🔍 No memories found{filter_desc}."

                # Format memories for display
                filter_info = []
                if query:
                    filter_info.append(f"query: '{query}'")
                if topic:
                    filter_info.append(f"topic: '{topic}'")
                if n_memories:
                    filter_info.append(f"limit: {n_memories}")

                filter_desc = f" ({', '.join(filter_info)})" if filter_info else ""
                result = f"🧠 Retrieved {len(memories)} memories{filter_desc}:\n\n"

                for i, memory in enumerate(memories, 1):
                    result += f"{i}. {memory.memory}\n"
                    if hasattr(memory, "topics") and memory.topics:
                        result += f"   Topics: {', '.join(memory.topics)}\n"
                    result += "\n"

                logger.info(
                    "Retrieved %d memories for user %s (query: %s, topic: %s, limit: %s)",
                    len(memories),
                    target_user_id,
                    query or "None",
                    topic or "None",
                    n_memories or "None",
                )
                return result

            except Exception as e:
                logger.error("Error retrieving memories: %s", e)
                return f"❌ Error retrieving memories: {str(e)}"

        # Add tools to the list
        tools.append(store_user_memory)
        tools.append(query_memory)
        tools.append(get_recent_memories)
        tools.append(retrieve_memory)

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

    async def initialize(
        self, recreate: bool = False, complexity_level: int = 4
    ) -> bool:
        """Initialize the agno agent with all components.

        :param recreate: Whether to recreate the agent knowledge bases
        :param complexity_level: Instruction complexity level (0=minimal, 4=full)
        :return: True if initialization successful, False otherwise
        """
        try:
            # Create model
            model = self._create_model()
            logger.info("Created model: %s", self.model_name)

            # Get rate limiting configuration
            rate_limit_config = get_duckduckgo_rate_limits()

            # Prepare tools list
            tmp_dir = Path(gettempdir())
            tools = [
                RateLimitedDuckDuckGoTools(**rate_limit_config),
                YFinanceTools(),
                PythonTools(base_dir=tmp_dir.joinpath("agents"), read_files=True),
                ShellTools(base_dir="/"),  # Configured for security
                PersonalAgentFilesystemTools(),
                PersonalAgentWebTools(),
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

                    # Knowledge tools will be automatically added via search_knowledge=True
                    # DO NOT manually add KnowledgeTools to avoid naming conflicts

                self.agno_memory = create_agno_memory(self.storage_dir)

                # Wrap with anti-duplicate memory system if memory was created successfully
                if self.agno_memory:
                    # Create model for the anti-duplicate memory
                    memory_model = self._create_model()

                    # Extract the database from the regular memory
                    memory_db = self.agno_memory.db

                    # Create anti-duplicate memory with proper parameters
                    self.agno_memory = AntiDuplicateMemory(
                        db=memory_db,
                        model=memory_model,
                        similarity_threshold=0.85,  # 85% similarity threshold
                        enable_semantic_dedup=True,
                        enable_exact_dedup=True,
                        debug_mode=self.debug,
                        enable_optimizations=True,
                    )
                    logger.info(
                        "Created Agno memory with anti-duplicate protection at: %s",
                        self.storage_dir,
                    )
                else:
                    logger.error("Failed to create base memory system")

                logger.info("Initialized Agno storage and knowledge backend")
            else:
                logger.info(
                    "Memory disabled, skipping storage and knowledge initialization"
                )

            # Add ReasoningTools for better reasoning capabilities
            # TEMPORARILY DISABLED to debug tool naming issue
            # try:
            #     from agno.tools.reasoning import ReasoningTools

            #     reasoning_tools = ReasoningTools(add_instructions=True)
            #     tools.append(reasoning_tools)
            #     logger.info("Added ReasoningTools for enhanced reasoning capabilities")
            # except ImportError:
            #     logger.warning(
            #         "ReasoningTools not available, continuing without reasoning capabilities"
            #     )

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
            instructions = create_agent_instructions(complexity_level)

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
    ) -> str:
        """Run a query through the agno agent.

        :param query: User query to process
        :param stream: Whether to stream the response
        :param add_thought_callback: Optional callback for adding thoughts during processing
        :return: Agent response
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
                # Clean the response before returning
                cleaned_content = self._clean_response(response.content)
                return response.content
            else:
                if add_thought_callback:
                    add_thought_callback("⚡ Running async reasoning...")

                response = await self.agent.arun(query, user_id=self.user_id)

                if add_thought_callback:
                    add_thought_callback("✅ Agent response generated")

                # Clean the response before returning
                cleaned_content = self._clean_response(response.content)

                return response.content

        except Exception as e:
            logger.error("Error running agno agent: %s", e)
            if add_thought_callback:
                add_thought_callback(f"❌ Error: {str(e)}")
            return f"Error processing request: {str(e)}"

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
    complexity_level: int = 4,
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

    success = await agent.initialize(complexity_level=complexity_level)
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


async def aload_agent_knowledge(
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


def load_agent_knowledge(
    knowledge_base: CombinedKnowledgeBase, recreate: bool = False
) -> None:
    """Load knowledge base content synchronously.

    This should be called after creating the agent to load the knowledge content.

    :param knowledge_base: Knowledge base instance to load
    :param recreate: Whether to recreate the knowledge base from scratch
    :return: None
    """
    if knowledge_base:
        load_combined_knowledge_base(knowledge_base, recreate=recreate)
        logger.info("✅ Knowledge base loaded successfully")
    else:
        logger.info("No knowledge base to load")
