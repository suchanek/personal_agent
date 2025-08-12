import asyncio
import sys
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

from src.personal_agent.core.agno_agent import create_agno_agent


async def main():
    """Initializes the agent and prints its information."""
    print("🚀 Initializing agent to test print_agent_info()...")
    try:
        # Use the factory function to create and initialize the agent
        agent = await create_agno_agent(
            user_id="Eric",
            enable_mcp=True,  # Disable MCP for a quicker, focused test
            debug=False,
        )

        print("\n" + "=" * 50)
        print("🤖 Calling print_agent_info()...")
        print("=" * 50 + "\n")

        # The print_agent_info method uses Rich Console to print formatted output
        agent.print_agent_info()

        print("\n" + "=" * 50)
        print("✅ Test script finished.")
        print("=" * 50)

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
