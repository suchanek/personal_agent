#!/usr/bin/env python3
"""
Test script to verify that memory stats and sync status functions work correctly
with the team mode in the fixed StreamlitMemoryHelper.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import get_current_user_id
from personal_agent.team.reasoning_team import create_team
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper


def create_team_wrapper(team):
    """Create a wrapper that makes the team look like an agent for the helpers."""
    
    class TeamWrapper:
        def __init__(self, team):
            self.team = team
            self.user_id = get_current_user_id()
            # Force initialization of the knowledge agent first
            self._force_knowledge_agent_init()
            # Now get memory and tools after initialization
            self.agno_memory = self._get_team_memory()
            self.memory_tools = self._get_memory_tools()

        def _force_knowledge_agent_init(self):
            """Force initialization of the knowledge agent (first team member)."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                # Force initialization if not already done
                if hasattr(knowledge_agent, "_ensure_initialized"):
                    try:
                        self._run_async_safely(knowledge_agent._ensure_initialized())
                    except Exception as e:
                        print(f"Failed to initialize knowledge agent: {e}")

        def _get_team_memory(self):
            """Get memory system from the knowledge agent in the team."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "agno_memory"):
                    return knowledge_agent.agno_memory
                elif hasattr(knowledge_agent, "memory"):
                    return knowledge_agent.memory
            return getattr(self.team, "agno_memory", None)

        def _get_memory_tools(self):
            """Get memory tools from the knowledge agent in the team."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "memory_tools"):
                    return knowledge_agent.memory_tools
            return None

        def _run_async_safely(self, coro):
            """Safely run async coroutines."""
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)
                    
            except RuntimeError:
                return asyncio.run(coro)

        # Expose memory functions from the knowledge agent
        def store_user_memory(self, content, topics=None):
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "store_user_memory"):
                    return self._run_async_safely(
                        knowledge_agent.store_user_memory(content=content, topics=topics)
                    )
            raise Exception("Team memory not available")

        def get_memory_stats(self):
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "get_memory_stats"):
                    return self._run_async_safely(knowledge_agent.get_memory_stats())
            raise Exception("Team memory not available")

        def get_all_memories(self):
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "get_all_memories"):
                    return self._run_async_safely(knowledge_agent.get_all_memories())
            raise Exception("Team memory not available")

        def clear_all_memories(self):
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "clear_all_memories"):
                    return self._run_async_safely(knowledge_agent.clear_all_memories())
            raise Exception("Team memory not available")

        def delete_memory(self, memory_id):
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "delete_memory"):
                    return self._run_async_safely(knowledge_agent.delete_memory(memory_id))
            raise Exception("Team memory not available")

        def _ensure_initialized(self):
            """Ensure the knowledge agent is initialized."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "_ensure_initialized"):
                    return knowledge_agent._ensure_initialized()
            return None

    return TeamWrapper(team)


async def test_team_memory_stats_and_sync():
    """Test memory stats and sync status functionality with team mode."""
    print("🧪 Testing Team Memory Stats and Sync Status Fix")
    print("=" * 50)
    
    # Initialize team
    print("1. Initializing team...")
    team = await create_team(use_remote=False, model_name="qwen2.5:14b")
    print(f"✅ Team initialized with {len(team.members)} members")
    
    # Create team wrapper
    print("\n2. Creating team wrapper...")
    team_wrapper = create_team_wrapper(team)
    print("✅ Team wrapper created")
    
    # Create memory helper
    print("\n3. Creating StreamlitMemoryHelper...")
    memory_helper = StreamlitMemoryHelper(team_wrapper)
    print("✅ Memory helper created")
    
    # Test memory stats
    print("\n4. Testing get_memory_stats()...")
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
    print("\n5. Testing get_memory_sync_status()...")
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
    
    print("\n" + "=" * 50)
    print("🧪 Team test completed!")


if __name__ == "__main__":
    asyncio.run(test_team_memory_stats_and_sync())
