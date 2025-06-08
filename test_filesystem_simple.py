#!/usr/bin/env python3
"""
Simple test to verify filesystem MCP integration with agno_main.py
"""

import asyncio
import logging
import os
import sys
import tempfile

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.agno_main import initialize_agno_system


async def test_agno_filesystem_integration():
    """Test the filesystem integration through the agno system."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("🚀 Testing agno filesystem integration...")

    try:
        # Initialize the agno system (this includes filesystem tools)
        agent = await initialize_agno_system()
        logger.info("✅ Agno system initialized successfully")

        # Test basic filesystem operations through the agent
        logger.info("🧪 Testing filesystem operations through agent...")

        # Test 1: List current directory
        logger.info("Test 1: List current directory")
        response = await agent.arun(
            message="List the contents of the current directory and show me what files are there",
            stream=False,
        )
        logger.info(
            "Response: %s",
            (
                response.content[:200] + "..."
                if len(response.content) > 200
                else response.content
            ),
        )

        # Test 2: Create a test file
        logger.info("Test 2: Create a test file")
        test_content = (
            "This is a test file created by the agno filesystem integration test."
        )
        response = await agent.arun(
            message=f"Create a file called 'agno_test.txt' with the content: {test_content}",
            stream=False,
        )
        logger.info("Create file response: %s", response.content)

        # Test 3: Read the test file back
        logger.info("Test 3: Read the test file back")
        response = await agent.arun(
            message="Read the contents of the agno_test.txt file that was just created",
            stream=False,
        )
        logger.info("Read file response: %s", response.content)

        # Test 4: List directory again to see the new file
        logger.info("Test 4: List directory to verify file creation")
        response = await agent.arun(
            message="List the current directory again and confirm agno_test.txt is there",
            stream=False,
        )
        logger.info("Final listing: %s", response.content)

        # Cleanup
        try:
            os.remove("agno_test.txt")
            logger.info("🧹 Cleaned up test file")
        except FileNotFoundError:
            pass

        logger.info("🎉 Filesystem integration test completed successfully!")
        return True

    except Exception as e:
        logger.error("❌ Test failed with error: %s", e)
        import traceback

        traceback.print_exc()
        return False


async def test_direct_mcp_tools():
    """Test the MCP tools directly using create_filesystem_mcp_tools."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("🔧 Testing direct MCP filesystem tools...")

    # Import the function we need
    from personal_agent.agno_main import create_filesystem_mcp_tools

    try:
        # Create a temp directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Using temp directory: %s", temp_dir)

            # Create filesystem MCP tools
            mcp_tools = await create_filesystem_mcp_tools(temp_dir)

            if mcp_tools:
                logger.info("✅ Filesystem MCP tools created successfully")

                # Test using the tools directly through the agno agent pattern
                from agno.agent import Agent

                # Create an agent with the MCP tools
                agent = Agent(tools=[mcp_tools])

                # Test filesystem operations
                response = await agent.arun("List the contents of this directory")
                logger.info("Directory listing: %s", response.content)

                # Test file creation
                response = await agent.arun(
                    "Create a file called 'direct_test.txt' with content 'Direct MCP test successful'"
                )
                logger.info("File creation: %s", response.content)

                # Test file reading
                response = await agent.arun("Read the contents of direct_test.txt")
                logger.info("File reading: %s", response.content)

                logger.info("🎉 Direct MCP tools test completed successfully!")
                return True
            else:
                logger.error("❌ Failed to create filesystem MCP tools")
                return False

    except Exception as e:
        logger.error("❌ Direct MCP test failed: %s", e)
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Filesystem Integration Tests")
    print("=" * 60)

    # Test 1: Integration through agno_main.py
    print("\n📋 Test 1: Agno System Integration")
    print("-" * 40)
    success1 = await test_agno_filesystem_integration()

    # Test 2: Direct MCP tools
    print("\n📋 Test 2: Direct MCP Tools")
    print("-" * 40)
    success2 = await test_direct_mcp_tools()

    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All filesystem integration tests PASSED!")
    else:
        print("❌ Some tests FAILED!")
        if not success1:
            print("  - Agno system integration failed")
        if not success2:
            print("  - Direct MCP tools test failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
