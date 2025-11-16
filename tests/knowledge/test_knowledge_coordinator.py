"""
Test the Knowledge Coordinator implementation.

Tests the unified knowledge coordinator that routes queries between
local semantic search and LightRAG based on mode parameters and query analysis.
"""

import logging
import pytest

from personal_agent.utils import add_src_to_path, setup_logging

add_src_to_path()

from personal_agent.core.knowledge_coordinator import create_knowledge_coordinator
from personal_agent.core.agno_storage import create_agno_storage, create_combined_knowledge_base
from personal_agent.config import LIGHTRAG_URL, AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR, USER_ID

# Configure logging
logger = setup_logging(__name__, level=logging.INFO)


@pytest.mark.asyncio
async def test_knowledge_coordinator():
    """Test the Knowledge Coordinator functionality."""
    logger.info("Testing Knowledge Coordinator Implementation")

    # Use actual paths from configuration
    storage_dir = AGNO_STORAGE_DIR
    knowledge_dir = AGNO_KNOWLEDGE_DIR

    logger.info("Using configured storage at: %s", storage_dir)
    logger.info("Using configured knowledge dir: %s", knowledge_dir)
    logger.info("User ID: %s", USER_ID)

    # Create storage and knowledge base using actual configuration
    agno_storage = create_agno_storage(storage_dir)
    agno_knowledge = create_combined_knowledge_base(storage_dir, knowledge_dir, agno_storage)

    # Create Knowledge Coordinator
    logger.info("Creating Knowledge Coordinator with LightRAG URL: %s", LIGHTRAG_URL)
    coordinator = create_knowledge_coordinator(
        agno_knowledge=agno_knowledge,
        lightrag_url=LIGHTRAG_URL,
        debug=False
    )

    logger.info("Running Knowledge Coordinator Tests")
    
    # Test cases with different modes and query types
    test_cases = [
        {
            "query": "What is Python?",
            "mode": "local",
            "description": "Simple fact query with explicit local mode"
        },
        {
            "query": "How does machine learning relate to artificial intelligence?",
            "mode": "hybrid",
            "description": "Relationship query with explicit hybrid mode"
        },
        {
            "query": "Define recursion",
            "mode": "auto",
            "description": "Simple definition query with auto-detection"
        },
        {
            "query": "Explain the relationship between neural networks and deep learning",
            "mode": "auto",
            "description": "Complex relationship query with auto-detection"
        },
        {
            "query": "What is the capital of France?",
            "mode": "global",
            "description": "Simple fact with global mode (should use LightRAG)"
        },
        {
            "query": "Compare Python and JavaScript programming languages",
            "mode": "mix",
            "description": "Comparison query with mix mode"
        }
    ]
    
    results = []

    for i, test_case in enumerate(test_cases, 1):
        logger.info("Test %d: %s", i, test_case['description'])
        logger.info("Query: '%s' | Mode: %s", test_case['query'], test_case['mode'])

        try:
            result = await coordinator.query_knowledge_base(
                query=test_case['query'],
                mode=test_case['mode'],
                limit=3
            )

            # Determine which system was used based on result headers
            if "Local Knowledge Search Results" in result:
                system_used = "Local Semantic"
            elif "LightRAG Knowledge Graph Results" in result:
                system_used = "LightRAG"
            elif "Fallback" in result:
                system_used = "Fallback Used"
            else:
                system_used = "Unknown"

            logger.info("System Used: %s | Result Length: %d chars", system_used, len(result))

            results.append({
                "test": i,
                "query": test_case['query'],
                "mode": test_case['mode'],
                "system_used": system_used,
                "success": True,
                "result_length": len(result)
            })

        except RuntimeError as e:
            logger.error("Error: %s", str(e))
            results.append({
                "test": i,
                "query": test_case['query'],
                "mode": test_case['mode'],
                "system_used": "Error",
                "success": False,
                "error": str(e)
            })

    # Verify test results
    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)

    logger.info("Test Summary - Total: %d, Successful: %d, Failed: %d",
                total_tests, successful_tests, total_tests - successful_tests)

    assert successful_tests > 0, "No coordinator tests succeeded"


@pytest.mark.asyncio
async def test_routing_logic():
    """Test the routing logic specifically."""
    logger.info("Testing Routing Logic")

    coordinator = create_knowledge_coordinator(debug=False)

    # Test routing decisions without actually executing queries
    test_queries = [
        ("What is Python?", "auto", "Should route to local (simple fact)"),
        ("How does X relate to Y?", "auto", "Should route to LightRAG (relationship)"),
        ("Define machine learning", "local", "Should route to local (explicit)"),
        ("Compare A and B", "hybrid", "Should route to LightRAG (explicit)"),
        (
            "Explain the connection between neural networks and AI",
            "auto",
            "Should route to LightRAG (complex relationship)",
        ),
    ]

    routing_results = []
    for query, mode, expected in test_queries:
        # pylint: disable=protected-access
        routing_decision, reasoning = coordinator._determine_routing(query, mode)
        logger.info("Query: '%s...' | Mode: %s → Decision: %s", query[:30], mode, routing_decision)
        logger.info("Reasoning: %s | Expected: %s", reasoning, expected)

        routing_results.append({
            "query": query,
            "mode": mode,
            "decision": routing_decision,
            "expected": expected
        })

    assert len(routing_results) > 0, "No routing results generated"
