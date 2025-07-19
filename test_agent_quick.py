#!/usr/bin/env python3
"""
Quick test to verify the MCP manager fix works in the actual agent.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.core.agno_agent import create_agno_agent


async def test_agent_initialization():
    """Test that the agent can initialize without MCP context errors."""
    print("🧪 Testing agent initialization with MCP manager fix...")
    
    try:
        # Create agent with minimal configuration to speed up testing
        agent = await create_agno_agent(
            debug=False,  # Disable debug to reduce output
            enable_memory=False,  # Disable memory to speed up init
            enable_mcp=True,  # Keep MCP enabled to test the fix
        )
        
        print("✅ Agent initialized successfully!")
        
        # Check that MCP tools were loaded
        if agent.agent and hasattr(agent.agent, 'tools'):
            tool_count = len(agent.agent.tools)
            mcp_tool_count = len(agent.mcp_tools_instances)
            print(f"📊 Agent has {tool_count} total tools ({mcp_tool_count} MCP tools)")
        
        # Test cleanup (this is where the old errors occurred)
        print("🧹 Testing cleanup...")
        await agent.cleanup()
        print("✅ Cleanup completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("MCP Manager Fix Verification Test")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_agent_initialization())
        
        if result:
            print("\n" + "=" * 50)
            print("🎉 SUCCESS: MCP manager fix is working!")
            print("The agent can initialize and cleanup without asyncio context errors.")
        else:
            print("\n" + "=" * 50)
            print("💥 FAILURE: Test failed - check the error output above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
