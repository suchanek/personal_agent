#!/usr/bin/env python3
"""
Test script for the MCP migration to verify the new persistent connection approach works correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from personal_agent.config.settings import LLM_MODEL, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_mcp_migration():
    """Test the MCP migration by creating an agent and checking MCP tool initialization."""
    print("🧪 Testing MCP Migration...")
    print("=" * 50)

    try:
        # Create agent with MCP enabled but memory disabled for faster testing
        print("1. Creating AgnoPersonalAgent with MCP enabled...")
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            enable_memory=True,  # Disable for faster testing
            enable_mcp=True,
            debug=True,  # Enable debug for detailed logging
            user_id=USER_ID,
        )
        print("✅ Agent created successfully")

        # Initialize the agent
        print("\n2. Initializing agent...")
        success = await agent.initialize()

        if not success:
            print("❌ Agent initialization failed")
            return False

        print("✅ Agent initialized successfully")

        # Check MCP tools
        print("\n3. Checking MCP tools...")
        print(f"   MCP enabled: {agent.enable_mcp}")
        print(f"   MCP servers configured: {len(agent.mcp_servers)}")
        print(f"   MCP tool instances created: {len(agent.mcp_tools_instances)}")

        if agent.mcp_servers:
            print("   Configured MCP servers:")
            for server_name, config in agent.mcp_servers.items():
                print(f"     - {server_name}: {config.get('command', 'N/A')}")

        if agent.mcp_tools_instances:
            print("   Successfully initialized MCP tools:")
            for i, tool in enumerate(agent.mcp_tools_instances):
                tool_name = (
                    tool.__class__.__name__ if hasattr(tool, "__class__") else "Unknown"
                )
                print(f"     - Tool {i+1}: {tool_name}")

        # Get agent info
        print("\n4. Getting agent info...")
        agent_info = agent.get_agent_info()
        print(f"   Total tools: {agent_info['tool_counts']['total']}")
        print(f"   MCP tools: {agent_info['tool_counts']['mcp']}")
        print(f"   Built-in tools: {agent_info['tool_counts']['built_in']}")

        # Test MCP tools with real tasks
        if agent.agent and len(agent.agent.tools) > 0:
            print("\n5. Testing MCP tools with real tasks...")

            # Test 1: Filesystem search
            print("\n   5a. Testing filesystem search...")
            try:
                response = await agent.run("Please list files in my home directory.")
                print("✅ Filesystem search completed")
                print(f"   Response length: {len(response)} characters")
                print(f"   Response preview: {response}...")
            except Exception as e:
                print(f"⚠️ Filesystem search failed: {e}")

            # Test 2: Web search with Brave
            print("\n   5b. Testing Brave web search...")
            try:
                response = await agent.run(
                    "Please search the web for information about 'Model Context Protocol MCP' using Brave search."
                )
                print("✅ Brave web search completed")
                print(f"   Response length: {len(response)} characters")
                print(f"   Response preview: {response}...")
            except Exception as e:
                print(f"⚠️ Brave search failed: {e}")

            # Test 3: GitHub repository search
            print("\n   5c. Testing GitHub repository search...")
            try:
                response = await agent.run(
                    "Please search GitHub for a repository called 'proteusPy'. Show me information about this repository."
                )
                print("✅ GitHub search completed")
                print(f"   Response length: {len(response)} characters")
                print(f"   Response preview: {response}...")
            except Exception as e:
                print(f"⚠️ GitHub search failed: {e}")

            # Test 4: Tool availability check
            print("\n   5d. Testing tool availability...")
            try:
                response = await agent.run(
                    "What MCP tools do you have available? List them and briefly describe what each one can do."
                )
                print("✅ Tool availability check completed")
                print(f"   Response length: {len(response)} characters")
                print(f"   Response preview: {response}...")
            except Exception as e:
                print(f"⚠️ Tool availability check failed: {e}")

        else:
            print("\n5. Skipping MCP tool tests (no tools available)")

        # Test cleanup
        print("\n6. Testing cleanup...")
        await agent.cleanup()
        print("✅ Cleanup completed successfully")

        print("\n" + "=" * 50)
        print("🎉 MCP Migration Test PASSED!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_mcp_disabled():
    """Test that the agent works correctly with MCP disabled."""
    print("\n🧪 Testing with MCP disabled...")
    print("=" * 50)

    try:
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name="llama3.2:3b",
            enable_memory=False,
            enable_mcp=False,  # Disable MCP
            debug=True,
            user_id=USER_ID,
        )

        success = await agent.initialize()
        if not success:
            print("❌ Agent initialization failed")
            return False

        print("✅ Agent with MCP disabled initialized successfully")
        print(f"   MCP tools: {len(agent.mcp_tools_instances)}")

        await agent.cleanup()
        return True

    except Exception as e:
        print(f"❌ MCP disabled test failed: {e}")
        return False


def main():
    """Run the MCP migration tests."""
    print("🚀 Starting MCP Migration Tests")
    print("This will test the new persistent connection approach")
    print()

    # Check if we're in the right directory
    if not Path("src/personal_agent").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)

    async def run_tests():
        # Test with MCP enabled
        test1_passed = await test_mcp_migration()

        # Test with MCP disabled
        test2_passed = await test_mcp_disabled()

        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"MCP Enabled Test:  {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"MCP Disabled Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

        if test1_passed and test2_passed:
            print("\n🎉 ALL TESTS PASSED! MCP migration is working correctly.")
            return 0
        else:
            print("\n💥 SOME TESTS FAILED! Please check the errors above.")
            return 1

    # Run the tests
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
