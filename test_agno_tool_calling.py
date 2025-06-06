#!/usr/bin/env python3
"""
Test agno agent tool calling specifically.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from personal_agent.agno_main import initialize_agno_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agno_tool_calling():
    """Test that agno agent can call GitHub tools properly."""
    print("=== Testing Agno Agent Tool Calling ===\n")

    # Set required environment variables
    if not os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN"):
        print("⚠️  Warning: GITHUB_PERSONAL_ACCESS_TOKEN not set")
        print("Setting MCP to disabled for this test")
        os.environ["USE_MCP"] = "false"

    try:
        # Initialize the agno system
        print("1. Initializing agno system...")
        agent = await initialize_agno_system()
        print(
            f"✅ Agent initialized with {len(agent.tools) if agent.tools else 0} tools"
        )

        if agent.tools:
            print("\nAvailable tools:")
            for i, tool in enumerate(agent.tools):
                print(f"  {i+1}. {tool.name}: {tool.description}")

        # Test a simple query without tools first
        print("\n2. Testing simple query (no tools)...")
        simple_query = "Hello, what's your name?"
        response = await agent.arun(simple_query)
        print(f"Simple query response: {response.content[:100]}...")

        # Test a query that should trigger tool use if tools are available
        if agent.tools and any("github" in tool.name.lower() for tool in agent.tools):
            print("\n3. Testing GitHub search query...")
            github_query = "Search GitHub for proteusPy"

            try:
                response = await agent.arun(github_query)
                print(f"GitHub query response: {response.content[:200]}...")

                if "proteusPy" in response.content or "suchanek" in response.content:
                    print("✅ GitHub search appears to have worked!")
                else:
                    print("❌ GitHub search may not have worked as expected")

            except Exception as e:
                print(f"❌ Error during GitHub search: {e}")
        else:
            print("\n3. No GitHub tools available, skipping GitHub test")

        print("\n✅ Agno tool calling test completed")

    except Exception as e:
        print(f"❌ Error during agno tool calling test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agno_tool_calling())
