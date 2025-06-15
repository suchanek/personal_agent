#!/usr/bin/env python3
"""
Test script for the new retrieve_memory tool.

This script demonstrates the usage of the new retrieve_memory tool with various
parameter combinations.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import LLM_MODEL, OLLAMA_URL
from personal_agent.core.agno_agent import create_agno_agent


async def test_retrieve_memory_tool():
    """Test the new retrieve_memory tool functionality."""
    print("🧠 Testing retrieve_memory tool functionality")
    print("=" * 60)

    # Create agent with memory enabled
    agent = await create_agno_agent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for simpler testing
        debug=True,
        user_id="test_user",
    )

    print("✅ Agent created successfully")
    print()

    # Test storing some sample memories first
    print("📝 Storing sample memories...")

    sample_memories = [
        ("I love pizza and pasta", ["food", "preferences"]),
        ("I work as a software engineer", ["work", "career"]),
        ("My favorite color is blue", ["preferences", "personal"]),
        ("I enjoy hiking on weekends", ["hobbies", "outdoor"]),
        ("I live in San Francisco", ["location", "personal"]),
        ("I prefer tea over coffee", ["food", "preferences", "drinks"]),
    ]

    for content, topics in sample_memories:
        response = await agent.run(f"Remember this: {content}")
        print(f"  Stored: {content}")

    print("\n" + "=" * 60)
    print("🔍 Testing retrieve_memory tool with different parameters")
    print("=" * 60)

    # Test cases for retrieve_memory
    test_cases = [
        {
            "description": "Get 3 recent memories",
            "query": "Use retrieve_memory with n_memories=3",
        },
        {
            "description": "Get memories about food preferences",
            "query": "Use retrieve_memory with topic='food'",
        },
        {
            "description": "Search for memories about 'work' with limit of 2",
            "query": "Use retrieve_memory with query='work' and n_memories=2",
        },
        {
            "description": "Get all memories about preferences",
            "query": "Use retrieve_memory with topic='preferences'",
        },
        {
            "description": "Search for memories about 'favorite' things",
            "query": "Use retrieve_memory with query='favorite'",
        },
        {
            "description": "Get 10 recent memories (should return all available)",
            "query": "Use retrieve_memory with n_memories=10",
        },
        {
            "description": "Search for non-existent topic",
            "query": "Use retrieve_memory with topic='nonexistent'",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']} - Query: '{test_case['query']}'")
        print("-" * 40)
        
        try:
            response = await agent.run(test_case['query'])
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ retrieve_memory tool testing completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_retrieve_memory_tool())
