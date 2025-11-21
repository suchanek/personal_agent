#!/usr/bin/env python3
"""
Test script to verify memory function access in AgnoPersonalAgent
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.config import LLM_MODEL, OLLAMA_URL, AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR

@pytest.mark.asyncio
async def test_memory_functions():
    """Test that all memory functions are accessible on AgnoPersonalAgent."""
    
    print("🧪 Testing AgnoPersonalAgent memory function access...")
    
    # Create agent
    agent = await AgnoPersonalAgent.create_with_init(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        enable_memory=True,
        storage_dir=AGNO_STORAGE_DIR,
        knowledge_dir=AGNO_KNOWLEDGE_DIR,
        debug=True
    )
    
    print(f"✅ Agent created: {type(agent).__name__}")
    print(f"✅ Agent initialized: {getattr(agent, '_initialized', False)}")
    
    # Test all memory functions
    memory_functions = [
        'store_user_memory', 'list_memories', 'query_memory', 
        'update_memory', 'delete_memory', 'get_recent_memories',
        'get_all_memories', 'get_memory_stats', 'get_memories_by_topic',
        'delete_memories_by_topic', 'get_memory_graph_labels', 'clear_all_memories'
    ]
    
    print("\n🔍 Checking memory function availability:")
    missing_functions = []
    
    for func_name in memory_functions:
        if hasattr(agent, func_name):
            func = getattr(agent, func_name)
            if callable(func):
                print(f"  ✅ {func_name}: Available and callable")
            else:
                print(f"  ❌ {func_name}: Available but not callable")
                missing_functions.append(func_name)
        else:
            print(f"  ❌ {func_name}: Missing")
            missing_functions.append(func_name)
    
    if missing_functions:
        print(f"\n❌ Missing functions: {missing_functions}")
        return False
    else:
        print(f"\n✅ All {len(memory_functions)} memory functions are available!")
        
        # Test calling list_memories
        try:
            print("\n🧪 Testing list_memories() call...")
            result = await agent.list_memories()
            print(f"✅ list_memories() returned: {result[:100]}..." if len(result) > 100 else f"✅ list_memories() returned: {result}")
            return True
        except Exception as e:
            print(f"❌ Error calling list_memories(): {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_memory_functions())
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)
