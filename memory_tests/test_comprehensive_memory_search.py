#!/usr/bin/env python3
"""
Comprehensive Memory Search Test Script

This script tests the improved memory search functionality by:
1. Creating many diverse memories
2. Testing various search queries
3. Verifying that ALL memories are being searched
4. Ensuring no memories are missed due to limits

Run this script to verify the memory search fix is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def create_test_memories(agent: AgnoPersonalAgent) -> None:
    """Create a diverse set of test memories to search through."""

    print("🧠 Creating test memories...")

    # Educational background memories
    education_memories = [
        "I got my PhD in Computer Science from Stanford University in 2018",
        "I completed my Master's degree at MIT in 2015, focusing on artificial intelligence",
        "My undergraduate degree was in Mathematics from UC Berkeley, graduated in 2013",
        "I did a summer research internship at Google during my PhD studies",
        "My PhD thesis was on 'Neural Networks for Natural Language Processing'",
        "I was a teaching assistant for the Machine Learning course at Stanford",
        "I received the Outstanding Graduate Student Award in 2017",
    ]

    # Personal preferences memories
    preference_memories = [
        "I love drinking coffee, especially dark roast in the morning",
        "My favorite programming language is Python, but I also enjoy Rust",
        "I prefer working in quiet environments with minimal distractions",
        "I'm a vegetarian and have been for over 5 years",
        "I enjoy reading science fiction novels in my free time",
        "My favorite author is Isaac Asimov, particularly the Foundation series",
        "I like to go hiking on weekends when the weather is nice",
        "I'm not a fan of spicy food, I prefer mild flavors",
    ]

    # Work and career memories
    career_memories = [
        "I currently work as a Senior Software Engineer at a tech startup",
        "I specialize in machine learning and natural language processing",
        "I've been programming for over 10 years now",
        "I started my career as a junior developer at a small consulting firm",
        "I've worked on several open-source projects related to AI",
        "I gave a talk at PyCon 2022 about neural language models",
        "I'm interested in pursuing a career in AI research",
        "I've mentored several junior developers throughout my career",
    ]

    # Hobbies and interests memories
    hobby_memories = [
        "I play the guitar and have been learning for about 3 years",
        "I enjoy photography, especially landscape and nature shots",
        "I'm learning Spanish and can hold basic conversations",
        "I like to cook Italian food, pasta is my specialty",
        "I practice yoga twice a week to stay flexible and relaxed",
        "I'm a big fan of chess and play online regularly",
        "I collect vintage computer hardware as a hobby",
        "I enjoy watching documentaries about space and astronomy",
    ]

    # Travel and location memories
    travel_memories = [
        "I live in San Francisco, California",
        "I've traveled to Japan twice and absolutely loved it",
        "I spent a semester abroad in London during my undergraduate studies",
        "I want to visit New Zealand someday for the beautiful landscapes",
        "I've been to most major cities on the West Coast",
        "I prefer mountains over beaches for vacation destinations",
        "I've never been to South America but it's on my bucket list",
    ]

    # Family and relationships memories
    family_memories = [
        "I have two younger siblings, a brother and a sister",
        "My parents live in Portland, Oregon",
        "I'm currently single but open to dating",
        "My brother is a doctor and my sister is a teacher",
        "I have a close relationship with my grandparents",
        "I grew up in a small town in Oregon",
        "My family has a tradition of camping every summer",
    ]

    # Health and fitness memories
    health_memories = [
        "I go to the gym 3 times a week, focusing on strength training",
        "I'm allergic to shellfish and have to be careful when dining out",
        "I try to get 8 hours of sleep every night",
        "I take vitamin D supplements during the winter months",
        "I had knee surgery in 2020 but have fully recovered",
        "I meditate for 10 minutes every morning",
        "I drink at least 8 glasses of water per day",
    ]

    # Combine all memories
    all_memories = (
        education_memories
        + preference_memories
        + career_memories
        + hobby_memories
        + travel_memories
        + family_memories
        + health_memories
    )

    # Store each memory with appropriate topics
    memory_topics = {
        "education": education_memories,
        "preferences": preference_memories,
        "career": career_memories,
        "hobbies": hobby_memories,
        "travel": travel_memories,
        "family": family_memories,
        "health": health_memories,
    }

    stored_count = 0
    for topic, memories in memory_topics.items():
        for memory in memories:
            # Use the agent's memory tools directly
            result = await agent._get_memory_tools()
            store_memory_func = None
            for tool in result:
                if hasattr(tool, "__name__") and tool.__name__ == "store_user_memory":
                    store_memory_func = tool
                    break

            if store_memory_func:
                result = await store_memory_func(memory, [topic])
                if "Successfully stored" in result or "already exists" in result:
                    stored_count += 1
                    print(f"  ✅ Stored: {memory[:50]}...")
                else:
                    print(f"  ❌ Failed: {memory[:50]}... - {result}")
            else:
                print("  ❌ Could not find store_user_memory function")

    print(f"\n📊 Total memories stored: {stored_count}/{len(all_memories)}")
    return stored_count


async def test_memory_searches(agent: AgnoPersonalAgent) -> None:
    """Test various search queries to verify comprehensive search."""

    print("\n🔍 Testing memory search functionality...")

    # Get the query_memory function
    memory_tools = await agent._get_memory_tools()
    query_memory_func = None
    for tool in memory_tools:
        if hasattr(tool, "__name__") and tool.__name__ == "query_memory":
            query_memory_func = tool
            break

    if not query_memory_func:
        print("❌ Could not find query_memory function")
        return

    # Test cases: (query, expected_keywords, description)
    test_cases = [
        (
            "PhD",
            ["Stanford", "Computer Science", "2018"],
            "Should find PhD information",
        ),
        (
            "education",
            ["Stanford", "MIT", "Berkeley"],
            "Should find all education memories",
        ),
        ("coffee", ["dark roast", "morning"], "Should find coffee preferences"),
        (
            "programming",
            ["Python", "Rust"],
            "Should find programming language preferences",
        ),
        ("travel", ["Japan", "London"], "Should find travel memories"),
        ("family", ["siblings", "brother", "sister"], "Should find family information"),
        ("guitar", ["3 years"], "Should find guitar hobby"),
        ("San Francisco", ["California"], "Should find location information"),
        ("vegetarian", ["5 years"], "Should find dietary preferences"),
        ("gym", ["3 times", "strength"], "Should find fitness routine"),
        ("allergic", ["shellfish"], "Should find allergy information"),
        ("startup", ["Senior Software Engineer"], "Should find current job"),
        (
            "thesis",
            ["Neural Networks", "Natural Language"],
            "Should find PhD thesis topic",
        ),
    ]

    successful_searches = 0
    total_searches = len(test_cases)

    for query, expected_keywords, description in test_cases:
        print(f"\n🔎 Testing query: '{query}' - {description}")

        try:
            result = await query_memory_func(query)

            # Check if the result indicates memories were found
            if "No memories found" in result:
                print(f"  ❌ No memories found for '{query}'")
                print(f"     Expected to find keywords: {expected_keywords}")
                continue

            # Check if expected keywords are in the result
            found_keywords = []
            missing_keywords = []

            for keyword in expected_keywords:
                if keyword.lower() in result.lower():
                    found_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)

            if missing_keywords:
                print(f"  ⚠️  Partial match for '{query}'")
                print(f"     Found keywords: {found_keywords}")
                print(f"     Missing keywords: {missing_keywords}")
            else:
                print(f"  ✅ Full match for '{query}' - found all expected keywords")
                successful_searches += 1

            # Extract and display the search statistics
            if "total memories" in result:
                import re

                stats_match = re.search(
                    r"(\d+) matches from (\d+) total memories", result
                )
                if stats_match:
                    matches, total = stats_match.groups()
                    print(
                        f"     📊 Found {matches} matches from {total} total memories"
                    )

        except Exception as e:
            print(f"  ❌ Error searching for '{query}': {str(e)}")

    print(f"\n📈 Search Results Summary:")
    print(f"  Successful searches: {successful_searches}/{total_searches}")
    print(f"  Success rate: {(successful_searches/total_searches)*100:.1f}%")


async def test_comprehensive_search(agent: AgnoPersonalAgent) -> None:
    """Test that the search actually goes through ALL memories."""

    print("\n🔍 Testing comprehensive search (ALL memories)...")

    # Get all memories directly from the memory system
    if hasattr(agent, "agno_memory") and agent.agno_memory:
        all_memories = agent.agno_memory.get_user_memories(user_id=USER_ID)
        total_stored = len(all_memories)
        print(f"📊 Total memories in database: {total_stored}")

        # Test a very broad search that should match many memories
        memory_tools = await agent._get_memory_tools()
        query_memory_func = None
        for tool in memory_tools:
            if hasattr(tool, "__name__") and tool.__name__ == "query_memory":
                query_memory_func = tool
                break

        if query_memory_func:
            # Search for a common word that appears in many memories
            result = await query_memory_func("I")  # Should match many memories with "I"

            print(f"\n🔎 Broad search results:")
            print(f"Query: 'I' (should match many memories)")

            # Extract statistics from the result
            import re

            stats_match = re.search(r"(\d+) matches from (\d+) total memories", result)
            if stats_match:
                matches, searched_total = stats_match.groups()
                print(
                    f"  📊 Found {matches} matches from {searched_total} total memories"
                )

                if int(searched_total) == total_stored:
                    print(
                        f"  ✅ SUCCESS: Searched through ALL {total_stored} memories!"
                    )
                else:
                    print(
                        f"  ❌ ISSUE: Only searched {searched_total} out of {total_stored} memories"
                    )
            else:
                print("  ⚠️  Could not extract search statistics from result")
                print(f"  Result preview: {result[:200]}...")
        else:
            print("❌ Could not find query_memory function")
    else:
        print("❌ Could not access memory system")


async def main():
    """Main test function."""
    print("🧪 Comprehensive Memory Search Test")
    print("=" * 50)

    # Initialize the agent
    print("🚀 Initializing AgnoPersonalAgent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="llama3.2:3b",  # Use a smaller model for testing
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for faster testing
        debug=True,
        user_id=USER_ID,
        storage_dir=AGNO_STORAGE_DIR,
    )

    # Initialize the agent
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return

    print("✅ Agent initialized successfully")

    # Clear existing memories for clean test
    print("\n🧹 Clearing existing memories for clean test...")
    if hasattr(agent, "agno_memory") and agent.agno_memory:
        try:
            # Try different methods to clear memories
            if hasattr(agent.agno_memory, "clear_user_memories") and callable(
                getattr(agent.agno_memory, "clear_user_memories", None)
            ):
                agent.agno_memory.clear_user_memories(user_id=USER_ID)
                print("✅ Cleared existing memories using clear_user_memories")
            else:
                # Try clear_memories method with try-except to avoid pylint issues
                try:
                    agent.agno_memory.clear_memories()
                    print("✅ Cleared existing memories using clear_memories")
                except (AttributeError, TypeError):
                    # Method doesn't exist or isn't callable, fall through to manual deletion
                    # Manually delete memories one by one
                    existing_memories = agent.agno_memory.get_user_memories(user_id=USER_ID)
                    deleted_count = 0
                    for memory in existing_memories:
                        if hasattr(memory, "memory_id") and memory.memory_id:
                            if agent.agno_memory.delete_user_memory(
                                memory.memory_id, USER_ID
                            ):
                                deleted_count += 1
                    print(f"✅ Manually deleted {deleted_count} existing memories")
        except Exception as e:
            print(f"⚠️  Could not clear memories: {e}")
            print("   Continuing with existing memories...")

    # Create test memories
    stored_count = await create_test_memories(agent)

    if stored_count == 0:
        print("❌ No memories were stored, cannot proceed with tests")
        return

    # Test memory searches
    await test_memory_searches(agent)

    # Test comprehensive search
    await test_comprehensive_search(agent)

    print("\n🎉 Test completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
