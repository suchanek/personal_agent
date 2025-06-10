#!/usr/bin/env python3
"""
Test with simpler search queries to avoid the apostrophe syntax error.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core import create_simple_personal_agent, load_agent_knowledge


async def test_simple_queries():
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
