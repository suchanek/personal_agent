#!/usr/bin/env python3
"""Test using absolute paths directly with MCP servers."""

import os
import sys

# Add src to path so we can import our modules
sys.path.insert(0, "src")

from personal_agent.config import get_mcp_servers, HOME_DIR, DATA_DIR
from personal_agent.core.mcp_client import SimpleMCPClient


def test_absolute_paths_direct():
    """Test using full absolute paths directly."""

    print("=== Testing Full Absolute Paths Directly ===")

    # Initialize MCP client
    server_configs = get_mcp_servers()
    mcp_client = SimpleMCPClient(server_configs)

    print("\n1. Testing filesystem-home with full absolute paths")
    server_name = "filesystem-home"

    # Start the server
    if server_name not in mcp_client.active_servers:
        result = mcp_client.start_server_sync(server_name)
        print(f"   Server start result: {result}")

    # Try using the exact absolute paths
    abs_test_paths = [
        "/Users/egs",
        "/Users/egs/Documents",
        "/Users/egs/repos",
        "/Users/egs/data",
    ]

    for abs_path in abs_test_paths:
        print(f"\n   Testing absolute path: {abs_path}")
        try:
            result = mcp_client.call_tool_sync(
                server_name, "list_directory", {"path": abs_path}
            )
            if "Error:" in result or "error" in result.lower():
                print(f"     Result: {result}")
            else:
                lines = result.strip().split("\n") if result.strip() else []
                print(f"     Success: Listed {len(lines)} items")
                if lines:
                    print(f"     Sample: {lines[:3]}")
        except Exception as e:
            print(f"     Exception: {e}")

    print(f"\n2. Testing filesystem-root with absolute paths")
    server_name = "filesystem-root"

    if server_name not in mcp_client.active_servers:
        result = mcp_client.start_server_sync(server_name)
        print(f"   Server start result: {result}")

    # Test with actual system paths
    root_abs_paths = [
        "/",
        "/Users",
        "/Users/egs",
        "/etc",
        "/tmp",
    ]

    for abs_path in root_abs_paths:
        print(f"\n   Testing root absolute path: {abs_path}")
        try:
            result = mcp_client.call_tool_sync(
                server_name, "list_directory", {"path": abs_path}
            )
            if "Error:" in result or "error" in result.lower():
                print(f"     Result: {result}")
            else:
                lines = result.strip().split("\n") if result.strip() else []
                print(f"     Success: Listed {len(lines)} items")
                if lines and len(lines) <= 5:
                    print(f"     Items: {lines}")
                elif lines:
                    print(f"     First few: {lines[:3]}")
        except Exception as e:
            print(f"     Exception: {e}")

    print(f"\n3. Key Discovery")
    print("If absolute paths work with filesystem-root but not filesystem-home,")
    print(
        "it suggests the MCP servers may expect absolute paths rather than relative ones."
    )


if __name__ == "__main__":
    test_absolute_paths_direct()
