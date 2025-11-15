"""MCP server configurations."""

from typing import Any, Dict

from .settings import DATA_DIR, HOME_DIR, ROOT_DIR, USER_DATA_DIR, get_env_var

# Hide MCP_SERVERS from pdoc to prevent exposing secrets in documentation
__pdoc__ = {
    "MCP_SERVERS": False,
}


def _build_mcp_servers() -> Dict[str, Any]:
    """Build MCP server configurations with environment variables.
    
    This is a private function that constructs the MCP_SERVERS dictionary
    at runtime to avoid exposing secrets in documentation.
    """
    return {
    "filesystem-home": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", HOME_DIR],
        "description": "Access user's home directory filesystem operations",
    },
    "filesystem-data": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", USER_DATA_DIR],
        "description": "Access user-specific data directory for vector database",
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


# Build the actual MCP_SERVERS at module load time
MCP_SERVERS = _build_mcp_servers()


def get_mcp_servers() -> Dict[str, Any]:
    """Get MCP server configurations.
    
    Returns:
        Dict containing MCP server configurations with proper environment variables.
        Each server config includes command, args, description, and optional env vars.
    """
    return MCP_SERVERS
