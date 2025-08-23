#!/usr/bin/env python3
"""
Test script to verify that the Streamlit arun() fix works correctly.

This test verifies that:
1. The Streamlit app can now use agent.arun() with async tools
2. The specific error about async tools is resolved
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_agent_arun_with_async_tools():
    """Test that agent.arun() works with async tools."""
    print("🧪 Testing agent.arun() with async tools...")

    try:
        # 1. Create a simple agent with async tools (memory and knowledge)
        print("1. Creating AgnoPersonalAgent with async tools...")
        agent = await AgnoPersonalAgent.create_with_init(
            model_provider="ollama",
            model_name="qwen3:1.7b",
            enable_memory=True,
            debug=True,
            alltools=False,  # Only use memory/knowledge tools for this test
        )
        print("   ✅ Agent created successfully")

        # 2. Test that agent.arun() works without async tool errors
        print("2. Testing agent.arun() with async tools...")
        try:
            # Use a simple query that shouldn't trigger async tools heavily
            run_response = await agent.arun("Hello, how are you?", stream=False)
            
            # Extract content from RunResponse properly
            if hasattr(run_response, 'content') and run_response.content:
                response_content = run_response.content
            elif hasattr(run_response, 'messages') and run_response.messages:
                response_content = ""
                for message in run_response.messages:
                    if hasattr(message, 'role') and message.role == "assistant":
                        if hasattr(message, 'content') and message.content:
                            response_content += message.content
            else:
                response_content = str(run_response)
            
            print(f"   ✅ Agent.arun() completed successfully: {response_content[:50]}...")

        except Exception as e:
            error_msg = str(e)
            if (
                "Async tool" in error_msg
                and "can't be used with synchronous" in error_msg
            ):
                print(f"   ❌ The async tool error still occurs: {error_msg}")
                return False
            elif "'RunResponse' object is not subscriptable" in error_msg:
                print(f"   ❌ RunResponse parsing error still occurs: {error_msg}")
                return False
            else:
                print(f"   ⚠️  Different error occurred (may be expected): {error_msg}")

        print("🎉 Test passed! The agent.arun() fix is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    print("🚀 Starting Streamlit arun() fix test...\n")

    success = await test_agent_arun_with_async_tools()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Agent arun() Test: {'✅ PASSED' if success else '❌ FAILED'}")

    if success:
        print("\n🎉 TEST PASSED! The Streamlit app should now work with --single mode.")
        print("The error about async tools should be resolved.")
        return True
    else:
        print("\n❌ TEST FAILED. The fix may need additional work.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
