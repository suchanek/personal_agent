import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console

from personal_agent.cli.memory_commands import (
    delete_memory_by_id_cli,
    store_immediate_memory,
)
from personal_agent.config.user_id_mgr import get_userid


class CapturingConsole(Console):
    """A Rich Console that captures output for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captured_output = []

    def print(self, *args, **kwargs):
        """Capture print output."""
        output = " ".join(str(arg) for arg in args)
        self.captured_output.append(output)
        # super().print(*args, **kwargs) # Uncomment for debugging

    def get_output(self) -> list[str]:
        """Get the captured output."""
        return self.captured_output

    def clear_output(self):
        """Clear the captured output."""
        self.captured_output = []


def find_tool_by_name(agent, tool_name):
    if not agent.agent or not hasattr(agent.agent, "tools"):
        return None

    for toolkit in agent.agent.tools:
        if getattr(toolkit, "__name__", "") == tool_name:
            return toolkit

        if hasattr(toolkit, "tools") and isinstance(toolkit.tools, list):
            for tool in toolkit.tools:
                if hasattr(tool, "__name__") and tool.__name__ == tool_name:
                    return tool
    return None


def test_configuration_and_initialization():
    """Tests that the agent's configuration is loaded correctly and that the agent can be initialized."""
    print("--- Testing Configuration and Initialization ---")
    try:
        from personal_agent.config import settings
        from personal_agent.core.agno_agent import AgnoPersonalAgent

        print("✅ Configuration imported successfully.")

        # Check for essential settings
        user_id = get_userid()
        assert user_id, "Could not get user ID"
        assert hasattr(
            settings, "AGNO_STORAGE_DIR"
        ), "AGNO_STORAGE_DIR not found in settings"
        print(f"✅ Essential settings are present for user: {user_id}")

        # Initialize the agent
        agent = AgnoPersonalAgent(
            user_id=user_id,
            enable_memory=True,
            enable_mcp=False,  # Disable for faster, focused testing
            debug=False,
            initialize_agent=True,
        )
        print("✅ Agent initialized successfully.")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_memory_subsystem():
    """Tests the memory subsystem for basic functionality using CLI commands."""
    print("--- Testing Memory Subsystem ---")
    try:
        from personal_agent.core.agno_agent import AgnoPersonalAgent

        user_id = get_userid()
        agent = AgnoPersonalAgent(
            user_id=user_id,
            enable_memory=True,
            enable_mcp=False,
            debug=False,
            initialize_agent=True,
        )
        await agent.initialize()
        console = CapturingConsole()

        # Store a memory
        test_fact = "The diagnostic script is testing the memory subsystem."
        await store_immediate_memory(agent, test_fact, console)
        print(f"✅ Stored test memory for user: {user_id}")

        # Retrieve the memory and get its ID
        memories = agent.agno_memory.memory_manager.get_all_memories(
            db=agent.agno_memory.db, user_id=user_id
        )
        test_memory = next((m for m in memories if m.memory == test_fact), None)
        assert test_memory, "Test memory not found in database"
        memory_id = test_memory.memory_id
        print(f"✅ Retrieved test memory successfully with ID: {memory_id}")

        # Delete the memory
        await delete_memory_by_id_cli(agent, memory_id, console)
        print(f"✅ Deleted test memory with ID: {memory_id}")

        # Verify it's gone
        memories = agent.agno_memory.memory_manager.get_all_memories(
            db=agent.agno_memory.db, user_id=user_id
        )
        assert not any(
            m.memory_id == memory_id for m in memories
        ), "Test memory was not deleted"
        print("✅ Verified memory deletion.")

        return True
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"❌ Test failed: {e}")
        return False


async def test_tool_subsystem():
    """Tests the tool subsystem for basic functionality."""
    print("--- Testing Tool Subsystem ---")
    try:
        from personal_agent.core.agno_agent import AgnoPersonalAgent

        user_id = get_userid()
        agent = AgnoPersonalAgent(
            user_id=user_id, enable_memory=True, enable_mcp=False, debug=False
        )
        await agent.initialize()

        # Get the list of tools
        tools = agent.agent.tools
        print(f"✅ Found {len(tools)} tools.")

        # Check for a few key tools
        tool_names = []
        for tool in tools:
            tool_name = None
            for name_attr in ["name", "__name__"]:
                if hasattr(tool, name_attr):
                    tool_name = getattr(tool, name_attr)
                    if tool_name:
                        break
            if (
                not tool_name
                and hasattr(tool, "func")
                and hasattr(tool.func, "__name__")
            ):
                tool_name = tool.func.__name__
            if not tool_name:
                tool_name = str(type(tool).__name__)
            tool_names.append(tool_name)

        assert "store_user_memory" in tool_names, "store_user_memory tool not found"
        assert "query_memory" in tool_names, "query_memory tool not found"
        print("✅ Key tools are present.")

        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_core_agent_logic():
    """Tests the core agent logic for basic functionality."""
    print("--- Testing Core Agent Logic ---")
    try:
        from personal_agent.core.agno_agent import AgnoPersonalAgent

        user_id = get_userid()
        agent = AgnoPersonalAgent(
            user_id=user_id, enable_memory=True, enable_mcp=False, debug=True
        )
        await agent.initialize()

        # Test a simple query that should not call any tools
        response_stream = await agent.arun("Hello, how are you?")
        response = ""
        tool_calls = []
        async for chunk in response_stream:
            if hasattr(chunk, "content") and chunk.content:
                response += chunk.content
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)

        print(f"✅ Simple query response: {response}")
        assert not tool_calls, "Simple query should not call tools"

        # Test a query that should call a tool
        response_stream = await agent.arun("What is the stock price of NVDA?")
        response = ""
        tool_calls = []
        async for chunk in response_stream:
            if hasattr(chunk, "content") and chunk.content:
                response += chunk.content
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)

        print(f"✅ Tool query response: {response}")
        assert tool_calls, "Tool query should call a tool"

        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main function to run the diagnostic tests."""
    parser = argparse.ArgumentParser(
        description="Run diagnostic tests for the Personal Agent."
    )
    parser.add_argument(
        "--subsystem",
        type=str,
        help="Run tests for a specific subsystem (config, memory, tools, user, core).",
        default="all",
    )
    args = parser.parse_args()

    results = {}

    if args.subsystem == "all" or args.subsystem == "config":
        results["Configuration and Initialization"] = (
            test_configuration_and_initialization()
        )
    if args.subsystem == "all" or args.subsystem == "memory":
        results["Memory Subsystem"] = asyncio.run(test_memory_subsystem())
    if args.subsystem == "all" or args.subsystem == "tools":
        results["Tool Subsystem"] = asyncio.run(test_tool_subsystem())
    # if args.subsystem == "all" or args.subsystem == "user":
    #     results["User Management Subsystem"] = asyncio.run(test_user_management_subsystem())
    if args.subsystem == "all" or args.subsystem == "core":
        results["Core Agent Logic"] = asyncio.run(test_core_agent_logic())

    print("\n--- Diagnostic Summary ---")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test}: {status}")


if __name__ == "__main__":
    main()
