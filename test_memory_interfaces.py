#!/usr/bin/env python3
"""
Test script to verify the new memory function interfaces in AgnoPersonalAgent.

This script tests the newly added memory functions that follow the same pattern
as store_user_memory() by delegating to the memory_manager.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_memory_interfaces():
    """Test the new memory function interfaces."""
    print("🧪 Testing AgnoPersonalAgent memory function interfaces...")
    
    # Create agent with memory enabled
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="llama3.2:3b",
        enable_memory=True,
        debug=True,
        user_id="test_user"
    )
    
    try:
        # Test 1: Store a test memory
        print("\n1. Testing store_user_memory()...")
        result = await agent.store_user_memory(
            "I love testing new memory interfaces", 
            topics=["testing", "development"]
        )
        print(f"   Result: {result.status.name} - {result.message}")
        
        # Test 2: List all memories
        print("\n2. Testing list_memories()...")
        memories_list = await agent.list_memories()
        print(f"   Found memories: {len(memories_list.split('📝')[1].split('\\n')) if '📝' in memories_list else 0}")
        
        # Test 3: Query memories
        print("\n3. Testing query_memory()...")
        query_result = await agent.query_memory("testing", limit=5)
        print(f"   Query result length: {len(query_result)} characters")
        
        # Test 4: Get recent memories
        print("\n4. Testing get_recent_memories()...")
        recent_memories = await agent.get_recent_memories(limit=3)
        print(f"   Recent memories length: {len(recent_memories)} characters")
        
        # Test 5: Get all memories
        print("\n5. Testing get_all_memories()...")
        all_memories = await agent.get_all_memories()
        print(f"   All memories length: {len(all_memories)} characters")
        
        # Test 6: Get memory stats
        print("\n6. Testing get_memory_stats()...")
        stats = await agent.get_memory_stats()
        print(f"   Stats length: {len(stats)} characters")
        
        # Test 7: Get memories by topic
        print("\n7. Testing get_memories_by_topic()...")
        topic_memories = await agent.get_memories_by_topic(["testing"])
        print(f"   Topic memories length: {len(topic_memories)} characters")
        
        # Test 8: Get memory graph labels
        print("\n8. Testing get_memory_graph_labels()...")
        labels = await agent.get_memory_graph_labels()
        print(f"   Labels length: {len(labels)} characters")
        
        print("\n✅ All memory interface tests completed successfully!")
        
        # Show available methods
        print("\n📋 Available memory methods in AgnoPersonalAgent:")
        memory_methods = [method for method in dir(agent) if 'memory' in method.lower() and not method.startswith('_')]
        for method in sorted(memory_methods):
            print(f"   - {method}()")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await agent.cleanup()


async def test_method_signatures():
    """Test that all new methods have the correct signatures."""
    print("\n🔍 Testing method signatures...")
    
    agent = AgnoPersonalAgent(enable_memory=True, user_id="test_user")
    
    # Test that methods exist and are callable
    methods_to_test = [
        'list_memories',
        'query_memory', 
        'update_memory',
        'delete_memory',
        'get_recent_memories',
        'get_all_memories',
        'get_memory_stats',
        'get_memories_by_topic',
        'delete_memories_by_topic',
        'get_memory_graph_labels'
    ]
    
    for method_name in methods_to_test:
        if hasattr(agent, method_name):
            method = getattr(agent, method_name)
            if callable(method):
                print(f"   ✅ {method_name}() - exists and callable")
            else:
                print(f"   ❌ {method_name}() - exists but not callable")
        else:
            print(f"   ❌ {method_name}() - does not exist")
    
    await agent.cleanup()


if __name__ == "__main__":
    print("🚀 Starting memory interface tests...")
    
    # Run signature tests first (faster)
    asyncio.run(test_method_signatures())
    
    # Run full functionality tests
    asyncio.run(test_memory_interfaces())
    
    print("\n🎉 Testing complete!")
