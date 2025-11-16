"""Test querying the agent about its knowledge base contents."""

import logging

import pytest

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.core.agno_agent import AgnoPersonalAgent

# Configure logging
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_knowledge_query():
    """Test querying the agent about its knowledge base contents."""
    logger.info("Initializing Agno Personal Agent...")

    agent = AgnoPersonalAgent(
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for focused knowledge testing
        debug=False,
    )

    success = await agent.initialize()
    assert success, "Failed to initialize agent"

    logger.info("Agent initialized successfully")

    # Test queries about knowledge base contents
    queries = [
        "What knowledge do you have in your knowledge base?",
        "What files are in your knowledge base?",
        "What information do you know about me?",
        "Search your knowledge base for any available information",
        "What personal information is stored in your knowledge?",
    ]

    for i, query in enumerate(queries, 1):
        logger.info("Query %d: %s", i, query)

        response = await agent.run(query, stream=False)
        assert response is not None, f"Query {i} returned None"
        assert isinstance(response, str), f"Query {i} response is not a string"
        logger.info("Response: %s...", response[:100])
