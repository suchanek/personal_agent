#!/usr/bin/env python3
"""Test script to verify filesystem path mapping works correctly."""

import os
import sys
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from personal_agent.config import HOME_DIR, ROOT_DIR, DATA_DIR, get_mcp_servers
from personal_agent.core.mcp_client import SimpleMCPClient
from personal_agent.tools import filesystem


def test_path_mapping():
    """Test that path mapping works correctly for different scenarios."""

    print("=== Testing Filesystem Path Mapping ===")
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

    # Test cases for different paths
    test_paths = [
        "/home/egs",  # Linux-style home path
        "~/Documents",  # Tilde expansion
        HOME_DIR,  # Actual home directory
        f"{HOME_DIR}/Documents",  # Path within home
        "/etc/passwd",  # System file (should use root server)
        f"{DATA_DIR}/test.txt",  # Data directory file
        "data/test.txt",  # Relative data path
    ]

    print("=== Testing Directory Listing ===")
    for path in test_paths:
        print(f"\nTesting path: {path}")
        try:
            result = filesystem.mcp_list_directory(path)
            if "Error:" in result:
                print(f"  Result: {result}")
            else:
                print(f"  Success: Listed {len(result.split())} items")
        except Exception as e:
            print(f"  Exception: {e}")

    print("\n=== Testing File Reading ===")
    # Test reading a common file that should exist
    test_file = f"{HOME_DIR}/.bashrc"
    if os.path.exists(test_file):
        print(f"\nTesting file read: {test_file}")
        try:
            result = filesystem.mcp_read_file(test_file)
            if "Error:" in result:
                print(f"  Result: {result}")
            else:
                print(f"  Success: Read {len(result)} characters")
        except Exception as e:
            print(f"  Exception: {e}")
    else:
        print(f"\nSkipping file read test - {test_file} does not exist")


if __name__ == "__main__":
    test_path_mapping()
