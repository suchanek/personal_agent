#!/usr/bin/env python3
"""Test script to verify logger injection is working correctly."""

import logging
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from personal_agent.config import USE_MCP, USE_WEAVIATE, get_mcp_servers
from personal_agent.core import SimpleMCPClient, setup_weaviate
from personal_agent.tools import get_all_tools
from personal_agent.utils import setup_logging


def test_logger_injection():
    """Test that logger is properly injected into all tool modules."""
    logger = setup_logging()
    logger.info("=== Testing Logger Injection ===")

    # Initialize MCP if enabled
    mcp_client = None
    if USE_MCP:
        logger.info("Initializing MCP...")
        mcp_servers = get_mcp_servers()
        mcp_client = SimpleMCPClient(mcp_servers)
        mcp_client.start_servers()
        logger.info("MCP initialized")

    # Initialize Weaviate if enabled
    weaviate_client = None
    vector_store = None
    if USE_WEAVIATE:
        logger.info("Initializing Weaviate...")
        success = setup_weaviate()
        if success:
            from personal_agent.core.memory import vector_store, weaviate_client

            logger.info("Weaviate initialized")

    # Test tool creation with logger injection
    logger.info("Creating tools with logger injection...")
    tools = get_all_tools(mcp_client, weaviate_client, vector_store, logger)
    logger.info(f"Created {len(tools)} tools")

    # Test that logger is properly injected by checking module variables
    from personal_agent.tools import filesystem, memory_tools, research, system, web

    logger.info("Checking logger injection in modules:")
    logger.info(f"  web.logger: {web.logger is not None}")
    logger.info(f"  filesystem.logger: {filesystem.logger is not None}")
    logger.info(f"  system.logger: {system.logger is not None}")
    logger.info(f"  research.logger: {research.logger is not None}")
    logger.info(f"  memory_tools.logger: {memory_tools.logger is not None}")

    # Test calling a tool that uses logger to make sure it doesn't crash
    if USE_MCP and mcp_client:
        logger.info(
            "Testing web search tool (this should not crash with logger errors)..."
        )
        try:
            # Find the brave search tool
            brave_search_tool = None
            for tool in tools:
                if hasattr(tool, "name") and tool.name == "mcp_brave_search":
                    brave_search_tool = tool
                    break

            if brave_search_tool:
                logger.info("Found brave search tool, testing...")
                result = brave_search_tool.invoke({"query": "test query"})
                logger.info("Search completed without logger errors!")
                logger.info(f"Result preview: {result[:100]}...")
            else:
                logger.warning("Brave search tool not found")
        except Exception as e:
            logger.error(f"Test failed with error: {e}")

    logger.info("=== Logger Injection Test Complete ===")


if __name__ == "__main__":
    test_logger_injection()
