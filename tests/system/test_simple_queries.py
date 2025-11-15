#!/usr/bin/env python3
"""
Test with simpler search queries to avoid the apostrophe syntax error.
"""

import asyncio
import sys
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from personal_agent.core import create_simple_personal_agent, load_agent_knowledge


async def test_simple_queries():
    """Test simple knowledge search queries without special characters."""
    # Create agent
    agent, knowledge_base = create_simple_personal_agent()

    # Load knowledge
    if knowledge_base:
        await load_agent_knowledge(knowledge_base, recreate=False)

    # Test simple queries without apostrophes
    queries = [
        "Eric Suchanek",
        "Personal AI Agent",
        "Agno framework",
        "technology stack",
        "architecture benefits",
    ]

    for query in queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 50)
        response = await agent.arun(query)
        print(response)
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_simple_queries())
