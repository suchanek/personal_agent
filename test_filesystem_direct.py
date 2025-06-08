#!/usr/bin/env python3
"""
Simple test to verify filesystem integration works with available models.
"""
import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.agno_main import create_filesystem_mcp_tools


async def test_direct_filesystem_mcp():
    """Test filesystem MCP tools directly."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("🧪 Testing direct filesystem MCP tools...")

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info("Using temp directory: %s", temp_dir)

        # Create the filesystem MCP tools
        mcp_tools = await create_filesystem_mcp_tools(temp_dir)

        if not mcp_tools:
            logger.error("❌ Failed to create filesystem MCP tools")
            return False

        logger.info("✅ Filesystem MCP tools created successfully")

        try:
            # Test 1: List root directory (should be empty)
            logger.info("Test 1: List root directory")
            from agno.utils.mcp import call_tool

            list_result = await call_tool(
                mcp_tools.session, "list_directory", {"path": "."}
            )
            logger.info("Root directory listing: %s", list_result)

            # Test 2: Create a directory
            logger.info("Test 2: Create directory")
            await call_tool(
                mcp_tools.session, "create_directory", {"path": "test_folder"}
            )
            logger.info("✅ Created directory: test_folder")

            # Test 3: Write a file
            logger.info("Test 3: Write file")
            await call_tool(
                mcp_tools.session,
                "write_file",
                {
                    "path": "test_folder/hello.txt",
                    "content": "Hello from filesystem MCP test!",
                },
            )
            logger.info("✅ Created file: test_folder/hello.txt")

            # Test 4: Read the file
            logger.info("Test 4: Read file")
            read_result = await call_tool(
                mcp_tools.session, "read_file", {"path": "test_folder/hello.txt"}
            )
            logger.info("File content: %s", read_result)

            # Test 5: List directory with files
            logger.info("Test 5: List directory with files")
            final_list = await call_tool(
                mcp_tools.session, "list_directory", {"path": "test_folder"}
            )
            logger.info("test_folder contents: %s", final_list)

            logger.info("🎉 All filesystem MCP tests passed!")
            return True

        except Exception as e:
            logger.error("❌ Test failed: %s", e)
            return False
        finally:
            # Clean up the session
            if hasattr(mcp_tools, "_exit_stack"):
                await mcp_tools._exit_stack.aclose()


async def main():
    """Main test function."""
    print("🚀 Testing Filesystem MCP Integration (Direct)")
    print("=" * 50)

    success = await test_direct_filesystem_mcp()

    if success:
        print("\n🎉 Test completed successfully!")
        print("✅ Filesystem tools are properly integrated and working!")
        return 0
    else:
        print("\n❌ Test failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
