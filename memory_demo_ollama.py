#!/usr/bin/env python3
"""
Memory Demo Script using Ollama instead of OpenAI.

This script demonstrates Agno's memory capabilities using a local Ollama model
instead of OpenAI's API.
"""

import time

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from rich.pretty import pprint

from src.personal_agent.config import LLM_MODEL, OLLAMA_URL

# UserId for the memories
user_id = "ava"
# Database file for memory and storage
db_file = "/tmp/agent.db"

# Initialize memory.v2 using Ollama through OpenAI-compatible interface
memory = Memory(
    # Use Ollama model for creating memories via OpenAI-compatible API
    model=OpenAIChat(
        id=LLM_MODEL,
        api_key="ollama",  # Dummy key for local Ollama
        base_url=f"{OLLAMA_URL}/v1",
    ),
    db=SqliteMemoryDb(table_name="user_memories", db_file=db_file),
)
memory.clear()

# Initialize storage
storage = SqliteStorage(table_name="agent_sessions", db_file=db_file)

# Initialize Agent using Ollama
memory_agent = Agent(
    model=OpenAIChat(
        id=LLM_MODEL,
        api_key="ollama",  # Dummy key for local Ollama
        base_url=f"{OLLAMA_URL}/v1",
    ),
    # Store memories in a database
    memory=memory,
    # Give the Agent the ability to update memories
    enable_agentic_memory=False,
    # OR - Run the MemoryManager after each response
    enable_user_memories=True,
    # Store the chat history in the database
    storage=storage,
    # Add the chat history to the messages
    add_history_to_messages=True,
    # Number of history runs
    num_history_runs=3,
    markdown=True,
)

print(f"🤖 Using Ollama model: {LLM_MODEL}")
print(f"🔗 Ollama URL: {OLLAMA_URL}")
print(f"💾 Database file: {db_file}")
print()

# Clear existing memories for fresh start
print("🗑️  Clearing existing memories...")

# Method 1: Use Agno's clear method
try:
    memory.clear()
    print("✅ Agno memory.clear() completed")
except Exception as e:
    print(f"⚠️  Agno clear() failed: {e}")

# Method 2: Direct SQL cleanup to ensure complete clearing
try:
    import sqlite3
    from pathlib import Path

    if Path(db_file).exists():
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check if table exists and get initial count
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_memories'"
        )
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM user_memories")
            before_count = cursor.fetchone()[0]

            if before_count > 0:
                print(f"🧹 Found {before_count} existing memory records, clearing...")

                # Delete all memory records
                cursor.execute("DELETE FROM user_memories")
                deleted_count = cursor.rowcount

                # Reset auto-increment counter
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='user_memories'")

                conn.commit()
                print(f"✅ Deleted {deleted_count} memory records via SQL")

                # Verify clearing
                cursor.execute("SELECT COUNT(*) FROM user_memories")
                remaining_count = cursor.fetchone()[0]

                if remaining_count == 0:
                    print("✅ Memory database is now clean")
                else:
                    print(f"⚠️  Warning: {remaining_count} records still remain")
            else:
                print("✅ Memory database was already empty")
        else:
            print("ℹ️  No memory table exists yet")

        conn.close()
    else:
        print("ℹ️  Database file does not exist yet")

except Exception as e:
    print(f"⚠️  SQL cleanup failed: {e}")

# Final verification
remaining_memories = memory.get_user_memories(user_id=user_id)
if remaining_memories:
    print(f"⚠️  Warning: {len(remaining_memories)} memories still exist after cleanup")
    for i, mem in enumerate(remaining_memories[:3]):
        print(f"   {i+1}. '{mem.memory}' [topics: {mem.topics}]")
    if len(remaining_memories) > 3:
        print(f"   ... and {len(remaining_memories) - 3} more")
else:
    print("✅ Memory database confirmed clean")

print("\n🧪 Testing memory capabilities with Ollama...")
print("=" * 50)

# List of random facts about Ava to test memory storage
ava_facts = [
    "My name is Ava and I like to ski.",
    "I live in San Francisco, California.",
    "I work as a software engineer at a tech startup.",
    "My favorite color is deep blue like the ocean.",
    "I have a golden retriever named Max who loves hiking.",
    "I'm allergic to shellfish but love sushi.",
    "I speak three languages: English, Spanish, and French.",
    "My birthday is on March 15th, and I'm 28 years old.",
    "I play the piano and have been taking lessons for 10 years.",
    "I'm a vegetarian and love cooking Italian food.",
    "I drive a red Tesla Model 3.",
    "My favorite book is 'The Alchemist' by Paulo Coelho.",
]

print(f"🔄 Testing memory storage with {len(ava_facts)} facts about Ava...")
print("=" * 60)

# Process each fact and check memory storage
for i, fact in enumerate(ava_facts, 1):
    print(f"\n🗣️  Fact {i}/{len(ava_facts)}: {fact}")

    memory_agent.print_response(
        fact,
        user_id=user_id,
        stream=True,
        stream_intermediate_steps=True,
    )

    # Allow time for memory processing
    time.sleep(2)

    print(f"\n📝 Memories stored after fact {i}:")
    memories = memory.get_user_memories(user_id=user_id)
    print(f"Total memories: {len(memories)}")
    for j, mem in enumerate(memories, 1):
        print(f"  {j}. '{mem.memory}' [topics: {mem.topics}]")
    print()

print("\n🎯 Testing memory retrieval with a question...")
memory_agent.print_response(
    "Tell me everything you know about me. Include my personal details, preferences, and lifestyle.",
    user_id=user_id,
    stream=True,
    stream_intermediate_steps=True,
)

# Allow time for processing
time.sleep(2)

print("\n🏔️  Testing specific memory usage...")
memory_agent.print_response(
    "Where should I move to ski more? Only give me a single city name within a 4 hour drive.",
    user_id=user_id,
    stream=True,
    stream_intermediate_steps=True,
)

# Allow time for processing
time.sleep(2)

print("\n📊 Final Memory Analysis:")
print("=" * 50)
final_memories = memory.get_user_memories(user_id=user_id)
print(f"Total memories stored: {len(final_memories)}")
print(f"Input facts provided: {len(ava_facts)}")
print(
    f"Memory storage efficiency: {len(final_memories)}/{len(ava_facts)} = {len(final_memories)/len(ava_facts)*100:.1f}%"
)

print("\n🧠 Detailed Memory Breakdown:")
topic_counts = {}
for i, memory_obj in enumerate(final_memories, 1):
    print(f"\n{i}. Memory: '{memory_obj.memory}'")
    print(f"   Topics: {memory_obj.topics}")
    print(f"   Created: {memory_obj.last_updated}")

    # Count topics for analysis (handle None case)
    if memory_obj.topics:
        for topic in memory_obj.topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    else:
        topic_counts["[No Topics]"] = topic_counts.get("[No Topics]", 0) + 1

print(f"\n🏷️  Topic Distribution:")
for topic, count in sorted(topic_counts.items()):
    print(f"   {topic}: {count} memories")

print(f"\n🔍 Memory Quality Analysis:")
memories_with_topics = len([m for m in final_memories if m.topics])
memories_without_topics = len([m for m in final_memories if not m.topics])
duplicate_memories = len(final_memories) - len(set([m.memory for m in final_memories]))

print(f"   Memories with topics: {memories_with_topics}")
print(f"   Memories without topics: {memories_without_topics}")
print(f"   Duplicate memories detected: {duplicate_memories}")
print(f"   Unique memories: {len(set([m.memory for m in final_memories]))}")

if duplicate_memories > 0:
    print(f"\n⚠️  Duplicate Memory Issues Detected:")
    memory_texts = [m.memory for m in final_memories]
    seen = set()
    duplicates = set()
    for memory_text in memory_texts:
        if memory_text in seen:
            duplicates.add(memory_text)
        else:
            seen.add(memory_text)

    for duplicate in duplicates:
        count = memory_texts.count(duplicate)
        print(f"   '{duplicate}' appears {count} times")

print("\n✅ Comprehensive memory demo completed!")
