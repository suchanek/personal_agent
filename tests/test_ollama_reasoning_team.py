#!/usr/bin/env python3
"""
Test script for the Ollama-based Multi-Purpose Reasoning Team

This script tests the new team to ensure all agents work correctly with your local Ollama instance.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from examples.teams.reasoning_team import create_team


async def test_team():
    """Test the Ollama reasoning team with various queries."""

    print("🚀 Testing Ollama Multi-Purpose Reasoning Team")
    print("=" * 60)

    try:
        # Create the team
        print("📝 Creating team...")
        team = await create_team()
        print("✅ Team created successfully!")

        # Test queries for each agent
        test_queries = [
            {
                "query": "Hi! What are you capable of doing?",
                "expected_agent": "Team coordinator",
                "description": "Test team introduction and capabilities",
            },
            {
                "query": "Remember that I love skiing and live in Colorado",
                "expected_agent": "Memory Agent",
                "description": "Test memory storage functionality",
            },
            {
                "query": "What do you remember about me?",
                "expected_agent": "Memory Agent",
                "description": "Test memory retrieval functionality",
            },
            {
                "query": "What is the current stock price of AAPL?",
                "expected_agent": "Finance Agent",
                "description": "Test financial data retrieval",
            },
            {
                "query": "Calculate the square root of 144",
                "expected_agent": "Calculator Agent",
                "description": "Test mathematical calculations",
            },
            {
                "query": "Search for the latest news about artificial intelligence",
                "expected_agent": "Web Agent",
                "description": "Test web search functionality",
            },
            {
                "query": "Write a haiku about local AI models",
                "expected_agent": "Writer Agent",
                "description": "Test content generation",
            },
        ]

        # Run tests
        for i, test in enumerate(test_queries, 1):
            print(f"\n🧪 Test {i}/{len(test_queries)}: {test['description']}")
            print(f"Expected agent: {test['expected_agent']}")
            print(f"Query: {test['query']}")
            print("-" * 40)

            try:
                await team.aprint_response(test["query"], stream=True)
                print("✅ Test completed successfully")
            except Exception as e:
                print(f"❌ Test failed: {str(e)}")

            print("\n" + "=" * 60)

        print("🎉 All tests completed!")

    except Exception as e:
        print(f"❌ Failed to create or test team: {str(e)}")
        import traceback

        traceback.print_exc()


async def test_memory_persistence():
    """Test that memory persists across team instances."""

    print("\n🧠 Testing Memory Persistence")
    print("=" * 60)

    try:
        # Create first team instance
        team1 = await create_team()

        # Store a memory
        print("📝 Storing memory in first team instance...")
        await team1.aprint_response(
            "Remember that I work as a software engineer at Google"
        )

        # Create second team instance
        team2 = await create_team()

        # Try to retrieve the memory
        print("\n🔍 Retrieving memory from second team instance...")
        await team2.aprint_response("What do you remember about my job?")

        print("✅ Memory persistence test completed")

    except Exception as e:
        print(f"❌ Memory persistence test failed: {str(e)}")


async def main():
    """Main test function."""

    # Test basic team functionality
    await test_team()

    # Test memory persistence
    await test_memory_persistence()

    print("\n🏁 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
