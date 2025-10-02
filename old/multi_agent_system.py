"""
Multi-agent system architecture for Personal AI Agent using smolagents.

This module implements a coordinated multi-agent approach with specialized tool routing
for different domains (filesystem, web research, memory, etc.) with intelligent
task coordination.
"""

import logging
from typing import Dict, List, Optional

from smolagents import CodeAgent, LiteLLMModel, ToolCallingAgent

from ..config import LLM_MODEL, OLLAMA_URL, USE_WEAVIATE
from ....old.multiple_tools import (
    get_joke,
    get_news_headlines,
    get_random_fact,
    get_weather,
)
from ..tools.smol_tools import (
    ALL_TOOLS,
    clear_knowledge_base,
    comprehensive_research,
    github_search_repositories,
    intelligent_file_search,
    mcp_create_directory,
    mcp_list_directory,
    mcp_read_file,
    mcp_write_file,
    query_knowledge_base,
    set_mcp_client,
    set_memory_components,
    shell_command,
    store_interaction,
    web_search,
)

logger = logging.getLogger(__name__)


def create_smolagents_model() -> LiteLLMModel:
    """
    Create LiteLLM model for Ollama integration.

    :return: Configured LiteLLM model instance
    """
    return LiteLLMModel(
        model_id=f"ollama_chat/{LLM_MODEL}",
        api_base=OLLAMA_URL,
        api_key="ollama_local",
    )


class MultiAgentSystem:
    """
    Multi-agent system with specialized tools for different domains.

    This system uses CodeAgent as a coordinator with all tools available directly:
    - Filesystem operations: File reading, writing, directory listing
    - Research operations: Web search, GitHub search, comprehensive research
    - Memory operations: Knowledge base storage and retrieval
    - System operations: Shell commands and system tasks
    """

    def __init__(
        self,
        mcp_client=None,
        weaviate_client=None,
        vector_store=None,
        model: Optional[LiteLLMModel] = None,
    ):
        """
        Initialize the multi-agent system.

        Args:
            mcp_client: MCP client instance for tool functionality
            weaviate_client: Weaviate client for memory functionality
            vector_store: Vector store for memory operations
            model: Optional LiteLLM model instance
        """
        self.model = model or create_smolagents_model()
        self.mcp_client = mcp_client
        self.weaviate_client = weaviate_client
        self.vector_store = vector_store

        # Set up global dependencies for tools
        if mcp_client:
            set_mcp_client(mcp_client)
            logger.info("MCP client set for multi-agent tools")

        if weaviate_client and vector_store:
            set_memory_components(weaviate_client, vector_store, USE_WEAVIATE)
            logger.info("Memory components set for multi-agent tools")

        # Create specialized tool groups
        self.tool_groups = self._create_tool_groups()

        # Create the intelligent routing agent
        self.agent = self._create_routing_agent()

        logger.info("Multi-agent system initialized with CodeAgent coordinator")

    def _create_tool_groups(self) -> Dict[str, List]:
        """
        Create specialized tool groups for different domains.

        :return: Dictionary of tool groups by domain
        """
        tool_groups = {}

        # Filesystem tools
        tool_groups["filesystem"] = [
            mcp_read_file,
            mcp_write_file,
            mcp_list_directory,
            mcp_create_directory,
            intelligent_file_search,
        ]

        # Research tools
        tool_groups["research"] = [
            web_search,
            github_search_repositories,
            comprehensive_research,
            get_news_headlines,
            get_weather,
        ]

        # Memory tools (if available)
        if USE_WEAVIATE and self.weaviate_client and self.vector_store:
            tool_groups["memory"] = [
                store_interaction,
                query_knowledge_base,
                clear_knowledge_base,
            ]

        # System tools
        tool_groups["system"] = [shell_command]
        # Fun tools
        tool_groups["fun"] = [get_joke, get_random_fact]

        return tool_groups

    def _create_routing_agent(self) -> CodeAgent:
        """
        Create the routing agent that coordinates all tools directly.

        :return: Configured CodeAgent as coordinator
        """
        # Combine all tools from all groups
        all_tools = []
        for tools in self.tool_groups.values():
            all_tools.extend(tools)

        # Create the coordinating agent with all tools
        agent = CodeAgent(
            tools=all_tools,
            model=self.model,
            additional_authorized_imports=["time", "json", "re", "os"],
            stream_outputs=True,
            description=(
                "This agent coordinates multiple specialized tools for different domains. "
                "It can handle filesystem operations, web research, memory management, "
                "system commands, and fun tasks. Available specialists:\n"
                f"{self._get_specialist_descriptions()}"
            ),
        )

        return agent

    def _get_specialist_descriptions(self) -> str:
        """
        Get descriptions of all available specialists.

        :return: Formatted string describing all specialists
        """
        descriptions = []
        for group_name, tools in self.tool_groups.items():
            if tools:
                tool_names = [tool.name for tool in tools]
                descriptions.append(f"- {group_name}: {', '.join(tool_names)}")
        return "\n".join(descriptions)

    def run(self, query: str) -> str:
        """
        Process a query using the multi-agent system.

        Args:
            query: User query to process

        :return: Response from the coordinated agent system
        """
        logger.info("Processing query with multi-agent system: %s", query[:100])

        try:
            result = self.agent.run(query)
            logger.info("Multi-agent system completed query successfully")
            return result
        except Exception as e:
            logger.error("Error in multi-agent system: %s", str(e))
            return f"Error processing query: {str(e)}"

    def get_agent_info(self) -> Dict[str, str]:
        """
        Get information about all available tool groups.

        :return: Dictionary with tool group names and descriptions
        """
        info = {}
        for group_name, tools in self.tool_groups.items():
            tool_names = [tool.name for tool in tools]
            info[group_name] = (
                f"Handles {group_name} operations with tools: {', '.join(tool_names)}"
            )
        return info

    def list_available_tools(self) -> List[str]:
        """
        List all tools available across all groups.

        :return: List of tool names
        """
        all_tools = []
        for group_name, tools in self.tool_groups.items():
            tool_names = [tool.name for tool in tools]
            all_tools.extend([f"{group_name}.{tool}" for tool in tool_names])
        return all_tools


def create_multi_agent_system(
    mcp_client=None,
    weaviate_client=None,
    vector_store=None,
    model: Optional[LiteLLMModel] = None,
) -> MultiAgentSystem:
    """
    Create and configure the multi-agent system.

    Args:
        mcp_client: MCP client instance for tool functionality
        weaviate_client: Weaviate client for memory functionality
        vector_store: Vector store for memory operations
        model: Optional LiteLLM model instance

    :return: Configured MultiAgentSystem instance
    """
    return MultiAgentSystem(
        mcp_client=mcp_client,
        weaviate_client=weaviate_client,
        vector_store=vector_store,
        model=model,
    )
