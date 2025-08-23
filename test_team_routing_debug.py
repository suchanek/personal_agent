#!/usr/bin/env python3
"""
Debug script to understand why team routing isn't working.
"""

import asyncio
import logging
from src.personal_agent.team.personal_agent_team import create_personal_agent_team

# Set up logging to see diagnostic messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_team_routing():
    """Test team routing to see what's actually happening."""
    print("🔍 Testing Team Routing Debug")
    print("="*60)
    
    try:
        # Create team
        team = create_personal_agent_team(
            model_provider="ollama",
            model_name="qwen3:1.7b",
            debug=True
        )
        
        print(f"✅ Team created: {team.name}")
        print(f"   Mode: {team.mode}")
        print(f"   Members: {len(team.members)}")
        
        # Test a simple writing request
        query = "Write a limerick about debugging"
        print(f"\n📝 Testing query: {query}")
        
        response = await team.arun(query)
        
        print(f"\n📋 Response type: {type(response)}")
        print(f"📋 Response content: {response.content}")
        
        # Check response structure
        print(f"\n🔍 Response attributes:")
        for attr in dir(response):
            if not attr.startswith('_'):
                value = getattr(response, attr)
                if not callable(value):
                    print(f"   {attr}: {type(value)} = {value}")
        
        # Check for member responses specifically
        if hasattr(response, 'member_responses'):
            print(f"\n🔍 Member responses: {len(response.member_responses) if response.member_responses else 0}")
            if response.member_responses:
                for i, member_resp in enumerate(response.member_responses):
                    print(f"   Member {i}: {type(member_resp)}")
                    if hasattr(member_resp, 'content'):
                        print(f"      Content: {member_resp.content[:100]}...")
        else:
            print("\n❌ No member_responses attribute found")
        
        # Check messages
        if hasattr(response, 'messages'):
            print(f"\n🔍 Messages: {len(response.messages) if response.messages else 0}")
            if response.messages:
                for i, msg in enumerate(response.messages):
                    print(f"   Message {i}: role={getattr(msg, 'role', 'unknown')}")
                    print(f"      Content: {getattr(msg, 'content', 'No content')[:100]}...")
        else:
            print("\n❌ No messages attribute found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_team_routing())