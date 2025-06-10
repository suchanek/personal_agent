#!/usr/bin/env python3
"""Test the updated GitHub tools in smol_tools.py"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config.mcp_servers import MCP_SERVERS
from personal_agent.core.mcp_client import SimpleMCPClient
from personal_agent.tools.smol_tools import (
    github_repository_info,
    github_search_repositories,
    set_mcp_client,
)


def test_github_tools():
    """Test the GitHub tools with various scenarios."""
    print("🧪 Testing GitHub Tools in smol_tools.py")
    print("=" * 50)

    # Initialize MCP client
    print("🔧 Initializing MCP client...")
    mcp_client = SimpleMCPClient(MCP_SERVERS)
    set_mcp_client(mcp_client)
    print("✅ MCP client initialized")

    # Test cases
    test_cases = [
        {
            "name": "Repository Info - microsoft/vscode",
            "function": github_repository_info,
            "args": ["microsoft/vscode"],
        },
        {
            "name": "Repository Search - search for pytorch",
            "function": github_search_repositories,
            "args": ["pytorch"],
        },
        {
            "name": "Repository Info with Search - tell me about",
            "function": github_search_repositories,
            "args": ["info", "microsoft/vscode"],
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)

        try:
            if len(test_case["args"]) == 1:
                result = test_case["function"](test_case["args"][0])
            else:
                result = test_case["function"](*test_case["args"])

            # Truncate result for readability
            result_preview = result[:500] + "..." if len(result) > 500 else result
            print(f"✅ Success:")
            print(result_preview)

        except Exception as e:
            print(f"❌ Error: {e}")

        print()

    # Cleanup
    print("🧹 Cleaning up...")
    try:
        mcp_client.stop_all_servers()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


if __name__ == "__main__":
    test_github_tools()
