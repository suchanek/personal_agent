#!/usr/bin/env python3
"""
Test script to verify that the fixed TeamWrapper now handles async execution properly
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import LLM_MODEL, OLLAMA_URL, AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR
from personal_agent.team.reasoning_team import create_team as create_personal_agent_team

# Import the actual create_team_wrapper function from the Streamlit file
sys.path.insert(0, str(Path(__file__).parent))
from src.personal_agent.tools.paga_streamlit_agno import create_team_wrapper

async def test_fixed_teamwrapper_memory_functions():
    """Test that the fixed TeamWrapper handles async execution properly."""
    
    print("🧪 Testing FIXED TeamWrapper memory function access...")
    
    # Create team
    team = await create_personal_agent_team(use_remote=False, model_name=LLM_MODEL)
    
    print(f"✅ Team created: {type(team).__name__}")
    print(f"✅ Team members: {len(getattr(team, 'members', []))}")
    
    # Create the actual fixed TeamWrapper using the real function
    wrapper = create_team_wrapper(team)
    
    print(f"✅ TeamWrapper created: {type(wrapper).__name__}")
    
    # Test all memory functions
    memory_functions = [
        'list_memories', 'query_memory', 'get_all_memories', 'get_memory_stats'
    ]
    
    print("\n🔍 Checking memory function availability on FIXED TeamWrapper:")
    missing_functions = []
    successful_calls = 0
    
    for func_name in memory_functions:
        if hasattr(wrapper, func_name):
            func = getattr(wrapper, func_name)
            if callable(func):
                print(f"  ✅ {func_name}: Available and callable")
                
                # Test calling the function with the new _run_async_safely method
                try:
                    if func_name == 'query_memory':
                        result = func("test query", 5)
                    elif func_name in ['list_memories', 'get_all_memories', 'get_memory_stats']:
                        result = func()
                    
                    print(f"    ✅ {func_name}() call successful!")
                    successful_calls += 1
                except Exception as e:
                    print(f"    ⚠️ {func_name}() call failed: {e}")
            else:
                print(f"  ❌ {func_name}: Available but not callable")
                missing_functions.append(func_name)
        else:
            print(f"  ❌ {func_name}: Missing")
            missing_functions.append(func_name)
    
    if missing_functions:
        print(f"\n❌ Missing functions: {missing_functions}")
        return False
    elif successful_calls == len(memory_functions):
        print(f"\n✅ All {len(memory_functions)} memory functions are available and working!")
        return True
    else:
        print(f"\n⚠️ Functions available but some calls failed. Successful: {successful_calls}/{len(memory_functions)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_teamwrapper_memory_functions())
    if success:
        print("\n🎉 FIXED TeamWrapper memory function test passed!")
        sys.exit(0)
    else:
        print("\n💥 FIXED TeamWrapper memory function test failed!")
        sys.exit(1)
