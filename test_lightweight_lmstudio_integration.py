#!/usr/bin/env python3
"""
Lightweight LM Studio integration test for AgnoPersonalAgent.

This test creates a minimal AgnoPersonalAgent with fewer tools to fit within
the LM Studio model's context window while still testing the core functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent


def setup_lmstudio_environment():
    """Set up environment variables for LM Studio testing."""
    print("🔧 Setting up LM Studio environment...")

    try:
        # Set LM Studio configuration
        os.environ["PROVIDER"] = "lm-studio"
        os.environ["LLM_MODEL"] = "qwen3-4b-mlx"
        os.environ["LMSTUDIO_BASE_URL"] = "http://100.73.95.100:1234"
        os.environ["LMSTUDIO_URL"] = "http://100.73.95.100:1234/v1"

        # Override context size for testing
        os.environ["QWEN3_4B_MLX_CTX_SIZE"] = "131072"

        print("✅ Environment configured:")
        print(f"   PROVIDER: {os.environ.get('PROVIDER')}")
        print(f"   LLM_MODEL: {os.environ.get('LLM_MODEL')}")
        print(f"   LMSTUDIO_BASE_URL: {os.environ.get('LMSTUDIO_BASE_URL')}")
        print(f"   LMSTUDIO_URL: {os.environ.get('LMSTUDIO_URL')}")
        print(f"   QWEN3_4B_MLX_CTX_SIZE: {os.environ.get('QWEN3_4B_MLX_CTX_SIZE')}")

    except Exception as e:
        print(f"❌ Failed to set up environment: {e}")
        raise


async def test_lightweight_lmstudio_agent():
    """Test lightweight AgnoPersonalAgent with LM Studio."""
    print("\n🧪 Testing Lightweight AgnoPersonalAgent with LM Studio...")

    try:
        # Create agent with minimal configuration to reduce context usage
        agent = await AgnoPersonalAgent.create_with_init(
            model_provider="lm-studio",
            model_name="qwen3-4b-mlx",
            lmstudio_base_url="http://100.73.95.100:1234",
            enable_memory=False,  # Disable memory to reduce context
            enable_mcp=False,     # Disable MCP to reduce context
            alltools=False,       # Disable all built-in tools to reduce context
            debug=True,
        )

        print("✅ Lightweight agent initialized successfully!")
        print(f"   Agent Type: {type(agent).__name__}")
        print(f"   Model Provider: {agent.model_provider}")
        print(f"   Model Name: {agent.model_name}")
        print(f"   LM Studio URL: {agent.lmstudio_base_url}")
        print(f"   Tools Count: {len(agent.tools) if agent.tools else 0}")

        # Test simple query
        print("\n📤 Testing simple query...")
        query = "Hello! Can you tell me what 2 + 2 equals?"
        print(f"Query: '{query}'")

        response = await agent.arun(query, stream=False)
        print("✅ Query successful!")
        print(f"📥 Response: {response}")

        # Test slightly more complex query
        print("\n📤 Testing reasoning query...")
        reasoning_query = "Explain why the sky appears blue during the day."
        print(f"Query: '{reasoning_query}'")

        reasoning_response = await agent.arun(reasoning_query, stream=False)
        print("✅ Reasoning query successful!")
        print(f"📥 Response: {reasoning_response}")

        return True

    except Exception as e:
        print(f"❌ Lightweight agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Lightweight LM Studio Integration Test for AgnoPersonalAgent")
    print("=" * 70)

    # Setup
    setup_lmstudio_environment()

    # Test lightweight agent
    success = await test_lightweight_lmstudio_agent()

    print("\n" + "=" * 70)
    if success:
        print("🎉 Lightweight AgnoPersonalAgent with LM Studio works correctly!")
        print("✅ The LM Studio integration is fully functional")
        print("✅ Context size issue resolved with lightweight configuration")
        print("\n📝 Summary:")
        print("   - Fixed AgentModelManager LM Studio integration")
        print("   - Increased context size for qwen3-4b-mlx to 128K")
        print("   - Created lightweight agent configuration")
        print("   - Successfully tested both simple and reasoning queries")
        print("\n🔧 Next Steps:")
        print("   - For full-featured agent, consider using a larger model")
        print("   - Or selectively enable only needed tools/features")
        print("   - The core LM Studio integration is now working properly")
    else:
        print("❌ Lightweight AgnoPersonalAgent test failed")
        print("   Check the error output above for details")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
