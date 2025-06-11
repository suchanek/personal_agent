#!/usr/bin/env python3
"""
Simple memory system debug script to investigate duplication issues
"""

import asyncio
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Import directly from the agno_main module
import personal_agent.agno_main as agno_main

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_memory_simple():
    """Simple memory debug test"""
    print("🔍 Simple Memory Debug Test")
    print("=" * 50)

    try:
        # Create agent
        print("🤖 Creating agent...")
        agent = await agno_main.create_agno_agent(
            enable_memory=True, debug=True, storage_dir="./data/debug_agno"
        )
        print("✅ Agent created")

        # Check if memory system exists
        if hasattr(agent, "memory") and agent.memory:
            print("💾 Memory system found")

            # Get current memories
            print("📋 Retrieving current memories...")
            try:
                memories = await agent.memory.aget_memories(user_id="debug_user")
                print(f"📊 Found {len(memories)} memories")

                # Show first few memories
                for i, memory in enumerate(memories[:10]):
                    print(f"  {i+1}. {memory}")

                if len(memories) > 10:
                    print(f"  ... and {len(memories) - 10} more")

            except Exception as e:
                print(f"❌ Error retrieving memories: {e}")

            # Try to clear memories if there are too many duplicates
            if len(memories) > 20:
                print("🧹 Too many duplicate memories found, clearing...")
                try:
                    await agent.memory.aclear_memory_for_user(user_id="debug_user")
                    print("✅ Memories cleared")
                except Exception as e:
                    print(f"❌ Error clearing memories: {e}")
        else:
            print("❌ No memory system found")

    except Exception as e:
        print(f"❌ Error in debug test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_memory_simple())
