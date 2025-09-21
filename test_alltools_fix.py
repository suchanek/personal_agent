#!/usr/bin/env python3
"""
Test script to verify that the alltools parameter works correctly in AgnoPersonalAgent.

This script tests both standalone mode (alltools=True) and team mode (alltools=False)
to ensure tools are properly added or excluded based on the parameter.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.config.settings import LLM_MODEL, PROVIDER


async def test_alltools_parameter():
    """Test that alltools parameter correctly controls tool availability."""
    
    print("🧪 Testing alltools parameter functionality...")
    print("=" * 60)
    
    # Test 1: Create agent with alltools=True (standalone mode)
    print("\n📋 Test 1: Creating agent with alltools=True (standalone mode)")
    try:
        standalone_agent = await AgnoPersonalAgent.create_with_init(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            enable_memory=True,
            debug=True,
            alltools=True,  # Should include all built-in tools
            user_id="test_user"
        )
        
        standalone_tool_count = len(standalone_agent.tools) if standalone_agent.tools else 0
        print(f"✅ Standalone agent created with {standalone_tool_count} tools")
        
        # List the tools
        if standalone_agent.tools:
            print("   Tools available:")
            for i, tool in enumerate(standalone_agent.tools, 1):
                tool_name = getattr(tool, '__class__', type(tool)).__name__
                print(f"   {i:2d}. {tool_name}")
        
        await standalone_agent.cleanup()
        
    except Exception as e:
        print(f"❌ Error creating standalone agent: {e}")
        return False
    
    # Test 2: Create agent with alltools=False (team mode)
    print("\n📋 Test 2: Creating agent with alltools=False (team mode)")
    try:
        team_agent = await AgnoPersonalAgent.create_with_init(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            enable_memory=True,
            debug=True,
            alltools=False,  # Should only include memory tools
            user_id="test_user"
        )
        
        team_tool_count = len(team_agent.tools) if team_agent.tools else 0
        print(f"✅ Team agent created with {team_tool_count} tools")
        
        # List the tools
        if team_agent.tools:
            print("   Tools available:")
            for i, tool in enumerate(team_agent.tools, 1):
                tool_name = getattr(tool, '__class__', type(tool)).__name__
                print(f"   {i:2d}. {tool_name}")
        
        await team_agent.cleanup()
        
    except Exception as e:
        print(f"❌ Error creating team agent: {e}")
        return False
    
    # Test 3: Verify the difference
    print("\n📊 Test Results:")
    print(f"   Standalone agent (alltools=True):  {standalone_tool_count} tools")
    print(f"   Team agent (alltools=False):       {team_tool_count} tools")
    
    if standalone_tool_count > team_tool_count:
        print("✅ SUCCESS: alltools parameter works correctly!")
        print(f"   Standalone mode has {standalone_tool_count - team_tool_count} more tools than team mode")
        return True
    else:
        print("❌ FAILURE: alltools parameter is not working correctly!")
        print("   Expected standalone mode to have more tools than team mode")
        return False


async def main():
    """Main test function."""
    print("🚀 Starting alltools parameter test...")
    
    try:
        success = await test_alltools_parameter()
        
        if success:
            print("\n🎉 All tests passed! The alltools fix is working correctly.")
            return 0
        else:
            print("\n💥 Tests failed! The alltools parameter is not working as expected.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
