#!/usr/bin/env python3
"""Debug script to list all available tools from the GitHub MCP server."""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config.settings import get_env_var
from personal_agent.core.mcp_client import SimpleMCPClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_github_tools():
    """
    Debug function to list all available tools from GitHub MCP server.

    :return: None
    """
    print("🔍 Debugging GitHub MCP Server Tools")
    print("=" * 50)

    # Check if GitHub token is available
    github_token = get_env_var("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not github_token:
        print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set")
        return

    print("✅ GitHub token found")

    # Initialize MCP client with server configs
    from personal_agent.config.mcp_servers import MCP_SERVERS

    mcp_client = SimpleMCPClient(MCP_SERVERS)

    try:
        # Start the GitHub server
        print("\n📡 Starting GitHub MCP server...")
        server_name = "github"

        # Start server using existing config
        success = mcp_client.start_server_sync(server_name)

        if not success:
            print("❌ Failed to start GitHub server")
            return

        print("✅ GitHub server started successfully")

        # List all available tools
        print("\n🛠️ Available tools:")
        print("-" * 30)

        tools = mcp_client.list_tools_sync(server_name)

        if tools:
            for i, tool in enumerate(tools, 1):
                name = tool.get("name", "Unknown")
                description = tool.get("description", "No description")
                print(f"{i}. {name}")
                print(f"   Description: {description}")

                # Show input schema if available
                if "inputSchema" in tool:
                    schema = tool["inputSchema"]
                    if "properties" in schema:
                        print(f"   Parameters:")
                        for param_name, param_info in schema["properties"].items():
                            param_type = param_info.get("type", "unknown")
                            param_desc = param_info.get("description", "")
                            required = param_name in schema.get("required", [])
                            req_marker = " (required)" if required else " (optional)"
                            print(f"     - {param_name}: {param_type}{req_marker}")
                            if param_desc:
                                print(f"       {param_desc}")
                print()
        else:
            print("❌ No tools found")

        # Test a simple repository info call if tools are available
        print("\n🧪 Testing repository tools...")
        try:
            # Try common GitHub API tools
            test_repo = "microsoft/vscode"

            tool_tests = [
                ("get_repository", {"owner": "microsoft", "repo": "vscode"}),
                ("get_repo", {"owner": "microsoft", "repo": "vscode"}),
                ("repository_info", {"repo": test_repo}),
                ("search_repositories", {"q": "microsoft vscode"}),
                ("search_repositories", {"query": "microsoft vscode"}),
            ]

            for tool_name, params in tool_tests:
                try:
                    result = mcp_client.call_tool_sync(server_name, tool_name, params)
                    print(f"✅ Tool '{tool_name}' works:")
                    print(f"   Params: {params}")
                    print(f"   Result: {str(result)[:300]}...")
                    break
                except Exception as e:
                    print(f"❌ Tool '{tool_name}' failed: {e}")

        except Exception as e:
            print(f"❌ Error testing tools: {e}")

    except Exception as e:
        logger.error("Error in debug_github_tools: %s", e)
        print(f"❌ Error: {e}")

    finally:
        # Cleanup
        try:
            mcp_client.stop_server_sync(server_name)
            print("\n🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


def debug_github_tools_sync():
    """
    Synchronous version for easier debugging.

    :return: None
    """
    print("🔍 Debugging GitHub MCP Server Tools (Sync)")
    print("=" * 50)

    # Check if GitHub token is available
    github_token = get_env_var("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not github_token:
        print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set")
        return

    print("✅ GitHub token found")

    # Initialize MCP client with server configs
    from personal_agent.config.mcp_servers import MCP_SERVERS

    mcp_client = SimpleMCPClient(MCP_SERVERS)

    try:
        # Start the GitHub server
        print("\n📡 Starting GitHub MCP server...")
        server_name = "github"

        # Start server using existing config
        success = mcp_client.start_server_sync(server_name)

        if not success:
            print("❌ Failed to start GitHub server")
            return

        print("✅ GitHub server started successfully")

        # List all available tools
        print("\n🛠️ Available tools:")
        print("-" * 30)

        tools = mcp_client.list_tools_sync(server_name)

        if tools:
            for i, tool in enumerate(tools, 1):
                name = tool.get("name", "Unknown")
                description = tool.get("description", "No description")
                print(f"{i}. {name}")
                print(f"   Description: {description}")

                # Show input schema if available
                if "inputSchema" in tool:
                    schema = tool["inputSchema"]
                    if "properties" in schema:
                        print(f"   Parameters:")
                        for param_name, param_info in schema["properties"].items():
                            param_type = param_info.get("type", "unknown")
                            param_desc = param_info.get("description", "")
                            required = param_name in schema.get("required", [])
                            req_marker = " (required)" if required else " (optional)"
                            print(f"     - {param_name}: {param_type}{req_marker}")
                            if param_desc:
                                print(f"       {param_desc}")
                print()
        else:
            print("❌ No tools found")

        # Test specific tools for repository information
        print("\n🧪 Testing repository tools...")
        test_repo_owner = "microsoft"
        test_repo_name = "vscode"

        tool_tests = [
            ("search_repositories", {"query": "microsoft vscode"}),
            (
                "get_file_contents",
                {"owner": test_repo_owner, "repo": test_repo_name, "path": "README.md"},
            ),
            (
                "list_commits",
                {
                    "owner": test_repo_owner,
                    "repo": test_repo_name,
                    "page": 1,
                    "perPage": 5,
                },
            ),
        ]

        for tool_name, params in tool_tests:
            try:
                result = mcp_client.call_tool_sync(server_name, tool_name, params)
                print(f"✅ Tool '{tool_name}' works:")
                print(f"   Params: {params}")
                print(f"   Result: {str(result)[:500]}...")
                print()
            except Exception as e:
                print(f"❌ Tool '{tool_name}' failed: {e}")

    except Exception as e:
        logger.error("Error in debug_github_tools_sync: %s", e)
        print(f"❌ Error: {e}")

    finally:
        # Cleanup
        try:
            mcp_client.stop_server_sync(server_name)
            print("\n🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_github_tools())
