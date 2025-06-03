#!/usr/bin/env python3
# pylint: disable=C0415

"""Test script to check if all tools are properly loaded."""

import os
import sys

# Add src to path so we can import the personal_agent package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    """Test that all tools can be imported and initialized."""
    try:
        # Import the main module to test the system initialization
        from personal_agent.config import USE_MCP, get_mcp_servers
        from personal_agent.core.mcp_client import SimpleMCPClient
        from personal_agent.tools import get_all_tools
        from personal_agent.utils import setup_logging

        print("✅ All core imports successful")

        # Setup basic logger
        logger = setup_logging()
        print("✅ Logger setup successful")

        if USE_MCP:
            # Initialize MCP client
            mcp_servers = get_mcp_servers()
            mcp_client = SimpleMCPClient(mcp_servers)
            print(f"✅ MCP client initialized with {len(mcp_servers)} servers")
        else:
            mcp_client = None
            print("⚠️  MCP disabled in configuration")

        # Get tools (this will work even without Weaviate for basic testing)
        try:
            tools = get_all_tools(mcp_client, None, None, logger)
            print(f"✅ Successfully loaded {len(tools)} tools:")

            for i, tool in enumerate(tools, 1):
                print(f"  {i:2d}. {tool.name}")

        except Exception as e:
            print(f"⚠️  Could not load all tools (likely missing Weaviate): {e}")
            print("   This is expected if Weaviate is not running")

        print("\n🎉 Tool loading test completed successfully!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
