#!/usr/bin/env python3
"""Debug MCP client functionality."""

import logging

from src.personal_agent.config.mcp_servers import MCP_SERVERS
from src.personal_agent.core.mcp_client import SimpleMCPClient

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_mcp_client():
    """Test MCP client functionality."""
    # Initialize MCP client
    client = SimpleMCPClient(MCP_SERVERS)

    # Start servers
    logger.info("Starting MCP servers...")
    if client.start_servers():
        logger.info("✅ MCP servers started successfully")
    else:
        logger.error("❌ Failed to start MCP servers")
        return

    # List available servers
    logger.info(f"Active servers: {list(client.active_servers.keys())}")

    # Test filesystem-data server
    if "filesystem-data" in client.active_servers:
        logger.info("Testing filesystem-data server...")

        # List tools
        tools = client.list_tools_sync("filesystem-data")
        logger.info(f"Available tools: {[tool.get('name') for tool in tools]}")

        # Try to call list_directory
        result = client.call_tool_sync(
            "filesystem-data", "list_directory", {"path": "."}
        )
        logger.info(f"list_directory result: {result}")
    else:
        logger.error("filesystem-data server not active")

    # Cleanup
    client.stop_all_servers()


if __name__ == "__main__":
    test_mcp_client()
