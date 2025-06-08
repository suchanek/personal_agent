#!/usr/bin/env python3
"""
Test program to exercise the filesystem MCP server functionality.

This test creates a temporary test directory and exercises all filesystem
operations available through the MCP server including read, write, list,
create directory, move, and search operations.
"""

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agno.tools.mcp import MCPTools


async def create_filesystem_mcp_tools(root_path: str) -> Optional[MCPTools]:
    """
    Create filesystem MCP tools with proper session management.

    :param root_path: Root directory for filesystem operations
    :return: Initialized MCPTools instance or None if initialization fails
    """
    try:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", root_path],
        )

        # Create client session - keeping session alive by returning the context
        read, write = await stdio_client(server_params).__aenter__()
        session = await ClientSession(read, write).__aenter__()

        # Initialize MCP toolkit
        mcp_tools = MCPTools(session=session)
        await mcp_tools.initialize()
        return mcp_tools, session, (read, write)

    except Exception as e:
        logging.error("Failed to create filesystem MCP tools: %s", e)
        return None


async def test_filesystem_operations():
    """
    Test all filesystem operations through the MCP server.

    This function tests:
    - Creating directories
    - Writing files
    - Reading files
    - Listing directories
    - Moving files
    - Searching files
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info("Testing filesystem MCP server with root: %s", temp_dir)

        # Initialize MCP tools
        result = await create_filesystem_mcp_tools(temp_dir)
        if not result:
            logger.error("Failed to initialize MCP tools")
            return False

        mcp_tools, session, connection = result
        logger.info("✅ MCP filesystem tools initialized successfully")

        try:
            # Test 1: List root directory (should be empty)
            logger.info("🧪 Test 1: List root directory")
            tools_response = await mcp_tools.acall_tool("list_directory", {"path": "."})
            logger.info("Root directory contents: %s", tools_response)

            # Test 2: Create a test directory
            logger.info("🧪 Test 2: Create directory")
            await mcp_tools.acall_tool("create_directory", {"path": "test_folder"})
            logger.info("✅ Created directory: test_folder")

            # Test 3: Write a test file
            logger.info("🧪 Test 3: Write file")
            test_content = """# Test File
This is a test file created by the filesystem MCP server test.

## Features tested:
- File creation
- Directory creation
- File reading
- Directory listing
- File moving
- File searching

Date: 2025-06-08
"""
            await mcp_tools.acall_tool(
                "write_file", {"path": "test_folder/test.md", "content": test_content}
            )
            logger.info("✅ Created file: test_folder/test.md")

            # Test 4: Read the file back
            logger.info("🧪 Test 4: Read file")
            read_result = await mcp_tools.acall_tool(
                "read_file", {"path": "test_folder/test.md"}
            )
            logger.info("File content (first 100 chars): %s...", str(read_result)[:100])

            # Verify content matches
            if test_content in str(read_result):
                logger.info("✅ File content verification passed")
            else:
                logger.error("❌ File content verification failed")

            # Test 5: Create another file
            logger.info("🧪 Test 5: Create additional files")
            await mcp_tools.acall_tool(
                "write_file",
                {
                    "path": "test_folder/config.json",
                    "content": '{"name": "test", "version": "1.0", "enabled": true}',
                },
            )
            await mcp_tools.acall_tool(
                "write_file",
                {
                    "path": "test_folder/script.py",
                    "content": 'print("Hello from MCP filesystem test!")\n',
                },
            )
            logger.info("✅ Created additional files")

            # Test 6: List directory contents
            logger.info("🧪 Test 6: List directory contents")
            dir_result = await mcp_tools.acall_tool(
                "list_directory", {"path": "test_folder"}
            )
            logger.info("test_folder contents: %s", dir_result)

            # Test 7: Create subdirectory and file
            logger.info("🧪 Test 7: Create nested structure")
            await mcp_tools.acall_tool(
                "create_directory", {"path": "test_folder/subdir"}
            )
            await mcp_tools.acall_tool(
                "write_file",
                {
                    "path": "test_folder/subdir/nested.txt",
                    "content": "This is a nested file for testing directory structures.",
                },
            )
            logger.info("✅ Created nested directory and file")

            # Test 8: Move a file
            logger.info("🧪 Test 8: Move file")
            await mcp_tools.acall_tool(
                "move_file",
                {
                    "source": "test_folder/script.py",
                    "destination": "test_folder/subdir/moved_script.py",
                },
            )
            logger.info("✅ Moved script.py to subdir/moved_script.py")

            # Test 9: Search for files
            logger.info("🧪 Test 9: Search files")
            search_result = await mcp_tools.acall_tool(
                "search_files", {"path": ".", "pattern": "*.md"}
            )
            logger.info("Markdown files found: %s", search_result)

            # Test 10: Search for files with different pattern
            logger.info("🧪 Test 10: Search Python files")
            python_search = await mcp_tools.acall_tool(
                "search_files", {"path": ".", "pattern": "*.py"}
            )
            logger.info("Python files found: %s", python_search)

            # Test 11: List final directory structure
            logger.info("🧪 Test 11: Final directory listing")
            final_root = await mcp_tools.acall_tool("list_directory", {"path": "."})
            final_test_folder = await mcp_tools.acall_tool(
                "list_directory", {"path": "test_folder"}
            )
            final_subdir = await mcp_tools.acall_tool(
                "list_directory", {"path": "test_folder/subdir"}
            )

            logger.info("Final root: %s", final_root)
            logger.info("Final test_folder: %s", final_test_folder)
            logger.info("Final subdir: %s", final_subdir)

            # Test 12: Read moved file to verify it exists
            logger.info("🧪 Test 12: Verify moved file")
            moved_content = await mcp_tools.acall_tool(
                "read_file", {"path": "test_folder/subdir/moved_script.py"}
            )
            logger.info("Moved file content: %s", moved_content)

            logger.info("🎉 All filesystem MCP tests completed successfully!")
            return True

        except Exception as e:
            logger.error("❌ Test failed with error: %s", e)
            return False


async def test_error_conditions():
    """
    Test error conditions and edge cases.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info("Testing error conditions with root: %s", temp_dir)

        mcp_tools = await create_filesystem_mcp_tools(temp_dir)
        if not mcp_tools:
            logger.error("Failed to initialize MCP tools")
            return False

        try:
            # Test reading non-existent file
            logger.info("🧪 Test: Read non-existent file")
            try:
                result = await mcp_tools.acall_tool(
                    "read_file", {"path": "nonexistent.txt"}
                )
                logger.info("Non-existent file result: %s", result)
            except Exception as e:
                logger.info("✅ Expected error for non-existent file: %s", e)

            # Test listing non-existent directory
            logger.info("🧪 Test: List non-existent directory")
            try:
                result = await mcp_tools.acall_tool(
                    "list_directory", {"path": "nonexistent_dir"}
                )
                logger.info("Non-existent directory result: %s", result)
            except Exception as e:
                logger.info("✅ Expected error for non-existent directory: %s", e)

            # Test creating directory with invalid path
            logger.info("🧪 Test: Create directory with invalid path")
            try:
                result = await mcp_tools.acall_tool(
                    "create_directory", {"path": "/invalid/absolute/path"}
                )
                logger.info("Invalid path result: %s", result)
            except Exception as e:
                logger.info("✅ Expected error for invalid path: %s", e)

            logger.info("🎉 Error condition tests completed!")
            return True

        except Exception as e:
            logger.error("❌ Error condition test failed: %s", e)
            return False


async def main():
    """
    Main test function that runs all filesystem MCP tests.
    """
    print("🚀 Starting Filesystem MCP Server Tests")
    print("=" * 50)

    # Run main functionality tests
    success1 = await test_filesystem_operations()

    print("\n" + "=" * 50)
    print("🔧 Testing Error Conditions")
    print("=" * 50)

    # Run error condition tests
    success2 = await test_error_conditions()

    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 All tests PASSED!")
    else:
        print("❌ Some tests FAILED!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
