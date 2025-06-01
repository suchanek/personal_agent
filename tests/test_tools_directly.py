#!/usr/bin/env python3
"""Test smolagents tools directly."""

import logging
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from personal_agent.config import MCP_SERVERS
from personal_agent.core.mcp_client import SimpleMCPClient
from personal_agent.tools.smol_tools import (
    ALL_TOOLS,
    mcp_list_directory,
    set_mcp_client,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_tools_directly():
    """Test smolagents tools directly without the agent."""
    # Initialize MCP client
    client = SimpleMCPClient(MCP_SERVERS)

    # Start servers
    logger.info("Starting MCP servers...")
    if not client.start_servers():
        logger.error("❌ Failed to start MCP servers")
        return

    # Set the global MCP client
    set_mcp_client(client)

    # Test the list directory tool directly
    logger.info("Testing mcp_list_directory tool directly...")
    result = mcp_list_directory(".")
    logger.info(f"Direct tool result: {result}")

    # List all available tools
    tools = ALL_TOOLS
    logger.info("Available smolagents tools: %s", [tool.name for tool in tools])

    # Cleanup
    client.stop_all_servers()


if __name__ == "__main__":
    test_tools_directly()
