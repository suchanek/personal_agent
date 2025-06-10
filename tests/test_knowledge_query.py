#!/usr/bin/env python3
"""Test asking the agent about what knowledge is in its knowledge base."""

import asyncio
import logging

from src.personal_agent.config import LLM_MODEL
from src.personal_agent.core.agno_agent import AgnoPersonalAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_knowledge_query():
    """Test querying the agent about its knowledge base contents."""
    print("🔄 Initializing Agno Personal Agent...")

    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for focused knowledge testing
        storage_dir="./data/agno",
        knowledge_dir="./data/knowledge",
        debug=True,  # Enable debug to see tool calls
    )

    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return

    print("✅ Agent initialized successfully")
    print()

    # Test queries about knowledge base contents
    queries = [
        "What knowledge do you have in your knowledge base?",
        "What files are in your knowledge base?",
        "What information do you know about me?",
        "Search your knowledge base for any available information",
        "What personal information is stored in your knowledge?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"🔍 Query {i}: {query}")
        print("-" * 60)

        try:
            response = await agent.run(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")

        print()
        print("=" * 80)
        print()


if __name__ == "__main__":
    asyncio.run(test_knowledge_query())
