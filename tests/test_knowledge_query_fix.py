#!/usr/bin/env python3
"""
Test script to verify the knowledge query fix works correctly. - works for user charlie!
Author: Eric G. Suchanek, PhD
Last Modification: 2025-08-25 23:17:50
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import at top level to fix Pylint warnings
from personal_agent.tools.knowledge_tools import KnowledgeTools


async def test_knowledge_queries():
    """Test various knowledge queries to ensure they work correctly."""
    print("🧪 Testing Knowledge Query Fix")
    print("=" * 50)

    try:
        # Initialize KnowledgeTools (the correct class name)
        tools = KnowledgeTools(knowledge_manager=None, agno_knowledge=None)

        # Test queries that should work
        test_cases = [
            ("Who is Lucy", "Should return info about Lucy from Peanuts"),
            ("Who is Schroeder", "Should return info about Schroeder from Peanuts"),
            ("Lucy", "Simple name query - might work depending on context"),
            ("Schroeder", "Simple name query - might work depending on context"),
            ("What is Peanuts", "Should return info about the comic strip"),
        ]

        for query, description in test_cases:
            print(f"\n🔍 Testing: '{query}'")
            print(f"   Expected: {description}")
            print("-" * 40)

            try:
                result = await tools.query_knowledge_base(
                    query, mode="hybrid", limit=10
                )

                # Check if we got meaningful results
                if "🧠 KNOWLEDGE BASE QUERY" in result and len(result) > 100:
                    print("✅ SUCCESS - Got detailed response")
                    print(f"   Response length: {len(result)} characters")
                    print(f"   Preview: {result[:150]}...")
                elif "No relevant knowledge found" in result:
                    print("⚠️  NO RESULTS - Knowledge base doesn't contain this info")
                elif "❌" in result:
                    print(f"❌ ERROR - {result}")
                else:
                    print(f"🤔 UNCLEAR - {result[:100]}...")

            except Exception as e:
                print(f"❌ EXCEPTION - {e}")

        # Test mode parameter works correctly
        print(f"\n🔧 Testing different modes for 'Who is Lucy':")
        print("-" * 40)

        for mode in ["hybrid", "global", "naive"]:
            try:
                result = await tools.query_knowledge_base(
                    "Who is Lucy", mode=mode, limit=5
                )
                success = "🧠 KNOWLEDGE BASE QUERY" in result and len(result) > 100
                print(
                    f"   Mode '{mode}': {'✅ SUCCESS' if success else '⚠️  NO RESULTS'}"
                )
            except Exception as e:
                print(f"   Mode '{mode}': ❌ ERROR - {e}")

        print(f"\n{'='*50}")
        print("🏁 Knowledge query testing complete!")

    except Exception as e:
        print(f"❌ Failed to import or initialize tools: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_knowledge_queries())
