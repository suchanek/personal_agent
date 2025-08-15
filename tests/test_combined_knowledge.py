#!/usr/bin/env python3
"""Test the new combined knowledge base implementation."""

import asyncio
import logging

from personal_agent.utils import add_src_to_path

add_src_to_path()

from src.personal_agent.config import LLM_MODEL
from src.personal_agent.core.agno_agent import AgnoPersonalAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_combined_knowledge():
    """Test the combined knowledge base implementation."""
    print("🔄 Testing Combined Knowledge Base Implementation...")

    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for cleaner output
        debug=True,  # Enable debug to see tool calls
    )

    success = await agent.initialize(recreate=False)
    if not success:
        print("❌ Failed to initialize agent")
        return False

    print("✅ Agent initialized successfully")
    print()

    # Test knowledge base queries
    test_queries = [
        "What do you know about Eric?",
        "What is in your knowledge base?",
        "Search your knowledge base for AI",
        "What kind of information do you have about projects?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 60)

        try:
            response = await agent.run(query)
            print(f"Response: {response}")
            print("-" * 60)
        except Exception as e:
            print(f"❌ Query failed: {e}")
            print("-" * 60)

    print("\n✅ Combined knowledge base test completed")
    return True


async def main():
    """Run the test asynchronously."""
    await test_combined_knowledge()


if __name__ == "__main__":
    asyncio.run(main())
