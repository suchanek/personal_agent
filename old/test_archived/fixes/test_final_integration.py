#!/usr/bin/env python3
"""
Test script to verify the final integration of memory stats and sync status functionality.

This script tests:
1. AgentMemoryManager.get_graph_entity_count() method
2. AgnoPersonalAgent delegation to AgentMemoryManager
3. StreamlitMemoryHelper functionality with both single agent and team modes
4. Memory stats and sync status retrieval
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper
from personal_agent.team.reasoning_team import create_team


async def test_agent_memory_manager_direct():
    """Test AgentMemoryManager.get_graph_entity_count() directly."""
    print("=" * 60)
    print("TEST 1: AgentMemoryManager.get_graph_entity_count() Direct Test")
    print("=" * 60)
    
    try:
        # Create and initialize agent
        agent = AgnoPersonalAgent(debug=True, enable_memory=True)
        await agent.initialize()
        
        # Test the memory manager's get_graph_entity_count method directly
        if agent.memory_manager:
            entity_count = await agent.memory_manager.get_graph_entity_count()
            print(f"✅ AgentMemoryManager.get_graph_entity_count() returned: {entity_count}")
            print(f"   Type: {type(entity_count)}")
            
            if isinstance(entity_count, int) and entity_count >= 0:
                print("✅ Method returns valid integer count")
            else:
                print(f"❌ Method returned invalid type or negative value: {entity_count}")
                return False
        else:
            print("❌ Memory manager not initialized")
            return False
            
        await agent.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Error testing AgentMemoryManager directly: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agno_agent_delegation():
    """Test AgnoPersonalAgent delegation to AgentMemoryManager."""
    print("\n" + "=" * 60)
    print("TEST 2: AgnoPersonalAgent Delegation Test")
    print("=" * 60)
    
    try:
        # Create and initialize agent
        agent = AgnoPersonalAgent(debug=True, enable_memory=True)
        await agent.initialize()
        
        # Test the agent's get_graph_entity_count method (should delegate)
        entity_count = await agent.get_graph_entity_count()
        print(f"✅ AgnoPersonalAgent.get_graph_entity_count() returned: {entity_count}")
        print(f"   Type: {type(entity_count)}")
        
        if isinstance(entity_count, int) and entity_count >= 0:
            print("✅ Delegation works correctly - returns valid integer count")
        else:
            print(f"❌ Delegation failed - invalid type or negative value: {entity_count}")
            return False
            
        await agent.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Error testing AgnoPersonalAgent delegation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streamlit_helper_single_agent():
    """Test StreamlitMemoryHelper with single AgnoPersonalAgent."""
    print("\n" + "=" * 60)
    print("TEST 3: StreamlitMemoryHelper with Single Agent")
    print("=" * 60)
    
    try:
        # Create and initialize agent
        agent = AgnoPersonalAgent(debug=True, enable_memory=True)
        await agent.initialize()
        
        # Create StreamlitMemoryHelper
        helper = StreamlitMemoryHelper(agent)
        
        # Test memory stats (synchronous method)
        print("Testing get_memory_stats()...")
        stats = helper.get_memory_stats()
        print(f"✅ Memory stats: {stats}")
        
        if isinstance(stats, dict) and "total_memories" in stats:
            print("✅ Memory stats returns proper dictionary format")
        else:
            print(f"❌ Memory stats returned invalid format: {type(stats)}")
            return False
        
        # Test memory sync status (synchronous method)
        print("\nTesting get_memory_sync_status()...")
        sync_status = helper.get_memory_sync_status()
        print(f"✅ Memory sync status: {sync_status}")
        
        if isinstance(sync_status, dict) and "local_memory_count" in sync_status and "graph_entity_count" in sync_status:
            print("✅ Memory sync status returns proper dictionary format")
            print(f"   Local count: {sync_status.get('local_memory_count', 'N/A')}")
            print(f"   Graph count: {sync_status.get('graph_entity_count', 'N/A')}")
            print(f"   Sync status: {sync_status.get('status', 'N/A')}")
        else:
            print(f"❌ Memory sync status returned invalid format: {type(sync_status)}")
            return False
            
        await agent.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Error testing StreamlitMemoryHelper with single agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streamlit_helper_team_mode():
    """Test StreamlitMemoryHelper with Team (team mode)."""
    print("\n" + "=" * 60)
    print("TEST 4: StreamlitMemoryHelper with Team Mode")
    print("=" * 60)
    
    try:
        # Create and initialize team
        team = await create_team(use_remote=False)
        
        # Create StreamlitMemoryHelper with team
        helper = StreamlitMemoryHelper(team)
        
        # Test memory stats (synchronous method)
        print("Testing get_memory_stats() with team...")
        stats = helper.get_memory_stats()
        print(f"✅ Team memory stats: {stats}")
        
        if isinstance(stats, dict) and "total_memories" in stats:
            print("✅ Team memory stats returns proper dictionary format")
        else:
            print(f"❌ Team memory stats returned invalid format: {type(stats)}")
            return False
        
        # Test memory sync status (synchronous method)
        print("\nTesting get_memory_sync_status() with team...")
        sync_status = helper.get_memory_sync_status()
        print(f"✅ Team memory sync status: {sync_status}")
        
        if isinstance(sync_status, dict) and "local_memory_count" in sync_status and "graph_entity_count" in sync_status:
            print("✅ Team memory sync status returns proper dictionary format")
            print(f"   Local count: {sync_status.get('local_memory_count', 'N/A')}")
            print(f"   Graph count: {sync_status.get('graph_entity_count', 'N/A')}")
            print(f"   Sync status: {sync_status.get('status', 'N/A')}")
        else:
            print(f"❌ Team memory sync status returned invalid format: {type(sync_status)}")
            return False
            
        # Clean up team resources
        if hasattr(team, 'members'):
            for member in team.members:
                if hasattr(member, 'cleanup'):
                    await member.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Error testing StreamlitMemoryHelper with team: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests to verify the final integration."""
    print("🧪 Testing Final Integration of Memory Stats and Sync Status")
    print("=" * 80)
    
    # Run all tests
    tests = [
        ("AgentMemoryManager Direct", test_agent_memory_manager_direct),
        ("AgnoPersonalAgent Delegation", test_agno_agent_delegation),
        ("StreamlitHelper Single Agent", test_streamlit_helper_single_agent),
        ("StreamlitHelper Team Mode", test_streamlit_helper_team_mode),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Final integration is complete and working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
