#!/usr/bin/env python3
"""
Test script to verify memory deletion works in team mode.
This script tests the TeamWrapper functionality for memory operations.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.personal_agent_team import create_personal_agent_team
from personal_agent.config import AGNO_STORAGE_DIR, get_current_user_id
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper

USER_ID = get_current_user_id()

def create_team_wrapper(team):
    """Create a wrapper that makes the team look like an agent for the helpers."""

    class TeamWrapper:
        def __init__(self, team):
            self.team = team
            self.user_id = USER_ID
            # Don't initialize here - we'll do it explicitly later
            self.agno_memory = None
            self.memory_tools = None

        async def _force_knowledge_agent_init(self):
            """Force initialization of the knowledge agent (first team member)."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                # Force initialization if not already done
                if hasattr(knowledge_agent, "_ensure_initialized"):
                    try:
                        await knowledge_agent._ensure_initialized()
                        print("   ✅ Knowledge agent initialized successfully")
                    except Exception as e:
                        print(f"   ❌ Failed to initialize knowledge agent: {e}")

        def _get_team_memory(self):
            """Get memory system from the knowledge agent in the team."""
            if hasattr(self.team, "members") and self.team.members:
                # The first member should be the knowledge agent (PersonalAgnoAgent)
                knowledge_agent = self.team.members[0]
                print(f"   DEBUG: Knowledge agent type: {type(knowledge_agent)}")
                print(f"   DEBUG: Has agno_memory: {hasattr(knowledge_agent, 'agno_memory')}")
                if hasattr(knowledge_agent, "agno_memory"):
                    print(f"   DEBUG: agno_memory is not None: {knowledge_agent.agno_memory is not None}")
                    return knowledge_agent.agno_memory
                elif hasattr(knowledge_agent, "memory"):
                    return knowledge_agent.memory

            # Fallback: check if team has direct memory access
            return getattr(self.team, "agno_memory", None)

        def _get_memory_tools(self):
            """Get memory tools from the knowledge agent in the team."""
            if hasattr(self.team, "members") and self.team.members:
                # The first member should be the knowledge agent (PersonalAgnoAgent)
                knowledge_agent = self.team.members[0]
                print(f"   DEBUG: Has memory_tools: {hasattr(knowledge_agent, 'memory_tools')}")
                if hasattr(knowledge_agent, "memory_tools"):
                    print(f"   DEBUG: memory_tools is not None: {knowledge_agent.memory_tools is not None}")
                    return knowledge_agent.memory_tools
            return None

        def _ensure_initialized(self):
            """Ensure the knowledge agent is initialized."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "_ensure_initialized"):
                    return knowledge_agent._ensure_initialized()
            return None

        async def store_user_memory(self, content, topics=None):
            # Use the knowledge agent (first team member) for memory storage with fact restating
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]  # First member is the knowledge agent
                if hasattr(knowledge_agent, "store_user_memory"):
                    # This will properly restate facts and process them through the LLM
                    return await knowledge_agent.store_user_memory(content=content, topics=topics)

            # Fallback to direct memory storage (bypasses LLM processing)
            if self.agno_memory and hasattr(self.agno_memory, "memory_manager"):
                # Use the SemanticMemoryManager's add_memory method directly
                result = self.agno_memory.memory_manager.add_memory(
                    memory_text=content,
                    db=self.agno_memory.db,
                    user_id=self.user_id,
                    topics=topics,
                )
                print(f"Memory stored in team memory: {result}")
                return result

            raise Exception("Team memory not available")

    return TeamWrapper(team)


async def test_memory_deletion():
    """Test memory deletion functionality in team mode."""
    print("🧪 Testing Memory Deletion in Team Mode")
    print("=" * 50)
    
    try:
        # Initialize team
        print("1. Initializing team...")
        team = create_personal_agent_team(
            model_provider="ollama",
            model_name="llama3.2:3b",  # Use a lightweight model for testing
            ollama_base_url="http://localhost:11434",
            storage_dir=AGNO_STORAGE_DIR,
            user_id=USER_ID,
            debug=True,
        )
        print(f"   ✅ Team initialized with {len(getattr(team, 'members', []))} members")
        
        # Create team wrapper and force initialization
        print("2. Creating team wrapper and forcing initialization...")
        team_wrapper = create_team_wrapper(team)
        await team_wrapper._force_knowledge_agent_init()
        
        # Now get the components after initialization
        team_wrapper.agno_memory = team_wrapper._get_team_memory()
        team_wrapper.memory_tools = team_wrapper._get_memory_tools()
        
        print(f"   ✅ Team wrapper created")
        print(f"   - Memory tools available: {team_wrapper.memory_tools is not None}")
        print(f"   - Memory system available: {team_wrapper.agno_memory is not None}")
        
        # Create memory helper
        print("3. Creating memory helper...")
        memory_helper = StreamlitMemoryHelper(team_wrapper)
        print("   ✅ Memory helper created")
        
        # Add a test memory
        print("4. Adding test memory...")
        result = await team_wrapper.store_user_memory(
            content="This is a test memory for deletion testing",
            topics=["test"]
        )
        
        # Parse the result
        if hasattr(result, "is_success"):
            success = result.is_success
            message = result.message
            memory_id = getattr(result, "memory_id", None)
        else:
            success = "✅" in str(result)
            message = str(result)
            memory_id = None
        
        if success:
            print(f"   ✅ Memory added successfully: {message}")
            print(f"   - Memory ID: {memory_id}")
        else:
            print(f"   ❌ Failed to add memory: {message}")
            return False
            
        # List memories to confirm it was added
        print("5. Listing memories...")
        memories = memory_helper.get_all_memories()
        print(f"   ✅ Found {len(memories)} memories")
        
        if memories:
            test_memory = None
            for memory in memories:
                if "test memory for deletion testing" in memory.memory:
                    test_memory = memory
                    break
            
            if test_memory:
                print(f"   - Test memory found: {test_memory.memory[:50]}...")
                print(f"   - Memory ID: {getattr(test_memory, 'memory_id', 'N/A')}")
                
                # Test deletion
                print("6. Testing memory deletion...")
                delete_success, delete_message = memory_helper.delete_memory(test_memory.memory_id)
                
                if delete_success:
                    print(f"   ✅ Memory deleted successfully: {delete_message}")
                    
                    # Verify deletion
                    print("7. Verifying deletion...")
                    memories_after = memory_helper.get_all_memories()
                    print(f"   ✅ Memories after deletion: {len(memories_after)}")
                    
                    # Check if the test memory is gone
                    test_memory_found = False
                    for memory in memories_after:
                        if "test memory for deletion testing" in memory.memory:
                            test_memory_found = True
                            break
                    
                    if not test_memory_found:
                        print("   ✅ Test memory successfully deleted!")
                        return True
                    else:
                        print("   ❌ Test memory still exists after deletion")
                        return False
                else:
                    print(f"   ❌ Memory deletion failed: {delete_message}")
                    return False
            else:
                print("   ❌ Test memory not found in memory list")
                return False
        else:
            print("   ❌ No memories found")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the memory deletion test."""
    print("Starting Memory Deletion Test...")
    print()
    
    success = asyncio.run(test_memory_deletion())
    
    print()
    print("=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! Memory deletion works in team mode.")
    else:
        print("💥 TEST FAILED! Memory deletion needs further investigation.")
    print("=" * 50)


if __name__ == "__main__":
    main()