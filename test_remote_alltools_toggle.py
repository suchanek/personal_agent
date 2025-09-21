#!/usr/bin/env python3
"""
Test script to verify that the alltools parameter is automatically toggled based on the --remote flag.

This script tests that:
- When use_remote=False (local), stand_alone defaults to False (team mode, fewer tools)
- When use_remote=True (remote), stand_alone defaults to True (standalone mode, all tools)
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.team.reasoning_team import create_memory_agent
from personal_agent.config.settings import LLM_MODEL, PROVIDER


async def test_remote_alltools_toggle():
    """Test that alltools parameter is automatically toggled based on use_remote flag."""
    
    print("🧪 Testing automatic alltools toggling based on --remote flag...")
    print("=" * 70)
    
    # Test 1: Local mode (use_remote=False) should default to team mode (fewer tools)
    print("\n📋 Test 1: Local mode (use_remote=False) - should be team mode")
    try:
        local_agent = await create_memory_agent(
            user_id="test_user",
            debug=True,
            use_remote=False,  # Local mode
            model_name=LLM_MODEL,
            # stand_alone not specified - should auto-detect to False
        )
        
        local_tool_count = len(local_agent.tools) if local_agent.tools else 0
        print(f"✅ Local agent created with {local_tool_count} tools")
        
        # List the tools
        if local_agent.tools:
            print("   Tools available:")
            for i, tool in enumerate(local_agent.tools, 1):
                tool_name = getattr(tool, '__class__', type(tool)).__name__
                print(f"   {i:2d}. {tool_name}")
        
        await local_agent.cleanup()
        
    except Exception as e:
        print(f"❌ Error creating local agent: {e}")
        return False
    
    # Test 2: Remote mode (use_remote=True) should default to standalone mode (more tools)
    print("\n📋 Test 2: Remote mode (use_remote=True) - should be standalone mode")
    try:
        remote_agent = await create_memory_agent(
            user_id="test_user",
            debug=True,
            use_remote=True,  # Remote mode
            model_name=LLM_MODEL,
            # stand_alone not specified - should auto-detect to True
        )
        
        remote_tool_count = len(remote_agent.tools) if remote_agent.tools else 0
        print(f"✅ Remote agent created with {remote_tool_count} tools")
        
        # List the tools
        if remote_agent.tools:
            print("   Tools available:")
            for i, tool in enumerate(remote_agent.tools, 1):
                tool_name = getattr(tool, '__class__', type(tool)).__name__
                print(f"   {i:2d}. {tool_name}")
        
        await remote_agent.cleanup()
        
    except Exception as e:
        print(f"❌ Error creating remote agent: {e}")
        return False
    
    # Test 3: Explicit override should work
    print("\n📋 Test 3: Explicit stand_alone=True should override auto-detection")
    try:
        explicit_agent = await create_memory_agent(
            user_id="test_user",
            debug=True,
            use_remote=False,  # Local mode
            model_name=LLM_MODEL,
            stand_alone=True,  # Explicitly set to True (override auto-detection)
        )
        
        explicit_tool_count = len(explicit_agent.tools) if explicit_agent.tools else 0
        print(f"✅ Explicit agent created with {explicit_tool_count} tools")
        
        await explicit_agent.cleanup()
        
    except Exception as e:
        print(f"❌ Error creating explicit agent: {e}")
        return False
    
    # Test 4: Verify the results
    print("\n📊 Test Results:")
    print(f"   Local mode (use_remote=False):   {local_tool_count} tools")
    print(f"   Remote mode (use_remote=True):   {remote_tool_count} tools")
    print(f"   Explicit override (stand_alone=True): {explicit_tool_count} tools")
    
    # Verify expectations
    success = True
    
    if remote_tool_count <= local_tool_count:
        print("❌ FAILURE: Remote mode should have more tools than local mode!")
        success = False
    else:
        print("✅ SUCCESS: Remote mode has more tools than local mode")
    
    if explicit_tool_count <= local_tool_count:
        print("❌ FAILURE: Explicit override should have more tools than local mode!")
        success = False
    else:
        print("✅ SUCCESS: Explicit override works correctly")
    
    if success:
        print("\n🎉 All tests passed! The --remote flag correctly toggles alltools parameter.")
        print(f"   - Local mode: {local_tool_count} tools (team mode)")
        print(f"   - Remote mode: {remote_tool_count} tools (standalone mode)")
        print(f"   - Difference: {remote_tool_count - local_tool_count} additional tools in remote mode")
    else:
        print("\n💥 Tests failed! The --remote flag is not working as expected.")
    
    return success


async def main():
    """Main test function."""
    print("🚀 Starting --remote flag alltools toggle test...")
    
    try:
        success = await test_remote_alltools_toggle()
        
        if success:
            print("\n🎉 All tests passed! The --remote flag functionality is working correctly.")
            return 0
        else:
            print("\n💥 Tests failed! The --remote flag is not working as expected.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
