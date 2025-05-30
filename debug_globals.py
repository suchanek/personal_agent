#!/usr/bin/env python3
"""Debug script to check global variable states during initialization."""

import logging
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.config import USE_MCP, USE_WEAVIATE, get_mcp_servers
from personal_agent.core import SimpleMCPClient, setup_weaviate
from personal_agent.tools import get_all_tools

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def debug_initialization():
    """Debug the initialization process step by step."""
    logger.info("=== Starting Debug Initialization ===")

    # Initialize variables
    weaviate_client = None
    vector_store = None

    # Check initial state
    logger.info("Initial global states:")
    logger.info(f"  weaviate_client: {weaviate_client}")
    logger.info(f"  vector_store: {vector_store}")
    logger.info(f"  USE_WEAVIATE: {USE_WEAVIATE}")
    logger.info(f"  USE_MCP: {USE_MCP}")

    # Initialize MCP if enabled
    mcp_client = None
    if USE_MCP:
        logger.info("Initializing MCP...")
        mcp_servers = get_mcp_servers()
        mcp_client = SimpleMCPClient(mcp_servers)
        mcp_client.start_servers()
        logger.info("MCP initialized")

    # Initialize Weaviate if enabled
    if USE_WEAVIATE:
        logger.info("Initializing Weaviate...")
        success = setup_weaviate()
        logger.info(f"Weaviate setup result: {success}")

        # Import globals directly from memory module to get updated values (like main.py does)
        from personal_agent.core.memory import vector_store, weaviate_client

        # Check state after setup
        logger.info("After Weaviate setup:")
        logger.info(f"  weaviate_client: {weaviate_client}")
        logger.info(f"  vector_store: {vector_store}")

        # Import and check the globals from the module directly
        from personal_agent.core.memory import vector_store as mem_vector_store
        from personal_agent.core.memory import weaviate_client as mem_weaviate_client

        logger.info("Direct module globals:")
        logger.info(f"  memory.weaviate_client: {mem_weaviate_client}")
        logger.info(f"  memory.vector_store: {mem_vector_store}")

    # Test tool creation
    logger.info("Creating tools...")
    tools = get_all_tools(mcp_client, weaviate_client, vector_store)
    logger.info(f"Total tools created: {len(tools)}")

    # List all tools
    for i, tool in enumerate(tools):
        tool_name = getattr(tool, "name", "Unknown")
        logger.info(f"  Tool {i+1}: {tool_name}")

    # Test memory tools specifically
    if weaviate_client and vector_store:
        logger.info("Testing memory tools factory directly...")
        from personal_agent.tools.memory_tools import create_memory_tools

        memory_tools = create_memory_tools(weaviate_client, vector_store)
        logger.info(f"Memory tools from factory: {len(memory_tools)}")
        for tool in memory_tools:
            logger.info(f"  Memory tool: {getattr(tool, 'name', 'Unknown')}")
    else:
        logger.warning("Cannot test memory tools - missing dependencies")
        logger.info(f"  weaviate_client is None: {weaviate_client is None}")
        logger.info(f"  vector_store is None: {vector_store is None}")


if __name__ == "__main__":
    debug_initialization()
