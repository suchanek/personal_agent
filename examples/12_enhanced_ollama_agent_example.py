#!/usr/bin/env python3
"""
Practical Example: Using AntiDuplicateMemory with Ollama Agent.

This example shows how to create a production-ready agent using
the AntiDuplicateMemory class to prevent duplicate memories.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.models.ollama import Ollama
from rich import print
from rich.console import Console
from rich.panel import Panel

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, USER_ID
from personal_agent.core.anti_duplicate_memory import create_anti_duplicate_memory


class EnhancedOllamaAgent:
    """Production-ready Ollama agent with anti-duplicate memory."""

    def __init__(
        self,
        model_name: str = LLM_MODEL,
        user_id: str = USER_ID,
        similarity_threshold: float = 0.8,
        debug_mode: bool = False,
    ):
        """
        Initialize the enhanced agent.

        :param model_name: Ollama model to use
        :param user_id: User ID for memory management
        :param similarity_threshold: Threshold for duplicate detection
        :param debug_mode: Enable debug output
        """
        self.model_name = model_name
        self.user_id = user_id
        self.debug_mode = debug_mode

        # Initialize memory database
        self.memory_db = SqliteMemoryDb(
            table_name="enhanced_agent_memory",
            db_file=f"{AGNO_STORAGE_DIR}/enhanced_agent.db",
        )

        # Create anti-duplicate memory
        self.memory = create_anti_duplicate_memory(
            db=self.memory_db,
            model=Ollama(id=model_name, host="http://100.100.248.61:11434"),
            similarity_threshold=similarity_threshold,
            debug_mode=debug_mode,
        )

        # Create the agent
        self.agent = Agent(
            model=Ollama(id=model_name, host="http://100.100.248.61:11434"),
            user_id=user_id,
            memory=self.memory,
            enable_user_memories=True,
            enable_agentic_memory=False,
            add_history_to_messages=False,
            instructions=self._get_optimized_instructions(),
            debug_mode=debug_mode,
        )

        print(f"🤖 Enhanced Ollama Agent initialized")
        print(f"   Model: {model_name}")
        print(f"   User ID: {user_id}")
        print(f"   Similarity threshold: {similarity_threshold}")
        print(f"   Debug mode: {debug_mode}")

    def _get_optimized_instructions(self) -> str:
        """Get optimized instructions for Ollama models."""
        return """You are a helpful personal assistant with excellent memory management.

SPECIAL COMMAND: When the user begins a statement with a ! IMMEDIATELY call the store user memory tool with the remainder of the input as a literal string.

MEMORY CREATION GUIDELINES:
1. Create separate, specific memories for distinct facts
2. Each memory should contain only ONE piece of information
3. Avoid combining multiple facts into a single memory
4. Be precise and factual in your memory descriptions

EXAMPLES OF GOOD MEMORIES:
- "User's name is John"
- "User works as a software engineer"
- "User lives in Seattle"
- "User's favorite color is blue"

EXAMPLES OF BAD MEMORIES (too combined):
- "User's name is John and he works as a software engineer in Seattle"
- "User likes blue and green colors and also enjoys hiking"

When users share personal information, focus on creating clean, 
granular memories that will be useful for future conversations."""

    async def chat(self, message: str) -> str:
        """
        Chat with the agent and manage memories.

        :param message: User message
        :return: Agent response
        """
        if self.debug_mode:
            print(f"\n💬 User: {message}")

        # Check memory state before
        memories_before = self.memory.get_user_memories(user_id=self.user_id)

        # Get response from agent
        response = await self.agent.arun(message)

        # Check memory state after
        memories_after = self.memory.get_user_memories(user_id=self.user_id)
        new_memories = memories_after[len(memories_before) :]

        if self.debug_mode and new_memories:
            print(f"🧠 New memories created: {len(new_memories)}")
            for i, mem in enumerate(new_memories, 1):
                print(f"   {i}. {mem.memory}")

        return response

    def get_memory_summary(self) -> dict:
        """Get a summary of current memories."""
        return self.memory.get_memory_stats(user_id=self.user_id)

    def print_memory_analysis(self):
        """Print detailed memory analysis."""
        self.memory.print_memory_analysis(user_id=self.user_id)

    def list_all_memories(self):
        """List all current memories."""
        memories = self.memory.get_user_memories(user_id=self.user_id)
        if not memories:
            print("📝 No memories found")
            return

        print(f"📝 All memories ({len(memories)}):")
        for i, mem in enumerate(memories, 1):
            print(f"  {i}. {mem.memory}")
            if mem.topics:
                print(f"     Topics: {', '.join(mem.topics)}")

    def clear_memories(self):
        """Clear all memories (use with caution)."""
        self.memory_db.clear()
        print("🗑️  All memories cleared")


async def interactive_demo():
    """Run an interactive demo of the enhanced agent."""
    console = Console()

    console.print(
        Panel.fit(
            "🚀 Enhanced Ollama Agent with Anti-Duplicate Memory\n\n"
            "This demo shows how the AntiDuplicateMemory class prevents\n"
            "duplicate memory creation in Ollama models.\n\n"
            "Commands:\n"
            "• Type your message to chat\n"
            "• 'memories' - Show all memories\n"
            "• 'analysis' - Show memory analysis\n"
            "• 'stats' - Show memory statistics\n"
            "• 'clear' - Clear all memories\n"
            "• 'quit' - Exit the demo",
            style="bold blue",
        )
    )

    # Create enhanced agent
    agent = EnhancedOllamaAgent(debug_mode=True)

    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == "memories":
                agent.list_all_memories()
                continue
            elif user_input.lower() == "analysis":
                agent.print_memory_analysis()
                continue
            elif user_input.lower() == "stats":
                stats = agent.get_memory_summary()
                print(f"📊 Memory Stats: {stats}")
                continue
            elif user_input.lower() == "clear":
                agent.clear_memories()
                continue

            # Get response from agent
            response = await agent.chat(user_input)
            print(f"🤖 Assistant: {response}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"💥 Error: {e}")


async def automated_demo():
    """Run an automated demo showing the difference."""
    console = Console()

    console.print(
        Panel.fit(
            "🎭 Automated Demo: Testing Anti-Duplicate Memory", style="bold green"
        )
    )

    # Create enhanced agent
    agent = EnhancedOllamaAgent(debug_mode=True)

    # Clear any existing memories
    agent.clear_memories()

    # Test messages that typically cause duplicates
    test_messages = [
        "Hi! My name is Sarah and I'm 28 years old.",
        "I work as a data scientist at Google in Mountain View.",
        "I love hiking and photography in my free time.",
        "I live in Mountain View, California.",  # Potential location duplicate
        "My hobbies include hiking and reading books.",  # Potential hobby duplicate
        "I'm a data scientist working on machine learning projects.",  # Potential job duplicate
    ]

    print(f"\n🧪 Running automated test with {len(test_messages)} messages...")

    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Message {i} ---")
        response = await agent.chat(message)
        print(f"🤖 Response: {response}")

        # Small delay for readability
        await asyncio.sleep(1)

    # Show final analysis
    print(f"\n📊 FINAL ANALYSIS:")
    agent.print_memory_analysis()

    print(f"\n✅ Automated demo complete!")


async def main():
    """Main function to choose demo type."""
    console = Console()

    console.print(
        Panel.fit(
            "Choose Demo Type:\n\n"
            "1. Interactive Demo - Chat with the agent\n"
            "2. Automated Demo - Run predefined test cases\n"
            "3. Both - Run automated demo first, then interactive",
            style="bold cyan",
        )
    )

    choice = input("\nEnter choice (1, 2, or 3): ").strip()

    if choice == "1":
        await interactive_demo()
    elif choice == "2":
        await automated_demo()
    elif choice == "3":
        await automated_demo()
        print(f"\n" + "=" * 50)
        print("Now starting interactive demo...")
        await interactive_demo()
    else:
        print("Invalid choice. Running interactive demo.")
        await interactive_demo()


if __name__ == "__main__":
    asyncio.run(main())
