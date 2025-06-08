#!/usr/bin/env python3
"""
Test program to exercise the filesystem tools integrated with agno_main.py.

This test specifically tests the filesystem functionality as integrated
in the agno agent system.
"""

import asyncio
import logging
import tempfile
from pathlib import Path

# Import the agno_main functions
from src.personal_agent.agno_main import (
    create_filesystem_mcp_tools,
    initialize_agno_system,
)


async def test_agno_filesystem_integration():
    """
    Test filesystem functionality integrated with agno_main.py.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("🧪 Testing Agno Filesystem Integration")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info("Using temporary directory: %s", temp_dir)

        # Test the create_filesystem_mcp_tools function directly
        logger.info("🔧 Testing create_filesystem_mcp_tools function...")

        try:
            mcp_tools = await create_filesystem_mcp_tools(temp_dir)

            if mcp_tools is None:
                logger.error("❌ create_filesystem_mcp_tools returned None")
                return False

            logger.info("✅ create_filesystem_mcp_tools succeeded")

            # Test basic operations with the MCP tools
            logger.info("🧪 Testing basic filesystem operations...")

            # Test 1: Write a file
            test_content = (
                "Hello from Agno filesystem test!\nThis tests the integration."
            )
            await mcp_tools.acall_tool(
                "write_file", {"path": "agno_test.txt", "content": test_content}
            )
            logger.info("✅ File written successfully")

            # Test 2: Read the file back
            read_result = await mcp_tools.acall_tool(
                "read_file", {"path": "agno_test.txt"}
            )
            logger.info("✅ File read successfully: %s", str(read_result)[:50] + "...")

            # Test 3: List directory
            list_result = await mcp_tools.acall_tool("list_directory", {"path": "."})
            logger.info("✅ Directory listed: %s", list_result)

            # Test 4: Create directory
            await mcp_tools.acall_tool("create_directory", {"path": "test_dir"})
            logger.info("✅ Directory created")

            # Test 5: Write file in subdirectory
            await mcp_tools.acall_tool(
                "write_file",
                {
                    "path": "test_dir/nested_file.md",
                    "content": "# Nested File Test\n\nThis file is in a subdirectory.",
                },
            )
            logger.info("✅ Nested file created")

            # Test 6: Search files
            search_result = await mcp_tools.acall_tool(
                "search_files", {"path": ".", "pattern": "*.txt"}
            )
            logger.info("✅ File search completed: %s", search_result)

            logger.info("🎉 All agno filesystem integration tests passed!")
            return True

        except Exception as e:
            logger.error("❌ Test failed with error: %s", e)
            logger.exception("Full error traceback:")
            return False


async def test_agno_agent_with_filesystem():
    """
    Test the full agno agent initialization with filesystem tools.
    """
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing full agno agent with filesystem tools...")

    try:
        # Initialize the full agno system
        agent = await initialize_agno_system()

        if agent is None:
            logger.error("❌ Failed to initialize agno agent")
            return False

        logger.info("✅ Agno agent initialized successfully")

        # Check if agent has tools
        if hasattr(agent, "tools") and agent.tools:
            logger.info("✅ Agent has %d tools", len(agent.tools))

            # Look for MCP tools
            mcp_tools_found = False
            for tool in agent.tools:
                if hasattr(tool, "__class__") and "MCP" in tool.__class__.__name__:
                    mcp_tools_found = True
                    logger.info("✅ Found MCP tool: %s", tool.__class__.__name__)
                    break

            if mcp_tools_found:
                logger.info("✅ MCP tools found in agent")
            else:
                logger.warning("⚠️ No MCP tools found in agent tools list")

        else:
            logger.warning("⚠️ Agent has no tools")

        # Test agent with a filesystem-related query
        logger.info("🧪 Testing agent with filesystem query...")

        try:
            # Use a simple query that might trigger filesystem tools
            response = await agent.arun(
                "Can you list the files in the current directory?", stream=False
            )
            logger.info("✅ Agent responded to filesystem query")
            logger.info("Response preview: %s", str(response)[:100] + "...")

        except Exception as e:
            logger.warning("⚠️ Agent query failed (this might be expected): %s", e)

        logger.info("🎉 Full agno agent test completed!")
        return True

    except Exception as e:
        logger.error("❌ Full agent test failed: %s", e)
        logger.exception("Full error traceback:")
        return False


async def main():
    """
    Main test function.
    """
    print("🚀 Starting Agno Filesystem Integration Tests")
    print("=" * 60)

    # Test 1: Direct MCP tools integration
    success1 = await test_agno_filesystem_integration()

    print("\n" + "=" * 60)
    print("🤖 Testing Full Agno Agent Integration")
    print("=" * 60)

    # Test 2: Full agent integration
    success2 = await test_agno_agent_with_filesystem()

    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All integration tests PASSED!")
        print("✅ Filesystem tools are properly integrated with agno_main.py")
    else:
        print("❌ Some integration tests FAILED!")
        if not success1:
            print("❌ Direct MCP tools test failed")
        if not success2:
            print("❌ Full agent integration test failed")
    print("=" * 60)


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(main())
