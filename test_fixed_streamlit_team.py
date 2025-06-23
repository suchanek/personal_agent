#!/usr/bin/env python3
"""
Test script to verify the fixed streamlit team implementation works correctly.
This tests the core functionality without running the full Streamlit app.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID
from personal_agent.team.personal_agent_team import create_personal_agent_team
from personal_agent.core.agno_storage import create_agno_memory


def test_team_creation():
    """Test that we can create the team successfully."""
    print("🧪 Testing team creation...")
    
    try:
        # Create team using the factory function (same as in streamlit app)
        team = create_personal_agent_team(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            storage_dir=AGNO_STORAGE_DIR,
            user_id=USER_ID,
            debug=True,
        )
        
        # Create memory system for compatibility (same as in streamlit app)
        agno_memory = create_agno_memory(AGNO_STORAGE_DIR, debug_mode=True)
        
        # Attach memory to team for access (same as in streamlit app)
        team.agno_memory = agno_memory
        
        print(f"✅ Team created successfully!")
        print(f"   - Team name: {getattr(team, 'name', 'Unknown')}")
        print(f"   - Members: {len(getattr(team, 'members', []))}")
        print(f"   - Memory system attached: {hasattr(team, 'agno_memory')}")
        
        # List team members
        members = getattr(team, 'members', [])
        if members:
            print("   - Team members:")
            for member in members:
                member_name = getattr(member, 'name', 'Unknown')
                member_role = getattr(member, 'role', 'Unknown')
                member_tools = len(getattr(member, 'tools', []))
                print(f"     • {member_name}: {member_role} ({member_tools} tools)")
        
        return team
        
    except Exception as e:
        print(f"❌ Team creation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_team_response(team):
    """Test that the team can respond to a simple query."""
    print("\n🧪 Testing team response...")
    
    if not team:
        print("❌ No team to test")
        return False
    
    try:
        # Test with a simple query (same method as in streamlit app)
        test_query = "Hello, can you introduce yourself?"
        print(f"   Query: {test_query}")
        
        response = await team.arun(test_query, user_id=USER_ID)
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        print(f"✅ Team responded successfully!")
        print(f"   Response length: {len(response_content)} characters")
        print(f"   Response preview: {response_content[:100]}...")
        
        # Check for tool calls (same as in streamlit app)
        tool_calls_made = 0
        if hasattr(response, 'messages') and response.messages:
            for message in response.messages:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls_made += len(message.tool_calls)
        
        print(f"   Tool calls made: {tool_calls_made}")
        
        return True
        
    except Exception as e:
        print(f"❌ Team response failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_system(team):
    """Test that the memory system is working."""
    print("\n🧪 Testing memory system...")
    
    if not team or not hasattr(team, 'agno_memory'):
        print("❌ No memory system to test")
        return False
    
    try:
        # Test memory retrieval (same as in streamlit app)
        memories = team.agno_memory.get_user_memories(user_id=USER_ID)
        print(f"✅ Memory system accessible!")
        print(f"   Current memories: {len(memories) if memories else 0}")
        
        # Test memory manager access (same as in streamlit app)
        if hasattr(team.agno_memory, 'memory_manager'):
            memory_manager = team.agno_memory.memory_manager
            print(f"   Memory manager available: {memory_manager is not None}")
            
            if hasattr(memory_manager, 'config'):
                config = memory_manager.config
                print(f"   Similarity threshold: {getattr(config, 'similarity_threshold', 'N/A')}")
                print(f"   Debug mode: {getattr(config, 'debug_mode', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory system test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing Fixed Streamlit Team Implementation")
    print("=" * 50)
    
    # Test 1: Team creation
    team = test_team_creation()
    
    # Test 2: Team response
    response_success = await test_team_response(team)
    
    # Test 3: Memory system
    memory_success = test_memory_system(team)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Team Creation: {'✅ PASS' if team else '❌ FAIL'}")
    print(f"   Team Response: {'✅ PASS' if response_success else '❌ FAIL'}")
    print(f"   Memory System: {'✅ PASS' if memory_success else '❌ FAIL'}")
    
    all_passed = team and response_success and memory_success
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 The fixed streamlit team implementation should work correctly!")
        print("   You can now run: streamlit run tools/paga_streamlit_team.py")
    else:
        print("\n⚠️  There are still issues that need to be resolved.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
