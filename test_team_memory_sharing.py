#!/usr/bin/env python3
"""
Test script to verify team memory sharing works correctly.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.personal_agent.team.ollama_reasoning_multi_purpose_team import create_team


async def test_team_memory_sharing():
    """Test that the team can properly share memory."""
    print("🧪 Testing team memory sharing...")
    
    # Create the team
    team = await create_team()
    print(f"✅ Team created with {len(team.members)} members")
    
    # List team members
    print("👥 Team members:")
    for i, member in enumerate(team.members):
        member_name = getattr(member, 'name', f'Member {i}')
        member_id = getattr(member, 'agent_id', 'unknown')
        print(f"  - {member_name} (ID: {member_id})")
    
    # Test storing a memory
    print("\n🚀 Testing memory storage...")
    response1 = await team.arun("Remember that I love testing software and debugging code")
    response1_content = getattr(response1, 'content', str(response1))
    print(f"📝 Storage response: {response1_content[:100]}...")
    
    # Test retrieving memories
    print("\n🚀 Testing memory retrieval...")
    response2 = await team.arun("What do you remember about me?")
    response2_content = getattr(response2, 'content', str(response2))
    print(f"📝 Retrieval response: {response2_content[:100]}...")
    
    # Test listing memories
    print("\n🚀 Testing memory listing...")
    response3 = await team.arun("List all my memories")
    response3_content = getattr(response3, 'content', str(response3))
    print(f"📝 List response: {response3_content[:100]}...")
    
    return team


async def main():
    """Run team memory sharing test."""
    print("🎯 Testing Team Memory Sharing")
    print("=" * 50)
    
    try:
        team = await test_team_memory_sharing()
        
        print("\n" + "=" * 50)
        print("🎉 Team memory sharing test completed!")
        print(f"✅ Team has {len(team.members)} members")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
