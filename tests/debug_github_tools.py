#!/usr/bin/env python3
"""
Debug script to discover available tools on GitHub MCP server.
"""

import os
import sys

# Add parent directory to path to import personal_agent
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

try:
    from personal_agent import USE_MCP, logger, mcp_client

    print("✅ Successfully imported from personal_agent")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)


def discover_github_tools():
    """Discover what tools are available on the GitHub MCP server."""
    print("🔍 Discovering GitHub MCP server tools...")

    if not USE_MCP:
        print("❌ MCP is disabled")
        return

    if mcp_client is None:
        print("❌ MCP client is not initialized")
        return

    server_name = "github"

    # Start GitHub server if not already running
    if server_name not in mcp_client.active_servers:
        print(f"🚀 Starting MCP server: {server_name}")
        result = mcp_client.start_server_sync(server_name)
        if not result:
            print(f"❌ Failed to start {server_name}")
            return
    else:
        print(f"✅ {server_name} already running")

    # List available tools
    try:
        tools = mcp_client.list_tools_sync(server_name)

        if tools:
            print(f"\n📋 Available tools on {server_name} server:")
            print("=" * 50)
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
            print(f"❌ No tools found on {server_name} server")

    except Exception as e:
        print(f"❌ Error listing tools: {e}")


if __name__ == "__main__":
    discover_github_tools()
