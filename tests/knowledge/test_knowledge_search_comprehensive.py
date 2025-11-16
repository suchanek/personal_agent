"""Test knowledge base search functionality (comprehensive)."""

import logging

import pytest

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.core.agno_agent import AgnoPersonalAgent

# Configure logging
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_knowledge_search_comprehensive():
    """Test knowledge base search functionality comprehensively."""
    logger.info("Testing Knowledge Base Search (Comprehensive)...")

    # Initialize agent
    logger.info("Initializing AgnoPersonalAgent...")
    agent = AgnoPersonalAgent(
        enable_memory=True,
        enable_mcp=False,
        debug=False,
    )

    success = await agent.initialize()
    assert success, "Failed to initialize agent"

    logger.info("Agent initialized successfully")

    # Test direct knowledge base search
    if agent.agno_knowledge:
        logger.info("Testing direct knowledge base search...")
        try:
            # Test direct search on knowledge base
            search_results = await agent.agno_knowledge.asearch("Eric", limit=3)
            logger.info("Direct search results for 'Eric': %d results", len(search_results))
            for i, result in enumerate(search_results, 1):
                logger.info("  %d. %s...", i, result.content[:100])
        except (RuntimeError, ValueError, AttributeError) as e:
            logger.error("Direct search failed: %s", e)

    # Test agent queries that should trigger knowledge search
    logger.info("Testing agent queries with knowledge search...")

    test_queries = [
        "What is my name?",
        "Who am I?",
        "Tell me about Eric",
        "What are my interests?",
        "What do you know about my skills?",
        "Search your knowledge base for information about me",
    ]

    for i, query in enumerate(test_queries, 1):
        logger.info("Query %d: %s", i, query)

        response = await agent.run(query, stream=False)
        assert response is not None, f"Query {i} returned None"
        assert isinstance(response, str), f"Query {i} response is not a string"
        logger.info("Response: %s...", response[:100])

    logger.info("Knowledge search test completed")
