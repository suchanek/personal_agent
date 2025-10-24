#!/usr/bin/env python3
"""
Test script to verify the StreamlitMemoryHelper fixes for sync/async handling.

This script tests the fixed StreamlitMemoryHelper to ensure it properly handles
async memory operations without the coroutine errors.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper
from personal_agent.tools.paga_streamlit_agno import create_team_wrapper, initialize_team


async def test_single_agent_memory_helper():
    """Test StreamlitMemoryHelper with a single AgnoPersonalAgent."""
    print("🧪 Testing StreamlitMemoryHelper with single agent...")
    
    try:
        # Create agent
        agent = await AgnoPersonalAgent.create_with_init(
            model_name="qwen2.5:7b-instruct",
            enable_memory=True,
            debug=True,
            recreate=False
        )
        
        # Create helper
        memory_helper = StreamlitMemoryHelper(agent)
        
        # Test add_memory
        print("  ✅ Testing add_memory...")
        success, message, memory_id, topics = memory_helper.add_memory(
            "I love testing async code", 
            topics=["testing", "programming"]
        )
        print(f"     Add result: {success}, {message}")
        
        # Test get_all_memories
        print("  ✅ Testing get_all_memories...")
        memories = memory_helper.get_all_memories()
        print(f"     Found {len(memories)} memories")
        
        # Test search_memories
        print("  ✅ Testing search_memories...")
        search_results = memory_helper.search_memories("testing", limit=5)
        print(f"     Search found {len(search_results)} results")
        
        # Test get_memory_stats
        print("  ✅ Testing get_memory_stats...")
        stats = memory_helper.get_memory_stats()
        print(f"     Stats: {stats}")
        
        print("✅ Single agent tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Single agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_team_wrapper_memory_helper():
    """Test StreamlitMemoryHelper with a team wrapper."""
    print("🧪 Testing StreamlitMemoryHelper with team wrapper...")
    
    try:
        # Create team
        team = initialize_team(
            model_name="qwen2.5:7b-instruct",
            ollama_url="http://localhost:11434",
            recreate=False
        )
        
        if not team:
            print("❌ Failed to create team")
            return False
        
        # Create team wrapper
        team_wrapper = create_team_wrapper(team)
        
        # Create helper
        memory_helper = StreamlitMemoryHelper(team_wrapper)
        
        # Test add_memory
        print("  ✅ Testing add_memory with team...")
        success, message, memory_id, topics = memory_helper.add_memory(
            "Teams are great for complex tasks", 
            topics=["teamwork", "ai"]
        )
        print(f"     Add result: {success}, {message}")
        
        # Test get_all_memories
        print("  ✅ Testing get_all_memories with team...")
        memories = memory_helper.get_all_memories()
        print(f"     Found {len(memories)} memories")
        
        # Test search_memories
        print("  ✅ Testing search_memories with team...")
        search_results = memory_helper.search_memories("teams", limit=5)
        print(f"     Search found {len(search_results)} results")
        
        print("✅ Team wrapper tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Team wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting StreamlitMemoryHelper fix verification tests...")
    print("=" * 60)
    
    # Test single agent
    single_success = await test_single_agent_memory_helper()
    print()
    
    # Test team wrapper
    team_success = test_team_wrapper_memory_helper()
    print()
    
    # Summary
    print("=" * 60)
    if single_success and team_success:
        print("🎉 All tests passed! StreamlitMemoryHelper fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
