#!/usr/bin/env python3
"""Test script to verify comprehensive_research tool works correctly."""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))


def test_comprehensive_research():
    """Test the comprehensive_research tool directly."""
    try:
        from personal_agent import USE_MCP, comprehensive_research, mcp_client

        print("🔍 Testing comprehensive_research tool...")
        print(f"MCP enabled: {USE_MCP}")
        print(f"MCP client available: {mcp_client is not None}")

        # Test with a simple topic
        test_topic = "Python programming basics"
        print(f"\n📋 Testing with topic: '{test_topic}'")

        result = comprehensive_research.invoke({"topic": test_topic, "max_results": 3})

        print("\n✅ Test completed successfully!")
        print(f"Result length: {len(result)} characters")
        print(f"Result preview: {result[:200]}...")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_agent_executor():
    """Test the agent executor with increased iterations."""
    try:
        from personal_agent import agent_executor

        print("\n🤖 Testing agent executor configuration...")
        print(f"Max iterations: {agent_executor.max_iterations}")
        print(f"Handle parsing errors: {agent_executor.handle_parsing_errors}")
        print(f"Verbose: {agent_executor.verbose}")

        # Simple test query
        test_query = "What tools do you have available?"
        print(f"\n📋 Testing with query: '{test_query}'")

        result = agent_executor.invoke(
            {"input": test_query, "context": "No previous context"}
        )

        print("\n✅ Agent executor test completed!")
        print(f"Response: {result.get('output', 'No output')[:200]}...")

        return True

    except Exception as e:
        print(f"❌ Agent executor test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Comprehensive Research Tool Test")
    print("=" * 50)

    success = True

    # Test 1: Direct tool test
    if not test_comprehensive_research():
        success = False

    # Test 2: Agent executor test
    if not test_agent_executor():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The comprehensive_research issue should be fixed.")
    else:
        print("❌ Some tests failed. Check the configuration.")

    sys.exit(0 if success else 1)
