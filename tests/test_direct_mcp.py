#!/usr/bin/env python3
"""Direct MCP test to understand path handling."""

import os
import sys

# Add src to path so we can import our modules
sys.path.insert(0, "src")

from personal_agent.config import get_mcp_servers
from personal_agent.core.mcp_client import SimpleMCPClient


def test_direct_mcp():
    """Test MCP servers directly."""

    print("=== Direct MCP Server Test ===")

    # Initialize MCP client
    server_configs = get_mcp_servers()
    mcp_client = SimpleMCPClient(server_configs)

    # Test filesystem-home server
    print("\n1. Testing filesystem-home server directly")
    server_name = "filesystem-home"

    # Start the server
    if server_name not in mcp_client.active_servers:
        result = mcp_client.start_server_sync(server_name)
        print(f"   Server start result: {result}")

    # Test different path variations
    test_paths = [".", "", "Documents", "repos", "repos/personal_agent"]

    for path in test_paths:
        print(f"\n   Testing path: '{path}'")
        try:
            result = mcp_client.call_tool_sync(
                server_name, "list_directory", {"path": path}
            )
            if "Error:" in result or "error" in result.lower():
                print(f"     Result: {result}")
            else:
                lines = result.strip().split("\n") if result.strip() else []
                print(f"     Success: {len(lines)} items")
                if lines:
                    print(f"     First few: {lines[:3]}")
        except Exception as e:
            print(f"     Exception: {e}")

    # Test the root server with /home/egs equivalent
    print(f"\n2. Testing filesystem-root server")
    server_name = "filesystem-root"

    if server_name not in mcp_client.active_servers:
        result = mcp_client.start_server_sync(server_name)
        print(f"   Server start result: {result}")

    # Test paths that should work with root access
    root_test_paths = ["Users/egs", "etc", "usr", "home"]

    for path in root_test_paths:
        print(f"\n   Testing root path: '{path}'")
        try:
            result = mcp_client.call_tool_sync(
                server_name, "list_directory", {"path": path}
            )
            if "Error:" in result or "error" in result.lower():
                print(f"     Result: {result}")
            else:
                lines = result.strip().split("\n") if result.strip() else []
                print(f"     Success: {len(lines)} items")
                if lines and len(lines) <= 5:
                    print(f"     Items: {lines}")
                elif lines:
                    print(f"     First few: {lines[:3]}")
        except Exception as e:
            print(f"     Exception: {e}")


if __name__ == "__main__":
    test_direct_mcp()
