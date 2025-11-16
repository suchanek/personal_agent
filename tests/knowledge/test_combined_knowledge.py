"""Test the new combined knowledge base implementation."""

import logging
import pytest

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.core.agno_agent import AgnoPersonalAgent

# Configure logging
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_combined_knowledge():
    """Test the combined knowledge base implementation."""
    logger.info("Testing Combined Knowledge Base Implementation...")

    agent = AgnoPersonalAgent(
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for cleaner output
        debug=False,
    )

    success = await agent.initialize(recreate=False)
    assert success, "Failed to initialize agent"

    logger.info("Agent initialized successfully")

    # Test knowledge base queries
    test_queries = [
        "What do you know about Eric?",
        "What is in your knowledge base?",
        "Search your knowledge base for AI",
        "What kind of information do you have about projects?",
    ]

    for i, query in enumerate(test_queries, 1):
        logger.info("Query %d: %s", i, query)

        response = await agent.run(query)
        assert response is not None, f"Query {i} returned None"
        assert isinstance(response, str), f"Query {i} response is not a string"
        logger.info("Response: %s...", response[:100])

    logger.info("Combined knowledge base test completed")
