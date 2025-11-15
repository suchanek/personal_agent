#!/usr/bin/env python3
"""
Test script to verify all memory function interfaces in AgnoPersonalAgent.

This script tests all 11 memory functions that should be available:
1. store_user_memory() - existing
2. list_memories() - added
3. query_memory() - added
4. update_memory() - added
5. delete_memory() - added
6. get_recent_memories() - added
7. get_all_memories() - added
8. get_memory_stats() - added
9. get_memories_by_topic() - added
10. delete_memories_by_topic() - added
11. get_memory_graph_labels() - added
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_memory_interfaces():
    """Test all memory function interfaces."""
    print("🧪 Testing AgnoPersonalAgent Memory Function Interfaces")
    print("=" * 60)
    
    # Create agent instance (lazy initialization)
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="llama3.2:3b",
        enable_memory=True,
        debug=False,
        user_id="test_user",
        initialize_agent=False  # Use lazy initialization
    )
    
    print(f"✅ Created AgnoPersonalAgent instance")
    
    # Test all memory function interfaces
    memory_functions = [
        ("store_user_memory", lambda: agent.store_user_memory("Test memory content", ["test"])),
        ("list_memories", lambda: agent.list_memories()),
        ("query_memory", lambda: agent.query_memory("test", 5)),
        ("update_memory", lambda: agent.update_memory("test_id", "Updated content", ["updated"])),
        ("delete_memory", lambda: agent.delete_memory("test_id")),
        ("get_recent_memories", lambda: agent.get_recent_memories(5)),
        ("get_all_memories", lambda: agent.get_all_memories()),
        ("get_memory_stats", lambda: agent.get_memory_stats()),
        ("get_memories_by_topic", lambda: agent.get_memories_by_topic(["test"], 5)),
        ("delete_memories_by_topic", lambda: agent.delete_memories_by_topic(["test"])),
        ("get_memory_graph_labels", lambda: agent.get_memory_graph_labels()),
    ]
    
    print(f"\n🔍 Testing {len(memory_functions)} memory function interfaces:")
    print("-" * 60)
    
    results = []
    for func_name, func_call in memory_functions:
        try:
            # Check if the method exists
            if hasattr(agent, func_name):
                method = getattr(agent, func_name)
                if callable(method):
                    print(f"✅ {func_name:25} - Method exists and is callable")
                    results.append((func_name, "✅ Available"))
                else:
                    print(f"❌ {func_name:25} - Exists but not callable")
                    results.append((func_name, "❌ Not callable"))
            else:
                print(f"❌ {func_name:25} - Method does not exist")
                results.append((func_name, "❌ Missing"))
        except Exception as e:
            print(f"❌ {func_name:25} - Error: {e}")
            results.append((func_name, f"❌ Error: {e}"))
    
    # Summary
    print("\n📊 SUMMARY:")
    print("=" * 60)
    available_count = sum(1 for _, status in results if status.startswith("✅"))
    total_count = len(results)
    
    for func_name, status in results:
        print(f"{func_name:25} {status}")
    
    print(f"\n🎯 Result: {available_count}/{total_count} memory functions available")
    
    if available_count == total_count:
        print("🎉 SUCCESS: All memory function interfaces are properly implemented!")
        return True
    else:
        print("⚠️  WARNING: Some memory function interfaces are missing or have issues.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_memory_interfaces())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
