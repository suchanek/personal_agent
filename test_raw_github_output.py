#!/usr/bin/env python3
"""Test script to see raw GitHub search output."""

import json
import logging
import sys
from pathlib import Path

# Add the package path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and initialize the package to get the global mcp_client
import personal_agent


def test_raw_github_output():
    """Test raw GitHub search output without sanitization."""

    print("=== Testing raw GitHub search output ===")

    # Get the global mcp_client from the package
    mcp_client = personal_agent.mcp_client

    if mcp_client is None:
        print("MCP client is None - package not initialized properly")
        return

    # Start GitHub server
    server_name = "github"
    if server_name not in mcp_client.active_servers:
        start_result = mcp_client.start_server_sync(server_name)
        if not start_result:
            print("Failed to start GitHub server")
            return

    # Test raw search_issues call
    print("\n1. Raw search_issues for 'suchanek/proteusPy':")
    try:
        result = mcp_client.call_tool_sync(
            server_name, "search_issues", {"q": "suchanek/proteusPy"}
        )
        print(f"Raw result type: {type(result)}")
        print(f"Raw result (first 2000 chars):\n{result[:2000]}")

        # Try to parse as JSON
        if isinstance(result, str) and result.strip().startswith("{"):
            try:
                parsed = json.loads(result)
                print(
                    f"\nParsed JSON keys: {parsed.keys() if isinstance(parsed, dict) else 'Not a dict'}"
                )
                if isinstance(parsed, dict) and "items" in parsed:
                    items = parsed["items"]
                    print(f"Number of items: {len(items)}")
                    if items:
                        first_item = items[0]
                        print(f"First item keys: {first_item.keys()}")
                        print(f"First item sample data:")
                        for key, value in list(first_item.items())[
                            :10
                        ]:  # First 10 keys
                            print(f"  {key}: {str(value)[:100]}")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_raw_github_output()
