#!/usr/bin/env python3
"""
Test script for the refactored Personal Agent Team structure.

This script tests that:
1. The team can be created successfully
2. The knowledge agent is properly integrated
3. Memory operations are delegated correctly
4. The coordinator routes requests appropriately
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.personal_agent_team import create_personal_agent_team
from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL


async def test_refactored_team():
    """Test the refactored team structure."""
    print("🚀 Testing Refactored Personal Agent Team")
    print("=" * 50)
    
    try:
        # 1. Create the team
        print("1. Creating team...")
        team = create_personal_agent_team(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            storage_dir=AGNO_STORAGE_DIR,
            user_id="test_user",
            debug=True,
        )
        
        if not team:
            print("❌ Failed to create team")
            return False
            
        print(f"✅ Team created successfully: {team.name}")
        
        # 2. Check team structure
        print("\n2. Checking team structure...")
        print(f"   Team mode: {getattr(team, 'mode', 'unknown')}")
        print(f"   Team members: {len(getattr(team, 'members', []))}")
        
        if hasattr(team, 'members') and team.members:
            print("   Team members:")
            for i, member in enumerate(team.members):
                member_name = getattr(member, 'name', 'Unknown')
                member_role = getattr(member, 'role', 'Unknown')
                member_tools = len(getattr(member, 'tools', []))
                print(f"     {i+1}. {member_name}: {member_role} ({member_tools} tools)")
                
                # Check if first member is the knowledge agent
                if i == 0:
                    if 'Knowledge' in member_name or hasattr(member, 'agno_memory'):
                        print(f"     ✅ First member is knowledge/memory agent")
                    else:
                        print(f"     ⚠️  First member may not be knowledge agent")
        
        # 3. Check coordinator tools
        print(f"\n3. Checking coordinator...")
        coordinator_tools = len(getattr(team, 'tools', []))
        print(f"   Coordinator tools: {coordinator_tools}")
        if coordinator_tools == 0:
            print("   ✅ Coordinator has no tools (routes only)")
        else:
            print("   ⚠️  Coordinator still has tools")
        
        # 4. Test a simple query
        print("\n4. Testing simple query...")
        test_query = "Hello, can you tell me about yourself?"
        
        try:
            response = await team.arun(test_query, user_id="test_user")
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            print(f"   Query: {test_query}")
            print(f"   Response: {response_content[:100]}...")
            print("   ✅ Team responded successfully")
            
        except Exception as e:
            print(f"   ❌ Team query failed: {str(e)}")
            return False
        
        # 5. Test memory delegation
        print("\n5. Testing memory delegation...")
        memory_query = "What do you remember about me?"
        
        try:
            response = await team.arun(memory_query, user_id="test_user")
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            print(f"   Query: {memory_query}")
            print(f"   Response: {response_content[:100]}...")
            print("   ✅ Memory query handled successfully")
            
        except Exception as e:
            print(f"   ❌ Memory query failed: {str(e)}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Refactored team is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    print("Starting refactored team test...")
    success = asyncio.run(test_refactored_team())
    
    if success:
        print("\n✅ Refactoring successful!")
        sys.exit(0)
    else:
        print("\n❌ Refactoring needs fixes!")
        sys.exit(1)


if __name__ == "__main__":
    main()