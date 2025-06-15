#!/usr/bin/env python3
"""Test script to verify the new path mapping logic with actual accessible directories."""

import os
import sys

# Add src to path so we can import our modules
sys.path.insert(0, "src")

from personal_agent.config import HOME_DIR, ROOT_DIR, DATA_DIR, get_mcp_servers
from personal_agent.core.mcp_client import SimpleMCPClient
from personal_agent.tools import filesystem


def test_accessible_paths():
    """Test paths that should be accessible."""

    print("=== Testing Accessible Filesystem Paths ===")
    print(f"ROOT_DIR: {ROOT_DIR}")
    print(f"HOME_DIR: {HOME_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print()

    # Initialize MCP client with proper config
    server_configs = get_mcp_servers()
    mcp_client = SimpleMCPClient(server_configs)

    # Inject dependencies
    filesystem.mcp_client = mcp_client

    # Create a simple logger class for testing
    class SimpleLogger:
        def debug(self, msg, *args):
            print(f"DEBUG: {msg % args if args else msg}")

        def info(self, msg, *args):
            print(f"INFO: {msg % args if args else msg}")

        def warning(self, msg, *args):
            print(f"WARNING: {msg % args if args else msg}")

        def error(self, msg, *args):
            print(f"ERROR: {msg % args if args else msg}")

    filesystem.logger = SimpleLogger()

    # Test with paths that should work
    print("=== Testing Home Directory Access ===")

    # Test home directory listing
    print(f"\n1. Testing HOME_DIR: {HOME_DIR}")
    try:
        result = filesystem.mcp_list_directory(HOME_DIR)
        if "Error:" in result:
            print(f"   Result: {result}")
        else:
            lines = result.strip().split("\n")
            print(f"   Success: Listed {len(lines)} items")
            # Show first few items
            for i, line in enumerate(lines[:5]):
                print(f"   - {line}")
            if len(lines) > 5:
                print(f"   ... and {len(lines) - 5} more items")
    except Exception as e:
        print(f"   Exception: {e}")

    # Test data directory
    print(f"\n2. Testing DATA_DIR: {DATA_DIR}")
    try:
        result = filesystem.mcp_list_directory(DATA_DIR)
        if "Error:" in result:
            print(f"   Result: {result}")
        else:
            lines = result.strip().split("\n")
            print(f"   Success: Listed {len(lines)} items")
            for line in lines[:5]:
                print(f"   - {line}")
    except Exception as e:
        print(f"   Exception: {e}")

    # Test ~ expansion
    print(f"\n3. Testing tilde expansion: ~")
    try:
        result = filesystem.mcp_list_directory("~")
        if "Error:" in result:
            print(f"   Result: {result}")
        else:
            lines = result.strip().split("\n")
            print(f"   Success: Listed {len(lines)} items (same as HOME_DIR)")
    except Exception as e:
        print(f"   Exception: {e}")

    # Test reading a file that should exist
    print(f"\n4. Testing file read: PROJECT_SUMMARY.md")
    project_file = os.path.join(os.getcwd(), "PROJECT_SUMMARY.md")
    print(f"   Full path: {project_file}")
    try:
        result = filesystem.mcp_read_file(project_file)
        if "Error:" in result:
            print(f"   Result: {result}")
        else:
            print(f"   Success: Read {len(result)} characters")
            # Show first line
            first_line = result.split("\n")[0] if result else ""
            print(f"   First line: {first_line}")
    except Exception as e:
        print(f"   Exception: {e}")

    print("\n=== Path Mapping Behavior Summary ===")
    print("The new logic should:")
    print("1. Map /home/egs -> HOME_DIR (no hardcoded paths)")
    print("2. Use filesystem-home for paths within HOME_DIR")
    print("3. Use filesystem-root for paths outside HOME_DIR")
    print("4. Use filesystem-data for paths within DATA_DIR")
    print("5. Handle ~ expansion correctly")


if __name__ == "__main__":
    test_accessible_paths()
