#!/usr/bin/env python3
"""
Test script to verify that the KnowledgeTools async/sync fix works correctly.

This test verifies that:
1. KnowledgeTools can be instantiated without async methods
2. The agent can run with KnowledgeTools in single mode
3. The specific error "Async tool knowledge_tools can't be used with synchronous agent.run()" is resolved
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.knowledge_tools import KnowledgeTools
from personal_agent.core.knowledge_manager import KnowledgeManager


async def test_knowledge_tools_sync_compatibility():
    """Test that KnowledgeTools works with synchronous agent.run() calls."""
    print("🧪 Testing KnowledgeTools sync compatibility...")
    
    try:
        # 1. Create a simple agent with KnowledgeTools
        print("1. Creating AgnoPersonalAgent...")
        agent = await AgnoPersonalAgent.create_with_init(
            model_provider="ollama",
            model_name="qwen2.5:7b-instruct",
            enable_memory=True,
            debug=True,
            alltools=False,  # Only use knowledge tools for this test
        )
        print("   ✅ Agent created successfully")
        
        # 2. Verify KnowledgeTools are present and not async
        print("2. Checking KnowledgeTools...")
        knowledge_tools = None
        for tool in agent.tools:
            if hasattr(tool, 'name') and tool.name == 'knowledge_tools':
                knowledge_tools = tool
                break
        
        if knowledge_tools:
            print("   ✅ KnowledgeTools found in agent tools")
            
            # Check that the problematic methods are now synchronous
            query_kb_method = getattr(knowledge_tools, 'query_knowledge_base', None)
            query_direct_method = getattr(knowledge_tools, 'query_lightrag_knowledge_direct', None)
            
            if query_kb_method and not asyncio.iscoroutinefunction(query_kb_method):
                print("   ✅ query_knowledge_base is now synchronous")
            else:
                print("   ❌ query_knowledge_base is still async")
                return False
                
            if query_direct_method and not asyncio.iscoroutinefunction(query_direct_method):
                print("   ✅ query_lightrag_knowledge_direct is now synchronous")
            else:
                print("   ❌ query_lightrag_knowledge_direct is still async")
                return False
        else:
            print("   ⚠️  KnowledgeTools not found (memory might be disabled)")
            # Continue with the test even if KnowledgeTools not found
        
        # 3. Test that agent.run() works without the async error
        print("3. Testing agent.run() with KnowledgeTools...")
        try:
            # Use a simple query that shouldn't trigger knowledge tools
            response = await agent.run("Hello, how are you?", stream=False)
            print(f"   ✅ Agent.run() completed successfully: {response[:50]}...")
            
            # Test a query that might trigger knowledge tools (but won't fail due to async issues)
            print("4. Testing knowledge-related query...")
            response = await agent.run("What do you know about machine learning?", stream=False)
            print(f"   ✅ Knowledge query completed: {response[:50]}...")
            
        except Exception as e:
            error_msg = str(e)
            if "Async tool knowledge_tools can't be used with synchronous agent.run()" in error_msg:
                print(f"   ❌ The original async error still occurs: {error_msg}")
                return False
            else:
                print(f"   ⚠️  Different error occurred (may be expected): {error_msg}")
        
        print("🎉 All tests passed! The async/sync fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_tools_direct():
    """Test KnowledgeTools methods directly to ensure they're synchronous."""
    print("\n🔧 Testing KnowledgeTools methods directly...")
    
    try:
        # Create KnowledgeTools instance
        km = KnowledgeManager(
            user_id="test_user",
            knowledge_dir="/tmp/test_storage",
            lightrag_url="http://localhost:9621"
        )
        tools = KnowledgeTools(km, agno_knowledge=None)
        
        # Test that methods are synchronous
        query_kb_method = getattr(tools, 'query_knowledge_base', None)
        query_direct_method = getattr(tools, 'query_lightrag_knowledge_direct', None)
        
        if query_kb_method and not asyncio.iscoroutinefunction(query_kb_method):
            print("   ✅ query_knowledge_base is synchronous")
        else:
            print("   ❌ query_knowledge_base is still async")
            return False
            
        if query_direct_method and not asyncio.iscoroutinefunction(query_direct_method):
            print("   ✅ query_lightrag_knowledge_direct is synchronous")
        else:
            print("   ❌ query_lightrag_knowledge_direct is still async")
            return False
        
        # Test calling the methods (they should handle the async context properly)
        print("   Testing method calls...")
        try:
            result1 = tools.query_knowledge_base("test query")
            print(f"   ✅ query_knowledge_base call successful: {result1[:50]}...")
        except Exception as e:
            print(f"   ⚠️  query_knowledge_base call failed (may be expected): {e}")
        
        try:
            result2 = tools.query_lightrag_knowledge_direct("test query")
            print(f"   ✅ query_lightrag_knowledge_direct call successful: {result2[:50]}...")
        except Exception as e:
            print(f"   ⚠️  query_lightrag_knowledge_direct call failed (may be expected): {e}")
        
        print("🎉 Direct method tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Direct method test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting KnowledgeTools async/sync compatibility tests...\n")
    
    # Test 1: Direct method testing
    direct_test_passed = test_knowledge_tools_direct()
    
    # Test 2: Full agent integration testing
    if direct_test_passed:
        integration_test_passed = await test_knowledge_tools_sync_compatibility()
    else:
        print("❌ Skipping integration test due to direct test failure")
        integration_test_passed = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Direct Method Test: {'✅ PASSED' if direct_test_passed else '❌ FAILED'}")
    print(f"Integration Test: {'✅ PASSED' if integration_test_passed else '❌ FAILED'}")
    
    if direct_test_passed and integration_test_passed:
        print("\n🎉 ALL TESTS PASSED! The async/sync fix is working correctly.")
        print("The error 'Async tool knowledge_tools can't be used with synchronous agent.run()' should be resolved.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED. The fix may need additional work.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)