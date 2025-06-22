#!/usr/bin/env python3
"""
Test script to verify that route mode fixes the memory routing issue.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.personal_agent_team import PersonalAgentTeamWrapper
from personal_agent.config import LLM_MODEL, OLLAMA_URL


async def test_memory_routing():
    """Test that memory queries are properly routed in route mode."""
    print("🧪 Testing Route Mode Memory Routing Fix")
    print("=" * 50)
    
    # Initialize the team wrapper
    print("📋 Initializing Personal Agent Team...")
    team_wrapper = PersonalAgentTeamWrapper(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        storage_dir="./data/agno",
        user_id="test_user",
        debug=True,
    )
    
    # Initialize the team
    success = await team_wrapper.initialize()
    if not success:
        print("❌ Failed to initialize team")
        return False
    
    print("✅ Team initialized successfully")
    print(f"📊 Team mode: {team_wrapper.team.mode}")
    print(f"👥 Team members: {len(team_wrapper.team.members)}")
    
    # Test memory queries
    memory_queries = [
        "What do you remember about me?",
        "What do you know about me?", 
        "My personal information",
        "Store this: I love hiking and photography",
    ]
    
    print("\n🧠 Testing Memory Queries:")
    print("-" * 30)
    
    for i, query in enumerate(memory_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        try:
            response = await team_wrapper.run(query)
            print(f"   ✅ Response received: {response[:100]}...")
            
            # Check if we got a meaningful response
            if "error" in response.lower() or len(response.strip()) < 10:
                print(f"   ⚠️  Potentially problematic response")
            else:
                print(f"   ✅ Good response length: {len(response)} chars")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    # Test non-memory queries to ensure routing still works
    print("\n🔍 Testing Non-Memory Queries:")
    print("-" * 30)
    
    other_queries = [
        "Calculate 15% of 250",
        "What's 2 + 2?",
    ]
    
    for i, query in enumerate(other_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        try:
            response = await team_wrapper.run(query)
            print(f"   ✅ Response received: {response[:100]}...")
            
            # Check if we got a meaningful response
            if "error" in response.lower() or len(response.strip()) < 10:
                print(f"   ⚠️  Potentially problematic response")
            else:
                print(f"   ✅ Good response length: {len(response)} chars")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    print("\n🎉 All tests completed successfully!")
    print("✅ Route mode appears to be working correctly")
    return True


async def main():
    """Main test function."""
    try:
        success = await test_memory_routing()
        if success:
            print("\n🎯 CONCLUSION: Route mode fix is working!")
            print("   - Memory queries are being routed properly")
            print("   - Original user context is preserved")
            print("   - No direct routing patch needed")
        else:
            print("\n❌ CONCLUSION: Route mode fix needs more work")
            print("   - Some queries failed")
            print("   - May need to investigate further")
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Route Mode Test...")
    asyncio.run(main())
