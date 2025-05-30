#!/usr/bin/env python3
"""
Debug script to test GitHub MCP server directly.
"""

import json
import os
import subprocess
import sys
import time

# Add parent directory to path to import personal_agent
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

try:
    from personal_agent import USE_MCP, logger, mcp_client

    print("✅ Successfully imported from personal_agent")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)


def test_github_tool_directly():
    """Test GitHub tool directly with detailed error reporting."""
    print("🔍 Testing GitHub tool directly...")

    # Check environment variable
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not github_token:
        print("❌ GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set")
        return False
    else:
        print(f"✅ GITHUB_PERSONAL_ACCESS_TOKEN is set (length: {len(github_token)})")

    if not USE_MCP or mcp_client is None:
        print("❌ MCP is disabled or client not initialized")
        return False

    server_name = "github"

    # Start GitHub server if not already running
    if server_name not in mcp_client.active_servers:
        print(f"🚀 Starting MCP server: {server_name}")
        result = mcp_client.start_server_sync(server_name)
        if not result:
            print(f"❌ Failed to start {server_name}")
            return False
    else:
        print(f"✅ {server_name} already running")

    # Get the server process to check if it's actually running
    server_info = mcp_client.active_servers.get(server_name)
    if server_info:
        process = server_info["process"]
        print(f"📊 Server process poll: {process.poll()}")
        if process.poll() is not None:
            print("❌ Server process has terminated!")
            # Read stderr to see what went wrong
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"🔥 Server stderr: {stderr_output}")
            return False

    # Test a simple search
    print("🔍 Testing search_repositories tool...")
    try:
        # Make the request manually for better error reporting
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_repositories",
                "arguments": {"query": "hello world"},
            },
        }

        response = mcp_client._send_request_sync(server_name, request)
        print(f"📥 Raw response: {json.dumps(response, indent=2)}")

        if response:
            if "error" in response:
                print(f"❌ MCP Error: {response['error']}")
                return False
            elif "result" in response:
                content = response["result"].get("content", [])
                if content and len(content) > 0:
                    result_text = content[0].get("text", "No text")
                    print(f"✅ Search successful: {result_text[:200]}...")
                    return True
                else:
                    print(f"⚠️ No content in result: {response['result']}")
            else:
                print(f"⚠️ Unexpected response format: {response}")
        else:
            print("❌ No response from server")

    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback

        traceback.print_exc()

    return False


if __name__ == "__main__":
    test_github_tool_directly()
