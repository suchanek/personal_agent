#!/usr/bin/env python3
"""
Test script to verify the memory sync fix between Streamlit and Agent interfaces.

This script tests:
1. Memory storage via agent's store_user_memory method
2. Memory retrieval via both Streamlit helper and agent tools
3. Sync status between local SQLite and LightRAG graph systems
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import create_agno_agent
from tools.streamlit_helpers import StreamlitMemoryHelper


async def test_memory_sync():
    """Test memory synchronization between different interfaces."""
    print("🧪 Testing Memory Sync Fix")
    print("=" * 50)
    
    # 1. Create agent
    print("\n1️⃣ Creating agent...")
    try:
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="qwen2.5:7b",
            debug=True,
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for simpler testing
            recreate=False
        )
        print("✅ Agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return
    
    # 2. Create Streamlit helper
    print("\n2️⃣ Creating Streamlit memory helper...")
    memory_helper = StreamlitMemoryHelper(agent)
    print("✅ Memory helper created")
    
    # 3. Test memory storage via agent
    print("\n3️⃣ Testing memory storage via agent...")
    test_memory = "I love testing memory synchronization systems"
    result = await agent.store_user_memory(content=test_memory, topics=["testing"])
    print(f"Storage result: {result}")
    
    # 4. Test memory retrieval via Streamlit helper
    print("\n4️⃣ Testing memory retrieval via Streamlit helper...")
    streamlit_memories = memory_helper.get_all_memories()
    print(f"Streamlit interface found: {len(streamlit_memories)} memories")
    
    # 5. Test memory retrieval via agent tools
    print("\n5️⃣ Testing memory retrieval via agent tools...")
    if agent.agent and hasattr(agent.agent, "tools"):
        for tool in agent.agent.tools:
            if getattr(tool, "__name__", "") == "get_all_memories":
                agent_result = await tool()
                # Count memories in agent result
                agent_count = agent_result.count("📝 All ") 
                if "📝 All " in agent_result:
                    # Extract number from "📝 All X memories:"
                    import re
                    match = re.search(r"📝 All (\d+) memories:", agent_result)
                    if match:
                        agent_count = int(match.group(1))
                    else:
                        agent_count = 0
                else:
                    agent_count = 0
                print(f"Agent tools found: {agent_count} memories")
                break
        else:
            print("❌ Could not find get_all_memories tool")
            agent_count = 0
    else:
        print("❌ Agent tools not available")
        agent_count = 0
    
    # 6. Test sync status
    print("\n6️⃣ Testing sync status...")
    sync_status = memory_helper.get_memory_sync_status()
    if "error" not in sync_status:
        print(f"Local memories: {sync_status.get('local_memory_count', 0)}")
        print(f"Graph entities: {sync_status.get('graph_entity_count', 0)}")
        print(f"Sync status: {sync_status.get('status', 'unknown')}")
    else:
        print(f"❌ Sync status error: {sync_status.get('error', 'Unknown')}")
    
    # 7. Compare results
    print("\n7️⃣ Comparing results...")
    streamlit_count = len(streamlit_memories)
    
    print(f"Streamlit helper: {streamlit_count} memories")
    print(f"Agent tools: {agent_count} memories")
    
    if streamlit_count == agent_count:
        print("✅ SUCCESS: Both interfaces show the same memory count!")
    else:
        print("⚠️ MISMATCH: Interfaces show different memory counts")
        print("This suggests the fix may need additional work")
    
    # 8. Show sample memories from both interfaces
    print("\n8️⃣ Sample memories from both interfaces...")
    
    print("\nStreamlit memories (first 3):")
    for i, memory in enumerate(streamlit_memories[:3]):
        print(f"  {i+1}. {memory.memory[:60]}...")
    
    print(f"\nAgent tool result preview:")
    if 'agent_result' in locals():
        lines = agent_result.split('\n')[:10]  # First 10 lines
        for line in lines:
            if line.strip():
                print(f"  {line}")
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    
    # Cleanup
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(test_memory_sync())
