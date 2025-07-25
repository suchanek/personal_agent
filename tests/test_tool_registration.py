#!/usr/bin/env python3
"""
Tool Registration Test Script

This script tests that the MemoryAndKnowledgeTools are properly registered
with the Agno agent and that all @tool decorators are working correctly.

Usage:
    python tests/test_tool_registration.py

This test will:
1. Initialize an Agno agent with memory and knowledge tools
2. Check that all expected tools are registered
3. Verify that tools can be called successfully
4. Test both sync and async tool methods
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Set

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.personal_agent.config.settings import OLLAMA_URL, USER_ID
from src.personal_agent.core.agent_instruction_manager import InstructionLevel
from src.personal_agent.core.agno_agent import create_agno_agent


class ToolRegistrationTester:
    """Test tool registration and functionality."""

    def __init__(self):
        """Initialize the tester."""
        self.agent = None
        self.expected_tools = {
            # Knowledge tools
            "ingest_knowledge_file",
            "ingest_knowledge_text", 
            "ingest_knowledge_from_url",
            "batch_ingest_directory",
            "query_knowledge_base",
            # Memory tools
            "store_user_memory",
            "query_memory",
            "update_memory",
            "delete_memory",
            "get_recent_memories",
            "get_all_memories",
            "get_memory_stats",
            "get_memories_by_topic",
            "list_memories",
            "store_graph_memory",
            "query_graph_memory",
            "get_memory_graph_labels",
            "clear_memories",
            "delete_memories_by_topic",
            "clear_all_memories",
        }

    async def initialize_agent(self) -> bool:
        """
        Initialize the Agno agent.
        
        Returns:
            True if initialization successful, False otherwise
        """
        print("🚀 Initializing Agno agent...")
        
        try:
            self.agent = await create_agno_agent(
                model_provider="ollama",
                model_name="qwen3:1.7b",  # Use a lightweight model for testing
                enable_memory=True,
                enable_mcp=False,  # Disable MCP for focused testing
                debug=False,
                ollama_base_url=OLLAMA_URL,
                user_id=USER_ID,
                recreate=False,
                instruction_level=InstructionLevel.MINIMAL,
            )
            print("✅ Agent initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return False

    def get_registered_tools(self) -> Set[str]:
        """
        Get the list of tools registered with the agent.
        
        Returns:
            Set of registered tool names
        """
        registered_tools = set()
        
        try:
            # The actual Agno agent is nested within the AgnoPersonalAgent
            actual_agent = self.agent.agent if hasattr(self.agent, 'agent') else self.agent
            
            # Check if agent has tools attribute
            if hasattr(actual_agent, 'tools') and actual_agent.tools:
                for tool in actual_agent.tools:
                    if hasattr(tool, 'name'):
                        registered_tools.add(tool.name)
                    elif hasattr(tool, '__name__'):
                        registered_tools.add(tool.__name__)
                        
            # Also check toolkit tools if available
            if hasattr(actual_agent, 'toolkits'):
                for toolkit in actual_agent.toolkits:
                    if hasattr(toolkit, 'tools'):
                        for tool in toolkit.tools:
                            if hasattr(tool, 'name'):
                                registered_tools.add(tool.name)
                            elif hasattr(tool, '__name__'):
                                registered_tools.add(tool.__name__)
                                
            # Check memory_and_knowledge_tools specifically on the wrapper agent
            if hasattr(self.agent, 'memory_and_knowledge_tools'):
                toolkit = self.agent.memory_and_knowledge_tools
                if hasattr(toolkit, 'tools'):
                    for tool in toolkit.tools:
                        if hasattr(tool, 'name'):
                            registered_tools.add(tool.name)
                        elif hasattr(tool, '__name__'):
                            registered_tools.add(tool.__name__)
                            
            # Also check the actual agent for memory_and_knowledge_tools
            if hasattr(actual_agent, 'memory_and_knowledge_tools'):
                toolkit = actual_agent.memory_and_knowledge_tools
                if hasattr(toolkit, 'tools'):
                    for tool in toolkit.tools:
                        if hasattr(tool, 'name'):
                            registered_tools.add(tool.name)
                        elif hasattr(tool, '__name__'):
                            registered_tools.add(tool.__name__)
                            
        except Exception as e:
            print(f"⚠️  Error getting registered tools: {e}")
            
        return registered_tools

    def check_tool_registration(self) -> bool:
        """
        Check that all expected tools are registered.
        
        Returns:
            True if all tools are registered, False otherwise
        """
        print("\n🔍 Checking tool registration...")
        
        registered_tools = self.get_registered_tools()
        
        print(f"📊 Found {len(registered_tools)} registered tools:")
        for tool in sorted(registered_tools):
            print(f"   • {tool}")
            
        # Check for missing tools
        missing_tools = self.expected_tools - registered_tools
        extra_tools = registered_tools - self.expected_tools
        
        if missing_tools:
            print(f"\n❌ Missing {len(missing_tools)} expected tools:")
            for tool in sorted(missing_tools):
                print(f"   • {tool}")
                
        if extra_tools:
            print(f"\n📝 Found {len(extra_tools)} additional tools:")
            for tool in sorted(extra_tools):
                print(f"   • {tool}")
                
        # Check if all expected tools are present
        all_registered = len(missing_tools) == 0
        
        if all_registered:
            print("✅ All expected tools are registered!")
        else:
            print(f"❌ {len(missing_tools)} tools are missing from registration")
            
        return all_registered

    async def test_tool_functionality(self) -> bool:
        """
        Test that some key tools can be called successfully.
        
        Returns:
            True if tests pass, False otherwise
        """
        print("\n🧪 Testing tool functionality...")
        
        test_results = []
        
        # Test 1: Memory stats (should work without setup)
        try:
            print("   Testing get_memory_stats...")
            response = await self.agent.run("get my memory stats")
            success = "memory" in response.lower() or "stats" in response.lower()
            test_results.append(("get_memory_stats", success, None))
            print(f"   {'✅' if success else '❌'} Memory stats: {response[:100]}...")
        except Exception as e:
            test_results.append(("get_memory_stats", False, str(e)))
            print(f"   ❌ Memory stats failed: {e}")

        # Test 2: List memories (should work even if empty)
        try:
            print("   Testing list_memories...")
            response = await self.agent.run("list my memories")
            success = "memories" in response.lower() or "no memories" in response.lower()
            test_results.append(("list_memories", success, None))
            print(f"   {'✅' if success else '❌'} List memories: {response[:100]}...")
        except Exception as e:
            test_results.append(("list_memories", False, str(e)))
            print(f"   ❌ List memories failed: {e}")

        # Test 3: Store a simple memory
        try:
            print("   Testing store_user_memory...")
            response = await self.agent.run("remember that I like testing tools")
            success = "✅" in response or "stored" in response.lower() or "remembered" in response.lower()
            test_results.append(("store_user_memory", success, None))
            print(f"   {'✅' if success else '❌'} Store memory: {response[:100]}...")
        except Exception as e:
            test_results.append(("store_user_memory", False, str(e)))
            print(f"   ❌ Store memory failed: {e}")

        # Test 4: Query the stored memory
        try:
            print("   Testing query_memory...")
            response = await self.agent.run("what do I like?")
            success = "testing" in response.lower() or "tools" in response.lower()
            test_results.append(("query_memory", success, None))
            print(f"   {'✅' if success else '❌'} Query memory: {response[:100]}...")
        except Exception as e:
            test_results.append(("query_memory", False, str(e)))
            print(f"   ❌ Query memory failed: {e}")

        # Test 5: Knowledge base query (should handle empty gracefully)
        try:
            print("   Testing query_knowledge_base...")
            response = await self.agent.run("search my knowledge base for information about Python")
            success = "knowledge" in response.lower() or "no relevant" in response.lower()
            test_results.append(("query_knowledge_base", success, None))
            print(f"   {'✅' if success else '❌'} Knowledge query: {response[:100]}...")
        except Exception as e:
            test_results.append(("query_knowledge_base", False, str(e)))
            print(f"   ❌ Knowledge query failed: {e}")

        # Summary
        successful_tests = sum(1 for _, success, _ in test_results if success)
        total_tests = len(test_results)
        
        print(f"\n📊 Tool functionality test results: {successful_tests}/{total_tests} passed")
        
        if successful_tests == total_tests:
            print("✅ All tool functionality tests passed!")
            return True
        else:
            print("❌ Some tool functionality tests failed")
            for test_name, success, error in test_results:
                if not success:
                    print(f"   • {test_name}: {error or 'Test failed'}")
            return False

    async def cleanup(self):
        """Clean up resources."""
        if self.agent and hasattr(self.agent, 'cleanup'):
            try:
                await self.agent.cleanup()
                print("🧹 Agent cleanup completed")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")

    async def run_tests(self) -> bool:
        """
        Run all tests.
        
        Returns:
            True if all tests pass, False otherwise
        """
        print("🔧 Starting Tool Registration Tests")
        print("=" * 50)
        
        try:
            # Initialize agent
            if not await self.initialize_agent():
                return False
                
            # Check tool registration
            registration_ok = self.check_tool_registration()
            
            # Test tool functionality
            functionality_ok = await self.test_tool_functionality()
            
            # Overall result
            all_tests_passed = registration_ok and functionality_ok
            
            print("\n" + "=" * 50)
            print("📋 TEST SUMMARY")
            print("=" * 50)
            print(f"🔧 Tool Registration: {'✅ PASS' if registration_ok else '❌ FAIL'}")
            print(f"🧪 Tool Functionality: {'✅ PASS' if functionality_ok else '❌ FAIL'}")
            print(f"🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
            print("=" * 50)
            
            return all_tests_passed
            
        except Exception as e:
            print(f"❌ Unexpected error during testing: {e}")
            return False
            
        finally:
            await self.cleanup()


async def main():
    """Main function to run the tool registration tests."""
    
    print("🚀 Tool Registration Test Suite")
    print("Testing @tool decorator registration in MemoryAndKnowledgeTools")
    print()
    
    tester = ToolRegistrationTester()
    
    try:
        success = await tester.run_tests()
        
        if success:
            print("\n🎉 All tests completed successfully!")
            print("The @tool decorators are working correctly.")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed!")
            print("Check the output above for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        await tester.cleanup()
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        await tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
