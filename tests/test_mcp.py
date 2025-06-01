#!/usr/bin/env python3
"""Test script to diagnose MCP server issues."""

import asyncio
import json
import logging
import os
import subprocess
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
from personal_agent import ROOT_DIR

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_mcp_server():
    """Test MCP server communication."""
    # Start the MCP server with home directory as root
    logger.info("Starting MCP server...")
    process = await asyncio.create_subprocess_exec(
        "npx",
        "@modelcontextprotocol/server-filesystem",
        ROOT_DIR,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Read stderr in background
    async def read_stderr():
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            logger.warning("STDERR: %s", line.decode().strip())

    asyncio.create_task(read_stderr())

    # Wait a bit for server to start
    await asyncio.sleep(2)

    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "0.1.0"},
        },
    }

    logger.info("Sending initialize request...")
    request_json = json.dumps(init_request) + "\n"
    process.stdin.write(request_json.encode())
    await process.stdin.drain()

    # Read response
    response_line = await process.stdout.readline()
    if response_line:
        response = json.loads(response_line.decode().strip())
        logger.info("Initialize response: %s", json.dumps(response, indent=2))

    # Get tools list
    tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

    logger.info("Sending tools/list request...")
    request_json = json.dumps(tools_request) + "\n"
    process.stdin.write(request_json.encode())
    await process.stdin.drain()

    # Read response
    response_line = await process.stdout.readline()
    if response_line:
        response = json.loads(response_line.decode().strip())
        logger.info("Tools response: %s", json.dumps(response, indent=2))

        # Print available tools
        if "result" in response and "tools" in response["result"]:
            logger.info("\nAvailable tools:")
            for tool in response["result"]["tools"]:
                logger.info("  - %s: %s", tool["name"], tool.get("description", ""))

    # Test list_directory - use "." to list the root of the restricted filesystem
    list_dir_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "list_directory", "arguments": {"path": "."}},
    }

    logger.info("\nSending list_directory request for root (.)...")
    request_json = json.dumps(list_dir_request) + "\n"
    process.stdin.write(request_json.encode())
    await process.stdin.drain()

    # Read response
    response_line = await process.stdout.readline()
    if response_line:
        response = json.loads(response_line.decode().strip())
        logger.info("List directory response: %s", json.dumps(response, indent=2))

    # Terminate the process
    process.terminate()
    await process.wait()


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
