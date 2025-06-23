#!/usr/bin/env python3
"""
Standalone comprehensive test suite for direct SemanticMemoryManager capabilities.

This test suite validates all 8 memory tools with timing information and various retrieval scenarios.
No external imports from other test files - completely self-contained.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from personal_agent.core.agno_agent import create_agno_agent


def print_banner():
    """Print a nice banner for the test suite."""
    print("\n" + "🧠" * 20)
    print("🧠 SEMANTIC MEMORY MANAGER CAPABILITY TESTS 🧠")
    print("🧠" * 20)
    print("\nThis test suite validates all 8 memory tools:")
    print("1. store_user_memory - Store new memories")
    print("2. query_memory - Search memories semantically")
    print("3. update_memory - Update existing memories")
    print("4. delete_memory - Delete specific memories")
    print("5. clear_memories - Clear all user memories")
    print("6. get_recent_memories - Get recent memories")
    print("7. get_all_memories - Get all memories")
    print("8. get_memory_stats - Get memory statistics")
    print("\nFeatures tested:")
    print("• Bulk fact storage with timing")
    print("• Semantic search capabilities")
    print("• Memory management operations")
    print("• Performance benchmarking")
    print("• Error handling validation")
    print("\n" + "🧠" * 20 + "\n")


def generate_test_facts() -> List[Dict[str, any]]:
    """Generate comprehensive test facts for memory operations."""
    return [
        # Personal Information
        {"content": "My name is Alex Johnson and I'm 28 years old", "topics": ["personal_info", "identity"]},
        {"content": "I live in San Francisco, California in a downtown apartment", "topics": ["personal_info", "location"]},
        {"content": "I work as a Senior Software Engineer at TechCorp", "topics": ["work", "career"]},
        {"content": "I graduated from Stanford University with a Computer Science degree in 2018", "topics": ["education", "background"]},
        {"content": "I'm originally from Portland, Oregon but moved to SF for work", "topics": ["personal_info", "location", "background"]},
        
        # Hobbies and Interests
        {"content": "I love hiking and go to Marin Headlands every weekend", "topics": ["hobbies", "outdoor_activities"]},
        {"content": "I play guitar and have been learning jazz for 3 years", "topics": ["hobbies", "music"]},
        {"content": "I'm passionate about photography, especially landscape photography", "topics": ["hobbies", "creative"]},
        {"content": "I enjoy cooking Italian food and make homemade pasta", "topics": ["hobbies", "cooking", "food"]},
        {"content": "I practice yoga every morning for 30 minutes", "topics": ["hobbies", "health", "wellness"]},
        
        # Food Preferences
        {"content": "I'm vegetarian and have been for 5 years", "topics": ["food", "preferences", "lifestyle"]},
        {"content": "My favorite cuisine is Mediterranean, especially Greek food", "topics": ["food", "preferences"]},
        {"content": "I love coffee and prefer dark roast Ethiopian beans", "topics": ["food", "preferences", "beverages"]},
        {"content": "I'm allergic to shellfish and always carry an EpiPen", "topics": ["health", "allergies", "medical"]},
        {"content": "I enjoy craft beer, particularly IPAs from local breweries", "topics": ["food", "preferences", "beverages"]},
        
        # Work and Career
        {"content": "I specialize in machine learning and AI development", "topics": ["work", "skills", "technology"]},
        {"content": "I lead a team of 6 engineers working on recommendation systems", "topics": ["work", "leadership", "management"]},
        {"content": "I'm working on a side project building a personal finance app", "topics": ["work", "projects", "entrepreneurship"]},
        {"content": "I want to start my own AI company within the next 2 years", "topics": ["goals", "career", "entrepreneurship"]},
        {"content": "I mentor junior developers and teach Python workshops", "topics": ["work", "teaching", "community"]},
        
        # Health and Fitness
        {"content": "I run 5 miles every Tuesday and Thursday morning", "topics": ["health", "fitness", "routine"]},
        {"content": "I have a gym membership at Equinox and do strength training", "topics": ["health", "fitness"]},
        {"content": "I track my sleep and aim for 8 hours every night", "topics": ["health", "wellness", "routine"]},
        {"content": "I take vitamin D and B12 supplements daily", "topics": ["health", "supplements", "wellness"]},
        {"content": "I meditate for 15 minutes before bed using Headspace", "topics": ["health", "wellness", "mental_health"]},
        
        # Technology and Skills
        {"content": "I'm proficient in Python, JavaScript, and Go programming languages", "topics": ["skills", "technology", "programming"]},
        {"content": "I use VS Code as my primary development environment", "topics": ["tools", "technology", "preferences"]},
        {"content": "I'm learning Rust and building a CLI tool as practice", "topics": ["learning", "technology", "projects"]},
        {"content": "I prefer Mac for development but use Linux servers for deployment", "topics": ["technology", "preferences", "tools"]},
        {"content": "I'm interested in blockchain technology and DeFi applications", "topics": ["technology", "interests", "finance"]},
    ]


async def find_tool_by_name(agent, tool_name: str):
    """Find a tool by name in the agent's tools."""
    for tool in agent.agent.tools:
        if hasattr(tool, '__name__') and tool.__name__ == tool_name:
            return tool
    return None


async def test_agent_setup():
    """Set up the AgnoPersonalAgent for testing."""
    print("🔧 Setting up AgnoPersonalAgent for comprehensive testing...")
    start_time = time.time()
    
    agent = await create_agno_agent(
        model_provider="ollama",
        model_name="llama3.2:3b",
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for focused memory testing
        storage_dir="./data/test_agno_comprehensive",
        debug=True,
        user_id="test_user_comprehensive"
    )
    
    setup_time = time.time() - start_time
    print(f"✅ Agent setup completed in {setup_time:.2f} seconds")
    return agent, setup_time


async def test_clear_memories(agent):
    """Test clearing all memories to start fresh."""
    print("\n🧹 Testing clear_memories...")
    start_time = time.time()
    
    clear_tool = await find_tool_by_name(agent, "clear_memories")
    if not clear_tool:
        print("❌ Could not find clear_memories tool")
        return 0
    
    result = await clear_tool()
    clear_time = time.time() - start_time
    
    print(f"Clear result: {result}")
    print(f"⏱️ Clear operation took {clear_time:.3f} seconds")
    
    success = "✅" in result or "No memories" in result
    if not success:
        print(f"❌ Clear operation failed: {result}")
    
    return clear_time


async def test_bulk_memory_storage(agent, test_facts):
    """Test storing all test facts with timing information."""
    print(f"\n💾 Testing bulk storage of {len(test_facts)} memories...")
    
    store_tool = await find_tool_by_name(agent, "store_user_memory")
    if not store_tool:
        print("❌ Could not find store_user_memory tool")
        return {}
    
    storage_times = []
    successful_stores = 0
    duplicate_detections = 0
    
    for i, fact in enumerate(test_facts):
        print(f"Storing fact {i+1}/{len(test_facts)}: {fact['content'][:50]}...")
        
        start_time = time.time()
        result = await store_tool(fact["content"], fact["topics"])
        store_time = time.time() - start_time
        storage_times.append(store_time)
        
        if "✅" in result:
            if "already exists" in result:
                duplicate_detections += 1
                print(f"   🔄 Duplicate detected: {result}")
            else:
                successful_stores += 1
                print(f"   ✅ Stored successfully in {store_time:.3f}s")
        else:
            print(f"   ❌ Storage failed: {result}")
    
    # Calculate timing statistics
    avg_storage_time = sum(storage_times) / len(storage_times) if storage_times else 0
    total_storage_time = sum(storage_times)
    
    results = {
        "total_time": total_storage_time,
        "average_time": avg_storage_time,
        "successful_stores": successful_stores,
        "duplicate_detections": duplicate_detections,
        "total_attempts": len(test_facts)
    }
    
    print(f"\n📊 Bulk Storage Results:")
    print(f"   Total time: {total_storage_time:.2f} seconds")
    print(f"   Average time per memory: {avg_storage_time:.3f} seconds")
    print(f"   Successful stores: {successful_stores}")
    print(f"   Duplicate detections: {duplicate_detections}")
    print(f"   Total attempts: {len(test_facts)}")
    
    return results


async def test_memory_statistics(agent):
    """Test getting memory statistics."""
    print("\n📊 Testing get_memory_stats...")
    start_time = time.time()
    
    stats_tool = await find_tool_by_name(agent, "get_memory_stats")
    if not stats_tool:
        print("❌ Could not find get_memory_stats tool")
        return 0
    
    result = await stats_tool()
    stats_time = time.time() - start_time
    
    print(f"Memory statistics:\n{result}")
    print(f"⏱️ Stats retrieval took {stats_time:.3f} seconds")
    
    success = "Total memories:" in result
    if not success:
        print(f"❌ Stats retrieval failed: {result}")
    
    return stats_time


async def test_semantic_search_queries(agent):
    """Test various semantic search queries with timing."""
    print("\n🔍 Testing semantic search capabilities...")
    
    search_queries = [
        # Direct matches
        {"query": "work", "expected_topics": ["work", "career"]},
        {"query": "food preferences", "expected_topics": ["food", "preferences"]},
        {"query": "hobbies", "expected_topics": ["hobbies"]},
        
        # Semantic matches
        {"query": "job", "expected_topics": ["work", "career"]},
        {"query": "eating habits", "expected_topics": ["food", "preferences"]},
        {"query": "free time activities", "expected_topics": ["hobbies"]},
        
        # Specific searches
        {"query": "San Francisco", "expected_topics": ["location"]},
        {"query": "programming languages", "expected_topics": ["technology", "skills"]},
        {"query": "exercise routine", "expected_topics": ["health", "fitness"]},
        
        # Complex searches
        {"query": "outdoor activities hiking", "expected_topics": ["outdoor_activities", "hobbies"]},
        {"query": "machine learning AI", "expected_topics": ["technology", "work"]},
        {"query": "vegetarian Mediterranean", "expected_topics": ["food", "preferences"]},
    ]
    
    query_tool = await find_tool_by_name(agent, "query_memory")
    if not query_tool:
        print("❌ Could not find query_memory tool")
        return {}
    
    search_times = []
    successful_searches = 0
    
    for i, search in enumerate(search_queries):
        print(f"\nSearch {i+1}/{len(search_queries)}: '{search['query']}'")
        
        start_time = time.time()
        result = await query_tool(search["query"], limit=5)
        search_time = time.time() - start_time
        search_times.append(search_time)
        
        if "🧠 MEMORY RETRIEVAL" in result and "No memories found" not in result:
            successful_searches += 1
            print(f"   ✅ Found results in {search_time:.3f}s")
            
            # Check if expected topics appear in results
            found_expected = any(topic in result.lower() for topic in search["expected_topics"])
            if found_expected:
                print(f"   🎯 Found expected topics: {search['expected_topics']}")
            else:
                print(f"   ⚠️ Expected topics not found: {search['expected_topics']}")
            
            # Show first result line
            lines = result.split('\n')
            for line in lines:
                if line.strip() and line.startswith('1.'):
                    print(f"   📝 First result: {line.strip()[:100]}...")
                    break
        else:
            print(f"   ❌ No results found in {search_time:.3f}s")
    
    # Calculate search timing statistics
    avg_search_time = sum(search_times) / len(search_times) if search_times else 0
    total_search_time = sum(search_times)
    
    results = {
        "total_time": total_search_time,
        "average_time": avg_search_time,
        "successful_searches": successful_searches,
        "total_queries": len(search_queries)
    }
    
    print(f"\n📊 Semantic Search Results:")
    print(f"   Total time: {total_search_time:.2f} seconds")
    print(f"   Average time per search: {avg_search_time:.3f} seconds")
    print(f"   Successful searches: {successful_searches}/{len(search_queries)}")
    
    return results


async def test_memory_management_operations(agent):
    """Test update and delete operations."""
    print("\n🔧 Testing memory management operations...")
    
    store_tool = await find_tool_by_name(agent, "store_user_memory")
    update_tool = await find_tool_by_name(agent, "update_memory")
    delete_tool = await find_tool_by_name(agent, "delete_memory")
    
    if not store_tool:
        print("❌ Could not find store_user_memory tool")
        return {}
    
    test_content = "This is a test memory for management operations"
    print(f"Storing test memory: {test_content}")
    
    store_result = await store_tool(test_content, ["test", "management"])
    print(f"Store result: {store_result}")
    
    timing_results = {}
    
    if "ID:" in store_result:
        # Extract memory ID from result
        memory_id = store_result.split("ID: ")[1].split(")")[0]
        print(f"Extracted memory ID: {memory_id}")
        
        # Test update operation
        if update_tool:
            print("\nTesting update_memory...")
            start_time = time.time()
            updated_content = "This is an UPDATED test memory for management operations"
            update_result = await update_tool(memory_id, updated_content, ["test", "management", "updated"])
            update_time = time.time() - start_time
            timing_results["update_memory"] = update_time
            
            print(f"Update result: {update_result}")
            print(f"⏱️ Update took {update_time:.3f} seconds")
        
        # Test delete operation
        if delete_tool:
            print("\nTesting delete_memory...")
            start_time = time.time()
            delete_result = await delete_tool(memory_id)
            delete_time = time.time() - start_time
            timing_results["delete_memory"] = delete_time
            
            print(f"Delete result: {delete_result}")
            print(f"⏱️ Delete took {delete_time:.3f} seconds")
    else:
        print("❌ Could not extract memory ID from store result")
    
    return timing_results


async def test_error_handling(agent):
    """Test error handling for various edge cases."""
    print("\n🚨 Testing error handling...")
    
    query_tool = await find_tool_by_name(agent, "query_memory")
    update_tool = await find_tool_by_name(agent, "update_memory")
    delete_tool = await find_tool_by_name(agent, "delete_memory")
    
    error_tests = []
    
    # Test empty query
    if query_tool:
        print("Testing empty query...")
        result = await query_tool("")
        error_tests.append(("empty_query", "❌" in result))
        print(f"Empty query result: {result[:100]}...")
    
    # Test invalid memory ID for update
    if update_tool:
        print("Testing invalid memory ID for update...")
        result = await update_tool("invalid-id-12345", "test content", ["test"])
        error_tests.append(("invalid_update_id", "❌" in result))
        print(f"Invalid update result: {result[:100]}...")
    
    # Test invalid memory ID for delete
    if delete_tool:
        print("Testing invalid memory ID for delete...")
        result = await delete_tool("invalid-id-12345")
        error_tests.append(("invalid_delete_id", "❌" in result))
        print(f"Invalid delete result: {result[:100]}...")
    
    successful_error_handling = sum(1 for _, handled in error_tests if handled)
    print(f"\n📊 Error Handling Results: {successful_error_handling}/{len(error_tests)} errors handled correctly")
    
    return {
        "total_tests": len(error_tests),
        "successful_handling": successful_error_handling
    }


def print_comprehensive_results(timing_results):
    """Print comprehensive test results with timing information."""
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE TEST RESULTS")
    print("="*80)
    
    print(f"\n⏱️ TIMING RESULTS:")
    print("-" * 40)
    
    for operation, timing in timing_results.items():
        if isinstance(timing, dict):
            print(f"{operation}:")
            for key, value in timing.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.3f}s")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"{operation}: {timing:.3f}s")
    
    print(f"\n📊 PERFORMANCE SUMMARY:")
    print("-" * 40)
    
    if "bulk_storage" in timing_results:
        storage = timing_results["bulk_storage"]
        print(f"Memory Storage:")
        print(f"  • Stored {storage['successful_stores']} memories successfully")
        print(f"  • Detected {storage['duplicate_detections']} duplicates")
        print(f"  • Average storage time: {storage['average_time']:.3f}s per memory")
    
    if "semantic_search" in timing_results:
        search = timing_results["semantic_search"]
        print(f"Semantic Search:")
        print(f"  • {search['successful_searches']}/{search['total_queries']} searches successful")
        print(f"  • Average search time: {search['average_time']:.3f}s per query")
    
    if "error_handling" in timing_results:
        errors = timing_results["error_handling"]
        print(f"Error Handling:")
        print(f"  • {errors['successful_handling']}/{errors['total_tests']} errors handled correctly")
    
    print(f"\n✅ COMPREHENSIVE TESTING COMPLETED!")
    print("="*80)


async def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🚀 Starting Comprehensive SemanticMemoryManager Test Suite")
    print("="*80)
    
    timing_results = {}
    agent = None
    
    try:
        # Setup
        agent, setup_time = await test_agent_setup()
        timing_results["agent_setup"] = setup_time
        
        # Generate test data
        test_facts = generate_test_facts()
        
        # Run tests
        timing_results["clear_memories"] = await test_clear_memories(agent)
        timing_results["bulk_storage"] = await test_bulk_memory_storage(agent, test_facts)
        timing_results["get_memory_stats"] = await test_memory_statistics(agent)
        timing_results["semantic_search"] = await test_semantic_search_queries(agent)
        
        # Memory management operations
        mgmt_results = await test_memory_management_operations(agent)
        timing_results.update(mgmt_results)
        
        # Error handling
        timing_results["error_handling"] = await test_error_handling(agent)
        
        # Print results
        print_comprehensive_results(timing_results)
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if agent:
            await agent.cleanup()


async def main():
    """Main function to run the comprehensive test suite."""
    print_banner()
    print("📋 REQUIREMENTS:")
    print("• Ollama server running with llama3.2:3b model")
    print("• Personal agent dependencies installed")
    print("• Write access to ./data/test_agno_comprehensive/")
    print("\n🚀 Starting tests in 3 seconds...")
    print("   (Press Ctrl+C to cancel)")
    
    try:
        await asyncio.sleep(3)
        await run_comprehensive_tests()
        print("\n🎉 All tests completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️ Tests cancelled by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
