#!/usr/bin/env python3
"""Script to install all MCP servers required by the Personal AI Agent."""

import subprocess
import sys
from typing import Dict, List


def run_command(command: List[str], description: str) -> bool:
    """Run a command and return True if successful."""
    try:
        print(f"🔧 {description}...")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"   Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ {description} - Command not found: {command[0]}")
        return False


def check_prerequisites() -> bool:
    """Check if required tools are available."""
    print("🔍 Checking prerequisites...")

    # Check Node.js
    try:
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        )
        print(f"✅ Node.js: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js not found. Please install Node.js first:")
        print("   brew install node")
        return False

    # Check npm
    try:
        result = subprocess.run(
            ["npm", "--version"], capture_output=True, text=True, check=True
        )
        print(f"✅ npm: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm not found. Please install npm first:")
        print("   brew install node")
        return False

    return True


def install_mcp_servers() -> Dict[str, bool]:
    """Install all MCP servers."""
    servers = {
        "@modelcontextprotocol/server-filesystem": "File system operations",
        "@modelcontextprotocol/server-github": "GitHub repository operations",
        "@modelcontextprotocol/server-brave-search": "Brave Search web search",
        "@modelcontextprotocol/server-puppeteer": "Browser automation and web content fetching",
    }

    results = {}

    print("\n🚀 Installing MCP servers...")
    print("=" * 50)

    for package, description in servers.items():
        success = run_command(
            ["npm", "install", "-g", package], f"Installing {package} ({description})"
        )
        results[package] = success

    return results


def print_summary(results: Dict[str, bool]) -> None:
    """Print installation summary."""
    print("\n" + "=" * 50)
    print("📊 Installation Summary")
    print("=" * 50)

    successful = [pkg for pkg, success in results.items() if success]
    failed = [pkg for pkg, success in results.items() if not success]

    if successful:
        print("✅ Successfully installed:")
        for pkg in successful:
            print(f"   • {pkg}")

    if failed:
        print("\n❌ Failed to install:")
        for pkg in failed:
            print(f"   • {pkg}")
        print("\n💡 You can try installing these manually:")
        for pkg in failed:
            print(f"   npm install -g {pkg}")

    if len(successful) == len(results):
        print("\n🎉 All MCP servers installed successfully!")
        print(
            "\n🔑 Optional: Configure API keys in .env file for enhanced functionality:"
        )
        print("   • GITHUB_PERSONAL_ACCESS_TOKEN (for repository search)")
        print("   • BRAVE_API_KEY (for web search)")
        print("   • See .env.example for complete configuration options")
        print("\n🧪 Test your installation:")
        print("   poetry run test-tools")
    else:
        print(f"\n⚠️  {len(failed)}/{len(results)} servers failed to install")


def main():
    """Main installation function."""
    print("🤖 Personal AI Agent - MCP Server Installation")
    print("=" * 50)

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Install servers
    results = install_mcp_servers()

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    failed_count = len([r for r in results.values() if not r])
    sys.exit(failed_count)


if __name__ == "__main__":
    main()
