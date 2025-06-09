"""
Agno-based agent implementation for the Personal AI Agent.

This module provides an agno framework integration that maintains compatibility
with the existing MCP infrastructure while leveraging agno's enhanced capabilities
including native MCP support, async operations, and advanced agent features.
"""

import asyncio
import logging
from textwrap import dedent
from typing import Any, Dict, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..config import LLM_MODEL, OLLAMA_URL, USE_MCP, get_mcp_servers
from ..core import create_agno_knowledge, create_agno_memory, create_agno_storage

# Configure logging
logger = logging.getLogger(__name__)


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
    ):
        """
        Initialize the Agno Personal Agent.

        :param model_provider: LLM provider ('ollama' or 'openai')
        :param model_name: Model name to use
        :param enable_memory: Whether to enable memory and knowledge features
        :param enable_mcp: Whether to enable MCP tool integration
        :param storage_dir: Directory for Agno storage files
        :param knowledge_dir: Directory containing knowledge files to load
        :param debug: Enable debug logging and tool call visibility
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.enable_memory = enable_memory
        self.enable_mcp = enable_mcp and USE_MCP
        self.storage_dir = storage_dir
        self.knowledge_dir = knowledge_dir
        self.debug = debug

        # Agno native storage components
        self.agno_storage = None
        self.agno_knowledge = None
        self.agno_memory = None

        # MCP configuration
        self.mcp_servers = get_mcp_servers() if self.enable_mcp else {}

        # Agent instance
        self.agent = None

        logger.info(
            "Initialized AgnoPersonalAgent with model=%s, memory=%s, mcp=%s",
            f"{model_provider}:{model_name}",
            self.enable_memory,
            self.enable_mcp,
        )

    def _create_model(self):
        """Create the appropriate model instance based on provider."""
        if self.model_provider == "openai":
            return OpenAIChat(id=self.model_name)
        elif self.model_provider == "ollama":
            # Use OpenAI-compatible interface for Ollama
            return OpenAIChat(
                id=self.model_name,
                api_key="ollama",  # Dummy key for local Ollama
                base_url=f"{OLLAMA_URL}/v1",
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def _get_mcp_tools_as_functions(self) -> List:
        """Get MCP server runners as callable tools for the main agent."""
        if not self.enable_mcp or not self.mcp_servers:
            return []

        tools = []

        for server_name, config in self.mcp_servers.items():
            # Create async function for each MCP server
            command = config.get("command", "npx")
            args = config.get("args", [])
            env = config.get("env", {})
            description = config.get(
                "description", f"Access to {server_name} MCP server"
            )

            # Create the actual tool function with closure
            def make_mcp_tool(
                name: str, cmd: str, tool_args: List, tool_env: Dict, desc: str
            ):
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
                mcp_tool.__doc__ = f"Use {name} MCP server for: {desc}\n\nArgs:\n    query: The query or task to execute using {name}\n\nReturns:\n    str: Result from the MCP server"

                return mcp_tool

            tool_func = make_mcp_tool(server_name, command, args, env, description)
            tools.append(tool_func)
            logger.info("Created MCP tool function for: %s", server_name)

        return tools

    def _create_agent_instructions(self) -> str:
        """Create comprehensive instructions for the agno agent."""
        base_instructions = dedent(
            """\
            You are an advanced personal AI assistant with comprehensive capabilities and built-in memory.
            
            ## Core Guidelines
            
            - **Be Direct**: Execute tasks immediately without asking for confirmation unless critical
            - **Use Tools FIRST**: Always check available tools before saying you can't do something
            - **Built-in Memory**: You have automatic memory that persists across conversations
            - **Be Thorough**: When searching or researching, provide complete and organized results
            - **Use Tables**: Display data in tables when appropriate for better readability
            - **Show Reasoning**: Use your reasoning capabilities to break down complex problems
            - **Maintain Context**: Your memory automatically builds upon previous conversations
            
            ## CRITICAL TOOL USAGE RULES
            
            1. **For Personal Questions**: ALWAYS use knowledge base search tools first (e.g., "what is my name?", "who am I?", "my preferences")
            2. **For GitHub Tasks**: Use available GitHub tools for repository information
            3. **For File Operations**: Use filesystem tools for file management
            4. **For Research**: Use web search tools for current information
            5. **Never say "I can't" without first trying relevant tools**
            
            ## Knowledge Base Usage
            
            **MANDATORY**: For any question about the user (name, preferences, personal info), you MUST:
            1. Use available knowledge search tools (like asearch_knowledge_base)
            2. Search for relevant keywords
            3. Only say information is unavailable AFTER searching
            
            **Examples of when to search knowledge base:**
            - "What is my name?" → Search for "name", "user", "identity"
            - "Who am I?" → Search for "user information", "identity", "profile"
            - "My preferences?" → Search for "preferences", "settings", "likes"
            
            ## Available Capabilities
            
            - **Knowledge Base Search**: Search personal knowledge and memory for information about the user
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

    async def initialize(self) -> bool:
        """
        Initialize the agno agent with all components.

        :return: True if initialization successful, False otherwise
        """
        try:
            # Create model
            model = self._create_model()
            logger.info("Created model: %s", self.model_name)

            # Prepare tools list
            tools = []

            # Initialize Agno native storage and knowledge
            if self.enable_memory:
                self.agno_storage = create_agno_storage(self.storage_dir)
                self.agno_memory = create_agno_memory(self.storage_dir)
                self.agno_knowledge = await create_agno_knowledge(
                    self.storage_dir, self.knowledge_dir
                )

                # Add KnowledgeTools for explicit knowledge base interaction
                if self.agno_knowledge:
                    try:
                        from agno.tools.knowledge import KnowledgeTools

                        knowledge_tools = KnowledgeTools(
                            knowledge=self.agno_knowledge,
                            search=True,
                            think=True,
                            analyze=True,
                            add_instructions=True,
                        )
                        tools.append(knowledge_tools)
                        logger.info(
                            "Added KnowledgeTools for knowledge base interaction"
                        )
                    except ImportError:
                        logger.warning(
                            "KnowledgeTools not available, relying on automatic search"
                        )

                logger.info("Initialized Agno storage and knowledge backend")

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
                mcp_tool_functions = self._get_mcp_tools_as_functions()
                tools.extend(mcp_tool_functions)

            # Create agent instructions
            instructions = self._create_agent_instructions()

            # Create the agno agent with appropriate storage/knowledge
            agent_kwargs = {
                "model": model,
                "tools": tools,
                "instructions": instructions,
                "markdown": True,
                "show_tool_calls": self.debug,
                "add_history_to_messages": True,  # Enable conversation history
                "num_history_responses": 5,  # Keep last 5 exchanges in context
                "read_chat_history": True,  # Enable reading chat history
                "enable_agentic_memory": True,  # Enable automatic memory capabilities
                "enable_user_memories": True,  # Enable user-specific memory storage
                "add_memory_references": True,  # Add memory references in responses
                "search_knowledge": True,  # Enable automatic knowledge search
                "update_knowledge": True,  # Allow knowledge updates
            }

            # Add storage and knowledge if memory is enabled
            if self.enable_memory:
                agent_kwargs["storage"] = self.agno_storage
                agent_kwargs["knowledge"] = self.agno_knowledge
                agent_kwargs["memory"] = self.agno_memory

            self.agent = Agent(**agent_kwargs)

            # Calculate tool counts for logging
            mcp_tool_count = (
                len(self._get_mcp_tools_as_functions()) if self.enable_mcp else 0
            )

            logger.info(
                "Successfully initialized agno agent with native storage: %d total tools (%d MCP)",
                len(tools),
                mcp_tool_count,
            )
            return True

        except Exception as e:
            logger.error("Failed to initialize agno agent: %s", e)
            return False

    async def run(
        self, query: str, stream: bool = False, add_thought_callback=None
    ) -> str:
        """
        Run a query through the agno agent.

        Args:
            query: User query to process
            stream: Whether to stream the response
            add_thought_callback: Optional callback for adding thoughts during processing

        Returns:
            str: Agent response
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
                response = await self.agent.arun(query)
                return response.content
            else:
                if add_thought_callback:
                    add_thought_callback("⚡ Running async reasoning...")

                response = await self.agent.arun(query)

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
        """Clean up resources."""
        try:
            # With the new on-demand pattern, MCP tools are created and cleaned up
            # automatically within their async context managers
            logger.info(
                "Agno agent cleanup completed - MCP tools auto-cleaned with context managers"
            )
        except Exception as e:
            logger.error("Error during agno agent cleanup: %s", e)

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the agent configuration."""
        return {
            "framework": "agno",
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "memory_enabled": self.enable_memory,
            "mcp_enabled": self.enable_mcp,
            "mcp_servers": len(self.mcp_servers),
            "debug_mode": self.debug,
            "initialized": self.agent is not None,
        }


async def create_agno_agent(
    model_provider: str = "ollama",
    model_name: str = "qwen2.5:7b-instruct",
    enable_memory: bool = True,
    enable_mcp: bool = True,
    storage_dir: str = "./data/agno",
    knowledge_dir: str = "./data/knowledge",
    debug: bool = False,
) -> AgnoPersonalAgent:
    """
    Create and initialize an agno-based personal agent.

    Args:
        model_provider: LLM provider ('ollama' or 'openai')
        model_name: Model name to use
        enable_memory: Whether to enable memory and knowledge features
        enable_mcp: Whether to enable MCP tool integration
        storage_dir: Directory for Agno storage files
        knowledge_dir: Directory containing knowledge files to load
        debug: Enable debug mode

    Returns:
        AgnoPersonalAgent: Initialized agent instance
    """
    agent = AgnoPersonalAgent(
        model_provider=model_provider,
        model_name=model_name,
        enable_memory=enable_memory,
        enable_mcp=enable_mcp,
        storage_dir=storage_dir,
        knowledge_dir=knowledge_dir,
        debug=debug,
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
) -> AgnoPersonalAgent:
    """
    Synchronous wrapper for creating agno agent.

    Returns:
        AgnoPersonalAgent: Initialized agent instance
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
        )
    )
