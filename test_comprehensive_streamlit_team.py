#!/usr/bin/env python3
"""
Comprehensive test script for the fixed streamlit team implementation.
Tests all team members, memory operations, and tool functionality.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID
from personal_agent.team.personal_agent_team import create_personal_agent_team
from personal_agent.core.agno_storage import create_agno_memory


class TeamTester:
    """Comprehensive tester for the Personal Agent Team."""
    
    def __init__(self):
        self.team = None
        self.test_results = {}
        
    def log_test(self, test_name, success, details=""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if details:
            print(f"      {details}")
        self.test_results[test_name] = success
        
    def setup_team(self):
        """Set up the team for testing."""
        print("🚀 Setting up Personal Agent Team for comprehensive testing...")
        print("=" * 60)
        
        try:
            # Create team using the factory function
            self.team = create_personal_agent_team(
                model_provider="ollama",
                model_name=LLM_MODEL,
                ollama_base_url=OLLAMA_URL,
                storage_dir=AGNO_STORAGE_DIR,
                user_id=USER_ID,
                debug=True,
            )
            
            # Create memory system for compatibility
            agno_memory = create_agno_memory(AGNO_STORAGE_DIR, debug_mode=True)
            
            # Attach memory to team for access
            self.team.agno_memory = agno_memory
            
            print(f"✅ Team setup complete!")
            print(f"   - Team: {getattr(self.team, 'name', 'Unknown')}")
            print(f"   - Members: {len(getattr(self.team, 'members', []))}")
            print(f"   - Memory system: {hasattr(self.team, 'agno_memory')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Team setup failed: {str(e)}")
            return False
    
    async def test_memory_operations(self):
        """Test memory storage and retrieval operations."""
        print("\n🧠 Testing Memory Operations...")
        
        if not self.team or not hasattr(self.team, 'agno_memory'):
            self.log_test("Memory System Available", False, "No memory system found")
            return
        
        try:
            # Test 1: Store a memory
            test_memory = "I love hiking in the mountains and prefer early morning hikes."
            query1 = f"Remember this about me: {test_memory}"
            
            print(f"   Storing memory: {test_memory}")
            response1 = await self.team.arun(query1, user_id=USER_ID)
            
            # Check if memory was stored
            memories_after = self.team.agno_memory.get_user_memories(user_id=USER_ID)
            memory_stored = any(test_memory.lower() in getattr(mem, 'memory', '').lower() 
                              for mem in memories_after)
            
            self.log_test("Store Memory", memory_stored, 
                         f"Response: {response1.content[:100]}...")
            
            # Test 2: Retrieve memory
            query2 = "What do you remember about my hiking preferences?"
            print(f"   Retrieving memory: {query2}")
            response2 = await self.team.arun(query2, user_id=USER_ID)
            
            memory_retrieved = "hiking" in response2.content.lower()
            self.log_test("Retrieve Memory", memory_retrieved,
                         f"Response: {response2.content[:100]}...")
            
            # Test 3: Memory search functionality
            search_results = self.team.agno_memory.search_user_memories(
                user_id=USER_ID,
                query="hiking",
                retrieval_method="last_n",
                limit=5
            )
            
            self.log_test("Memory Search", len(search_results) > 0,
                         f"Found {len(search_results)} memories")
            
        except Exception as e:
            self.log_test("Memory Operations", False, f"Error: {str(e)}")
    
    async def test_web_research_agent(self):
        """Test the web research agent."""
        print("\n🌐 Testing Web Research Agent...")
        
        try:
            # Test web search functionality
            query = "Search for the latest news about artificial intelligence"
            print(f"   Query: {query}")
            
            start_time = time.time()
            response = await self.team.arun(query, user_id=USER_ID)
            response_time = time.time() - start_time
            
            # Check if response contains web search results
            has_web_content = any(keyword in response.content.lower() 
                                for keyword in ["search", "found", "news", "ai", "artificial"])
            
            # Check for tool calls
            tool_calls = 0
            if hasattr(response, 'messages') and response.messages:
                for message in response.messages:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        tool_calls += len(message.tool_calls)
            
            self.log_test("Web Search", has_web_content,
                         f"Response time: {response_time:.2f}s, Tool calls: {tool_calls}")
            
        except Exception as e:
            self.log_test("Web Research Agent", False, f"Error: {str(e)}")
    
    async def test_calculator_agent(self):
        """Test the calculator agent."""
        print("\n🧮 Testing Calculator Agent...")
        
        try:
            # Test basic calculation
            query = "Calculate 15% of 250 and explain the result"
            print(f"   Query: {query}")
            
            response = await self.team.arun(query, user_id=USER_ID)
            
            # Check if response contains calculation result (15% of 250 = 37.5)
            has_calculation = any(str(num) in response.content 
                                for num in ["37.5", "37", "38"])
            
            # Check for tool calls
            tool_calls = 0
            if hasattr(response, 'messages') and response.messages:
                for message in response.messages:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        tool_calls += len(message.tool_calls)
            
            self.log_test("Calculator", has_calculation,
                         f"Tool calls: {tool_calls}, Response: {response.content[:100]}...")
            
        except Exception as e:
            self.log_test("Calculator Agent", False, f"Error: {str(e)}")
    
    async def test_finance_agent(self):
        """Test the finance agent."""
        print("\n💰 Testing Finance Agent...")
        
        try:
            # Test stock price query
            query = "What's the current stock price of Apple (AAPL)?"
            print(f"   Query: {query}")
            
            response = await self.team.arun(query, user_id=USER_ID)
            
            # Check if response contains financial data
            has_finance_data = any(keyword in response.content.lower() 
                                 for keyword in ["price", "stock", "aapl", "apple", "$"])
            
            # Check for tool calls
            tool_calls = 0
            if hasattr(response, 'messages') and response.messages:
                for message in response.messages:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        tool_calls += len(message.tool_calls)
            
            self.log_test("Finance Data", has_finance_data,
                         f"Tool calls: {tool_calls}, Response: {response.content[:100]}...")
            
        except Exception as e:
            self.log_test("Finance Agent", False, f"Error: {str(e)}")
    
    async def test_file_operations_agent(self):
        """Test the file operations agent."""
        print("\n📁 Testing File Operations Agent...")
        
        try:
            # Test file listing
            query = "List the files in the current directory"
            print(f"   Query: {query}")
            
            response = await self.team.arun(query, user_id=USER_ID)
            
            # Check if response contains file listing
            has_file_data = any(keyword in response.content.lower() 
                              for keyword in ["file", "directory", ".py", "folder"])
            
            # Check for tool calls
            tool_calls = 0
            if hasattr(response, 'messages') and response.messages:
                for message in response.messages:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        tool_calls += len(message.tool_calls)
            
            self.log_test("File Operations", has_file_data,
                         f"Tool calls: {tool_calls}, Response: {response.content[:100]}...")
            
        except Exception as e:
            self.log_test("File Operations Agent", False, f"Error: {str(e)}")
    
    async def test_multi_agent_coordination(self):
        """Test coordination between multiple agents."""
        print("\n🤝 Testing Multi-Agent Coordination...")
        
        try:
            # Test query that requires multiple agents
            query = ("Remember that I'm interested in tech stocks, then search for recent "
                    "news about Tesla stock performance and calculate what a 5% gain "
                    "would mean for a $1000 investment")
            print(f"   Complex query: {query[:80]}...")
            
            start_time = time.time()
            response = await self.team.arun(query, user_id=USER_ID)
            response_time = time.time() - start_time
            
            # Check if response addresses multiple aspects
            has_memory = "remember" in response.content.lower() or "noted" in response.content.lower()
            has_search = any(keyword in response.content.lower() 
                           for keyword in ["tesla", "news", "search"])
            has_calculation = any(keyword in response.content.lower() 
                                for keyword in ["50", "$50", "5%", "gain"])
            
            # Count tool calls
            tool_calls = 0
            if hasattr(response, 'messages') and response.messages:
                for message in response.messages:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        tool_calls += len(message.tool_calls)
            
            coordination_success = has_memory or has_search or has_calculation
            
            self.log_test("Multi-Agent Coordination", coordination_success,
                         f"Time: {response_time:.2f}s, Tool calls: {tool_calls}")
            self.log_test("Memory Component", has_memory)
            self.log_test("Search Component", has_search)
            self.log_test("Calculation Component", has_calculation)
            
        except Exception as e:
            self.log_test("Multi-Agent Coordination", False, f"Error: {str(e)}")
    
    async def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n⚠️  Testing Error Handling...")
        
        try:
            # Test with empty query
            response1 = await self.team.arun("", user_id=USER_ID)
            empty_handled = len(response1.content) > 0
            self.log_test("Empty Query Handling", empty_handled)
            
            # Test with very long query
            long_query = "Tell me about " + "artificial intelligence " * 100
            response2 = await self.team.arun(long_query, user_id=USER_ID)
            long_handled = len(response2.content) > 0
            self.log_test("Long Query Handling", long_handled)
            
            # Test with special characters
            special_query = "What about émojis 🤖 and spëcial chars?"
            response3 = await self.team.arun(special_query, user_id=USER_ID)
            special_handled = len(response3.content) > 0
            self.log_test("Special Characters", special_handled)
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {str(e)}")
    
    def test_memory_statistics(self):
        """Test memory statistics functionality."""
        print("\n📊 Testing Memory Statistics...")
        
        try:
            if not hasattr(self.team, 'agno_memory'):
                self.log_test("Memory Statistics", False, "No memory system")
                return
            
            # Get all memories
            memories = self.team.agno_memory.get_user_memories(user_id=USER_ID)
            self.log_test("Memory Count", len(memories) > 0, f"Found {len(memories)} memories")
            
            # Test memory manager stats
            if hasattr(self.team.agno_memory, 'memory_manager'):
                memory_manager = self.team.agno_memory.memory_manager
                if hasattr(memory_manager, 'get_memory_stats'):
                    stats = memory_manager.get_memory_stats(
                        self.team.agno_memory.db, USER_ID
                    )
                    self.log_test("Memory Statistics", True, 
                                 f"Total: {stats.get('total_memories', 0)}")
                else:
                    self.log_test("Memory Statistics", False, "No stats method")
            else:
                self.log_test("Memory Statistics", False, "No memory manager")
                
        except Exception as e:
            self.log_test("Memory Statistics", False, f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all comprehensive tests."""
        print("🧪 COMPREHENSIVE PERSONAL AGENT TEAM TESTING")
        print("=" * 60)
        
        # Setup
        if not self.setup_team():
            return False
        
        # Run all test suites
        await self.test_memory_operations()
        await self.test_web_research_agent()
        await self.test_calculator_agent()
        await self.test_finance_agent()
        await self.test_file_operations_agent()
        await self.test_multi_agent_coordination()
        await self.test_error_handling()
        self.test_memory_statistics()
        
        # Summary
        self.print_summary()
        
        return all(self.test_results.values())
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        print(f"Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print()
        
        # Group results by category
        categories = {
            "Core Functionality": ["Store Memory", "Retrieve Memory", "Memory Search", "Memory Count", "Memory Statistics"],
            "Agent Tools": ["Web Search", "Calculator", "Finance Data", "File Operations"],
            "Advanced Features": ["Multi-Agent Coordination", "Memory Component", "Search Component", "Calculation Component"],
            "Error Handling": ["Empty Query Handling", "Long Query Handling", "Special Characters"]
        }
        
        for category, tests in categories.items():
            category_results = [self.test_results.get(test, False) for test in tests if test in self.test_results]
            if category_results:
                category_passed = sum(category_results)
                category_total = len(category_results)
                status = "✅" if category_passed == category_total else "⚠️" if category_passed > 0 else "❌"
                print(f"{status} {category}: {category_passed}/{category_total}")
        
        print()
        
        # Detailed results
        print("Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {test_name}")
        
        print("\n" + "=" * 60)
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! The streamlit team is fully functional!")
            print("   Ready for production use: streamlit run tools/paga_streamlit_team.py")
        elif passed > total * 0.8:
            print("✅ Most tests passed! The streamlit team is largely functional.")
            print("   Minor issues may exist but core functionality works.")
        elif passed > total * 0.5:
            print("⚠️  Some tests failed. The streamlit team has partial functionality.")
            print("   Review failed tests before production use.")
        else:
            print("❌ Many tests failed. The streamlit team needs significant fixes.")
            print("   Do not use in production until issues are resolved.")


async def main():
    """Run comprehensive testing."""
    tester = TeamTester()
    success = await tester.run_all_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
