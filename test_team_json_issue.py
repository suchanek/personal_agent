#!/usr/bin/env python3
"""
Test script to isolate and fix the team JSON response issue.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_team_json_issue():
    """Test the team agent JSON response issue."""
    print("🧪 Testing team agent JSON response issue...")
    
    # Create agent exactly like the team does
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="llama3.2:3b",
        enable_memory=True,
        user_id="team_member",
        debug=True,
        recreate=False
    )
    
    print(f"✅ Team agent created: {agent.model_name}")
    print(f"📊 Debug mode: {agent.debug}")
    print(f"📊 Show tool calls: {agent.show_tool_calls}")
    
    # Test the exact query that's causing issues
    print("🚀 Testing team query that returns JSON...")
    response = await agent.run("Team test query")
    print(f"📝 Response: {response}")
    
    # Check if response contains JSON
    if '{"name":' in response or '"parameters":' in response:
        print("❌ ISSUE: Response contains JSON!")
        print("🔧 Let's check the agent's instructions...")
        
        # Check agent info after initialization
        info = agent.get_agent_info()
        print(f"📊 Initialized: {info['initialized']}")
        print(f"📊 Tools count: {info['tool_counts']['total']}")
        
        # Check instructions
        if hasattr(agent, 'instructions'):
            print("📋 Agent instructions:")
            for i, instruction in enumerate(agent.instructions):
                print(f"  {i+1}. {instruction[:100]}...")
        
        # Try a more explicit memory query
        print("\n🚀 Testing explicit memory query...")
        response2 = await agent.run("What do you remember about me?")
        print(f"📝 Response 2: {response2}")
        
        if '{"name":' in response2 or '"parameters":' in response2:
            print("❌ Still returning JSON!")
        else:
            print("✅ Explicit memory query works!")
            
    else:
        print("✅ No JSON in response!")
    
    return agent


async def main():
    """Run team JSON issue test."""
    print("🎯 Testing Team Agent JSON Response Issue")
    print("=" * 50)
    
    try:
        agent = await test_team_json_issue()
        
        print("\n" + "=" * 50)
        print("🎉 Team JSON issue test completed!")
        print(f"✅ Agent: {agent.user_id} (initialized: {agent._initialized})")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
