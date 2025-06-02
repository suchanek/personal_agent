"""Smolagents-based agent implementation."""

import logging
from typing import List, Optional

from smolagents import CodeAgent, LiteLLMModel, ToolCallingAgent, tool

from ..config import LLM_MODEL, OLLAMA_URL, USE_WEAVIATE
from ..tools.smol_tools import ALL_TOOLS, set_mcp_client, set_memory_components

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


def create_smolagents_executor(
    mcp_client=None,
    weaviate_client=None,
    vector_store=None,
    tools: Optional[List] = None,
    model: Optional[LiteLLMModel] = None,
) -> ToolCallingAgent:
    """
    Create smolagents ToolCallingAgent with all tools and dependencies.

    :param mcp_client: MCP client instance for tool functionality
    :param weaviate_client: Weaviate client for memory functionality
    :param vector_store: Vector store for memory operations
    :param tools: Optional custom list of tools (uses ALL_TOOLS by default)
    :param model: Optional LiteLLM model instance
    :return: Configured ToolCallingAgent
    """
    if model is None:
        model = create_smolagents_model()

    # Set up global dependencies for tools
    if mcp_client:
        set_mcp_client(mcp_client)
        logger.info("MCP client set for smolagents tools")

    if weaviate_client and vector_store:
        set_memory_components(weaviate_client, vector_store, USE_WEAVIATE)
        logger.info("Memory components set for smolagents tools")

    # Use provided tools or default to all available tools
    if tools is None:
        tools = ALL_TOOLS

    agent = ToolCallingAgent(tools=tools, model=model)
    # agent = CodeAgent(tools=tools, model=model)
    logger.info("Created smolagents CodeAgent with %d tools", len(tools))
    return agent
