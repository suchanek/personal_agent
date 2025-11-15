#!/usr/bin/env python3
"""Test script to check availability of all MCP servers."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

try:
    from personal_agent.config.mcp_servers import MCP_SERVERS
except ImportError as e:
    print(f"❌ Failed to import MCP server configurations: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


# Load environment variables from .env file if it exists
def load_env_file():
    """Load environment variables from .env file."""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


def load_mcp_config() -> Dict[str, Dict]:
    """Load MCP server configurations from mcp_servers.py."""
    return MCP_SERVERS


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

    # Load environment variables from .env file
    load_env_file()

    # Load server configurations from mcp_servers.py
    mcp_configs = load_mcp_config()

    if not mcp_configs:
        print("❌ No MCP server configurations found")
        return 1

    # Separate servers by whether they need API tokens
    no_token_servers = [
        "filesystem-home",
        "filesystem-data",
        "filesystem-root",
        "puppeteer",
    ]
    api_servers = ["github", "brave-search"]

    results = []
    available_count = 0
    total_tested = 0

    print("Testing servers without API requirements...")
    print("-" * 30)

    # Test servers that don't require API tokens
    for server_name in no_token_servers:
        if server_name not in mcp_configs:
            print(f"❌ {server_name}: Not found in MCP configuration")
            continue

        config = mcp_configs[server_name]
        total_tested += 1

        # Add description based on server type
        descriptions = {
            "filesystem-home": "Access home directory filesystem operations",
            "filesystem-data": "Access data directory for vector database",
            "filesystem-root": "Access root directory filesystem operations",
            "puppeteer": "Browser automation and web content fetching",
        }

        env = config.get("env")
        if env:
            # Convert env dict to proper environment variables
            test_env = os.environ.copy()
            test_env.update(env)
        else:
            test_env = None

        success, message = test_mcp_server(
            server_name, config["command"], config["args"], test_env
        )

        results.append(
            (server_name, success, message, descriptions.get(server_name, "Unknown"))
        )
        if success:
            available_count += 1

        print(message)
        print(f"   📝 {descriptions.get(server_name, 'Unknown')}")
        print()

    print("\nTesting API-required servers...")
    print("-" * 30)

    # Test API servers with their configured tokens
    for server_name in api_servers:
        if server_name not in mcp_configs:
            print(f"❌ {server_name}: Not found in MCP configuration")
            continue

        config = mcp_configs[server_name]
        total_tested += 1

        # Add description based on server type
        descriptions = {
            "github": "GitHub repository operations",
            "brave-search": "Web search operations",
        }

        # Check if API keys are configured
        env_vars = config.get("env", {})
        missing_keys = []

        if server_name == "github" and not env_vars.get("GITHUB_PERSONAL_ACCESS_TOKEN"):
            missing_keys.append("GITHUB_PERSONAL_ACCESS_TOKEN")
        elif server_name == "brave-search" and not env_vars.get("BRAVE_API_KEY"):
            missing_keys.append("BRAVE_API_KEY")

        if missing_keys:
            message = f"❌ {server_name}: Missing API key(s): {', '.join(missing_keys)}"
            results.append(
                (server_name, False, message, descriptions.get(server_name, "Unknown"))
            )
            print(message)
            print(f"   📝 {descriptions.get(server_name, 'Unknown')}")
            print()
            continue

        # Test with configured environment
        test_env = os.environ.copy()
        test_env.update(env_vars)

        success, message = test_mcp_server(
            server_name, config["command"], config["args"], test_env
        )

        results.append(
            (server_name, success, message, descriptions.get(server_name, "Unknown"))
        )
        if success:
            available_count += 1

        print(message)
        print(f"   📝 {descriptions.get(server_name, 'Unknown')}")
        print()

    # Summary
    print("=" * 50)
    print(f"📊 Summary: {available_count}/{total_tested} servers available and working")
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

    if unavailable_servers:
        print("💡 To install missing servers:")
        print("   npm install -g @modelcontextprotocol/server-filesystem")
        print("   npm install -g @modelcontextprotocol/server-github")
        print("   npm install -g @modelcontextprotocol/server-brave-search")
        print("   npm install -g @modelcontextprotocol/server-puppeteer")
        print()

    print("🔑 API Key Configuration:")
    print("   • GitHub: Configure GITHUB_PERSONAL_ACCESS_TOKEN in .env file")
    print("   • Brave Search: Configure BRAVE_API_KEY in .env file")

    if available_count == total_tested:
        print("🎉 All MCP servers are available and working!")
        return 0
    else:
        print(f"⚠️  {total_tested - available_count} servers need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
