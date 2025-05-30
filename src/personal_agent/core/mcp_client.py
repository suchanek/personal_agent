"""MCP client implementation."""

import json
import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

from ..config import DATA_DIR, ROOT_DIR

logger = logging.getLogger(__name__)


class SimpleMCPClient:
    """Simple MCP client based on the working test_mcp.py implementation."""

    def __init__(self, server_configs: Dict[str, Dict[str, Any]]):
        self.server_configs = server_configs
        self.active_servers = {}

    def start_server_sync(self, server_name: str) -> bool:
        """Start an MCP server process synchronously."""
        if server_name not in self.server_configs:
            logger.error("Unknown MCP server: %s", server_name)
            return False

        if server_name in self.active_servers:
            logger.info("MCP server %s already running", server_name)
            return True

        config = self.server_configs[server_name]
        try:
            # Start the MCP server process
            # Set working directory based on the server root path
            cwd = None
            if server_name == "filesystem-home":
                cwd = ROOT_DIR
            elif server_name == "filesystem-data":
                cwd = DATA_DIR

            # Prepare environment variables
            env = os.environ.copy()  # Start with current environment
            if "env" in config:
                env.update(config["env"])  # Add server-specific env vars

            process = subprocess.Popen(
                [config["command"]] + config["args"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=cwd,
                env=env,  # Pass environment variables
            )

            self.active_servers[server_name] = {"process": process, "config": config}

            # Wait a moment for server to start
            time.sleep(1)

            # Initialize the server
            if self._initialize_server_sync(server_name):
                logger.info("Started MCP server: %s", server_name)
                return True
            else:
                logger.error("Failed to initialize MCP server: %s", server_name)
                return False

        except Exception as e:
            logger.error("Failed to start MCP server %s: %s", server_name, e)
            return False

    def _initialize_server_sync(self, server_name: str) -> bool:
        """Initialize server synchronously."""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "personal-agent", "version": "0.1.0"},
                },
            }

            response = self._send_request_sync(server_name, init_request)
            if response and response.get("result"):
                logger.info("Initialized MCP server: %s", server_name)
                return True

        except Exception as e:
            logger.error("Failed to initialize MCP server %s: %s", server_name, e)

        return False

    def _send_request_sync(
        self, server_name: str, request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request to an MCP server synchronously."""
        if server_name not in self.active_servers:
            return None

        try:
            process = self.active_servers[server_name]["process"]
            request_json = json.dumps(request) + "\n"

            # Send request
            process.stdin.write(request_json)
            process.stdin.flush()

            # Read response
            response_line = process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())

        except Exception as e:
            logger.error("Error sending request to MCP server %s: %s", server_name, e)

        return None

    def call_tool_sync(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        """Call a tool on an MCP server synchronously."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }

            response = self._send_request_sync(server_name, request)
            if response and response.get("result"):
                content = response["result"].get("content", [])
                if content and len(content) > 0:
                    return content[0].get("text", "No response")

        except Exception as e:
            logger.error(
                "Error calling tool %s on server %s: %s", tool_name, server_name, e
            )

        return f"Error calling tool {tool_name}"

    def list_tools_sync(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools on an MCP server synchronously."""
        try:
            request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

            response = self._send_request_sync(server_name, request)
            if response and response.get("result"):
                tools = response["result"].get("tools", [])
                logger.debug(
                    "Available tools on %s: %s",
                    server_name,
                    [tool.get("name") for tool in tools],
                )
                return tools

        except Exception as e:
            logger.error("Error listing tools on server %s: %s", server_name, e)

        return []

    def stop_server_sync(self, server_name: str) -> bool:
        """Stop a specific MCP server."""
        if server_name not in self.active_servers:
            logger.debug("MCP server %s not running", server_name)
            return True

        try:
            server_info = self.active_servers[server_name]
            process = server_info["process"]

            # Terminate the process
            process.terminate()

            # Wait for it to exit gracefully
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't exit gracefully
                process.kill()
                process.wait()

            # Remove from active servers
            del self.active_servers[server_name]
            logger.info("Stopped MCP server: %s", server_name)
            return True

        except Exception as e:
            logger.error("Error stopping MCP server %s: %s", server_name, e)
            return False

    def start_servers(
        self, server_configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> bool:
        """Start all configured MCP servers."""
        configs = server_configs or self.server_configs
        success = True

        for server_name in configs:
            if not self.start_server_sync(server_name):
                logger.error("Failed to start MCP server: %s", server_name)
                success = False

        return success

    def stop_all_servers(self):
        """Stop all active MCP servers."""
        for server_name, server_info in self.active_servers.items():
            try:
                process = server_info["process"]
                process.terminate()
                process.wait(timeout=5)  # Wait up to 5 seconds
                logger.info("Stopped MCP server: %s", server_name)
            except Exception as e:
                logger.error("Error stopping MCP server %s: %s", server_name, e)

        self.active_servers.clear()
