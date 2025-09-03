#!/usr/bin/env python3
"""
Test script to verify that memory stats and sync status functions work correctly
in the fixed StreamlitMemoryHelper.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, get_current_user_id
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper


async def test_memory_stats_and_sync():
    """Test memory stats and sync status functionality."""
    print("🧪 Testing Memory Stats and Sync Status Fix")
    print("=" * 50)
    
    # Initialize agent
    print("1. Initializing agent...")
    agent = await AgnoPersonalAgent.create_with_init(
        model_provider="ollama",
        model_name="qwen2.5:14b",
        user_id=get_current_user_id(),
        debug=True,
        enable_memory=True,
        storage_dir=AGNO_STORAGE_DIR,
        recreate=False,
    )
    print(f"✅ Agent initialized: {type(agent).__name__}")
    
    # Create memory helper
    print("\n2. Creating StreamlitMemoryHelper...")
    memory_helper = StreamlitMemoryHelper(agent)
    print("✅ Memory helper created")
    
    # Test memory stats
    print("\n3. Testing get_memory_stats()...")
    stats = memory_helper.get_memory_stats()
    print(f"Stats result type: {type(stats)}")
    print(f"Stats result: {stats}")
    
    if isinstance(stats, dict):
        if "error" in stats:
            print(f"❌ Error in stats: {stats['error']}")
        else:
            print("✅ Memory stats returned as dictionary:")
            print(f"  - Total memories: {stats.get('total_memories', 'N/A')}")
            print(f"  - Recent (24h): {stats.get('recent_memories_24h', 'N/A')}")
            print(f"  - Average length: {stats.get('average_memory_length', 'N/A')}")
            print(f"  - Topic distribution: {len(stats.get('topic_distribution', {}))}")
    else:
        print(f"❌ Stats returned wrong type: {type(stats)}")
    
    # Test memory sync status
    print("\n4. Testing get_memory_sync_status()...")
    sync_status = memory_helper.get_memory_sync_status()
    print(f"Sync status result type: {type(sync_status)}")
    print(f"Sync status result: {sync_status}")
    
    if isinstance(sync_status, dict):
        if "error" in sync_status:
            print(f"❌ Error in sync status: {sync_status['error']}")
        else:
            print("✅ Memory sync status returned as dictionary:")
            print(f"  - Local memory count: {sync_status.get('local_memory_count', 'N/A')}")
            print(f"  - Graph entity count: {sync_status.get('graph_entity_count', 'N/A')}")
            print(f"  - Sync ratio: {sync_status.get('sync_ratio', 'N/A')}")
            print(f"  - Status: {sync_status.get('status', 'N/A')}")
    else:
        print(f"❌ Sync status returned wrong type: {type(sync_status)}")
    
    # Test adding a memory to ensure we have some data
    print("\n5. Testing memory addition...")
    success, message, memory_id, topics = memory_helper.add_memory(
        "This is a test memory for stats verification", 
        ["test"]
    )
    print(f"Add memory result: success={success}, message={message}")
    
    if success:
        # Test stats again with data
        print("\n6. Re-testing stats with data...")
        stats = memory_helper.get_memory_stats()
        if isinstance(stats, dict) and "error" not in stats:
            print("✅ Memory stats with data:")
            print(f"  - Total memories: {stats.get('total_memories', 'N/A')}")
            print(f"  - Recent (24h): {stats.get('recent_memories_24h', 'N/A')}")
            print(f"  - Average length: {stats.get('average_memory_length', 'N/A')}")
            print(f"  - Topic distribution: {stats.get('topic_distribution', {})}")
        else:
            print(f"❌ Stats still failing: {stats}")
    
    print("\n" + "=" * 50)
    print("🧪 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_memory_stats_and_sync())
