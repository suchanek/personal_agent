#!/usr/bin/env python3
"""
Test script to diagnose SQLite/LanceDB knowledge base search issues.

This script tests the knowledge base search functionality to understand why
the Streamlit UI isn't returning results when Charlie Brown memories are
successfully stored via the REST API.

The script will:
1. Initialize an agent with knowledge base
2. Check if knowledge base is properly configured
3. Perform direct knowledge base searches
4. Compare with memory searches to understand the difference
5. Provide diagnostic information about the knowledge base state

Usage:
    python test_kb_search.py

Expected outcome:
    - Verify if knowledge base search works at all
    - Identify if the issue is with initialization, search, or data storage
    - Provide recommendations for fixing the Streamlit UI issue

Author: Eric G. Suchanek, PhD
Date: 2025-11-16
Branch: v0.8.77ldev
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import get_current_user_id
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.streamlit_helpers import StreamlitKnowledgeHelper, StreamlitMemoryHelper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_knowledge_base_search():
    """Test knowledge base search functionality."""
    logger.info("=" * 80)
    logger.info("KNOWLEDGE BASE SEARCH DIAGNOSTIC TEST")
    logger.info("=" * 80)

    # Get current user
    user_id = get_current_user_id()
    logger.info(f"Current user: {user_id}")

    # Initialize agent
    logger.info("\n1. Initializing AgnoPersonalAgent...")
    agent = AgnoPersonalAgent(
        user_id=user_id,
        enable_memory=True,
        debug=True
    )

    success = await agent.initialize()
    if not success:
        logger.error("❌ Failed to initialize agent")
        return

    logger.info("✅ Agent initialized successfully")

    # Check agent configuration
    logger.info("\n2. Checking agent configuration...")
    logger.info(f"   - Agent has agno_knowledge: {hasattr(agent, 'agno_knowledge')}")
    logger.info(f"   - Agent has agno_memory: {hasattr(agent, 'agno_memory')}")
    logger.info(f"   - Agent has memory_manager: {hasattr(agent, 'memory_manager')}")

    if hasattr(agent, 'agno_knowledge') and agent.agno_knowledge:
        logger.info(f"   - agno_knowledge type: {type(agent.agno_knowledge)}")
        logger.info(f"   - agno_knowledge has search: {hasattr(agent.agno_knowledge, 'search')}")
    else:
        logger.warning("⚠️  Agent does not have agno_knowledge properly initialized")

    # Test memory search first (we know this works)
    logger.info("\n3. Testing MEMORY search (baseline - we know this works)...")
    memory_helper = StreamlitMemoryHelper(agent)

    memory_results = memory_helper.search_memories(
        query="Charlie Brown",
        limit=5,
        similarity_threshold=0.3
    )

    logger.info(f"   Memory search returned {len(memory_results)} results")
    if memory_results:
        logger.info("   Sample memory result:")
        for i, item in enumerate(memory_results[:3], 1):
            # Handle tuple format (memory, score) or object format
            if isinstance(item, tuple):
                mem, score = item
                logger.info(f"     {i}. (score: {score:.3f}) {mem.memory[:80]}...")
            else:
                logger.info(f"     {i}. {item.memory[:80]}...")

    # Test knowledge base search
    logger.info("\n4. Testing KNOWLEDGE BASE search (the problematic one)...")
    knowledge_helper = StreamlitKnowledgeHelper(agent)

    # First check if knowledge_manager is accessible
    km = knowledge_helper.knowledge_manager
    logger.info(f"   - knowledge_manager accessible: {km is not None}")

    if km:
        logger.info(f"   - knowledge_manager type: {type(km)}")
        logger.info(f"   - knowledge_manager has search: {hasattr(km, 'search')}")

        # Try to get knowledge base info
        if hasattr(km, 'vector_db'):
            logger.info(f"   - knowledge_manager has vector_db: {km.vector_db is not None}")
        if hasattr(km, 'knowledge_bases'):
            logger.info(f"   - knowledge_manager has knowledge_bases: {len(km.knowledge_bases) if km.knowledge_bases else 0}")

    # Attempt the actual search
    test_queries = [
        "Charlie Brown",
        "Peanuts",
        "Snoopy",
        "friends",
        "baseball"
    ]

    for query in test_queries:
        logger.info(f"\n   Testing query: '{query}'")
        try:
            kb_results = knowledge_helper.search_knowledge(
                query=query,
                limit=5
            )

            logger.info(f"   ✅ Query executed - returned {len(kb_results) if kb_results else 0} results")

            if kb_results:
                logger.info(f"   Sample knowledge result:")
                for i, result in enumerate(kb_results[:2], 1):
                    if hasattr(result, 'content'):
                        logger.info(f"     {i}. Content: {result.content[:80]}...")
                        logger.info(f"        Title: {getattr(result, 'title', 'N/A')}")
                        logger.info(f"        Source: {getattr(result, 'source', 'N/A')}")
                    elif isinstance(result, dict):
                        logger.info(f"     {i}. Content: {result.get('content', 'N/A')[:80]}...")
                    else:
                        logger.info(f"     {i}. Result: {str(result)[:80]}...")
            else:
                logger.warning(f"   ⚠️  No results found for '{query}'")

        except Exception as e:
            logger.error(f"   ❌ Error during search: {e}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")

    # Compare knowledge base vs memory storage
    logger.info("\n5. ANALYSIS: Knowledge Base vs Memory Storage")
    logger.info("   " + "-" * 70)
    logger.info(f"   Memory search found: {len(memory_results)} results")
    logger.info(f"   Knowledge search found: 0 results (or errors)")
    logger.info("   " + "-" * 70)

    # Provide diagnostic conclusions
    logger.info("\n6. DIAGNOSTIC CONCLUSIONS:")
    logger.info("   " + "=" * 70)

    if not km:
        logger.error("   ❌ ISSUE: Knowledge manager not accessible")
        logger.info("   RECOMMENDATION: Check agent initialization and knowledge base setup")
    elif memory_results and not any([knowledge_helper.search_knowledge(q, 5) for q in test_queries]):
        logger.warning("   ⚠️  ISSUE: Memory search works but knowledge search doesn't")
        logger.info("   ANALYSIS: The issue is likely one of:")
        logger.info("     1. Knowledge base and memory are SEPARATE storage systems")
        logger.info("     2. Charlie Brown facts were stored in MEMORY, not KNOWLEDGE")
        logger.info("     3. Knowledge base search requires different data ingestion")
        logger.info("   ")
        logger.info("   RECOMMENDATION:")
        logger.info("     - Memories (from inject_charlie_brown_friends_facts.py) go to:")
        logger.info("       * SQLite memory database")
        logger.info("       * LightRAG graph memory (for entity extraction)")
        logger.info("     ")
        logger.info("     - Knowledge base expects:")
        logger.info("       * Documents/files ingested via knowledge tools")
        logger.info("       * Content stored in LanceDB vector database")
        logger.info("       * Different API endpoints/methods for ingestion")
        logger.info("     ")
        logger.info("   FIX OPTIONS:")
        logger.info("     A. Update Streamlit UI to use MEMORY search instead of KNOWLEDGE search")
        logger.info("     B. Create a unified search that queries both memory and knowledge")
        logger.info("     C. Add a knowledge ingestion endpoint to store facts as documents")
        logger.info("     D. Clarify in UI that 'SQLite/LanceDB' searches knowledge docs, not memories")

    logger.info("   " + "=" * 70)
    logger.info("\n✅ Diagnostic test complete")


async def main():
    """Main entry point."""
    await test_knowledge_base_search()


if __name__ == "__main__":
    asyncio.run(main())
