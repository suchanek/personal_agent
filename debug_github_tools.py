#!/usr/bin/env python3
"""Debug GitHub MCP tools availability."""

import asyncio
import json
import logging
import subprocess
import time

from personal_agent.config.mcp_servers import get_mcp_servers

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_github_mcp():
    """Test GitHub MCP server directly."""

    # Start GitHub MCP server
    mcp_servers = get_mcp_servers()
    github_config = mcp_servers["github"]

    print("Starting GitHub MCP server...")
    print(f"Command: {github_config['command']} {' '.join(github_config['args'])}")

    try:
        process = subprocess.Popen(
            [github_config["command"]] + github_config["args"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=github_config.get("env", {}),
        )

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "debug-client", "version": "1.0.0"},
            },
        }

        print("Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print("Initialize response:", json.dumps(response, indent=2))

        # Send tools/list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        print("Sending tools/list request...")
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()

        # Read tools response
        tools_response_line = process.stdout.readline()
        if tools_response_line:
            tools_response = json.loads(tools_response_line.strip())
            print("Tools response:", json.dumps(tools_response, indent=2))

            if "result" in tools_response and "tools" in tools_response["result"]:
                print("\nAvailable tools:")
                for tool in tools_response["result"]["tools"]:
                    print(
                        f"  - {tool['name']}: {tool.get('description', 'No description')}"
                    )

        # Cleanup
        process.terminate()
        process.wait(timeout=5)

    except Exception as e:
        print(f"Error: {e}")
        if "process" in locals():
            process.terminate()


if __name__ == "__main__":
    asyncio.run(test_github_mcp())
