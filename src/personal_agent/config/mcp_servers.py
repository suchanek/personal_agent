"""MCP server configurations."""

from typing import Any, Dict

from .settings import DATA_DIR, HOME_DIR, ROOT_DIR, get_env_var

# MCP Server configurations
MCP_SERVERS = {
    "filesystem-home": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", HOME_DIR],
        "description": "Access user's home directory filesystem operations",
    },
    "filesystem-data": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", DATA_DIR],
        "description": "Access data directory for vector database",
    },
    "filesystem-root": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", ROOT_DIR],
        "description": "Access full filesystem operations (root access)",
    },
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "description": "GitHub repository operations and code search",
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": get_env_var(
                "GITHUB_PERSONAL_ACCESS_TOKEN", ""
            )
        },
    },
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "description": "Web search for research and technical information",
        "env": {"BRAVE_API_KEY": get_env_var("BRAVE_API_KEY", "")},
    },
    "puppeteer": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "description": "Browser automation and web content fetching",
    },
}


def get_mcp_servers() -> Dict[str, Any]:
    """Get MCP server configurations."""
    return MCP_SERVERS
