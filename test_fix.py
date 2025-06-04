#!/usr/bin/env python3
"""Test the GitHub search fix in the tools module directly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import USE_MCP, get_mcp_servers
from personal_agent.core.mcp_client import SimpleMCPClient
from personal_agent.tools import web
from personal_agent.utils import setup_logging


def test_github_search_fix():
    """Test that the GitHub search fix works correctly."""
    logger = setup_logging()
    logger.info("=== Testing GitHub Search Fix ===")

    # Initialize MCP client
    if USE_MCP:
        mcp_servers = get_mcp_servers()
        mcp_client = SimpleMCPClient(mcp_servers)

        # Start MCP servers
        if mcp_client.start_servers():
            logger.info("MCP servers started successfully")

            # Inject dependencies into web module
            web.mcp_client = mcp_client
            web.USE_MCP = True
            web.logger = logger

            # Test the search with proteusPy (should now use search_repositories)
            logger.info("Testing GitHub search for 'proteusPy'...")
            try:
                result = web.mcp_github_search.invoke({"query": "proteusPy"})
                logger.info(
                    "Search result preview: %s",
                    result[:200] + "..." if len(result) > 200 else result,
                )

                if "proteusPy" in result or "suchanek" in result:
                    logger.info("✅ SUCCESS: Found proteusPy-related repositories!")
                else:
                    logger.warning(
                        "⚠️  Search completed but didn't find expected results"
                    )

            except Exception as e:
                logger.error("❌ Search failed: %s", e)

            # Cleanup
            mcp_client.stop_all_servers()
        else:
            logger.error("Failed to start MCP servers")
    else:
        logger.error("MCP is disabled")


if __name__ == "__main__":
    test_github_search_fix()
