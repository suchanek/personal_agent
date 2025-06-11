#!/usr/bin/env python3
"""
Simplified Memory Demo Script using Ollama.

This script demonstrates Agno's memory capabilities with a smaller set of facts
to better test memory storage quality and avoid overwhelming the system.
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
db_file = "/tmp/agent_simplified.db"

# Initialize memory.v2 using Ollama through OpenAI-compatible interface
memory = Memory(
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
    memory=memory,
    enable_agentic_memory=False,
    enable_user_memories=True,
    storage=storage,
    add_history_to_messages=True,
    num_history_runs=3,
    markdown=True,
)

print(f"🤖 Using Ollama model: {LLM_MODEL}")
print(f"🔗 Ollama URL: {OLLAMA_URL}")
print(f"💾 Database file: {db_file}")
print()

# Clear existing memories for fresh start
memory.clear()

# Curated set of diverse facts about Ava to test memory categorization
ava_facts = [
    "My name is Ava and I like to ski.",
    "I live in San Francisco, California.",
    "I work as a software engineer at a tech startup.",
    "My favorite color is deep blue like the ocean.",
    "I have a golden retriever named Max who loves hiking.",
    "I'm allergic to shellfish but love sushi.",
]

print(f"🧪 Testing memory storage with {len(ava_facts)} carefully selected facts...")
print("=" * 70)

# Process each fact with detailed analysis
for i, fact in enumerate(ava_facts, 1):
    print(f"\n🗣️  Processing Fact {i}/{len(ava_facts)}: '{fact}'")

    memory_agent.print_response(
        fact,
        user_id=user_id,
        stream=False,  # Disable streaming for cleaner output
        stream_intermediate_steps=False,
    )

    # Allow time for memory processing
    time.sleep(3)

    print(f"\n📝 Memory Status after fact {i}:")
    current_memories = memory.get_user_memories(user_id=user_id)
    print(f"   Total memories: {len(current_memories)}")

    # Show only new memories added
    if i == 1:
        new_memories = current_memories
    else:
        previous_count = len(
            memory.get_user_memories(user_id=user_id)[: len(current_memories) - 1]
        )
        new_memories = current_memories[previous_count:]

    for j, mem in enumerate(new_memories, 1):
        topics_str = f"[{', '.join(mem.topics)}]" if mem.topics else "[No topics]"
        print(f"   New: '{mem.memory}' {topics_str}")
    print()

print("\n🎯 Testing comprehensive memory retrieval...")
memory_agent.print_response(
    "Tell me a brief summary of what you know about me, including my name, location, job, pet, and interests.",
    user_id=user_id,
    stream=False,
    stream_intermediate_steps=False,
)

time.sleep(2)

print("\n🏔️ Testing memory application...")
memory_agent.print_response(
    "Based on what you know about me, suggest a weekend activity that would suit my interests.",
    user_id=user_id,
    stream=False,
    stream_intermediate_steps=False,
)

time.sleep(2)

print("\n📊 Final Memory Analysis:")
print("=" * 50)
final_memories = memory.get_user_memories(user_id=user_id)
print(f"Total memories stored: {len(final_memories)}")
print(f"Input facts provided: {len(ava_facts)}")
efficiency = len(final_memories) / len(ava_facts) * 100
print(
    f"Memory storage ratio: {len(final_memories)}/{len(ava_facts)} = {efficiency:.1f}%"
)

print(f"\n🧠 Complete Memory Inventory:")
topic_counts = {}
memories_with_topics = 0
memories_without_topics = 0

for i, memory_obj in enumerate(final_memories, 1):
    print(f"\n{i}. '{memory_obj.memory}'")
    if memory_obj.topics:
        topics_display = f"[{', '.join(memory_obj.topics)}]"
        print(f"   Topics: {topics_display}")
        memories_with_topics += 1
        for topic in memory_obj.topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    else:
        print("   Topics: [No topics assigned]")
        memories_without_topics += 1
        topic_counts["[No Topics]"] = topic_counts.get("[No Topics]", 0) + 1

    print(f"   Stored: {memory_obj.last_updated.strftime('%H:%M:%S')}")

print(f"\n🏷️ Topic Analysis:")
print(f"   Memories with topics: {memories_with_topics}")
print(f"   Memories without topics: {memories_without_topics}")
print(f"   Topic coverage: {memories_with_topics/len(final_memories)*100:.1f}%")

print(f"\n🔖 Topic Distribution:")
for topic, count in sorted(topic_counts.items()):
    print(f"   {topic}: {count} memories")

print(f"\n✅ Simplified memory demo completed successfully!")
