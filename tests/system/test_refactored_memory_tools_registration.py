#!/usr/bin/env python3
"""
Test script to verify that all memory tools are properly registered in PersagMemoryTools.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from personal_agent.tools.persag_memory_tools import PersagMemoryTools


def test_memory_tools_registration():
    """Test that all memory tools are properly registered in PersagMemoryTools."""

    # Expected tool methods that should be registered
    expected_tools = [
        "store_user_memory",
        "query_memory",
        "update_memory",
        "delete_memory",
        "get_recent_memories",
        "get_all_memories",
        "get_memory_stats",
        "get_memories_by_topic",
        "list_memories",
        "store_graph_memory",
        "query_graph_memory",
        "get_memory_graph_labels",
        "clear_semantic_memories",
        "delete_memories_by_topic",
        "clear_all_memories",
    ]

    print("🧪 Testing PersagMemoryTools registration...")
    print(f"Expected {len(expected_tools)} tools to be registered")

    try:
        # Create a mock memory manager (we don't need a real one for registration testing)
        class MockMemoryManager:
            def __init__(self):
                self.user_id = "test_user"

        mock_memory_manager = MockMemoryManager()

        # Initialize the PersagMemoryTools
        memory_tools = PersagMemoryTools(mock_memory_manager)

        print(f"\n📋 PersagMemoryTools initialized successfully")
        print(f"Toolkit name: {memory_tools.name}")
        print(f"Number of tools registered: {len(memory_tools.tools)}")

        # Get the list of registered tool names
        registered_tool_names = []
        for tool in memory_tools.tools:
            if hasattr(tool, "__name__"):
                registered_tool_names.append(tool.__name__)
            elif hasattr(tool, "func") and hasattr(tool.func, "__name__"):
                registered_tool_names.append(tool.func.__name__)
            else:
                registered_tool_names.append(str(tool))

        print(f"\n✅ Registered tools:")
        for i, tool_name in enumerate(sorted(registered_tool_names), 1):
            print(f"  {i:2d}. {tool_name}")

        # Check if all expected tools are registered
        missing_tools = []
        for expected_tool in expected_tools:
            if expected_tool not in registered_tool_names:
                missing_tools.append(expected_tool)

        extra_tools = []
        for registered_tool in registered_tool_names:
            if registered_tool not in expected_tools:
                extra_tools.append(registered_tool)

        # Report results
        print(f"\n📊 Registration Analysis:")
        print(f"Expected tools: {len(expected_tools)}")
        print(f"Registered tools: {len(registered_tool_names)}")
        print(f"Missing tools: {len(missing_tools)}")
        print(f"Extra tools: {len(extra_tools)}")

        if missing_tools:
            print(f"\n❌ Missing tools:")
            for tool in missing_tools:
                print(f"  - {tool}")

        if extra_tools:
            print(f"\n⚠️  Extra tools (not in expected list):")
            for tool in extra_tools:
                print(f"  - {tool}")

        # Verify that all expected tools have corresponding methods
        print(f"\n🔍 Verifying tool methods exist:")
        method_check_results = {}
        for tool_name in expected_tools:
            has_method = hasattr(memory_tools, tool_name)
            method_check_results[tool_name] = has_method
            status = "✅" if has_method else "❌"
            print(f"  {status} {tool_name}")

        # Final assessment
        all_tools_registered = len(missing_tools) == 0
        all_methods_exist = all(method_check_results.values())

        print(f"\n🎯 Final Assessment:")
        print(
            f"All expected tools registered: {'✅ YES' if all_tools_registered else '❌ NO'}"
        )
        print(f"All tool methods exist: {'✅ YES' if all_methods_exist else '❌ NO'}")

        if all_tools_registered and all_methods_exist:
            print(
                f"\n🎉 SUCCESS: All {len(expected_tools)} memory tools are properly registered!"
            )
            return True
        else:
            print(f"\n💥 FAILURE: Tool registration issues detected!")
            return False

    except Exception as e:
        print(f"\n💥 ERROR during testing: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_toolkit_properties():
    """Test that the toolkit has the expected properties."""

    print(f"\n🔧 Testing toolkit properties...")

    try:

        class MockMemoryManager:
            def __init__(self):
                self.user_id = "test_user"

        mock_memory_manager = MockMemoryManager()
        memory_tools = PersagMemoryTools(mock_memory_manager)

        # Test toolkit properties
        assert (
            memory_tools.name == "persag_memory_tools"
        ), f"Expected name 'persag_memory_tools', got '{memory_tools.name}'"
        assert hasattr(memory_tools, "tools"), "Toolkit should have 'tools' attribute"
        assert hasattr(
            memory_tools, "instructions"
        ), "Toolkit should have 'instructions' attribute"
        assert len(memory_tools.tools) > 0, "Toolkit should have at least one tool"

        print(f"✅ Toolkit name: {memory_tools.name}")
        print(f"✅ Tools count: {len(memory_tools.tools)}")
        print(f"✅ Has instructions: {bool(memory_tools.instructions)}")

        return True

    except Exception as e:
        print(f"❌ Toolkit properties test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING REFACTORED MEMORY TOOLS REGISTRATION")
    print("=" * 60)

    # Run the tests
    registration_success = test_memory_tools_registration()
    properties_success = test_toolkit_properties()

    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)

    if registration_success and properties_success:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED!")
        sys.exit(1)
