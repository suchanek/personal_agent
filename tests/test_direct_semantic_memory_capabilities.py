#!/usr/bin/env python3
"""
Comprehensive test suite for direct SemanticMemoryManager capabilities in AgnoPersonalAgent.

This test suite validates all 8 memory tools with timing information and various retrieval scenarios:
1. store_user_memory - Store new memories
2. query_memory - Search memories semantically  
3. update_memory - Update existing memories
4. delete_memory - Delete specific memories
5. clear_memories - Clear all user memories
6. get_recent_memories - Get recent memories
7. get_all_memories - Get all memories
8. get_memory_stats - Get memory statistics

Tests include:
- Bulk fact storage with timing
- Semantic search capabilities
- Memory management operations
- Performance benchmarking
- Error handling validation
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from personal_agent.core.agno_agent import create_agno_agent


class MemoryTestSuite:
    """Comprehensive test suite for direct SemanticMemoryManager capabilities."""
    
    def __init__(self):
        self.agent = None
        self.test_user_id = "test_user_comprehensive"
        self.test_storage_dir = "./data/test_agno_comprehensive"
        self.timing_results = {}
        self.test_facts = self._generate_test_facts()
        
    def _generate_test_facts(self) -> List[Dict[str, any]]:
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
            
            # Relationships and Social
            {"content": "I'm dating Sarah who works as a graphic designer", "topics": ["relationships", "personal_info"]},
            {"content": "My best friend Mike lives in Seattle and we video call weekly", "topics": ["relationships", "friends"]},
            {"content": "I have a close relationship with my parents who still live in Portland", "topics": ["relationships", "family"]},
            {"content": "I have a rescue dog named Luna who's a golden retriever mix", "topics": ["pets", "personal_info"]},
            {"content": "I'm part of a hiking group that meets every Saturday", "topics": ["social", "hobbies", "community"]},
            
            # Goals and Aspirations
            {"content": "I want to climb Mount Whitney next summer", "topics": ["goals", "outdoor_activities", "challenges"]},
            {"content": "I'm saving money to buy a house in the Bay Area", "topics": ["goals", "financial", "housing"]},
            {"content": "I plan to learn Spanish and take classes starting next month", "topics": ["goals", "education", "languages"]},
            {"content": "I want to travel to Japan and experience the culture", "topics": ["goals", "travel", "culture"]},
            {"content": "I'm considering getting an MBA from Berkeley in a few years", "topics": ["goals", "education", "career"]},
            
            # Technology and Skills
            {"content": "I'm proficient in Python, JavaScript, and Go programming languages", "topics": ["skills", "technology", "programming"]},
            {"content": "I use VS Code as my primary development environment", "topics": ["tools", "technology", "preferences"]},
            {"content": "I'm learning Rust and building a CLI tool as practice", "topics": ["learning", "technology", "projects"]},
            {"content": "I prefer Mac for development but use Linux servers for deployment", "topics": ["technology", "preferences", "tools"]},
            {"content": "I'm interested in blockchain technology and DeFi applications", "topics": ["technology", "interests", "finance"]},
            
            # Miscellaneous
            {"content": "I read 2-3 books per month, mostly sci-fi and business books", "topics": ["hobbies", "reading", "learning"]},
            {"content": "I listen to podcasts during commute, especially tech and entrepreneurship", "topics": ["learning", "interests", "routine"]},
            {"content": "I volunteer at a local animal shelter on weekends", "topics": ["volunteering", "community", "animals"]},
            {"content": "I collect vintage vinyl records, especially jazz and blues", "topics": ["hobbies", "collecting", "music"]},
            {"content": "I'm learning to play chess and practice on Chess.com daily", "topics": ["hobbies", "games", "learning"]},
        ]
    
    async def setup_agent(self) -> None:
        """Set up the AgnoPersonalAgent for testing."""
        print("🔧 Setting up AgnoPersonalAgent for comprehensive testing...")
        start_time = time.time()
        
        self.agent = await create_agno_agent(
            model_provider="ollama",
            model_name="llama3.2:3b",
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for focused memory testing
            storage_dir=self.test_storage_dir,
            debug=True,
            user_id=self.test_user_id
        )
        
        setup_time = time.time() - start_time
        self.timing_results["agent_setup"] = setup_time
        print(f"✅ Agent setup completed in {setup_time:.2f} seconds")
    
    async def test_clear_memories(self) -> None:
        """Test clearing all memories to start fresh."""
        print("\n🧹 Testing clear_memories...")
        start_time = time.time()
        
        result = await self.agent.agent.tools[-1]()  # clear_memories is the last tool
        
        clear_time = time.time() - start_time
        self.timing_results["clear_memories"] = clear_time
        
        print(f"Clear result: {result}")
        print(f"⏱️ Clear operation took {clear_time:.3f} seconds")
        
        assert "✅" in result or "No memories" in result, f"Clear operation failed: {result}"
    
    async def test_bulk_memory_storage(self) -> None:
        """Test storing all test facts with timing information."""
        print(f"\n💾 Testing bulk storage of {len(self.test_facts)} memories...")
        
        storage_times = []
        successful_stores = 0
        duplicate_detections = 0
        
        for i, fact in enumerate(self.test_facts):
            print(f"Storing fact {i+1}/{len(self.test_facts)}: {fact['content'][:50]}...")
            
            start_time = time.time()
            
            # Find the store_user_memory tool
            store_tool = None
            for tool in self.agent.agent.tools:
                if hasattr(tool, '__name__') and tool.__name__ == 'store_user_memory':
                    store_tool = tool
                    break
            
            if not store_tool:
                print("❌ Could not find store_user_memory tool")
                continue
            
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
        
        self.timing_results["bulk_storage"] = {
            "total_time": total_storage_time,
            "average_time": avg_storage_time,
            "successful_stores": successful_stores,
            "duplicate_detections": duplicate_detections,
            "total_attempts": len(self.test_facts)
        }
        
        print(f"\n📊 Bulk Storage Results:")
        print(f"   Total time: {total_storage_time:.2f} seconds")
        print(f"   Average time per memory: {avg_storage_time:.3f} seconds")
        print(f"   Successful stores: {successful_stores}")
        print(f"   Duplicate detections: {duplicate_detections}")
        print(f"   Total attempts: {len(self.test_facts)}")
        
        assert successful_stores > 0, "No memories were successfully stored"
    
    async def test_memory_statistics(self) -> None:
        """Test getting memory statistics."""
        print("\n📊 Testing get_memory_stats...")
        start_time = time.time()
        
        # Find the get_memory_stats tool
        stats_tool = None
        for tool in self.agent.agent.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'get_memory_stats':
                stats_tool = tool
                break
        
        if not stats_tool:
            print("❌ Could not find get_memory_stats tool")
            return
        
        result = await stats_tool()
        stats_time = time.time() - start_time
        self.timing_results["get_memory_stats"] = stats_time
        
        print(f"Memory statistics:\n{result}")
        print(f"⏱️ Stats retrieval took {stats_time:.3f} seconds")
        
        assert "Total memories:" in result, f"Stats retrieval failed: {result}"
    
    async def test_semantic_search_queries(self) -> None:
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
        
        search_times = []
        successful_searches = 0
        
        # Find the query_memory tool
        query_tool = None
        for tool in self.agent.agent.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'query_memory':
                query_tool = tool
                break
        
        if not query_tool:
            print("❌ Could not find query_memory tool")
            return
        
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
        
        self.timing_results["semantic_search"] = {
            "total_time": total_search_time,
            "average_time": avg_search_time,
            "successful_searches": successful_searches,
            "total_queries": len(search_queries)
        }
        
        print(f"\n📊 Semantic Search Results:")
        print(f"   Total time: {total_search_time:.2f} seconds")
        print(f"   Average time per search: {avg_search_time:.3f} seconds")
        print(f"   Successful searches: {successful_searches}/{len(search_queries)}")
        
        assert successful_searches > 0, "No semantic searches were successful"
    
    async def test_memory_retrieval_methods(self) -> None:
        """Test different memory retrieval methods."""
        print("\n📋 Testing memory retrieval methods...")
        
        retrieval_tests = [
            {"method": "get_recent_memories", "limit": 10},
            {"method": "get_recent_memories", "limit": 20},
            {"method": "get_all_memories", "limit": None},
        ]
        
        for test in retrieval_tests:
            method_name = test["method"]
            limit = test["limit"]
            
            print(f"\nTesting {method_name}" + (f" (limit={limit})" if limit else ""))
            
            # Find the tool
            tool = None
            for t in self.agent.agent.tools:
                if hasattr(t, '__name__') and t.__name__ == method_name:
                    tool = t
                    break
            
            if not tool:
                print(f"❌ Could not find {method_name} tool")
                continue
            
            start_time = time.time()
            
            if limit and method_name == "get_recent_memories":
                result = await tool(limit)
            else:
                result = await tool()
            
            retrieval_time = time.time() - start_time
            self.timing_results[f"{method_name}_{limit or 'all'}"] = retrieval_time
            
            if "📝" in result and "No memories found" not in result:
                # Count memories in result
                memory_count = result.count('\n\n') - 1  # Rough count
                print(f"   ✅ Retrieved ~{memory_count} memories in {retrieval_time:.3f}s")
            else:
                print(f"   ❌ No memories retrieved in {retrieval_time:.3f}s")
    
    async def test_memory_management_operations(self) -> None:
        """Test update and delete operations."""
        print("\n🔧 Testing memory management operations...")
        
        # First, store a test memory to manage
        store_tool = None
        for tool in self.agent.agent.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'store_user_memory':
                store_tool = tool
                break
        
        if not store_tool:
            print("❌ Could not find store_user_memory tool")
            return
        
        test_content = "This is a test memory for management operations"
        print(f"Storing test memory: {test_content}")
        
        store_result = await store_tool(test_content, ["test", "management"])
        print(f"Store result: {store_result}")
        
        if "ID:" in store_result:
            # Extract memory ID from result
            memory_id = store_result.split("ID: ")[1].split(")")[0]
            print(f"Extracted memory ID: {memory_id}")
            
            # Test update operation
            print("\nTesting update_memory...")
            update_tool = None
            for tool in self.agent.agent.tools:
                if hasattr(tool, '__name__') and tool.__name__ == 'update_memory':
                    update_tool = tool
                    break
            
            if update_tool:
                start_time = time.time()
                updated_content = "This is an UPDATED test memory for management operations"
                update_result = await update_tool(memory_id, updated_content, ["test", "management", "updated"])
                update_time = time.time() - start_time
                self.timing_results["update_memory"] = update_time
                
                print(f"Update result: {update_result}")
                print(f"⏱️ Update took {update_time:.3f} seconds")
            
            # Test delete operation
            print("\nTesting delete_memory...")
            delete_tool = None
            for tool in self.agent.agent.tools:
                if hasattr(tool, '__name__') and tool.__name__ == 'delete_memory':
                    delete_tool = tool
                    break
            
            if delete_tool:
                start_time = time.time()
                delete_result = await delete_tool(memory_id)
                delete_time = time.time() - start_time
                self.timing_results["delete_memory"] = delete_time
                
                print(f"Delete result: {delete_result}")
                print(f"⏱️ Delete took {delete_time:.3f} seconds")
        else:
            print("❌ Could not extract memory ID from store result")
    
    async def test_error_handling(self) -> None:
        """Test error handling for various edge cases."""
        print("\n🚨 Testing error handling...")
        
        # Find tools
        query_tool = None
        update_tool = None
        delete_tool = None
        
        for tool in self.agent.agent.tools:
            if hasattr(tool, '__name__'):
                if tool.__name__ == 'query_memory':
                    query_tool = tool
                elif tool.__name__ == 'update_memory':
                    update_tool = tool
                elif tool.__name__ == 'delete_memory':
                    delete_tool = tool
        
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
        
        self.timing_results["error_handling"] = {
            "total_tests": len(error_tests),
            "successful_handling": successful_error_handling
        }
    
    def print_comprehensive_results(self) -> None:
        """Print comprehensive test results with timing information."""
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE TEST RESULTS")
        print("="*80)
        
        print(f"\n⏱️ TIMING RESULTS:")
        print("-" * 40)
        
        for operation, timing in self.timing_results.items():
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
        
        if "bulk_storage" in self.timing_results:
            storage = self.timing_results["bulk_storage"]
            print(f"Memory Storage:")
            print(f"  • Stored {storage['successful_stores']} memories successfully")
            print(f"  • Detected {storage['duplicate_detections']} duplicates")
            print(f"  • Average storage time: {storage['average_time']:.3f}s per memory")
        
        if "semantic_search" in self.timing_results:
            search = self.timing_results["semantic_search"]
            print(f"Semantic Search:")
            print(f"  • {search['successful_searches']}/{search['total_queries']} searches successful")
            print(f"  • Average search time: {search['average_time']:.3f}s per query")
        
        if "error_handling" in self.timing_results:
            errors = self.timing_results["error_handling"]
            print(f"Error Handling:")
            print(f"  • {errors['successful_handling']}/{errors['total_tests']} errors handled correctly")
        
        print(f"\n✅ COMPREHENSIVE TESTING COMPLETED!")
        print("="*80)
    
    async def run_comprehensive_tests(self) -> None:
        """Run all comprehensive tests."""
        print("🚀 Starting Comprehensive SemanticMemoryManager Test Suite")
        print("="*80)
        
        try:
            await self.setup_agent()
            await self.test_clear_memories()
            await self.test_bulk_memory_storage()
            await self.test_memory_statistics()
            await self.test_semantic_search_queries()
            await self.test_memory_retrieval_methods()
            await self.test_memory_management_operations()
            await self.test_error_handling()
            
            self.print_comprehensive_results()
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.agent:
                await self.agent.cleanup()


async def main():
    """Main function to run the comprehensive test suite."""
    test_suite = MemoryTestSuite()
    await test_suite.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())
