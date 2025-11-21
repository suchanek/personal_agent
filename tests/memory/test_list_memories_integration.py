#!/usr/bin/env python3
"""
Test script to verify that the list_memories method is properly integrated
between the StreamlitMemoryHelper and the AgentMemoryManager.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper


@pytest.mark.asyncio
async def test_list_memories_integration():
    """Test that list_memories method works correctly."""
    print("🧪 Testing list_memories integration...")

    # Create a temporary directory for this test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")

        # Initialize the agent
        agent = AgnoPersonalAgent(
            user_id="test_user", storage_dir=temp_dir, enable_memory=True, debug=False
        )

        # Initialize the agent
        await agent._ensure_initialized()
        print("✅ Agent initialized successfully")

        # Create StreamlitMemoryHelper
        memory_helper = StreamlitMemoryHelper(agent)
        print("✅ StreamlitMemoryHelper created")

        # Test 1: List existing memories (may have some from previous tests)
        print("\n📝 Test 1: List existing memories")
        result = memory_helper.list_memories()
        print(f"Result: {result}")
        assert (
            "MEMORY LIST" in result
        ), f"Expected 'MEMORY LIST' in result, got: {result}"

        # Count existing memories
        import re

        existing_count = len(re.findall(r"^\d+\.", result, re.MULTILINE))
        print(f"Found {existing_count} existing memories")
        print("✅ List existing memories test passed")

        # Test 2: Add some memories and then list them
        print("\n📝 Test 2: Add memories and list them")

        # Add first memory
        success1, msg1, id1, topics1 = memory_helper.add_memory(
            "I love playing oboe", ["hobbies", "music"]
        )
        print(f"Memory 1 - Success: {success1}, Message: {msg1}")
        assert success1, f"Failed to add first memory: {msg1}"

        # Add second memory
        success2, msg2, id2, topics2 = memory_helper.add_memory(
            "I work as a audio engineer", ["career", "work"]
        )
        print(f"Memory 2 - Success: {success2}, Message: {msg2}")
        assert success2, f"Failed to add second memory: {msg2}"

        # Add third memory
        success3, msg3, id3, topics3 = memory_helper.add_memory(
            "I live in Washington DC", ["location", "personal"]
        )
        print(f"Memory 3 - Success: {success3}, Message: {msg3}")
        assert success3, f"Failed to add third memory: {msg3}"

        print("✅ All memories added successfully")

        # Test 3: List all memories
        print("\n📝 Test 3: List all memories")
        result = memory_helper.list_memories()
        print(f"List result:\n{result}")

        # Verify the result contains expected elements
        assert (
            "MEMORY LIST" in result
        ), f"Expected 'MEMORY LIST' in result, got: {result}"

        # Count total memories after adding our 3
        total_count = len(re.findall(r"^\d+\.", result, re.MULTILINE))
        expected_count = existing_count + 3
        assert (
            total_count == expected_count
        ), f"Expected {expected_count} total memories, got {total_count}"

        assert "guitar" in result, f"Expected 'guitar' in result, got: {result}"
        assert (
            "software engineer" in result
        ), f"Expected 'software engineer' in result, got: {result}"
        assert (
            "San Francisco" in result
        ), f"Expected 'San Francisco' in result, got: {result}"

        print("✅ List memories test passed")

        # Test 4: Verify the method exists on the agent
        print("\n📝 Test 4: Verify agent has list_all_memories method")
        assert hasattr(
            agent, "list_all_memories"
        ), "Agent should have list_all_memories method"

        # Test the agent method directly
        agent_result = await agent.list_all_memories()
        print(f"Agent direct result:\n{agent_result}")
        assert (
            "MEMORY LIST" in agent_result
        ), f"Expected 'MEMORY LIST' in agent result, got: {agent_result}"

        print("✅ Agent list_all_memories method test passed")

        # Test 5: Compare helper vs direct agent call
        print("\n📝 Test 5: Compare helper vs direct agent call")
        helper_result = memory_helper.list_memories()
        agent_result = await agent.list_all_memories()

        # Both should contain the same core information
        assert (
            "guitar" in helper_result and "guitar" in agent_result
        ), "Both should contain guitar memory"
        assert (
            "software engineer" in helper_result and "software engineer" in agent_result
        ), "Both should contain software engineer memory"

        print("✅ Helper vs agent comparison test passed")

        print(
            "\n🎉 All tests passed! The list_memories integration is working correctly."
        )

        return True


def main():
    """Main test function."""
    try:
        result = asyncio.run(test_list_memories_integration())
        if result:
            print(
                "\n✅ SUCCESS: list_memories integration test completed successfully!"
            )
            return 0
        else:
            print("\n❌ FAILURE: list_memories integration test failed!")
            return 1
    except Exception as e:
        print(f"\n💥 ERROR: Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
