#!/usr/bin/env python3
"""Test script to check availability of all MCP servers."""

import json
import subprocess
import sys
import time
from typing import Dict, List, Tuple


def test_mcp_server(
    server_name: str, command: str, args: List[str], env: Dict[str, str] = None
) -> Tuple[bool, str]:
    """Test if an MCP server is available and working."""
    try:
        print(f"Testing {server_name}...")

        # Start the MCP server process
        process = subprocess.Popen(
            [command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Give server a moment to start
        time.sleep(2)

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        # Send request
        request_json = json.dumps(init_request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()

        # Try to read response with timeout
        try:
            # Read response line
            response_line = process.stdout.readline()

            if response_line:
                response = json.loads(response_line.strip())
                if "result" in response:
                    # Server responded successfully
                    process.terminate()
                    return True, f"✅ {server_name}: Available and responding"
                elif "error" in response:
                    process.terminate()
                    return (
                        False,
                        f"❌ {server_name}: Server error - {response['error']}",
                    )

            # No response or invalid response
            process.terminate()
            return False, f"❌ {server_name}: No valid response"

        except json.JSONDecodeError:
            process.terminate()
            return False, f"❌ {server_name}: Invalid JSON response"
        except Exception as e:
            process.terminate()
            return False, f"❌ {server_name}: Error reading response - {e}"

    except FileNotFoundError:
        return False, f"❌ {server_name}: Command not found - {command}"
    except subprocess.TimeoutExpired:
        process.terminate()
        return False, f"❌ {server_name}: Timeout"
    except Exception as e:
        return False, f"❌ {server_name}: Error - {e}"


def main():
    """Test all MCP servers configured in the personal agent."""
    print("🔍 Testing MCP Server Availability")
    print("=" * 50)

    # Define servers that can be tested without API tokens
    servers = {
        "filesystem-home": {
            "command": "npx",
            "args": ["--yes", "@modelcontextprotocol/server-filesystem", "/Users/egs"],
            "description": "Access home directory filesystem operations",
        },
        "filesystem-data": {
            "command": "npx",
            "args": [
                "--yes",
                "@modelcontextprotocol/server-filesystem",
                "/Users/egs/data",
            ],
            "description": "Access data directory for vector database",
        },
        "filesystem-root": {
            "command": "npx",
            "args": ["--yes", "@modelcontextprotocol/server-filesystem", "/"],
            "description": "Access root directory filesystem operations",
        },
        "puppeteer": {
            "command": "npx",
            "args": ["--yes", "@modelcontextprotocol/server-puppeteer"],
            "description": "Browser automation and web content fetching",
        },
    }

    # Servers that require API tokens (not tested)
    api_servers = {
        "github": "GitHub repository operations (requires GITHUB_PERSONAL_ACCESS_TOKEN)",
        "brave-search": "Web search operations (requires BRAVE_API_KEY)",
    }

    results = []
    available_count = 0

    for server_name, config in servers.items():
        env = config.get("env", None)
        success, message = test_mcp_server(
            server_name, config["command"], config["args"], env
        )

        results.append((server_name, success, message, config["description"]))
        if success:
            available_count += 1

        print(message)
        print(f"   📝 {config['description']}")
        print()

    # Summary
    print("=" * 50)
    print(f"📊 Summary: {available_count}/{len(servers)} testable servers available")
    print()

    # Available servers
    available_servers = [r for r in results if r[1]]
    if available_servers:
        print("✅ Available Servers:")
        for name, _, _, desc in available_servers:
            print(f"   • {name}: {desc}")
        print()

    # Unavailable servers
    unavailable_servers = [r for r in results if not r[1]]
    if unavailable_servers:
        print("❌ Unavailable Servers:")
        for name, _, message, desc in unavailable_servers:
            print(f"   • {name}: {desc}")
            print(f"     Error: {message}")
        print()

    # API servers (not tested but available)
    print("🔑 API-Required Servers (installed but need tokens):")
    for server_name, description in api_servers.items():
        print(f"   • {server_name}: {description}")
    print()

    if unavailable_servers:
        print("💡 To install missing servers:")
        print("   npm install -g @modelcontextprotocol/server-github")
        print("   npm install -g @modelcontextprotocol/server-brave-search")
        print("   npm install -g @modelcontextprotocol/server-puppeteer")
        print()

    print("🔑 To enable API servers, configure these in your environment:")
    print("   • GitHub: Set GITHUB_PERSONAL_ACCESS_TOKEN")
    print("   • Brave Search: Set BRAVE_API_KEY")

    if available_count == len(servers):
        print("🎉 All MCP servers are available and working!")
        return 0
    else:
        print(f"⚠️  {len(servers) - available_count} servers need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
