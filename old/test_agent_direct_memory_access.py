#!/usr/bin/env python3
"""
Test script for the full AgnoPersonalAgent lifecycle, including initialization,
direct memory storage with auto-topic generation, and querying.
"""

import asyncio
import shutil
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent, create_agno_agent


@pytest.mark.asyncio
async def test_agent_direct_memory_access():
    """
    Tests the full agent initialization, direct fact storage with auto-topic generation,
    and querying the agent to retrieve the information.
    """
    print("🧠 Testing Agent Direct Memory Access")
    print("=" * 60)

    # Use a dedicated storage directory for this test to ensure isolation
    test_user_id = "test_direct_access_user"
    test_storage_dir = f"./data/test_storage/{test_user_id}"

    # Cleanup previous test runs to ensure a clean slate
    if Path(test_storage_dir).exists():
        shutil.rmtree(test_storage_dir)
        print(f"🗑️  Removed existing test storage directory: {test_storage_dir}")

    # 1. Initialize the agent
    print("\n--- Initializing Agent ---")
    # Note: storage_dir and knowledge_dir are managed by the config system
    # We can only override user_id, recreate, and debug
    # Only pass supported arguments to create_agno_agent
    agent: AgnoPersonalAgent = await create_agno_agent(
        user_id=test_user_id, recreate=True, debug=True
    )
    print(
        f"✅ Agent initialized for user: '{agent.user_id}' in storage: '{agent.storage_dir}'"
    )
    # Disable verbose tool call output for cleaner test logs
    agent.agent.show_tool_calls = False

    # 2. Store facts using the agent, allowing for auto-topic generation
    print("\n--- Storing Facts ---")
    facts_to_store = [
        "My favorite color is sapphire blue.",
        "I work as a professional painter.",
        "I studied art history in college.",
        "I enjoy visiting modern art museums on the weekend.",
    ]

    for fact in facts_to_store:
        print(f"Storing fact: '{fact}'")
        # This query is designed to trigger the store_user_memory tool
        tool_call_query = f'Please remember this about me: "{fact}"'
        response = await agent.run(tool_call_query, stream=False)

        # Verify that the correct tool was called by inspecting the agent's last response
        last_tool_calls = agent.get_last_tool_calls()
        print(f"Tool calls made: {last_tool_calls}")

        # get_last_tool_calls() returns a list of tool call dicts
        assert len(last_tool_calls) > 0, "Agent did not call any tool."

        # Check if store_user_memory was called
        # Tool calls are dicts with 'type' and 'function' keys
        store_call_found = any(
            isinstance(call, dict)
            and call.get("type") == "function"
            and isinstance(call.get("function"), dict)
            and call.get("function", {}).get("name") == "store_user_memory"
            for call in last_tool_calls
        )

        assert (
            store_call_found
        ), f"store_user_memory tool was not called for fact: '{fact}'. Tool calls: {last_tool_calls}"
        print(f"✅ Verified 'store_user_memory' was called for the fact.")

    # 3. Query the agent to retrieve and verify the stored information
    print("\n--- Querying Agent for Stored Facts ---")

    # Test Case 1: Query for a specific fact using semantic search
    print("\nQuerying for 'favorite color'...")
    query1 = "What is my favorite color?"
    response1 = await agent.run(query1, stream=False)
    print(f"Agent Response: {response1}")
    assert isinstance(
        response1, str
    ), f"Expected string response, got {type(response1)}"
    assert "sapphire blue" in response1.lower()

    # Test Case 2: Query using a related concept (should trigger semantic search)
    print("\nQuerying for memories about my 'job'...")
    query2 = "What do you know about my job?"
    response2 = await agent.run(query2, stream=False)
    print(f"Agent Response: {response2}")
    assert isinstance(
        response2, str
    ), f"Expected string response, got {type(response2)}"
    assert "painter" in response2.lower()

    # Test Case 3: Use the get_memories_by_topic tool directly
    print("\nQuerying directly for topic 'education'...")
    # This query explicitly asks the agent to use the new tool
    query3 = "Use the get_memories_by_topic tool to find memories with the topic 'education'."
    response3 = await agent.run(query3, stream=False)
    print(f"Agent Response: {response3}")
    assert isinstance(
        response3, str
    ), f"Expected string response, got {type(response3)}"
    assert "art history" in response3.lower()
    assert "college" in response3.lower()

    # Test Case 4: Retrieve all memories to ensure everything was stored
    print("\nQuerying for all memories...")
    query4 = "Show me all my memories."
    response4 = await agent.run(query4, stream=False)
    print(f"Agent Response: {response4}")
    assert isinstance(
        response4, str
    ), f"Expected string response, got {type(response4)}"
    assert "sapphire blue" in response4
    assert "painter" in response4
    assert "art history" in response4
    assert "museums" in response4

    # Cleanup after the test
    print("\n--- Cleaning up ---")
    if Path(test_storage_dir).exists():
        shutil.rmtree(test_storage_dir)
        print(f"🗑️  Removed test storage directory: {test_storage_dir}")

    print("\n" + "=" * 60)
    print("✅ Agent direct memory access test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_agent_direct_memory_access())
