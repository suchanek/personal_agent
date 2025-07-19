"""
MCP Manager - Factory for creating MCP tool instances.

This module provides a factory for creating MCP (Model Context Protocol) tools
with proper configuration, avoiding the asyncio context management issues
that come with persistent singleton connections.
"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import Dict, List, Optional
from agno.tools.mcp import MCPTools

from ..config import get_mcp_servers
from ..config.settings import USE_MCP
from ..utils import setup_logging

logger = setup_logging(__name__)


class MCPManager:
    """
    Factory for creating MCP tool instances with proper configuration.
    
    This class creates fresh MCP tool instances for each agent, avoiding
    the asyncio context management issues that come with persistent connections
    across different tasks.
    
    Usage:
        manager = MCPManager()
        tools = manager.create_mcp_tools()
        # Use tools with proper async context management in your agent
    """
    
    _instance: Optional['MCPManager'] = None
    
    def __new__(cls) -> 'MCPManager':
        """Ensure singleton pattern for configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the MCP manager configuration."""
        if not hasattr(self, '_config_initialized'):
            self.mcp_servers = get_mcp_servers() if USE_MCP else {}
            self.enabled = USE_MCP and bool(self.mcp_servers)
            self._config_initialized = True
            logger.info(f"MCPManager initialized with {len(self.mcp_servers)} servers, enabled: {self.enabled}")
    
    def create_mcp_tools(self) -> List[MCPTools]:
        """
        Create fresh MCP tool instances based on configuration.
        
        Returns:
            List of MCPTools instances ready to be used as async context managers
        """
        if not self.enabled:
            logger.debug("MCP disabled, returning empty list")
            return []
        
        tools = []
        
        for server_name, config in self.mcp_servers.items():
            logger.debug(f"Creating MCPTools instance for server: {server_name}")
            
            command = config.get("command")
            args = config.get("args", [])
            env = config.get("env", {}).copy()
            
            # Apply server-specific environment variable mappings
            if server_name == "github" and "GITHUB_PERSONAL_ACCESS_TOKEN" in os.environ:
                env["GITHUB_TOKEN"] = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
                logger.debug("Mapped GITHUB_PERSONAL_ACCESS_TOKEN to GITHUB_TOKEN for GitHub MCP server")
            
            if command:
                # Combine command and args into a single command string
                full_command = f"{command} {' '.join(args)}" if args else command
                
                mcp_tool = MCPTools(
                    command=full_command,
                    env=env,
                    transport="stdio",
                    timeout_seconds=5,
                )
                tools.append(mcp_tool)
                logger.debug(f"Created MCPTools instance for: {server_name}")
            else:
                logger.warning(f"No command specified for MCP server: {server_name}")
        
        logger.info(f"Created {len(tools)} MCP tool instances")
        return tools
    
    def is_enabled(self) -> bool:
        """Check if MCP is enabled."""
        return self.enabled
    
    def get_tool_count(self) -> int:
        """Get the number of configured MCP servers."""
        return len(self.mcp_servers) if self.enabled else 0
    
    def get_server_info(self) -> Dict:
        """Get information about configured MCP servers."""
        server_details = {}
        
        if self.enabled and self.mcp_servers:
            for server_name, config in self.mcp_servers.items():
                server_details[server_name] = {
                    "command": config.get("command", "N/A"),
                    "description": config.get("description", f"Access to {server_name} MCP server"),
                    "args_count": len(config.get("args", [])),
                    "env_vars": len(config.get("env", {})),
                    "configured": True,
                }
        
        return server_details


# Global instance for easy access
mcp_manager = MCPManager()
