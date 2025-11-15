#!/usr/bin/env python3
"""
Quick Fact Recall Tester - Focused testing for immediate recall issues.

This is a streamlined version of the comprehensive fact recall tester,
designed for quick debugging and validation of specific recall problems.
"""

import asyncio
import sys
import time
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from personal_agent.config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def quick_fact_recall_test():
    """Quick test for fact recall issues."""
    print("🚀 Quick Fact Recall Test")
    print("=" * 40)
    
    # Initialize agent
    print("🤖 Initializing agent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return False
    
    print(f"✅ Agent initialized with model: {LLM_MODEL}")
    
    # Store a few key facts
    print("\n📝 Storing key facts...")
    key_facts = [
        "My name is Eric G. Suchanek.",
        "I have a Ph.D. degree.",
        "I work as a GeekSquad Agent at BestBuy.",
        "I am currently working on proteusPy.",
        "My email address is suchanek@mac.com.",
    ]
    
    stored_count = 0
    for fact in key_facts:
        try:
            response = await agent.run(f"Please remember this fact about me: {fact}")
            if any(indicator in response.lower() for indicator in ["stored", "remember", "noted", "✅", "🧠"]):
                stored_count += 1
                print(f"  ✅ Stored: {fact}")
            else:
                print(f"  ⚠️ Unclear: {fact}")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  ❌ Failed: {fact} - {e}")
    
    print(f"\n📊 Stored {stored_count}/{len(key_facts)} facts")
    
    if stored_count == 0:
        print("❌ No facts were stored successfully")
        return False
    
    # Wait for storage to settle
    print("\n⏳ Waiting for storage to settle...")
    await asyncio.sleep(2)
    
    # Test recall
    print("\n🔍 Testing fact recall...")
    test_queries = [
        ("What is my name?", ["Eric", "Suchanek"]),
        ("Where do I work?", ["BestBuy", "GeekSquad"]),
        ("What is my email?", ["suchanek@mac.com"]),
        ("What am I working on?", ["proteusPy"]),
        ("What degree do I have?", ["Ph.D", "PhD"]),
    ]
    
    passed = 0
    total = len(test_queries)
    
    for query, expected_terms in test_queries:
        print(f"\n  🔎 Query: {query}")
        
        try:
            start_time = time.time()
            response = await agent.run(query)
            end_time = time.time()
            
            # Check if expected terms are in the response
            found_terms = []
            for term in expected_terms:
                if term.lower() in response.lower():
                    found_terms.append(term)
            
            if found_terms:
                passed += 1
                print(f"    ✅ PASS ({end_time - start_time:.2f}s): Found {found_terms}")
                print(f"       Response: {response[:80]}...")
            else:
                print(f"    ❌ FAIL: Expected {expected_terms}, got none")
                print(f"       Response: {response[:120]}...")
                
        except Exception as e:
            print(f"    ❌ ERROR: {e}")
    
    success_rate = (passed / total) * 100
    print(f"\n📊 Results: {passed}/{total} ({success_rate:.1f}%) passed")
    
    # Overall assessment
    if success_rate >= 80:
        print("🎉 EXCELLENT: Fact recall is working well!")
        return True
    elif success_rate >= 60:
        print("⚠️ GOOD: Fact recall working with some issues")
        return True
    else:
        print("❌ POOR: Significant fact recall problems detected")
        return False


async def test_memory_search_directly():
    """Test memory search functionality directly."""
    print("\n🔍 Testing Direct Memory Search...")
    
    try:
        # Initialize agent
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            user_id=USER_ID,
            debug=True,
            enable_memory=True,
            enable_mcp=False,
            storage_dir=AGNO_STORAGE_DIR,
        )
        
        await agent.initialize()
        
        # Get memory tools directly
        memory_tools = await agent._get_memory_tools()
        search_function = None
        
        for tool in memory_tools:
            if hasattr(tool, '__name__') and 'search' in tool.__name__.lower():
                search_function = tool
                break
        
        if search_function:
            print(f"✅ Found memory search function: {search_function.__name__}")
            
            # Test direct search
            try:
                result = await search_function(query="Eric")
                print(f"📋 Search result: {result[:200]}...")
                return True
            except Exception as e:
                print(f"❌ Search function failed: {e}")
                return False
        else:
            print("❌ No memory search function found")
            return False
            
    except Exception as e:
        print(f"❌ Direct memory search test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🧪 Quick Fact Recall Tester")
    print("This test quickly validates basic fact recall functionality")
    print()
    
    try:
        # Run quick recall test
        recall_success = await quick_fact_recall_test()
        
        # Run direct memory search test
        search_success = await test_memory_search_directly()
        
        print("\n" + "=" * 50)
        print("📋 QUICK TEST SUMMARY")
        print("=" * 50)
        
        print(f"Fact Recall Test: {'✅ PASS' if recall_success else '❌ FAIL'}")
        print(f"Memory Search Test: {'✅ PASS' if search_success else '❌ FAIL'}")
        
        overall_success = recall_success and search_success
        
        if overall_success:
            print("\n🎉 OVERALL: Quick tests PASSED - Basic recall is working!")
            return True
        else:
            print("\n⚠️ OVERALL: Quick tests show issues - Need investigation")
            print("\n💡 Recommendations:")
            if not recall_success:
                print("  - Check memory storage mechanism")
                print("  - Verify model is processing memory tools correctly")
            if not search_success:
                print("  - Check memory search function implementation")
                print("  - Verify database connectivity")
            return False
            
    except Exception as e:
        print(f"\n❌ Quick test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Usage: python test_quick_fact_recall.py")
    print("This performs a quick validation of fact recall capabilities")
    print()
    
    # Run the tests
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Quick fact recall test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Quick fact recall test failed!")
        sys.exit(1)
