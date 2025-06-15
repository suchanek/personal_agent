#!/usr/bin/env python3
"""
Memory demonstration using Ollama with AntiDuplicateMemory.

This script shows how to use the AntiDuplicateMemory system with Ollama models
to create, store, and retrieve user memories while preventing duplication.
"""

import os
import sys
from pathlib import Path

from rich.pretty import pprint

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.storage.sqlite import SqliteStorage
from agno.tools.duckduckgo import DuckDuckGoTools

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL
from personal_agent.core.anti_duplicate_memory import AntiDuplicateMemory

# User ID for the memories
user_id = "maya"
# Database file for memory and storage
db_file = f"{AGNO_STORAGE_DIR}/ollama_memory_demo.db"

# Make sure the directory exists
os.makedirs(os.path.dirname(db_file), exist_ok=True)

# Initialize model
model = Ollama(id="llama3.1:8b")

# Initialize database
memory_db = SqliteMemoryDb(table_name="user_memories", db_file=db_file)

Nmemory = Memory(
    # Use any model for creating memories
    model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
    db=SqliteMemoryDb(table_name="user_memories", db_file=db_file),
)

# Initialize AntiDuplicateMemory
memory = AntiDuplicateMemory(
    model=model,
    db=memory_db,
    similarity_threshold=0.8,
    enable_semantic_dedup=True,
    enable_exact_dedup=True,
    debug_mode=True,
    enable_optimizations=True,
)

# Initialize storage
storage = SqliteStorage(table_name="agent_sessions", db_file=db_file)

# Initialize Agent
memory_agent = Agent(
    model=model,
    # Store memories in a database with anti-duplication
    memory=memory,
    # Give the Agent the ability to update memories
    enable_agentic_memory=True,
    # OR - Run the MemoryManager after each response
    enable_user_memories=True,
    # Store the chat history in the database
    storage=storage,
    # Add the chat history to the messages
    add_history_to_messages=True,
    # Number of history runs
    num_history_runs=3,
    tools=[DuckDuckGoTools()],
    markdown=True,
)


def clear_memory():
    """Clear all memories for the current user."""
    user_memories = memory.get_user_memories(user_id=user_id)
    for mem in user_memories:
        memory.delete_user_memory(mem.memory_id, user_id=user_id)
    print(f"✅ Cleared {len(user_memories)} memories for user {user_id}")


def display_memories():
    """Display all memories for the current user."""
    print(f"\n🧠 Memories about {user_id}:")
    memories = memory.get_user_memories(user_id=user_id)

    if not memories:
        print("No memories found.")
    else:
        for i, mem in enumerate(memories, 1):
            print(f"{i}. {mem.memory}")
            if mem.topics:
                print(f"   Topics: {', '.join(mem.topics)}")
    print()


def main():
    """Run the memory demonstration."""
    print("\n🧪 Starting Ollama Memory Demo with AntiDuplicateMemory")
    print("=" * 70)

    # Clear any existing memories
    clear_memory()
    display_memories()

    print("\n💬 Interaction 1: Basic personal information")
    memory_agent.print_response(
        "My name is Maya and I'm a software developer who specializes in machine learning. store this memory",
        user_id=user_id,
        stream=True,
        stream_intermediate_steps=True,
    )
    display_memories()

    print("\n💬 Interaction 2: Additional personal details")
    memory_agent.print_response(
        "I live in Seattle and I enjoy hiking in the mountains on weekends. store this memory",
        user_id=user_id,
        stream=True,
        stream_intermediate_steps=True,
    )
    display_memories()

    print("\n💬 Interaction 3: Similar information (testing deduplication)")
    memory_agent.print_response(
        "I'm a machine learning engineer based in Seattle who likes outdoor activities. store this memory",
        user_id=user_id,
        stream=True,
        stream_intermediate_steps=True,
    )
    display_memories()

    print("\n💬 Interaction 4: Question about local recommendations")
    memory_agent.print_response(
        "What are some good coffee shops near downtown Seattle? store this memory",
        user_id=user_id,
        stream=True,
        stream_intermediate_steps=True,
    )
    display_memories()

    print("\n🔍 Testing memory retrieval")
    search_terms = ["seattle", "software", "hiking"]

    for term in search_terms:
        print(f"\nSearching for: '{term}'")
        relevant_memories = memory.search_user_memories(
            query=term, user_id=user_id, limit=3
        )

        if relevant_memories:
            print(f"Found {len(relevant_memories)} relevant memories:")
            for i, mem in enumerate(relevant_memories, 1):
                print(f"  {i}. '{mem.memory}'")
        else:
            print("No relevant memories found")

    # Show memory statistics
    stats = memory.get_memory_stats(user_id=user_id)
    print("\n📊 Memory Statistics:")
    for key, value in stats.items():
        if key not in ["duplicate_pairs", "combined_memory_indices"]:
            print(f"  {key}: {value}")

    print("\n✅ Memory demo completed")
    print("\nTo clean up all memories for this demo, run:")
    print("python ollama_memory_demo.py --cleanup")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ollama Memory Demo")
    parser.add_argument("--cleanup", action="store_true", help="Clean up all memories")

    args = parser.parse_args()

    if args.cleanup:
        clear_memory()
        print(f"Database location: {db_file}")
    else:
        main()
