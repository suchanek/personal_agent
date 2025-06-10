#!/usr/bin/env python3
"""Test the specific use case: 'tell me about repository X'"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config.mcp_servers import MCP_SERVERS
from personal_agent.core.mcp_client import SimpleMCPClient
from personal_agent.tools.smol_tools import github_repository_info, set_mcp_client


def test_tell_me_about_repository():
    """Test the specific use case that was failing before."""
    print("🎯 Testing: 'Tell me about repository X' use case")
    print("=" * 60)

    # Initialize MCP client
    print("🔧 Initializing MCP client...")
    mcp_client = SimpleMCPClient(MCP_SERVERS)
    set_mcp_client(mcp_client)
    print("✅ MCP client initialized")

    # Test the exact use case that was failing
    test_cases = [
        {"query": "Tell me about microsoft/vscode", "repo": "microsoft/vscode"},
        {"query": "Tell me about pytorch/pytorch", "repo": "pytorch/pytorch"},
        {"query": "Tell me about golang/go", "repo": "golang/go"},
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['query']}")
        print("-" * 50)

        try:
            # Use the github_repository_info tool directly
            result = github_repository_info(test_case["repo"])

            # Show a preview of the result
            if len(result) > 800:
                print("✅ Success - Repository info retrieved:")
                print(result[:800] + "...")

                # Check for key sections
                sections_found = []
                if "## Repository Info" in result:
                    sections_found.append("Repository Info")
                if "## README" in result:
                    sections_found.append("README")
                if "## Repository Structure" in result:
                    sections_found.append("Repository Structure")
                if "## Recent Activity" in result:
                    sections_found.append("Recent Activity")

                print(f"\n📋 Sections found: {', '.join(sections_found)}")
            else:
                print(f"✅ Success: {result}")

        except Exception as e:
            print(f"❌ Error: {e}")

    # Cleanup
    print("\n🧹 Cleaning up...")
    try:
        mcp_client.stop_all_servers()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


if __name__ == "__main__":
    test_tell_me_about_repository()
