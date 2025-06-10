#!/usr/bin/env python3
"""Debug script to understand MCP server configurations."""

import os
import sys

# Add src to path so we can import our modules
sys.path.insert(0, "src")

from personal_agent.config import HOME_DIR, ROOT_DIR, DATA_DIR, get_mcp_servers


def debug_mcp_config():
    """Debug MCP server configurations."""

    print("=== MCP Server Configuration Debug ===")
    print(f"Environment Variables:")
    print(f"  ROOT_DIR: {ROOT_DIR}")
    print(f"  HOME_DIR: {HOME_DIR}")
    print(f"  DATA_DIR: {DATA_DIR}")
    print()

    server_configs = get_mcp_servers()

    print("MCP Server Configurations:")
    for name, config in server_configs.items():
        if "filesystem" in name:
            print(f"\n{name}:")
            print(f"  Command: {config['command']}")
            print(f"  Args: {config['args']}")
            print(f"  Description: {config['description']}")

            # The last argument should be the root directory for filesystem servers
            if config["args"] and len(config["args"]) > 2:
                root_dir = config["args"][-1]
                print(f"  Root Directory: {root_dir}")
                print(f"  Root Dir Exists: {os.path.exists(root_dir)}")
                if os.path.exists(root_dir):
                    try:
                        items = os.listdir(root_dir)
                        print(f"  Items in Root: {len(items)} items")
                        if items:
                            print(f"  Sample items: {items[:5]}")
                    except PermissionError:
                        print(f"  Permission denied to list {root_dir}")
                    except Exception as e:
                        print(f"  Error listing {root_dir}: {e}")

    print(f"\n=== Current Working Directory ===")
    cwd = os.getcwd()
    print(f"Current Working Directory: {cwd}")
    print(f"Items in CWD: {len(os.listdir(cwd))} items")

    print(f"\n=== Path Analysis ===")
    print("This explains why the MCP servers might be confused:")
    print("1. filesystem-home should have root at HOME_DIR")
    print("2. filesystem-data should have root at DATA_DIR")
    print("3. filesystem-root should have root at ROOT_DIR (full filesystem)")
    print()
    print("Current actual configuration:")
    for name, config in server_configs.items():
        if "filesystem" in name and config["args"] and len(config["args"]) > 2:
            root_dir = config["args"][-1]
            print(f"  {name}: {root_dir}")


if __name__ == "__main__":
    debug_mcp_config()
