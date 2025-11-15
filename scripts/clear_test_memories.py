#!/usr/bin/env python3
"""
Script to clear test memories from the database.
"""

import asyncio
import sys
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def clear_memories():
    """Clear all memories from the database."""
    print("🧹 Clearing test memories...")
    
    # Initialize agent
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=False,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return False
    
    # Clear all memories
    result = agent.agno_memory.memory_manager.clear_memories(
        db=agent.agno_memory.db, 
        user_id=USER_ID
    )
    
    if result[0]:  # success
        print(f"✅ {result[1]}")
        return True
    else:
        print(f"❌ {result[1]}")
        return False


if __name__ == "__main__":
    success = asyncio.run(clear_memories())
    if success:
        print("✅ Memories cleared successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to clear memories!")
        sys.exit(1)
