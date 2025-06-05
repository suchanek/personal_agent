#!/usr/bin/env python3
"""Test GitHub search without sanitization."""

import sys
from pathlib import Path

# Add the package path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import personal_agent
from agno.tools import tool


@tool
def github_search_raw(query: str, repo: str = "") -> str:
    """
    Test GitHub search without sanitization.

    Args:
        query: Search query terms
        repo: Optional specific repository to search within

    Returns:
        str: Raw search results
    """
    mcp_client = personal_agent.mcp_client

    if mcp_client is None:
        return "MCP client not available"

    try:
        server_name = "github"
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start GitHub server"

        # Raw search without sanitization
        if repo:
            params = {"q": f"repo:{repo} {query}"}
        else:
            params = {"q": query}

        result = mcp_client.call_tool_sync(server_name, "search_issues", params)

        # Return raw result
        return result

    except Exception as e:
        return f"Error: {str(e)}"


def test_raw_vs_sanitized():
    """Test raw output vs sanitized output."""

    print("=== Testing Raw vs Sanitized GitHub Search ===")

    # Import the sanitized version
    from personal_agent.tools.web import github_search

    query = "suchanek/proteusPy"

    print(f"\n1. 🔧 RAW GitHub search for '{query}':")
    raw_result = github_search_raw.entrypoint(query)
    print(f"Length: {len(raw_result) if isinstance(raw_result, str) else 'N/A'}")
    print(
        f"First 500 chars:\n{raw_result[:500] if isinstance(raw_result, str) else raw_result}"
    )

    print(f"\n2. ✨ SANITIZED GitHub search for '{query}':")
    sanitized_result = github_search.entrypoint(query)
    print(
        f"Length: {len(sanitized_result) if isinstance(sanitized_result, str) else 'N/A'}"
    )
    print(f"Result:\n{sanitized_result}")

    # Test if the raw JSON would cause issues with agno
    print(f"\n3. 🧪 Analysis:")
    print(
        f"- Raw result length: {len(raw_result) if isinstance(raw_result, str) else 'N/A'}"
    )
    print(
        f"- Sanitized result length: {len(sanitized_result) if isinstance(sanitized_result, str) else 'N/A'}"
    )

    if isinstance(raw_result, str):
        print(f"- Raw result starts with JSON: {raw_result.strip().startswith('{')}")
        print(f"- Raw result has newlines: {'\\n' in raw_result}")
        print(f"- Raw result very long: {len(raw_result) > 10000}")


if __name__ == "__main__":
    test_raw_vs_sanitized()
