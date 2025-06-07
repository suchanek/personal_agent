#!/usr/bin/env python3

import os
import sys

sys.path.append("/Users/egs/repos/personal_agent/src")

import logging

from personal_agent.core.mcp_client import MCPClient

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")


def test_mcp_directory_listing():
    """Test MCP directory listing with detailed debugging."""
    print("🔍 Testing MCP filesystem tool with enhanced debugging...")

    try:
        # Initialize MCP client
        client = MCPClient()

        # Test directory listing
        print("\n📁 Calling list_directory tool...")
        result = client.call_tool_sync(
            server_name="filesystem-home",
            tool_name="list_directory",
            arguments={"path": "/Users/egs"},
        )

        print(f"\n📋 Tool result type: {type(result)}")
        print(f"📋 Tool result length: {len(result) if result else 0}")
        print(f"📋 Tool result:\n{result}")

        # Also test a simple ls command
        print("\n📁 Calling shell tool with ls command...")
        result2 = client.call_tool_sync(
            server_name="filesystem-home",
            tool_name="shell",
            arguments={"command": "ls /Users/egs"},
        )

        print(f"\n📋 Shell result type: {type(result2)}")
        print(f"📋 Shell result length: {len(result2) if result2 else 0}")
        print(f"📋 Shell result:\n{result2}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_mcp_directory_listing()
