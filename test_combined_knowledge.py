#!/usr/bin/env python3
"""Test the new combined knowledge base implementation."""

import asyncio
import logging

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
        enable_mcp=False,  # Focus on knowledge base testing
        storage_dir="{DATA_DIR}/data/agno",
        knowledge_dir="{DATA_DIR}/data/knowledge",
        debug=True,
    )

    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return

    print("✅ Agent initialized successfully with combined knowledge base")
    print()

    # Test queries about knowledge base contents
    queries = [
        "What knowledge sources do you have available?",
        "Search your knowledge for any information about Eric",
        "What types of documents are in your knowledge base?",
        "What can you tell me about the user from your knowledge?",
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
    asyncio.run(test_combined_knowledge())
