"""
Agno-based agent implementation for the Personal AI Agent.

This module provides an agno framework integration that maintains compatibility
with the existing MCP infrastructure while leveraging agno's enhanced capabilities
including native MCP support, async operations, and advanced agent features.
"""

import asyncio
import logging
import os
from textwrap import dedent
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agno.tools.mcp import MCPTools, MultiMCPTools

from ..config import OLLAMA_URL, USE_MCP, USE_WEAVIATE, get_mcp_servers

logger = logging.getLogger(__name__)


class AgnoPersonalAgent:
    """
    Agno-based Personal AI Agent with MCP integration and Weaviate memory.

    This class provides a modern async agent implementation using the agno framework
    while maintaining compatibility with the existing personal agent ecosystem.
    """

    def __init__(
        self,
        model_provider: str = "ollama",
        model_name: str = "qwen2.5:7b-instruct",
        weaviate_client=None,
        vector_store=None,
        enable_memory: bool = True,
        enable_mcp: bool = True,
        debug: bool = False,
    ):
        """
        Initialize the Agno Personal Agent.

        Args:
            model_provider: LLM provider ('ollama' or 'openai')
            model_name: Model name to use
            weaviate_client: Weaviate client for memory operations
            vector_store: Vector store for memory operations
            enable_memory: Whether to enable Weaviate memory features
            enable_mcp: Whether to enable MCP tool integration
            debug: Enable debug logging and tool call visibility
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.weaviate_client = weaviate_client
        self.vector_store = vector_store
        self.enable_memory = enable_memory and USE_WEAVIATE
        self.enable_mcp = enable_mcp and USE_MCP
        self.debug = debug

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

    def _create_memory_instructions(self) -> str:
        """Create memory-related instructions for the agent."""
        if not self.enable_memory:
            return ""

        return dedent(
            """\
            
            ## Memory System Guidelines
            
            You have access to a persistent memory system powered by Weaviate vector database:
            
            - **Automatic Storage**: Important interactions are automatically stored for future reference
            - **Context Retrieval**: Relevant past interactions are retrieved to provide better context
            - **Topic Organization**: Information is categorized by topics for better organization
            - **Semantic Search**: Use natural language to find related information from past conversations
            
            When responding:
            1. Consider any retrieved context from past interactions
            2. Build upon previous conversations and learned preferences
            3. Reference relevant past information when appropriate
            4. Maintain continuity across sessions
        """
        )

    def _create_agent_instructions(self) -> str:
        """Create comprehensive instructions for the agno agent."""
        base_instructions = dedent(
            """\
            You are an advanced personal AI assistant with comprehensive capabilities.
            
            ## Core Guidelines
            
            - **Be Direct**: Execute tasks immediately without asking for confirmation unless critical
            - **Use Tools**: Leverage your available tools effectively for GitHub, file operations, web search, and memory
            - **Be Thorough**: When searching or researching, provide complete and organized results
            - **Use Tables**: Display data in tables when appropriate for better readability
            - **Show Reasoning**: Use your reasoning capabilities to break down complex problems
            - **Maintain Context**: Build upon previous conversations using memory
            
            ## Available Capabilities
            
            - **GitHub Integration**: Search repositories, analyze code, get repository information
            - **File System Operations**: Read, write, and manage files and directories  
            - **Web Research**: Search for current information and technical details
            - **Memory System**: Store and retrieve information across sessions
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

        memory_instructions = self._create_memory_instructions()

        return base_instructions + memory_instructions

    async def initialize(self) -> bool:
        """
        Initialize the agno agent with all components.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Create model
            model = self._create_model()
            logger.info("Created model: %s", self.model_name)

            # Prepare tools list starting with ReasoningTools
            tools = []

            # Add ReasoningTools for better reasoning capabilities
            try:
                from agno.tools.reasoning import ReasoningTools

                reasoning_tools = ReasoningTools(add_instructions=True)
                tools.append(reasoning_tools)
                logger.info("Added ReasoningTools for enhanced reasoning capabilities")
            except ImportError:
                logger.warning(
                    "ReasoningTools not available, continuing without reasoning capabilities"
                )

            # Get MCP tools as function wrappers (no pre-initialization)
            if self.enable_mcp:
                mcp_tool_functions = self._get_mcp_tools_as_functions()
                tools.extend(mcp_tool_functions)

            # Create agent instructions
            instructions = self._create_agent_instructions()

            # Create the agno agent
            self.agent = Agent(
                model=model,
                tools=tools,
                instructions=instructions,
                markdown=True,
                show_tool_calls=self.debug,
                add_history_to_messages=True,  # Enable conversation history
                num_history_responses=5,  # Keep last 5 exchanges in context
            )

            logger.info(
                "Successfully initialized agno agent with %d MCP tool wrapper(s)",
                len(tools),
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

            # Add memory context if available
            enhanced_query = await self._enhance_query_with_memory(query)

            if add_thought_callback:
                if self.enable_memory:
                    add_thought_callback("🧠 Memory context retrieved")
                add_thought_callback("🚀 Executing agno agent with MCP tools...")

            if stream:
                # For streaming, we'll need to handle this differently
                # For now, return the complete response
                response = await self.agent.arun(enhanced_query)
                return response.content
            else:
                if add_thought_callback:
                    add_thought_callback("⚡ Running async reasoning...")

                response = await self.agent.arun(enhanced_query)

                if add_thought_callback:
                    add_thought_callback("✅ Agent response generated")

                # Store interaction in memory if enabled
                if self.enable_memory and self.vector_store:
                    if add_thought_callback:
                        add_thought_callback("💾 Storing in memory...")
                    await self._store_interaction(query, response.content)

                return response.content

        except Exception as e:
            logger.error("Error running agno agent: %s", e)
            if add_thought_callback:
                add_thought_callback(f"❌ Error: {str(e)}")
            return f"Error processing request: {str(e)}"

    async def _enhance_query_with_memory(self, query: str) -> str:
        """Enhance query with relevant memory context."""
        if not self.enable_memory or not self.vector_store:
            return query

        try:
            # Simple memory retrieval (you can enhance this based on your memory implementation)
            # This would integrate with your existing memory tools
            enhanced_query = f"""
Context from previous interactions: [Retrieved from memory system]

Current query: {query}
"""
            return enhanced_query
        except Exception as e:
            logger.warning("Failed to enhance query with memory: %s", e)
            return query

    async def _store_interaction(self, query: str, response: str) -> None:
        """Store interaction in memory system."""
        if not self.enable_memory or not self.vector_store:
            return

        try:
            # This would integrate with your existing memory storage
            # For now, we'll just log the intention
            logger.info(
                "Would store interaction in memory: query=%s chars, response=%s chars",
                len(query),
                len(response),
            )
        except Exception as e:
            logger.warning("Failed to store interaction: %s", e)

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
    weaviate_client=None,
    vector_store=None,
    model_provider: str = "ollama",
    model_name: str = "qwen2.5:7b-instruct",
    debug: bool = False,
) -> AgnoPersonalAgent:
    """
    Create and initialize an agno-based personal agent.

    Args:
        weaviate_client: Weaviate client for memory operations
        vector_store: Vector store for memory operations
        model_provider: LLM provider ('ollama' or 'openai')
        model_name: Model name to use
        debug: Enable debug mode

    Returns:
        AgnoPersonalAgent: Initialized agent instance
    """
    agent = AgnoPersonalAgent(
        model_provider=model_provider,
        model_name=model_name,
        weaviate_client=weaviate_client,
        vector_store=vector_store,
        debug=debug,
        enable_memory=weaviate_client is not None and vector_store is not None,
        enable_mcp=USE_MCP,
    )

    success = await agent.initialize()
    if not success:
        raise RuntimeError("Failed to initialize agno agent")

    return agent


# Synchronous wrapper for compatibility
def create_agno_agent_sync(
    weaviate_client=None,
    vector_store=None,
    model_provider: str = "ollama",
    model_name: str = "qwen2.5:7b-instruct",
    debug: bool = False,
) -> AgnoPersonalAgent:
    """
    Synchronous wrapper for creating agno agent.

    Returns:
        AgnoPersonalAgent: Initialized agent instance
    """
    return asyncio.run(
        create_agno_agent(
            weaviate_client=weaviate_client,
            vector_store=vector_store,
            model_provider=model_provider,
            model_name=model_name,
            debug=debug,
        )
    )
