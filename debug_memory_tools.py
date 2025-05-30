#!/usr/bin/env python3
"""Debug script to test memory tools creation."""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_memory_tools():
    """Test memory tools creation directly."""
    print("🔧 Testing memory tools creation...")

    # Set up basic logging
    logging.basicConfig(level=logging.INFO)

    try:
        from personal_agent.tools.memory_tools import create_memory_tools

        print("✅ Successfully imported create_memory_tools")

        # Test with None values (should create dummy tools)
        tools = create_memory_tools(None, None)
        print(f"📦 Created {len(tools)} tools with None dependencies")

        for i, tool in enumerate(tools):
            print(f"  {i+1}. {tool.name}: {tool.description}")

        # Test with mock objects
        class MockClient:
            def collections(self):
                return self

            def exists(self, name):
                return False

        class MockVectorStore:
            def add_texts(self, **kwargs):
                pass

            def similarity_search(self, query, k=5):
                return []

        mock_client = MockClient()
        mock_store = MockVectorStore()

        tools_with_mocks = create_memory_tools(mock_client, mock_store)
        print(f"📦 Created {len(tools_with_mocks)} tools with mock dependencies")

        for i, tool in enumerate(tools_with_mocks):
            print(f"  {i+1}. {tool.name}: {tool.description}")

        return True

    except Exception as e:
        print(f"❌ Error testing memory tools: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_get_all_tools():
    """Test the get_all_tools function."""
    print("\n🔧 Testing get_all_tools function...")

    try:
        from personal_agent.tools import get_all_tools

        # Test with no dependencies
        tools = get_all_tools()
        print(f"📦 Created {len(tools)} tools with no dependencies")

        # Test with mock dependencies
        class MockClient:
            def collections(self):
                return self

            def exists(self, name):
                return False

        class MockVectorStore:
            def add_texts(self, **kwargs):
                pass

            def similarity_search(self, query, k=5):
                return []

        class MockMCPClient:
            def call_tool(self, **kwargs):
                return {"result": "mock"}

        mock_weaviate = MockClient()
        mock_vector = MockVectorStore()
        mock_mcp = MockMCPClient()

        tools_with_deps = get_all_tools(mock_mcp, mock_weaviate, mock_vector)
        print(f"📦 Created {len(tools_with_deps)} tools with mock dependencies")

        for i, tool in enumerate(tools_with_deps):
            print(f"  {i+1}. {tool.name}: {tool.description}")

        return True

    except Exception as e:
        print(f"❌ Error testing get_all_tools: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all debug tests."""
    print("🔍 Memory Tools Debug Session\n")

    test1 = test_memory_tools()
    test2 = test_get_all_tools()

    if test1 and test2:
        print("\n🎉 All debug tests passed!")
        return 0
    else:
        print("\n⚠️  Some debug tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())
