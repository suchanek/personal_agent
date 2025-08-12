#!/usr/bin/env python3
"""Test script to verify knowledge base search functionality (comprehensive)."""

import asyncio
import logging
import sys
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from src.personal_agent.config import DATA_DIR, LLM_MODEL
from src.personal_agent.core.agno_agent import AgnoPersonalAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


async def test_knowledge_search_comprehensive():
    """Test knowledge base search functionality comprehensively."""
    print("🔄 Testing Knowledge Base Search (Comprehensive)...")
    print(f"📁 DATA_DIR: {DATA_DIR}")
    print(f"🤖 LLM_MODEL: {LLM_MODEL}")
    print()

    # Initialize agent
    print("🚀 Initializing AgnoPersonalAgent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=f"{DATA_DIR}/agno",
        knowledge_dir=f"{DATA_DIR}/knowledge",
        debug=True,  # Enable debug to see tool calls
    )

    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return False

    print("✅ Agent initialized successfully")
    print()

    # Test direct knowledge base search
    if agent.agno_knowledge:
        print("🔍 Testing direct knowledge base search...")
        try:
            # Test direct search on knowledge base
            search_results = await agent.agno_knowledge.asearch("Eric", limit=3)
            print(f"Direct search results for 'Eric': {len(search_results)} results")
            for i, result in enumerate(search_results, 1):
                print(f"  {i}. {result.content[:100]}...")
            print()
        except Exception as e:
            print(f"❌ Direct search failed: {e}")
            print()

    # Test agent queries that should trigger knowledge search
    print("💬 Testing agent queries with knowledge search...")

    test_queries = [
        "What is my name?",
        "Who am I?",
        "Tell me about Eric",
        "What are my interests?",
        "What do you know about my skills?",
        "Search your knowledge base for information about me",
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

    print("\n✅ Knowledge search test completed")
    return True


async def main():
    """Run the test asynchronously."""
    await test_knowledge_search_comprehensive()


if __name__ == "__main__":
    asyncio.run(main())
