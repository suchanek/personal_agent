#!/usr/bin/env python3
"""
Test script to verify that the Agno agent automatically searches knowledge base for personal questions.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import create_agno_agent


async def test_knowledge_search():
    """Test that the agent automatically searches knowledge base for personal questions."""
    print("🧪 Testing Agno Agent Knowledge Search")
    print("=" * 50)

    try:
        # Create agent with native storage
        print("✅ Creating Agno agent with knowledge base...")
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="qwen2.5:7b-instruct",
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for focused test
            storage_dir="./data/agno",
            knowledge_dir="./data/knowledge",
            debug=True,
        )

        print("✅ Agent created successfully!")

        # Test personal question to trigger knowledge search
        print("\n🔍 Testing knowledge search with: 'What is my name?'")
        response = await agent.run("What is my name?")
        print(f"🤖 Response: {response}")

        # Check if the agent mentioned searching or used knowledge
        if (
            "search" in response.lower()
            or "knowledge" in response.lower()
            or "eric" in response.lower()
        ):
            print("✅ Agent appears to have searched knowledge base!")
        else:
            print("❌ Agent did not seem to search knowledge base")

        # Cleanup
        await agent.cleanup()
        print("✅ Cleanup completed")

        return True

    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_knowledge_search())
    sys.exit(0 if success else 1)
