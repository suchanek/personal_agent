"""
Agno-based agent implementation for the Personal AI Agent.

This module provides an agno framework integration that maintains compatibility
with the existing MCP infrastructure while leveraging agno's enhanced capabilities
including native MCP support, async operations, and advanced agent features.
"""

import asyncio
import os
from textwrap import dedent
from typing import Any, Dict, List, Optional

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
from agno.tools.mcp import MCPTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.yfinance import YFinanceTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.table import Table

from ..config import LLM_MODEL, OLLAMA_URL, USE_MCP, get_mcp_servers
from ..tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentWebTools,
)
from ..utils import setup_logging
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

        logger.info(
            "Initialized AgnoPersonalAgent with model=%s, memory=%s, mcp=%s, user_id=%s",
            f"{model_provider}:{model_name}",
            self.enable_memory,
            self.enable_mcp,
            self.user_id,
        )

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
                from agno.memory.v2.memory import UserMemory

                if topics is None:
                    topics = ["general"]

                memory_obj = UserMemory(memory=content, topics=topics)
                memory_id = self.agno_memory.add_user_memory(
                    memory=memory_obj, user_id=self.user_id
                )

                logger.info(
                    "Stored user memory: %s... (ID: %s)", content[:50], memory_id
                )
                return f"✅ Successfully stored memory: {content[:50]}... (ID: {memory_id})"

            except Exception as e:
                logger.error("Error storing user memory: %s", e)
                return f"❌ Error storing memory: {str(e)}"

        async def query_memory(query: str, limit: int = 5) -> str:
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

        # Add tools to the list
        tools.append(store_user_memory)
        tools.append(query_memory)
        tools.append(get_recent_memories)

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
        base_instructions = dedent(
            """\
            You are an advanced personal AI assistant with comprehensive capabilities and built-in memory.
            
            ## MEMORY-FIRST PRIORITY RULES
            
            **CRITICAL**: For ANY personal questions about the user:
            1. **ALWAYS check your memory FIRST** - you have automatic user memories available
            2. **DO NOT use web search** for personal information (name, location, preferences, etc.)
            3. **Your built-in memory contains all personal details** - trust it over external sources
            4. **Only use web search** for current events, technical info, or general knowledge
            
            ## Core Guidelines
            
            - **Be Direct**: Execute tasks immediately without asking for confirmation unless critical
            - **Built-in Memory**: You have automatic memory that persists across conversations
            - **Use Tools**: Always check available tools before saying you can't do something
            - **Be Thorough**: When searching or researching, provide complete and organized results
            - **Use Tables**: Display data in tables when appropriate for better readability
            - **Show Reasoning**: Use your reasoning capabilities to break down complex problems
            - **Maintain Context**: Your memory automatically builds upon previous conversations
            
            ## CRITICAL TOOL USAGE RULES
            
            2. **For GitHub Tasks**: Use available GitHub tools for repository information
            3. **For File Operations**: Use filesystem tools for file management
            4. **For Research**: Use web search tools for current information
            5. **Never say "I can't" without first trying relevant tools**
                        
            ### Available Knowledge Functions:
            - **search(query)** - Search the knowledge base for information (USE THIS FOR PERSONAL QUESTIONS!)
            - **think(query)** - Use reasoning capabilities  
            - **analyze(query)** - Analyze information from knowledge base
            
            ## Available Capabilities
            
            - **GitHub Integration**: Search repositories, analyze code, get repository information
            - **File System Operations**: Read, write, and manage files and directories  
            - **Web Research**: Search for current information and technical details
            - **Automatic Memory**: Built-in memory system that persists across sessions
            - **Reasoning**: Break down complex problems step by step
            
            ## Response Format
            
            - Use markdown formatting for better readability
            - Present data in tables when showing multiple items
            - Include relevant links when helpful
            - Show your reasoning process for complex queries

            ## Core Principles
            
            1. **Be Helpful**: Always strive to provide useful and actionable responses
            2. **Be Accurate**: Verify information and cite sources when possible
            3. **Be Efficient**: Use the most appropriate tools for each task
            4. **Be Contextual**: Consider past interactions and user preferences
            5. **Be Clear**: Provide well-structured, easy-to-understand responses
            6. **Be Proactive**: Suggest related actions or improvements when relevant
            
            ## Tool Usage Strategy
            
            - **Progressive Enhancement**: Start with simple operations, add complexity as needed
            - **Cross-Reference**: Validate information across multiple sources
            - **Context Building**: Use memory to enhance responses with relevant background
            - **Error Recovery**: Handle tool failures gracefully with alternative approaches
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
                DuckDuckGoTools(),
                YFinanceTools(),
                PythonTools(),
                ShellTools(base_dir="/tmp"),  # Configured for security
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

                # Wrap with anti-duplicate memory system
                if self.agno_memory:
                    self.agno_memory = AntiDuplicateMemory(
                        base_memory=self.agno_memory,
                        similarity_threshold=0.85,  # 85% similarity threshold
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
                enable_agentic_memory=False,  # Disable to avoid conflicts with user_memories
                enable_user_memories=self.enable_memory,  # Enable user memories for personal info
                add_history_to_messages=False,
                num_history_responses=5,
                knowledge=self.agno_knowledge if self.enable_memory else None,
                storage=self.agno_storage if self.enable_memory else None,
                memory=self.agno_memory if self.enable_memory else None,
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
    model_name: str = "qwen2.5:7b-instruct",
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
    model_name: str = "qwen2.5:7b-instruct",
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
