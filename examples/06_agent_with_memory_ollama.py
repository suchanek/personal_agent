"""
This example shows you how to use persistent memory with an Agent using Ollama.

After each run, user memories are created/updated.

To enable this, set `enable_user_memories=True` in the Agent config.

This version uses your Ollama setup instead of OpenAI and includes debugging.
"""

import logging
from uuid import uuid4

from agno.agent.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.storage.sqlite import SqliteStorage
from rich.pretty import pprint

# Enable debug logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Enable specific loggers that might show memory processing
logging.getLogger("agno.memory").setLevel(logging.DEBUG)
logging.getLogger("agno.agent").setLevel(logging.DEBUG)
logging.getLogger("agno.models").setLevel(logging.DEBUG)

# Use your Ollama configuration
OLLAMA_URL = "http://tesla.local:11434"
LLM_MODEL = "qwen3:1.7B"  # Available model on tesla.local

memory_db = SqliteMemoryDb(table_name="memory", db_file="tmp/memory_ollama.db")

# No need to set the model, it gets set by the agent to the agent's model
memory = Memory(db=memory_db)

# Reset the memory for this example
memory.clear()

session_id = str(uuid4())
eric_user_id = "Eric"  # Using your actual user ID


def print_memory_debug(step_name: str):
    """Print detailed memory debug information."""
    print(f"\n🔍 DEBUG - {step_name}")
    print("-" * 40)

    memories = memory.get_user_memories(user_id=eric_user_id)
    print(f"Total memories for Eric: {len(memories)}")

    for i, mem in enumerate(memories, 1):
        print(f"  {i}. Memory ID: {mem.memory_id}")
        print(f"     Content: {mem.memory}")
        print(f"     Topics: {mem.topics}")
        print(f"     Updated: {mem.last_updated}")
        print()


# Create agent with Ollama model
agent = Agent(
    model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
    memory=memory,
    storage=SqliteStorage(
        table_name="agent_sessions_ollama", db_file="tmp/persistent_memory_ollama.db"
    ),
    enable_user_memories=True,
    debug_mode=True,  # Enable debug mode
    show_tool_calls=True,  # Show tool calls
)

print("🚀 Testing Ollama Memory Agent")
print("=" * 50)

print_memory_debug("INITIAL STATE")

# Test 1: Store personal information
print("\n📝 Test 1: Storing personal information")
agent.print_response(
    "My name is Eric and I live in Ohio. I prefer Tea over coffee.",
    stream=True,
    user_id=eric_user_id,
    session_id=session_id,
)

print_memory_debug("AFTER TEST 1")

# Test 2: Ask about stored information
print("\n🔍 Test 2: Asking about stored information")
agent.print_response(
    "What do you know about me?",
    stream=True,
    user_id=eric_user_id,
    session_id=session_id,
)

print_memory_debug("AFTER TEST 2")

# Test 3: Update information
print("\n✏️ Test 3: Updating information")
agent.print_response(
    "Actually, I've moved to California and now I prefer tea over coffee.",
    stream=True,
    user_id=eric_user_id,
    session_id=session_id,
)

print_memory_debug("AFTER TEST 3")

# Test 4: Ask again to see if memory was updated
print("\n🔍 Test 4: Checking updated information")
agent.print_response(
    "Where do I live and what's my drink preference?",
    stream=True,
    user_id=eric_user_id,
    session_id=session_id,
)

print_memory_debug("FINAL STATE")

print("\n✅ Memory test completed!")

# Final comparison with original working OpenAI approach
print("\n🔍 COMPARISON WITH OPENAI APPROACH:")
print("- OpenAI: Creates distinct, non-duplicate memories")
print("- Ollama: Creates duplicate memories (if duplicates found above)")
print("- The issue is likely in how Ollama processes memory updates vs OpenAI")
agent.print_response(
    "Where do I live and what's my drink preference?",
    stream=True,
    user_id=eric_user_id,
    session_id=session_id,
)

# Print updated memories
memories = agent.get_user_memories(user_id=eric_user_id)
print("\n🧠 Eric's updated memories:")
pprint(memories)

print("\n✅ Memory test completed!")
