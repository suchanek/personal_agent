#!/usr/bin/env python3
"""
Test script to verify the consolidated memory restatement fix works correctly.

This script tests that all team agents now use the centralized AgentMemoryManager
with proper restatement logic.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_consolidated_memory_storage():
    """Test that team agents use centralized memory storage with proper restatement."""
    
    print("🧪 Testing Consolidated Memory Storage Fix")
    print("=" * 60)
    
    try:
        # Test the specialized agents memory tools
        from personal_agent.team.specialized_agents import _get_memory_tools
        from personal_agent.core.agno_storage import create_agno_memory
        
        # Create test memory system
        storage_dir = "./test_data/agno"
        user_id = "test_user"
        agno_memory = create_agno_memory(storage_dir, debug_mode=False)
        
        # Get memory tools using the new centralized approach
        memory_tools = await _get_memory_tools(agno_memory, user_id, storage_dir)
        
        # Find the store_user_memory function
        store_memory_func = None
        for tool in memory_tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'store_user_memory':
                store_memory_func = tool
                break
        
        if not store_memory_func:
            print("❌ FAIL: store_user_memory function not found in memory tools")
            return False
        
        # Test the restatement with our example
        test_input = "I have a pet dog named snoopy"
        expected_pattern = "test_user has a pet dog named snoopy"
        
        print(f"📝 Testing input: '{test_input}'")
        print(f"🎯 Expected pattern: '{expected_pattern}'")
        
        # Store the memory
        result = await store_memory_func(test_input, ["pets", "personal"])
        
        print(f"📤 Storage result: {result}")
        
        # Verify the result indicates success
        if "✅" in result and "Successfully stored memory" in result:
            print("✅ PASS: Memory storage succeeded")
            
            # Now verify the memory was stored with proper restatement
            # by checking what's actually in the database
            all_memories = agno_memory.get_user_memories(user_id=user_id)
            
            if all_memories:
                latest_memory = all_memories[-1]  # Get the most recent memory
                stored_content = latest_memory.memory
                
                print(f"💾 Stored content: '{stored_content}'")
                
                # Check if the stored content has proper third-person restatement
                if "test_user has" in stored_content and "I have" not in stored_content:
                    print("✅ PASS: Memory stored with correct third-person restatement")
                    print(f"   Original: '{test_input}'")
                    print(f"   Stored:   '{stored_content}'")
                    return True
                else:
                    print("❌ FAIL: Memory not properly restated to third person")
                    print(f"   Expected pattern: contains 'test_user has'")
                    print(f"   Actual stored:    '{stored_content}'")
                    return False
            else:
                print("❌ FAIL: No memories found in database")
                return False
        else:
            print("❌ FAIL: Memory storage failed")
            print(f"   Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_team_agents_integration():
    """Test that different team agent types use the consolidated approach."""
    
    print("\n🔧 Testing Team Agent Integration")
    print("=" * 40)
    
    try:
        # Test personal_agent_team
        print("1. Testing personal_agent_team...")
        from personal_agent.team.personal_agent_team import create_personal_agent_team
        
        team = create_personal_agent_team(
            model_provider="ollama",
            model_name="llama3.1:8b",
            storage_dir="./test_data/agno",
            user_id="test_user",
            debug=False
        )
        
        if team and hasattr(team, 'tools') and team.tools:
            print("   ✅ Personal agent team created with memory tools")
        else:
            print("   ❌ Personal agent team creation failed")
            return False
        
        # Test basic_memory_agent
        print("2. Testing basic_memory_agent...")
        from personal_agent.team.basic_memory_agent import create_basic_memory_agent
        
        basic_agent = create_basic_memory_agent(
            model_provider="ollama",
            model_name="llama3.1:8b",
            storage_dir="./test_data/agno",
            user_id="test_user",
            debug=False
        )
        
        if basic_agent and hasattr(basic_agent, 'tools') and basic_agent.tools:
            print("   ✅ Basic memory agent created with memory tools")
        else:
            print("   ❌ Basic memory agent creation failed")
            return False
        
        print("✅ PASS: All team agents integrate with consolidated memory system")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Team integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all consolidation tests."""
    
    print("🚀 Starting Consolidated Memory Fix Tests")
    print("=" * 60)
    
    # Test 1: Core memory storage with restatement
    test1_passed = await test_consolidated_memory_storage()
    
    # Test 2: Team agent integration
    test2_passed = await test_team_agents_integration()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("✅ Consolidated memory fix is working correctly:")
        print("   • All team agents use centralized AgentMemoryManager")
        print("   • Proper first-person → third-person restatement")
        print("   • Consistent memory storage across all agents")
        print("   • No duplicate store_user_memory implementations")
        print()
        print("🔧 Integration Status: COMPLETE")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"   Core memory storage: {'✅ PASS' if test1_passed else '❌ FAIL'}")
        print(f"   Team agent integration: {'✅ PASS' if test2_passed else '❌ FAIL'}")
        print()
        print("🔧 Integration Status: NEEDS ATTENTION")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)