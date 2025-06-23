#!/usr/bin/env python3
"""
Test script to verify the direct memory access refactoring in agno_agent.py

This script tests that the refactored memory tools work correctly with the new
direct access pattern: self.agno_memory.memory_manager.{method}() and self.agno_memory.db
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.config import LLM_MODEL, OLLAMA_URL
from personal_agent.utils import setup_logging

# Configure logging
logger = setup_logging(__name__)


async def test_direct_memory_access():
    """Test the refactored direct memory access functionality."""
    print("🧪 Testing Direct Memory Access Refactoring")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Create agent with memory enabled
        print("1. Creating AgnoPersonalAgent with memory enabled...")
        print(f"   Using model: {LLM_MODEL}")
        print(f"   Using Ollama URL: {OLLAMA_URL}")
        
        create_start = time.time()
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for simpler testing
            debug=True,
            ollama_base_url=OLLAMA_URL,
            user_id="test_user_direct_access"
        )
        create_time = time.time() - create_start
        print(f"   ⏱️  Agent creation took: {create_time:.3f}s")
        
        # Initialize the agent
        print("2. Initializing agent...")
        init_start = time.time()
        success = await agent.initialize()
        init_time = time.time() - init_start
        print(f"   ⏱️  Agent initialization took: {init_time:.3f}s")
        
        if not success:
            print("❌ Failed to initialize agent")
            return False
            
        print("✅ Agent initialized successfully")
        
        # Verify memory components are available
        print("3. Verifying memory components...")
        if not agent.agno_memory:
            print("❌ agno_memory is None")
            return False
            
        if not hasattr(agent.agno_memory, 'memory_manager'):
            print("❌ agno_memory.memory_manager not found")
            return False
            
        if not hasattr(agent.agno_memory, 'db'):
            print("❌ agno_memory.db not found")
            return False
            
        print("✅ Memory components verified")
        print(f"   - Memory manager type: {type(agent.agno_memory.memory_manager)}")
        print(f"   - Database type: {type(agent.agno_memory.db)}")
        
        # Test direct search memories method
        print("4. Testing direct search memories...")
        results = agent._direct_search_memories("test query", limit=5)
        print(f"✅ Direct search completed, found {len(results)} results")
        
        # Test memory tools by running some queries
        print("5. Testing memory tools through agent...")
        
        # Test storing a memory
        print("   Testing store_user_memory...")
        response = await agent.run("Remember that I love testing direct memory access patterns!")
        print(f"   Store response: {response[:100]}...")
        
        # Test querying memories
        print("   Testing query_memory...")
        response = await agent.run("What do you remember about me?")
        print(f"   Query response: {response[:100]}...")
        
        # Test getting recent memories
        print("   Testing get_recent_memories...")
        response = await agent.run("Show me my recent memories")
        print(f"   Recent memories response: {response[:100]}...")
        
        # Test memory stats
        print("   Testing get_memory_stats...")
        response = await agent.run("Show me my memory statistics")
        print(f"   Stats response: {response[:100]}...")
        
        print("6. Testing direct memory manager calls...")
        
        # Test direct add_memory call
        add_start = time.time()
        success, message, memory_id = agent.agno_memory.memory_manager.add_memory(
            memory_text="Direct test memory - I am testing the refactored code",
            db=agent.agno_memory.db,
            user_id=agent.user_id,
            topics=["testing", "refactoring"]
        )
        add_time = time.time() - add_start
        print(f"   Direct add_memory: success={success}, message='{message}', id={memory_id}")
        print(f"   ⏱️  add_memory took: {add_time:.3f}s")
        
        # Test direct search_memories call
        search_start = time.time()
        search_results = agent.agno_memory.memory_manager.search_memories(
            query="testing",
            db=agent.agno_memory.db,
            user_id=agent.user_id,
            limit=5,
            similarity_threshold=0.3
        )
        search_time = time.time() - search_start
        print(f"   Direct search_memories: found {len(search_results)} results")
        print(f"   ⏱️  search_memories took: {search_time:.3f}s")
        
        # Test direct get_memory_stats call
        stats_start = time.time()
        stats = agent.agno_memory.memory_manager.get_memory_stats(
            db=agent.agno_memory.db,
            user_id=agent.user_id
        )
        stats_time = time.time() - stats_start
        print(f"   Direct get_memory_stats: {stats}")
        print(f"   ⏱️  get_memory_stats took: {stats_time:.3f}s")
        
        total_time = time.time() - start_time
        print(f"\n⏱️  Total test time: {total_time:.3f}s")
        print("7. All tests completed successfully! ✅")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if 'agent' in locals():
            await agent.cleanup()


async def test_memory_tool_functions():
    """Test individual memory tool functions directly."""
    print("\n🔧 Testing Individual Memory Tool Functions")
    print("=" * 60)
    
    try:
        # Create agent
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            enable_memory=True,
            enable_mcp=False,
            debug=True,
            ollama_base_url=OLLAMA_URL,
            user_id="test_user_tools"
        )
        
        await agent.initialize()
        
        # Get memory tools
        memory_tools = await agent._get_memory_tools()
        print(f"Created {len(memory_tools)} memory tools")
        
        # Find specific tools
        tool_map = {tool.__name__: tool for tool in memory_tools}
        
        # Test store_user_memory
        if 'store_user_memory' in tool_map:
            print("Testing store_user_memory...")
            result = await tool_map['store_user_memory'](
                "I am testing the refactored memory tools",
                ["testing", "refactoring"]
            )
            print(f"Store result: {result}")
        
        # Test query_memory
        if 'query_memory' in tool_map:
            print("Testing query_memory...")
            result = await tool_map['query_memory']("testing")
            print(f"Query result: {result[:200]}...")
        
        # Test get_memory_stats
        if 'get_memory_stats' in tool_map:
            print("Testing get_memory_stats...")
            result = await tool_map['get_memory_stats']()
            print(f"Stats result: {result[:200]}...")
        
        print("✅ Memory tool functions test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Memory tool functions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'agent' in locals():
            await agent.cleanup()


async def main():
    """Run all tests."""
    print("🚀 Starting Direct Memory Access Refactoring Tests")
    print("=" * 80)
    
    # Test 1: Basic direct memory access
    test1_success = await test_direct_memory_access()
    
    # Test 2: Memory tool functions
    test2_success = await test_memory_tool_functions()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 40)
    print(f"Direct Memory Access Test: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Memory Tool Functions Test: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    overall_success = test1_success and test2_success
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 The direct memory access refactoring is working correctly!")
        print("The code successfully uses self.agno_memory.memory_manager and self.agno_memory.db")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
