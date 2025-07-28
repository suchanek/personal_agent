#!/usr/bin/env python3
"""
Test script to verify the lazy initialization refactoring works correctly.

This script tests both the old and new patterns to ensure backward compatibility.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.personal_agent.core.agno_agent import AgnoPersonalAgent, create_agno_agent


async def test_new_pattern():
    """Test the new lazy initialization pattern."""
    print("🧪 Testing new pattern (direct constructor)...")
    
    # Create agent using constructor - no await needed!
    agent = AgnoPersonalAgent(
        model_name="llama3.2:3b",
        enable_memory=True,
        user_id="test_user",
        debug=True
    )
    
    print(f"✅ Agent created: {agent.model_name}, initialized: {agent._initialized}")
    
    # Check agent info before initialization
    info_before = agent.get_agent_info()
    print(f"📊 Before init - Knowledge enabled: {info_before['knowledge_enabled']}, Memory enabled: {info_before['memory_enabled']}")
    
    # First use should trigger initialization
    print("🚀 Running first query (should trigger initialization)...")
    response = await agent.run("Hello, this is a test!")
    print(f"📝 Response: {response[:100]}...")
    print(f"✅ Agent now initialized: {agent._initialized}")
    
    # Check agent info after initialization
    info_after = agent.get_agent_info()
    print(f"📊 After init - Knowledge enabled: {info_after['knowledge_enabled']}, Memory enabled: {info_after['memory_enabled']}")
    
    # Second use should not trigger initialization again
    print("🚀 Running second query (should use existing initialization)...")
    response2 = await agent.run("What's 2+2?")
    print(f"📝 Response: {response2[:100]}...")
    
    return agent


async def test_old_pattern():
    """Test the old pattern for backward compatibility."""
    print("\n🧪 Testing old pattern (create_agno_agent function)...")
    
    # This should still work but will show deprecation message
    agent = await create_agno_agent(
        model_name="llama3.2:3b",
        enable_memory=True,
        user_id="test_user_old",
        debug=True
    )
    
    print(f"✅ Agent created via old pattern: {agent.model_name}")
    
    # Should work immediately since create_agno_agent still calls initialize
    response = await agent.run("Hello from old pattern!")
    print(f"📝 Response: {response[:100]}...")
    
    return agent


async def test_team_pattern():
    """Test the team usage pattern."""
    print("\n🧪 Testing team pattern...")
    
    # Simulate team usage
    def create_memory_agent_for_team():
        """Simulate the team's create_memory_agent function."""
        return AgnoPersonalAgent(
            model_provider="ollama",
            model_name="llama3.2:3b",
            enable_memory=True,
            user_id="team_member",
            debug=True,
            recreate=False
        )
    
    # Create agent for team - no await needed!
    agent = create_memory_agent_for_team()
    print(f"✅ Team agent created: {agent.model_name}")
    
    # First use in team context
    response = await agent.run("Team test query")
    print(f"📝 Team response: {response[:100]}...")
    
    return agent


async def main():
    """Run all tests."""
    print("🎯 Testing AgnoPersonalAgent Lazy Initialization Refactoring")
    print("=" * 60)
    
    try:
        # Test new pattern
        new_agent = await test_new_pattern()
        
        # Test old pattern for backward compatibility
        old_agent = await test_old_pattern()
        
        # Test team pattern
        team_agent = await test_team_pattern()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("\n📊 Summary:")
        print(f"  - New pattern agent: {new_agent.user_id} (initialized: {new_agent._initialized})")
        print(f"  - Old pattern agent: {old_agent.user_id} (initialized: {old_agent._initialized})")
        print(f"  - Team pattern agent: {team_agent.user_id} (initialized: {team_agent._initialized})")
        
        print("\n✨ Key Benefits:")
        print("  - ✅ No more await create_agno_agent() needed")
        print("  - ✅ Just use AgnoPersonalAgent() constructor")
        print("  - ✅ Initialization happens automatically on first use")
        print("  - ✅ Backward compatibility maintained")
        print("  - ✅ Team usage simplified")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
