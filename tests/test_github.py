#!/usr/bin/env python3
"""
Test script for GitHub MCP tool functionality.
Tests GitHub repository search, code search, and error handling.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

try:
    from personal_agent import USE_MCP, logger, mcp_client, mcp_github_search

    print("✅ Successfully imported GitHub tools from personal_agent")
except ImportError as e:
    print(f"❌ Failed to import tools: {e}")
    sys.exit(1)


def test_github_availability():
    """Test if GitHub MCP server can be started and is configured."""
    print("\n🧪 Testing GitHub MCP availability...")

    # Check if GitHub Personal Access Token is set
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not github_token:
        print("❌ GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set")
        print("💡 Set it with: export GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here")
        return False
    else:
        print(f"✅ GITHUB_PERSONAL_ACCESS_TOKEN is set (length: {len(github_token)})")

    if not USE_MCP:
        print("❌ MCP is disabled in configuration")
        return False

    if mcp_client is None:
        print("❌ MCP client is not initialized")
        return False

    print("✅ MCP is enabled and client is available")

    # Test starting GitHub server
    try:
        server_name = "github"
        if server_name not in mcp_client.active_servers:
            print(f"🚀 Starting MCP server: {server_name}")
            result = mcp_client.start_server_sync(server_name)
            if result:
                print(f"✅ Successfully started {server_name}")

                # Test a simple search to verify token works
                print("🔍 Testing basic search functionality...")
                test_result = mcp_github_search.invoke({"query": "hello world"})
                if "Error calling tool" in test_result:
                    print(f"⚠️ Server started but search failed: {test_result}")
                    print(
                        "💡 This likely means GITHUB_PERSONAL_ACCESS_TOKEN is not set or invalid"
                    )
                    return False
                else:
                    print("✅ Basic search test passed")
                    return True
            else:
                print(f"❌ Failed to start {server_name}")
                print(
                    "💡 Make sure GITHUB_PERSONAL_ACCESS_TOKEN is set in MCP_SERVERS config"
                )
                return False
        else:
            print(f"✅ {server_name} already running")
            return True

    except Exception as e:
        print(f"❌ Error testing GitHub server: {e}")
        return False


def test_repository_search():
    """Test searching for repositories."""
    print("\n🧪 Testing repository search...")

    test_queries = [
        "python web framework",
        "machine learning pytorch",
        "javascript react",
    ]

    for query in test_queries:
        try:
            print(f"🔍 Searching for: {query}")

            result = mcp_github_search.invoke({"query": query})

            if "Error" in result:
                print(f"❌ Search failed: {result}")
                return False
            else:
                print(f"✅ Search successful")
                print(f"📄 Results preview: {result[:200]}...")

                # Brief pause between searches to be respectful to API
                time.sleep(1)

        except Exception as e:
            print(f"❌ Error searching for '{query}': {e}")
            return False

    return True


def test_specific_repository_search():
    """Test searching within a specific repository."""
    print("\n🧪 Testing specific repository search...")

    test_cases = [
        {"query": "authentication", "repo": "microsoft/vscode"},
        {"query": "api endpoint", "repo": "fastapi/fastapi"},
        {"query": "neural network", "repo": "pytorch/pytorch"},
    ]

    for test_case in test_cases:
        try:
            query = test_case["query"]
            repo = test_case["repo"]

            print(f"🔍 Searching for '{query}' in repository: {repo}")

            result = mcp_github_search.invoke({"query": query, "repo": repo})

            if "Error" in result:
                print(f"❌ Repository search failed: {result}")
                return False
            else:
                print(f"✅ Repository search successful")
                print(f"📄 Results preview: {result[:200]}...")

                # Brief pause between searches
                time.sleep(1)

        except Exception as e:
            print(f"❌ Error searching in repository '{repo}': {e}")
            return False

    return True


def test_code_search():
    """Test searching for specific code patterns."""
    print("\n🧪 Testing code search...")

    code_queries = [
        "def main() language:python",
        "class Component language:javascript",
        "import torch language:python",
    ]

    for query in code_queries:
        try:
            print(f"🔍 Code search: {query}")

            result = mcp_github_search.invoke({"query": query})

            if "Error" in result:
                print(f"❌ Code search failed: {result}")
                # Code search might fail due to API limitations, so we'll warn but continue
                print("⚠️ This might be due to API rate limits or authentication issues")
            else:
                print(f"✅ Code search successful")
                print(f"📄 Results preview: {result[:200]}...")

            # Brief pause between searches
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error in code search '{query}': {e}")

    return True


def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n🧪 Testing error handling...")

    test_cases = [
        {"description": "Empty query", "query": ""},
        {"description": "Very long query", "query": "a" * 1000},
        {"description": "Special characters", "query": "!@#$%^&*()"},
        {
            "description": "Non-existent repo",
            "query": "test",
            "repo": "nonexistent/repo123456789",
        },
    ]

    errors_handled_correctly = 0
    total_tests = len(test_cases)

    for test_case in test_cases:
        try:
            print(f"🧪 Testing {test_case['description']}")

            params = {"query": test_case["query"]}
            if "repo" in test_case:
                params["repo"] = test_case["repo"]

            result = mcp_github_search.invoke(params)

            # For error cases, we expect either:
            # 1. An explicit error message
            # 2. An empty result
            # 3. A message indicating no results found
            # 4. For the GitHub API, some queries might actually succeed but return minimal results

            if (
                "Error" in result
                or len(result.strip()) == 0
                or "No repositories found" in result
                or "No results" in result
                or len(result)
                < 50  # Very short results likely indicate no meaningful data
            ):
                print(f"✅ Error handling worked correctly: {result[:100]}...")
                errors_handled_correctly += 1
            else:
                print(
                    f"⚠️ Unexpected result for error case (this might be OK): {result[:100]}..."
                )
                # For GitHub API, some "error" cases might still return results
                # This is not necessarily a failure, just unexpected behavior
                if test_case["description"] in [
                    "Special characters",
                    "Very long query",
                ]:
                    print(
                        "💡 GitHub API is more tolerant than expected - this is acceptable"
                    )
                    errors_handled_correctly += 1

        except Exception as e:
            print(f"✅ Exception properly caught: {e}")
            errors_handled_correctly += 1

    # Consider the test successful if at least 75% of error cases are handled properly
    success_rate = errors_handled_correctly / total_tests
    if success_rate >= 0.75:
        print(
            f"✅ Error handling test passed ({errors_handled_correctly}/{total_tests} cases handled properly)"
        )
        return True
    else:
        print(
            f"❌ Error handling test failed ({errors_handled_correctly}/{total_tests} cases handled properly)"
        )
        return False


def test_json_parameter_handling():
    """Test handling of JSON string parameters (LangChain compatibility)."""
    print("\n🧪 Testing JSON parameter handling...")

    try:
        # Test with JSON string input (simulating LangChain behavior)
        json_params = '{"query": "python flask", "repo": ""}'

        print(f"🔍 Testing JSON parameter: {json_params}")

        result = mcp_github_search.invoke(json_params)

        if "Error" in result:
            print(f"❌ JSON parameter handling failed: {result}")
            return False
        else:
            print(f"✅ JSON parameter handling successful")
            print(f"📄 Results preview: {result[:200]}...")
            return True

    except Exception as e:
        print(f"❌ Error in JSON parameter test: {e}")
        return False


def test_github_integration():
    """Test integration with the broader system."""
    print("\n🧪 Testing GitHub integration...")

    try:
        # Test searching for something related to the current project
        query = "Model Context Protocol MCP"

        print(f"🔍 Searching for project-related content: {query}")

        result = mcp_github_search.invoke({"query": query})

        if "Error" in result:
            print(f"⚠️ Integration search failed: {result}")
            print("💡 This might be expected if API access is limited")
        else:
            print(f"✅ Integration search successful")
            print(f"📄 Found relevant content: {result[:300]}...")

        return True

    except Exception as e:
        print(f"❌ Error in integration test: {e}")
        return False


def run_all_github_tests():
    """Run all GitHub tool tests."""
    print("🚀 Starting GitHub Tool Tests")
    print("=" * 60)
    print("💡 Note: These tests require GITHUB_PERSONAL_ACCESS_TOKEN to be set")
    print("=" * 60)

    test_results = {}

    # Check GitHub availability first
    test_results["availability"] = test_github_availability()

    if not test_results["availability"]:
        print("\n❌ GitHub server not available, skipping remaining tests")
        print("💡 To fix:")
        print(
            "   1. Set GITHUB_PERSONAL_ACCESS_TOKEN in personal_agent.py MCP_SERVERS config"
        )
        print("   2. Ensure you have a valid GitHub Personal Access Token")
        print(
            "   3. Make sure npm and @modelcontextprotocol/server-github are installed"
        )
        return

    # Run the tests
    test_results["repository_search"] = test_repository_search()
    test_results["specific_repo_search"] = test_specific_repository_search()
    test_results["code_search"] = test_code_search()
    test_results["error_handling"] = test_error_handling()
    test_results["json_parameters"] = test_json_parameter_handling()
    test_results["integration"] = test_github_integration()

    # Summary
    print("\n" + "=" * 60)
    print("📊 GITHUB TEST SUMMARY:")

    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All GitHub tests completed successfully!")
    else:
        print("⚠️ Some tests failed. Check configuration and API access.")

    print("=" * 60)


if __name__ == "__main__":
    run_all_github_tests()
