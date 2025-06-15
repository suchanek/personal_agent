#!/usr/bin/env python3
"""
Corrected Personal Ag    # Example interaction
    queries = [
        "Tell me about Eric G. Suchanek and his AI agent project",
        "What technology stack is being used for the personal AI agent?",
        "What are the key benefits of the current architecture?"
    ]ript - Fixed Sync/Async Pattern

This script demonstrates the corrected implementation where:
1. Knowledge base creation is synchronous (following knowledge_agent_example.py pattern)
2. Only knowledge loading is async
3. Agent creation uses the simple pattern: Agent(knowledge=knowledge_base, search_knowledge=True)

This replaces the complex AgnoPersonalAgent class with a simple, working implementation.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core import create_simple_personal_agent, load_agent_knowledge

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


async def main():
    """
    Main function demonstrating the corrected sync/async pattern.

    Pattern:
    1. Create agent and knowledge base synchronously
    2. Load knowledge base content asynchronously
    3. Use agent normally
    """
    logger.info("🚀 Starting Personal Agent with corrected sync/async pattern...")

    # Step 1: Create agent synchronously (no await needed!)
    agent, knowledge_base = create_simple_personal_agent()

    # Step 2: Load knowledge asynchronously (if knowledge base exists)
    if knowledge_base:
        await load_agent_knowledge(knowledge_base, recreate=False)

    # Step 3: Use the agent
    logger.info("💬 Agent ready! You can now interact with it.")

    # Example interaction
    queries = [
        "Tell me about Eric G. Suchanek AI agent project",
        "What technology stack is being used?",
        "What are the key benefits of the current architecture?",
    ]

    for i, query in enumerate(queries, 1):
        logger.info(f"\n📝 Query {i}: {query}")
        logger.info("🤖 Response:")
        logger.info("-" * 60)

        response = await agent.arun(query)
        print(response)

        logger.info("-" * 60)

    logger.info("✅ Demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
