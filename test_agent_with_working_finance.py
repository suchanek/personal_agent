#!/usr/bin/env python3
"""
Test script to verify the agent now uses working finance tools with proper fallback.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import create_agno_agent


async def test_agent_finance_tools():
    """Test the agent with working finance tools."""
    print("🚀 Testing Agent with Working Finance Tools")
    print("=" * 60)

    try:
        # Create agent with working finance tools
        print("🔧 Creating agent with working YFinance tools...")
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="qwen3:1.7b",
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for simpler testing
            debug=True,
            user_id="test_user",
        )

        print("✅ Agent created successfully!")

        # Test finance tool usage
        print("\n📊 Testing finance tool usage...")
        print("Query: 'call your yfinance tool with argument NVDA'")

        response = await agent.run("call your yfinance tool with argument NVDA")

        print(f"\n📋 Agent Response:")
        print(f"{response}")

        # Check if tools were called
        print(f"\n🔍 Debug Info:")
        print(f"- Agent has {len(agent.agent.tools)} tools")
        print(f"- Debug mode: {agent.debug}")

        # List available tools
        print(f"\n🛠️ Available Tools:")
        for i, tool in enumerate(agent.agent.tools, 1):
            tool_name = getattr(tool, "__name__", str(type(tool).__name__))
            print(f"  {i}. {tool_name}")

        await agent.cleanup()

    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main test function."""
    await test_agent_finance_tools()


if __name__ == "__main__":
    asyncio.run(main())
