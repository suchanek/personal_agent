#!/usr/bin/env python3
"""
Test the fixed sync/async pattern for personal agent creation.

This script tests the corrected implementation where:
1. Knowledge base creation is synchronous (like knowledge_agent_example.py)
2. Only knowledge loading is async
3. Agent creation uses the simple pattern: Agent(knowledge=knowledge_base, search_knowledge=True)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.core import create_simple_personal_agent, load_agent_knowledge

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def test_sync_agent_creation():
    """Test that agent creation is synchronous and works."""
    logger.info("🧪 Testing synchronous agent creation...")

    try:
        # This should work synchronously (no await needed)
        agent, knowledge_base = create_simple_personal_agent()

        logger.info("✅ Agent created successfully!")
        logger.info(f"   Agent name: {agent.name}")
        logger.info(f"   Knowledge base: {'Available' if knowledge_base else 'None'}")
        logger.info(f"   Search enabled: {agent.search_knowledge}")

        return agent, knowledge_base

    except Exception as e:
        logger.error(f"❌ Failed to create agent: {e}")
        raise


async def test_async_knowledge_loading(knowledge_base):
    """Test that knowledge loading is async and works."""
    logger.info("🧪 Testing asynchronous knowledge loading...")

    if not knowledge_base:
        logger.info("⚠️  No knowledge base to load")
        return

    try:
        # This should work asynchronously
        await load_agent_knowledge(knowledge_base, recreate=False)
        logger.info("✅ Knowledge base loaded successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to load knowledge: {e}")
        raise


async def test_agent_interaction(agent):
    """Test basic agent interaction."""
    logger.info("🧪 Testing agent interaction...")

    try:
        # Test a simple query
        test_query = "What information do you have about Eric G. Suchanek?"

        logger.info(f"Query: {test_query}")
        logger.info("Agent response:")
        logger.info("-" * 50)

        # Use the agent to respond
        response = await agent.arun(test_query)
        print(response)

        logger.info("-" * 50)
        logger.info("✅ Agent interaction successful!")

    except Exception as e:
        logger.error(f"❌ Failed agent interaction: {e}")
        raise


async def main():
    """Main test function."""
    logger.info("🚀 Starting sync/async pattern test...")

    try:
        # Test 1: Synchronous agent creation
        agent, knowledge_base = test_sync_agent_creation()

        # Test 2: Asynchronous knowledge loading
        await test_async_knowledge_loading(knowledge_base)

        # Test 3: Agent interaction
        await test_agent_interaction(agent)

        logger.info("🎉 All tests passed! The sync/async pattern is working correctly.")

    except Exception as e:
        logger.error(f"💥 Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
