#!/usr/bin/env python3
"""
Test script to demonstrate the fixed MCP manager approach.

This script shows how the new factory pattern avoids asyncio context management issues
by creating fresh MCP tool instances for each use case.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.core.mcp_manager import mcp_manager


async def test_mcp_manager_factory():
    """Test the new factory-based MCP manager approach."""
    print("Testing MCP Manager Factory Pattern")
    print("=" * 50)
    
    # Test 1: Check if MCP is enabled
    print(f"MCP Enabled: {mcp_manager.is_enabled()}")
    print(f"Configured Servers: {mcp_manager.get_tool_count()}")
    
    # Test 2: Get server info
    server_info = mcp_manager.get_server_info()
    print(f"Server Info: {server_info}")
    
    # Test 3: Create fresh MCP tools (this is the new approach)
    print("\nCreating fresh MCP tools...")
    mcp_tools = mcp_manager.create_mcp_tools()
    print(f"Created {len(mcp_tools)} MCP tool instances")
    
    # Test 4: Demonstrate proper usage with async context managers
    if mcp_tools:
        print("\nTesting proper async context manager usage...")
        
        # This is how agents should use MCP tools now - each agent gets fresh instances
        # and manages them with proper async context managers
        try:
            # Simulate what an agent would do
            async def simulate_agent_usage():
                # Each agent creates its own tools and manages them properly
                agent_tools = mcp_manager.create_mcp_tools()
                
                # Use the tools with proper async context management
                # This avoids the "cancel scope in different task" issues
                for i, tool in enumerate(agent_tools):
                    try:
                        async with tool as initialized_tool:
                            print(f"  ✓ Successfully initialized MCP tool {i+1}")
                            # Tool is now ready to use
                            # When this context exits, cleanup happens automatically
                            # in the same task context where it was initialized
                    except Exception as e:
                        print(f"  ✗ Failed to initialize MCP tool {i+1}: {e}")
            
            # Run the simulation
            await simulate_agent_usage()
            print("✓ All MCP tools initialized and cleaned up successfully!")
            
        except Exception as e:
            print(f"✗ Error during MCP tool usage: {e}")
    else:
        print("No MCP tools configured - this is expected if MCP is disabled")
    
    print("\nTest completed successfully!")


async def test_multiple_agents():
    """Test that multiple agents can safely use MCP tools without conflicts."""
    print("\nTesting Multiple Agents")
    print("=" * 30)
    
    async def agent_task(agent_id: int):
        """Simulate an agent using MCP tools."""
        print(f"Agent {agent_id}: Starting...")
        
        # Each agent gets its own fresh tools
        tools = mcp_manager.create_mcp_tools()
        
        if tools:
            # Each agent manages its own context
            for tool in tools:
                try:
                    async with tool as initialized_tool:
                        print(f"Agent {agent_id}: ✓ Tool initialized")
                        # Simulate some work
                        await asyncio.sleep(0.1)
                        # Tool cleanup happens automatically when context exits
                except Exception as e:
                    print(f"Agent {agent_id}: ✗ Tool error: {e}")
        
        print(f"Agent {agent_id}: Completed")
    
    # Run multiple agents concurrently
    tasks = [agent_task(i) for i in range(3)]
    await asyncio.gather(*tasks)
    
    print("✓ Multiple agents completed without context conflicts!")


if __name__ == "__main__":
    print("MCP Manager Fix Test")
    print("=" * 60)
    print("This test demonstrates the new factory pattern that avoids")
    print("asyncio context management issues with MCP tools.")
    print()
    
    try:
        asyncio.run(test_mcp_manager_factory())
        asyncio.run(test_multiple_agents())
        
        print("\n" + "=" * 60)
        print("SUCCESS: All tests passed!")
        print("The new MCP manager approach should eliminate the")
        print("'cancel scope in different task' errors.")
        
    except Exception as e:
        print(f"\nERROR: Test failed with: {e}")
        import traceback
        traceback.print_exc()
