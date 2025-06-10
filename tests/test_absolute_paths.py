#!/usr/bin/env python3
"""Test absolute paths with MCP servers."""

import os
import sys

# Add src to path so we can import our modules
sys.path.insert(0, "src")

from personal_agent.config import DATA_DIR, HOME_DIR, get_mcp_servers
from personal_agent.core.mcp_client import SimpleMCPClient


def test_absolute_paths():
    """Test using absolute paths with MCP servers."""

    print("=== Testing Absolute Paths with MCP ===")

    # Initialize MCP client
    server_configs = get_mcp_servers()
    mcp_client = SimpleMCPClient(server_configs)

    print("\n1. Testing filesystem-home with absolute paths inside HOME_DIR")
    server_name = "filesystem-home"

    # Start the server
    if server_name not in mcp_client.active_servers:
        result = mcp_client.start_server_sync(server_name)
        print(f"   Server start result: {result}")

    # Test paths using full absolute paths within HOME_DIR
    home_test_paths = [
        "/Users/egs",  # Root of home server
        "/Users/egs/Documents",  # Documents folder
        "/Users/egs/repos",  # Repos folder
        "/Users/egs/.bashrc",  # A typical file (might not exist)
    ]

    for abs_path in home_test_paths:
        # Convert absolute path to relative path for the server
        if abs_path.startswith(HOME_DIR):
            rel_path = abs_path[len(HOME_DIR) :].lstrip("/")
            if not rel_path:
                rel_path = "."
        else:
            rel_path = abs_path

        print(f"\n   Absolute path: {abs_path}")
        print(f"   Relative path for server: '{rel_path}'")

        try:
            # Try list_directory for directories, read_file for files
            if abs_path.endswith((".bashrc", ".txt", ".md")):
                # Try reading as file
                result = mcp_client.call_tool_sync(
                    server_name, "read_file", {"path": rel_path}
                )
                if "Error:" in result or "error" in result.lower():
                    print(f"     Read result: {result}")
                else:
                    print(f"     Success: Read {len(result)} characters")
            else:
                # Try listing as directory
                result = mcp_client.call_tool_sync(
                    server_name, "list_directory", {"path": rel_path}
                )
                if "Error:" in result or "error" in result.lower():
                    print(f"     List result: {result}")
                else:
                    lines = result.strip().split("\n") if result.strip() else []
                    print(f"     Success: Listed {len(lines)} items")
                    if lines:
                        print(f"     Sample: {lines[:3]}")
        except Exception as e:
            print(f"     Exception: {e}")

    print(f"\n2. Testing if MCP server working directory is the issue")
    print(f"Current working directory: {os.getcwd()}")
    print(f"HOME_DIR from config: {HOME_DIR}")
    print(f"Expected server root: {HOME_DIR}")

    # Let's try to understand what the server thinks is the root
    print(f"\n3. Testing with different relative path interpretations")

    # If the server root is actually HOME_DIR, then listing "." should list HOME_DIR contents
    # Let's see what happens with paths that exist in different interpretations

    potential_roots = [
        ("Current working dir", os.getcwd()),
        ("Home directory", HOME_DIR),
        ("System root", "/"),
    ]

    for desc, root in potential_roots:
        print(f"\n   If server root is {desc} ({root}):")
        if os.path.exists(root):
            try:
                items = os.listdir(root)[:5]
                print(f"     Contains: {items}")
            except Exception as e:
                print(f"     Error listing: {e}")


if __name__ == "__main__":
    test_absolute_paths()
