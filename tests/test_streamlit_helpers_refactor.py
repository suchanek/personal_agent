#!/usr/bin/env python3
"""
Test script to verify the refactored StreamlitMemoryHelper works with new agent memory functions.

This script tests that the simplified StreamlitMemoryHelper correctly uses the new
agent memory function interfaces we added to AgnoPersonalAgent.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper


async def test_streamlit_helper_refactor():
    """Test the refactored StreamlitMemoryHelper."""
    print("🧪 Testing refactored StreamlitMemoryHelper...")
    
    # Create agent with memory enabled
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="llama3.2:3b",
        enable_memory=True,
        debug=True,
        user_id="test_streamlit_user"
    )
    
    # Create the helper
    memory_helper = StreamlitMemoryHelper(agent)
    
    try:
        # Test 1: Check agent availability
        print("\n1. Testing agent availability check...")
        available, message = memory_helper._ensure_agent_available()
        print(f"   Agent available: {available}")
        if not available:
            print(f"   Message: {message}")
            return
        
        # Test 2: Add a memory using the helper
        print("\n2. Testing add_memory() via helper...")
        success, message, memory_id, topics = memory_helper.add_memory(
            "I love testing refactored Streamlit helpers", 
            topics=["testing", "streamlit", "refactoring"]
        )
        print(f"   Success: {success}")
        print(f"   Message: {message}")
        print(f"   Memory ID: {memory_id}")
        print(f"   Topics: {topics}")
        
        if not success:
            print("   ❌ Failed to add memory, skipping further tests")
            return
        
        # Test 3: Get all memories using the helper
        print("\n3. Testing get_all_memories() via helper...")
        memories = memory_helper.get_all_memories()
        print(f"   Found {len(memories)} memories")
        if memories:
            print(f"   Latest memory: {memories[-1].memory[:50]}...")
        
        # Test 4: Delete the memory using the helper
        if memory_id:
            print(f"\n4. Testing delete_memory() via helper...")
            success, message = memory_helper.delete_memory(memory_id)
            print(f"   Success: {success}")
            print(f"   Message: {message}")
        
        # Test 5: Get memory stats using the helper
        print("\n5. Testing get_memory_stats() via helper...")
        stats = memory_helper.get_memory_stats()
        print(f"   Stats: {stats}")
        
        # Test 6: Clear all memories using the helper
        print("\n6. Testing clear_memories() via helper...")
        success, message = memory_helper.clear_memories()
        print(f"   Success: {success}")
        print(f"   Message: {message}")
        
        print("\n✅ All StreamlitMemoryHelper tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await agent.cleanup()


async def test_direct_vs_helper_comparison():
    """Compare direct agent calls vs helper calls to ensure consistency."""
    print("\n🔍 Testing direct agent vs helper consistency...")
    
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="llama3.2:3b",
        enable_memory=True,
        debug=True,
        user_id="test_comparison_user"
    )
    
    memory_helper = StreamlitMemoryHelper(agent)
    
    try:
        # Test direct agent call
        print("\n1. Direct agent call:")
        direct_result = await agent.store_user_memory(
            "Direct agent memory test", 
            topics=["direct", "test"]
        )
        print(f"   Direct result: {direct_result.status.name} - {direct_result.message}")
        
        # Test helper call
        print("\n2. Helper call:")
        helper_success, helper_message, helper_id, helper_topics = memory_helper.add_memory(
            "Helper memory test", 
            topics=["helper", "test"]
        )
        print(f"   Helper result: {helper_success} - {helper_message}")
        
        # Compare results
        print("\n3. Comparison:")
        print(f"   Both successful: {direct_result.is_success and helper_success}")
        print(f"   Direct memory ID: {direct_result.memory_id}")
        print(f"   Helper memory ID: {helper_id}")
        
        print("\n✅ Direct vs helper comparison completed!")
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    print("🚀 Starting StreamlitMemoryHelper refactor tests...")
    
    # Run the main test
    asyncio.run(test_streamlit_helper_refactor())
    
    # Run the comparison test
    asyncio.run(test_direct_vs_helper_comparison())
    
    print("\n🎉 All tests complete!")
