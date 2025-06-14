"""
Fair comparison of memory behavior between OpenAI and Ollama using comparable models.

OpenAI: gpt-4o-mini (small, efficient)
Ollama: llama3.1:8b (larger, should be more capable)

This tests the SAME input to see how each model handles memory creation.
"""

import logging
from uuid import uuid4

from agno.agent.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from rich.pretty import pprint

# Configure logging to see memory decisions
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Enable memory logging
logging.getLogger("agno.memory").setLevel(logging.DEBUG)

# Test input
TEST_INPUT = "My name is Eric and I live in Ohio. I prefer tea over coffee."
TEST_QUESTION = "What do you know about me?"


def test_openai_memory():
    """Test OpenAI memory behavior with gpt-4o-mini."""
    print("\n🤖 TESTING OPENAI (gpt-4o-mini)")
    print("=" * 50)

    # Create fresh memory for OpenAI
    memory_db = SqliteMemoryDb(
        table_name="memory_openai", db_file="tmp/memory_comparison_openai.db"
    )
    memory = Memory(db=memory_db)
    memory.clear()

    session_id = str(uuid4())
    user_id = "Eric"

    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        memory=memory,
        storage=SqliteStorage(
            table_name="sessions_openai", db_file="tmp/sessions_comparison_openai.db"
        ),
        enable_user_memories=True,
    )

    print(f"\n📝 Input: {TEST_INPUT}")
    agent.print_response(
        TEST_INPUT,
        stream=False,  # Disable streaming for cleaner output
        user_id=user_id,
        session_id=session_id,
    )

    memories = memory.get_user_memories(user_id=user_id)
    print(f"\n🧠 OpenAI created {len(memories)} memories:")
    for i, mem in enumerate(memories, 1):
        print(f"  {i}. {mem.memory} (topics: {mem.topics})")

    print(f"\n🔍 Question: {TEST_QUESTION}")
    agent.print_response(
        TEST_QUESTION,
        stream=False,
        user_id=user_id,
        session_id=session_id,
    )

    return memories


def test_ollama_memory():
    """Test Ollama memory behavior with llama3.1:8b."""
    print("\n🦙 TESTING OLLAMA (llama3.1:8b)")
    print("=" * 50)

    # Create fresh memory for Ollama
    memory_db = SqliteMemoryDb(
        table_name="memory_ollama", db_file="tmp/memory_comparison_ollama.db"
    )
    memory = Memory(db=memory_db)
    memory.clear()

    session_id = str(uuid4())
    user_id = "Eric"

    agent = Agent(
        model=Ollama(id="llama3.1:8b", host="http://tesla.local:11434"),
        memory=memory,
        storage=SqliteStorage(
            table_name="sessions_ollama", db_file="tmp/sessions_comparison_ollama.db"
        ),
        enable_user_memories=True,
    )

    print(f"\n📝 Input: {TEST_INPUT}")
    agent.print_response(
        TEST_INPUT,
        stream=False,  # Disable streaming for cleaner output
        user_id=user_id,
        session_id=session_id,
    )

    memories = memory.get_user_memories(user_id=user_id)
    print(f"\n🧠 Ollama created {len(memories)} memories:")
    for i, mem in enumerate(memories, 1):
        print(f"  {i}. {mem.memory} (topics: {mem.topics})")

    print(f"\n🔍 Question: {TEST_QUESTION}")
    agent.print_response(
        TEST_QUESTION,
        stream=False,
        user_id=user_id,
        session_id=session_id,
    )

    return memories


def compare_results(openai_memories, ollama_memories):
    """Compare the memory creation results."""
    print("\n📊 COMPARISON RESULTS")
    print("=" * 50)

    print(f"OpenAI (gpt-4o-mini): {len(openai_memories)} memories")
    print(f"Ollama (llama3.1:8b): {len(ollama_memories)} memories")

    if len(openai_memories) != len(ollama_memories):
        print("\n⚠️  DIFFERENT NUMBER OF MEMORIES CREATED!")
        print("This suggests the models handle memory creation differently")
    else:
        print("\n✅ Same number of memories created")

    print("\n🔍 Detailed comparison:")

    max_memories = max(len(openai_memories), len(ollama_memories))
    for i in range(max_memories):
        print(f"\nMemory {i+1}:")

        if i < len(openai_memories):
            openai_mem = openai_memories[i]
            print(f"  OpenAI: {openai_mem.memory} (topics: {openai_mem.topics})")
        else:
            print(f"  OpenAI: (no memory {i+1})")

        if i < len(ollama_memories):
            ollama_mem = ollama_memories[i]
            print(f"  Ollama:  {ollama_mem.memory} (topics: {ollama_mem.topics})")
        else:
            print(f"  Ollama:  (no memory {i+1})")

    # Check for duplicates
    openai_contents = [m.memory for m in openai_memories]
    ollama_contents = [m.memory for m in ollama_memories]

    openai_duplicates = len(openai_contents) != len(set(openai_contents))
    ollama_duplicates = len(ollama_contents) != len(set(ollama_contents))

    print(f"\n🔄 Duplicate check:")
    print(f"  OpenAI has duplicates: {openai_duplicates}")
    print(f"  Ollama has duplicates: {ollama_duplicates}")

    if ollama_duplicates and not openai_duplicates:
        print(
            "\n🎯 FOUND THE ISSUE: Ollama creates duplicate memories, OpenAI doesn't!"
        )
    elif openai_duplicates and not ollama_duplicates:
        print("\n🤔 Interesting: OpenAI creates duplicates, Ollama doesn't")
    elif openai_duplicates and ollama_duplicates:
        print("\n😕 Both models create duplicates - might be a framework issue")
    else:
        print("\n🤷 No duplicates found in either model")


if __name__ == "__main__":
    print("🧪 FAIR MEMORY COMPARISON TEST")
    print("Testing identical input with comparable models")
    print(f"Input: '{TEST_INPUT}'")

    # Test both models
    openai_memories = test_openai_memory()
    ollama_memories = test_ollama_memory()

    # Compare results
    compare_results(openai_memories, ollama_memories)

    print("\n✅ Comparison complete!")
