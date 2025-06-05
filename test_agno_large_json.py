#!/usr/bin/env python3
"""Test agno tool with raw JSON output."""

import sys
from pathlib import Path

# Add the package path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import personal_agent
from agno import Agent
from agno.tools import tool


@tool
def test_large_json_output(query: str) -> str:
    """
    Test tool that returns large JSON output like GitHub API.

    Args:
        query: Test query

    Returns:
        str: Large JSON response
    """
    # Get a real GitHub response
    mcp_client = personal_agent.mcp_client

    if mcp_client is None:
        return "MCP client not available"

    try:
        server_name = "github"
        if server_name not in mcp_client.active_servers:
            mcp_client.start_server_sync(server_name)

        # Get raw GitHub response
        result = mcp_client.call_tool_sync(server_name, "search_issues", {"q": query})
        return result

    except Exception as e:
        return f"Error: {str(e)}"


def test_agno_with_large_json():
    """Test if agno can handle large JSON responses."""

    print("=== Testing agno with Large JSON Output ===")

    try:
        # Create a simple agent
        agent = Agent(model="gpt-4o-mini", tools=[test_large_json_output], max_steps=2)

        # Test with a query that returns large JSON
        print("\n🤖 Running agno agent with large JSON tool...")
        result = agent.run(
            "Search for 'python' on GitHub and tell me how many results were found"
        )

        print(f"\n✅ Agent completed successfully!")
        print(f"Result: {result}")

        return True

    except Exception as e:
        print(f"\n❌ Agent failed with error: {e}")
        print(f"Error type: {type(e)}")
        return False


if __name__ == "__main__":
    success = test_agno_with_large_json()
