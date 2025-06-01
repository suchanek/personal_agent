#!/usr/bin/env python3
"""Test smolagents integration with existing MCP infrastructure."""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from personal_agent.config import USE_WEAVIATE, get_mcp_servers
from personal_agent.core.mcp_client import SimpleMCPClient
from personal_agent.core.smol_agent import create_smolagents_executor
from personal_agent.utils.cleanup import setup_logging


def test_smolagents_integration():
    """
    Test smolagents integration with MCP infrastructure.

    :return: True if test passes, False otherwise
    """
    logger = setup_logging()
    logger.info("Testing smolagents integration")

    try:
        # Initialize MCP client
        mcp_servers = get_mcp_servers()
        mcp_client = SimpleMCPClient(mcp_servers)
        logger.info("Initialized MCP client with %d servers", len(mcp_servers))

        # Start MCP servers
        if not mcp_client.start_servers():
            logger.error("❌ Failed to start MCP servers")
            return False
        logger.info("✅ Started MCP servers successfully")

        # Initialize memory components if available
        weaviate_client = None
        vector_store = None
        if USE_WEAVIATE:
            try:
                from personal_agent.core.memory import vector_store, weaviate_client

                logger.info("✅ Loaded Weaviate memory components")
            except ImportError as e:
                logger.warning("⚠️  Could not load Weaviate components: %s", e)

        # Create smolagents agent with all dependencies
        agent = create_smolagents_executor(
            mcp_client=mcp_client,
            weaviate_client=weaviate_client,
            vector_store=vector_store,
        )
        logger.info("Created smolagents agent with full tool set")

        # Test simple query
        test_query = "List the files in the current directory"
        logger.info("Testing query: %s", test_query)

        result = agent.run(test_query)
        logger.info("Agent response: %s", result)

        # Cleanup MCP servers
        mcp_client.stop_all_servers()

        if result and len(result) > 10:  # Basic check for meaningful response
            logger.info("✅ Smolagents integration test passed")
            return True
        else:
            logger.error("❌ Agent response too short or empty")
            return False

    except Exception as e:
        logger.error("❌ Smolagents integration test failed: %s", e)
        import traceback

        traceback.print_exc()
        return False
    finally:
        # Always cleanup if mcp_client exists
        try:
            if "mcp_client" in locals():
                mcp_client.stop_all_servers()
        except Exception:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    success = test_smolagents_integration()
    sys.exit(0 if success else 1)
