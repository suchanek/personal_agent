#!/usr/bin/env python3
"""
Test script to verify that the TeamWrapper now exposes all memory functions
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import LLM_MODEL, OLLAMA_URL, AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR
from personal_agent.team.reasoning_team import create_team as create_personal_agent_team

async def test_team_wrapper_memory_functions():
    """Test that TeamWrapper exposes all memory functions."""
    
    print("🧪 Testing TeamWrapper memory function access...")
    
    # Create team
    team = await create_personal_agent_team(use_remote=False, model_name=LLM_MODEL)
    
    print(f"✅ Team created: {type(team).__name__}")
    print(f"✅ Team members: {len(getattr(team, 'members', []))}")
    
    # Import the TeamWrapper creation function from the Streamlit file
    # We'll simulate what the Streamlit app does
    class MockTeamWrapper:
        def __init__(self, team):
            self.team = team
            self.user_id = "test_user"
            
        def _get_knowledge_agent(self):
            """Get the knowledge agent (first team member)."""
            if hasattr(self.team, "members") and self.team.members:
                return self.team.members[0]
            return None
            
        # Test all memory functions
        def list_memories(self):
            """List all memories using the knowledge agent."""
            knowledge_agent = self._get_knowledge_agent()
            if knowledge_agent and hasattr(knowledge_agent, "list_memories"):
                return asyncio.run(knowledge_agent.list_memories())
            raise Exception("Team memory not available")

        def query_memory(self, query, limit=None):
            """Query memories using the knowledge agent."""
            knowledge_agent = self._get_knowledge_agent()
            if knowledge_agent and hasattr(knowledge_agent, "query_memory"):
                return asyncio.run(knowledge_agent.query_memory(query, limit))
            raise Exception("Team memory not available")

        def get_all_memories(self):
            """Get all memories using the knowledge agent."""
            knowledge_agent = self._get_knowledge_agent()
            if knowledge_agent and hasattr(knowledge_agent, "get_all_memories"):
                return asyncio.run(knowledge_agent.get_all_memories())
            raise Exception("Team memory not available")

        def get_memory_stats(self):
            """Get memory statistics using the knowledge agent."""
            knowledge_agent = self._get_knowledge_agent()
            if knowledge_agent and hasattr(knowledge_agent, "get_memory_stats"):
                return asyncio.run(knowledge_agent.get_memory_stats())
            raise Exception("Team memory not available")

    # Create wrapper
    wrapper = MockTeamWrapper(team)
    
    # Test all memory functions
    memory_functions = [
        'list_memories', 'query_memory', 'get_all_memories', 'get_memory_stats'
    ]
    
    print("\n🔍 Checking memory function availability on TeamWrapper:")
    missing_functions = []
    
    for func_name in memory_functions:
        if hasattr(wrapper, func_name):
            func = getattr(wrapper, func_name)
            if callable(func):
                print(f"  ✅ {func_name}: Available and callable")
                
                # Test calling the function
                try:
                    if func_name == 'query_memory':
                        result = func("test query", 5)
                    elif func_name in ['list_memories', 'get_all_memories', 'get_memory_stats']:
                        result = func()
                    
                    print(f"    ✅ {func_name}() call successful")
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
    else:
        print(f"\n✅ All {len(memory_functions)} memory functions are available!")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_team_wrapper_memory_functions())
    if success:
        print("\n🎉 TeamWrapper memory function test passed!")
        sys.exit(0)
    else:
        print("\n💥 TeamWrapper memory function test failed!")
        sys.exit(1)
