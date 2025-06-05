#!/usr/bin/env python3
"""
Test script to verify GitHub search functionality is working correctly.

This script tests:
1. Keyword detection logic fix (no false positive for "pr" in "proteusPy")
2. Complete MCP integration
3. GitHub repository search functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import USE_MCP, get_mcp_servers
from personal_agent.core.mcp_client import SimpleMCPClient
from personal_agent.tools.web import github_search
from personal_agent.utils import setup_logging


def test_keyword_detection() -> None:
    """Test that keyword detection logic works correctly."""
    print("Testing keyword detection logic...")

    test_cases = [
        ("proteusPy", False, "Should NOT trigger issues search"),
        ("pr 123", True, "Should trigger issues search"),
        ("fix pr", True, "Should trigger issues search"),
        ("issue with code", True, "Should trigger issues search"),
        ("pull request bug", True, "Should trigger issues search"),
        ("protein research", False, "Should NOT trigger issues search"),
    ]

    keywords = ["issue", "bug", "feature", "pull request"]

    for query, expected, description in test_cases:
        keyword_match = any(keyword in query.lower() for keyword in keywords)
        pr_match = (
            " pr " in f" {query.lower()} "
            or query.lower().startswith("pr ")
            or query.lower().endswith(" pr")
        )
        should_use_issues = keyword_match or pr_match

        status = "✅" if should_use_issues == expected else "❌"
        print(f"{status} '{query}': {description} -> {should_use_issues}")


def test_github_search() -> None:
    """Test actual GitHub search functionality."""
    print("\nTesting GitHub search functionality...")

    if not USE_MCP:
        print("❌ MCP is disabled, cannot test GitHub search")
        return

    # Initialize MCP client
    mcp_servers = get_mcp_servers()
    mcp_client = SimpleMCPClient(mcp_servers)

    # Inject dependencies
    import personal_agent.tools.web as web

    web.mcp_client = mcp_client
    web.USE_MCP = True
    web.logger = setup_logging()

    # Test proteusPy search (should use search_repositories)
    print("Searching for 'proteusPy'...")
    try:
        result = github_search.entrypoint("proteusPy")
        if "suchanek/proteusPy" in result:
            print("✅ Found proteusPy repository")
        else:
            print("❌ proteusPy repository not found")
            print(f"Result: {result[:200]}...")
    except Exception as e:
        print(f"❌ Error searching for proteusPy: {e}")

    # Test issue search (should use search_issues)
    print("\nSearching for 'issue with authentication'...")
    try:
        result = github_search.entrypoint("issue with authentication")
        print("✅ Issue search completed")
        print(f"Result preview: {result[:100]}...")
    except Exception as e:
        print(f"❌ Error searching for issues: {e}")


def main() -> None:
    """Run all tests."""
    print("=" * 60)
    print("GitHub Search Fix Verification")
    print("=" * 60)

    test_keyword_detection()
    test_github_search()

    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    main()
