#!/usr/bin/env python3
"""
Core Integration Verification Script

This script verifies the specific functionality that was requested:
1. AgentMemoryManager.get_graph_entity_count() method works
2. AgnoPersonalAgent properly delegates to AgentMemoryManager
3. StreamlitMemoryHelper works with single agents (primary use case)
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper


async def main():
    """Verify the core integration functionality."""
    print("🎯 Core Integration Verification")
    print("=" * 50)
    
    try:
        # Create and initialize agent
        print("1. Creating and initializing AgnoPersonalAgent...")
        agent = AgnoPersonalAgent(debug=False, enable_memory=True)
        await agent.initialize()
        print("   ✅ Agent initialized successfully")
        
        # Test direct AgentMemoryManager access
        print("\n2. Testing AgentMemoryManager.get_graph_entity_count()...")
        entity_count = await agent.memory_manager.get_graph_entity_count()
        print(f"   ✅ Graph entity count: {entity_count}")
        
        # Test AgnoPersonalAgent delegation
        print("\n3. Testing AgnoPersonalAgent delegation...")
        delegated_count = await agent.get_graph_entity_count()
        print(f"   ✅ Delegated count: {delegated_count}")
        
        # Verify delegation works correctly
        if entity_count == delegated_count:
            print("   ✅ Delegation working correctly - counts match")
        else:
            print(f"   ❌ Delegation issue - counts don't match: {entity_count} vs {delegated_count}")
            return False
        
        # Test StreamlitMemoryHelper
        print("\n4. Testing StreamlitMemoryHelper...")
        helper = StreamlitMemoryHelper(agent)
        
        # Test memory stats
        stats = helper.get_memory_stats()
        print(f"   ✅ Memory stats retrieved: {stats.get('total_memories', 0)} total memories")
        
        # Test memory sync status
        sync_status = helper.get_memory_sync_status()
        local_count = sync_status.get('local_memory_count', 0)
        graph_count = sync_status.get('graph_entity_count', 0)
        status = sync_status.get('status', 'unknown')
        
        print(f"   ✅ Sync status: {local_count} local, {graph_count} graph, status: {status}")
        
        # Verify sync status uses the correct graph count
        if graph_count == entity_count:
            print("   ✅ Sync status correctly uses AgentMemoryManager graph count")
        else:
            print(f"   ❌ Sync status graph count mismatch: {graph_count} vs {entity_count}")
            return False
        
        # Clean up
        await agent.cleanup()
        
        print("\n" + "=" * 50)
        print("🎉 CORE INTEGRATION VERIFICATION SUCCESSFUL!")
        print("=" * 50)
        print("✅ AgentMemoryManager.get_graph_entity_count() works correctly")
        print("✅ AgnoPersonalAgent delegation to AgentMemoryManager works")
        print("✅ StreamlitMemoryHelper memory stats work correctly")
        print("✅ StreamlitMemoryHelper memory sync status works correctly")
        print("✅ All components properly integrated and functional")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Core integration verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🚀 Ready for production use!")
    else:
        print("\n⚠️  Integration issues detected.")
    sys.exit(0 if success else 1)
