#!/usr/bin/env python3
"""
Quick test to verify knowledge search is working properly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.core import create_simple_personal_agent, load_agent_knowledge


async def test_knowledge_search():
    # Create agent
    agent, knowledge_base = create_simple_personal_agent()

    # Load knowledge
    if knowledge_base:
        await load_agent_knowledge(knowledge_base, recreate=False)

    # Test simple queries that should work
    queries = [
        "Eric Suchanek",
        "Personal AI Agent",
        "Agno framework",
        "technology stack",
    ]

    for query in queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 50)
        response = await agent.arun(query)
        print(response)
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_knowledge_search())
