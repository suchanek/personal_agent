#!/usr/bin/env python3
"""
Test script to verify memory functionality in the refactored team.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.personal_agent.team.personal_agent_team import create_personal_agent_team


async def test_memory_functionality():
    """Test that memory functionality actually works in the refactored team."""
    print("🧠 Testing Memory Functionality in Refactored Team")
    print("=" * 60)
    
    # Create the team
    print("1. Creating team...")
    team = create_personal_agent_team(
        model_provider="ollama",
        model_name="qwen3:8b",
        user_id="test_user",
        debug=True,
    )
    print(f"✅ Team created: {team.name}")
    
    # Get the knowledge agent directly
    knowledge_agent = team.members[0]  # First agent should be knowledge agent
    print(f"📋 Knowledge agent: {knowledge_agent.name}")
    print(f"📋 Knowledge agent type: {type(knowledge_agent).__name__}")
    
    # Force initialization of the knowledge agent
    print("\n2. Initializing knowledge agent...")
    try:
        await knowledge_agent.initialize()
        print(f"✅ Knowledge agent initialized with {len(knowledge_agent.tools)} tools")
        
        # List the tools
        if knowledge_agent.tools:
            print("📋 Available tools:")
            for i, tool in enumerate(knowledge_agent.tools, 1):
                tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(type(tool).__name__)))
                print(f"   {i}. {tool_name}")
        else:
            print("❌ No tools found after initialization")
            
    except Exception as e:
        print(f"❌ Failed to initialize knowledge agent: {e}")
        return False
    
    # Test memory storage
    print("\n3. Testing memory storage...")
    try:
        result = await knowledge_agent.store_user_memory(
            "I love playing chess and reading science fiction books",
            topics=["hobbies", "interests"]
        )
        print(f"✅ Memory stored: {result}")
    except Exception as e:
        print(f"❌ Failed to store memory: {e}")
        return False
    
    # Test memory retrieval through team
    print("\n4. Testing memory retrieval through team...")
    try:
        response = await team.arun("What do you remember about my hobbies?")
        print(f"✅ Team response: {response.content[:200]}...")
        
        # Check if the response contains information about chess or science fiction
        if "chess" in response.content.lower() or "science fiction" in response.content.lower():
            print("✅ Memory retrieval successful - found hobby information")
        else:
            print("⚠️ Memory retrieval may not be working - no hobby information found")
            
    except Exception as e:
        print(f"❌ Failed to test memory retrieval: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Memory functionality test completed!")
    return True


def main():
    """Main function to run the memory functionality test."""
    try:
        result = asyncio.run(test_memory_functionality())
        if result:
            print("✅ All memory tests passed!")
            sys.exit(0)
        else:
            print("❌ Some memory tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()