import asyncio
import os
import re
import sys
from unittest.mock import MagicMock
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath())

from src.personal_agent.cli.memory_commands import delete_memory_by_id_cli
from src.personal_agent.core.agno_agent import AgnoPersonalAgent, create_agno_agent


async def run_test():
    """
    Tests the full memory deletion flow, ensuring that the CLI command
    correctly finds and uses the unified tool to delete from both
    SQLite and the LightRAG graph memory.
    """
    # 1. Initialize the agent
    print("Initializing agent...")
    agent = await create_agno_agent(
        enable_mcp=False, recreate=True, user_id="charlie_test"  # Start with a clean slate
    )
    assert agent is not None, "Agent initialization failed"
    print("Agent initialized.")

    # 2. Create a memory to be deleted
    test_content = "This is a test memory for deletion."
    print(f"Creating memory: '{test_content}'")
    storage_result = await agent.store_user_memory(content=test_content)

    # Ensure memory was created successfully
    assert (
        storage_result.is_success
    ), f"Memory creation failed: {storage_result.message}"
    assert (
        storage_result.memory_id is not None
    ), "Memory creation did not return a memory_id"

    memory_id = storage_result.memory_id
    print(f"Created memory with ID: {memory_id}")

    # 3. Mock the console to capture output
    mock_console = MagicMock()

    # 4. Call the CLI function to delete the memory
    print(f"Attempting to delete memory with ID: {memory_id}")
    await delete_memory_by_id_cli(agent, memory_id, mock_console)

    # 5. Assert the output indicates success in both systems
    # We check the calls to the mock_console's print method.
    output_calls = mock_console.print.call_args_list
    assert output_calls, "The CLI command did not produce any output."

    # Combine all output into a single string for easier searching
    full_output = " ".join([str(call.args[0]) for call in output_calls])

    print(f"CLI Output: {full_output}")

    # Check for SQLite success message
    assert (
        "Successfully deleted memory from SQLite" in full_output
    ), "Missing SQLite deletion success message."

    # Check for Graph success message
    assert (
        "Successfully deleted from graph memory" in full_output
    ), "Missing graph memory deletion success message."

    # Check that the "tool not found" warning is NOT present
    assert (
        "tool not found" not in full_output.lower()
    ), "Fallback logic with 'tool not found' was incorrectly triggered."

    # 6. Verify the memory is actually gone
    print("Verifying memory deletion...")
    all_memories_str = await agent.memory_tools.get_all_memories()
    assert (
        memory_id not in all_memories_str
    ), "Deleted memory_id was found in get_all_memories."
    assert (
        test_content not in all_memories_str
    ), "Deleted memory content was found in get_all_memories."

    print(
        "\n✅ Test passed: Memory successfully deleted from both systems and verified."
    )


if __name__ == "__main__":
    asyncio.run(run_test())
