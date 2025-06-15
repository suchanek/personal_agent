#!/usr/bin/env python3
"""
Memory-Optimized Ollama Agent with Enhanced Prompting for Better Memory Managem        # Create memory instance
        self.memory = Memory(
            db=memory_db,
            model=Ollama(
                id=self.model_name,
            )
        )is example demonstrates how to improve Ollama model behavior for memory creation
to achieve similar granularity and intelligence as OpenAI models while maintaining
local privacy.

Key Enhancements:
1. Explicit memory creation prompting
2. Memory granularity guidance
3. Smart duplication prevention
4. Enhanced user interaction patterns

Addresses the issue where Ollama models create combined memories instead of
separate, focused memories like OpenAI models.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from rich import print
from rich.console import Console

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID


class MemoryOptimizedOllamaAgent:
    """An Ollama agent optimized for intelligent memory creation and management."""

    def __init__(self, user_id: str = USER_ID, model_name: str = LLM_MODEL):
        self.user_id = user_id
        self.model_name = model_name
        self.agent = None
        self.memory = None
        self.console = Console()

    def create_memory_instructions(self) -> str:
        """Create enhanced memory instructions for Ollama models."""
        return """
## ENHANCED MEMORY MANAGEMENT INSTRUCTIONS

### Memory Creation Philosophy:
- Create SEPARATE, FOCUSED memories for each distinct piece of information
- Avoid combining multiple facts into single memories
- Each memory should represent ONE clear concept or fact

### Memory Granularity Guidelines:
1. **Personal Identity**: Separate memories for name, age, location, etc.
2. **Professional Info**: Separate memories for job title, company, skills, etc.
3. **Preferences**: Individual memories for each preference, hobby, or interest
4. **Relationships**: Separate memories for different people and pets
5. **Experiences**: Individual memories for specific events or activities

### Memory Creation Examples:
❌ WRONG (Combined): "User is Eric, works as software engineer, likes Python and has a cat"
✅ CORRECT (Separated):
   - "User's name is Eric"
   - "User works as a software engineer" 
   - "User enjoys programming in Python"
   - "User has a cat"

### Processing New Information:
1. **Identify distinct facts** in user input
2. **Create separate memories** for each fact
3. **Use specific, clear language** for each memory
4. **Avoid redundancy** with existing memories
5. **Update existing memories** when information changes

### Memory Quality Standards:
- Be specific and concrete
- Use clear, searchable language
- Focus on factual information
- Separate opinions from facts
- Include relevant context when helpful

### Duplication Prevention:
- Before creating new memories, consider existing memories
- Update rather than duplicate when information overlaps
- Merge only when information is truly related
- Maintain granular separation of distinct concepts

Remember: Quality memory management enables better personalization and context awareness.
"""

    async def initialize_agent(self) -> bool:
        """Initialize the Ollama agent with memory optimization."""
        print("🧪 Initializing Memory-Optimized Ollama Agent")
        print("=" * 60)

        # Create memory database
        memory_db = SqliteMemoryDb(
            table_name="memory_optimized_agent",
            db_file=f"{AGNO_STORAGE_DIR}/memory_optimized_agent.db",
        )

        # Create memory instance
        self.memory = Memory(
            db=memory_db,
            model=Ollama(
                id=self.model_name,
            ),
        )

        # Create agent with enhanced instructions
        enhanced_instructions = f"""
You are a helpful AI assistant with enhanced memory management capabilities.

{self.create_memory_instructions()}

## Core Behavior:
- Always be helpful, friendly, and conversational
- Pay close attention to personal information shared by users
- Create intelligent, granular memories for better future interactions
- Acknowledge when you remember information about the user
- Ask clarifying questions when information is unclear

## Response Style:
- Be natural and conversational
- Reference relevant memories when appropriate
- Show that you remember and care about the user's information
- Provide personalized responses based on stored memories
"""

        self.agent = Agent(
            model=Ollama(
                id=self.model_name,
            ),
            user_id=self.user_id,
            memory=self.memory,
            enable_agentic_memory=True,  # Enable agentic memory
            enable_user_memories=False,  # Disable to avoid conflicts
            instructions=enhanced_instructions,
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True,
        )

        print(f"✅ Agent initialized successfully for user: {self.user_id}")
        print(f"📊 Model: {self.model_name}")
        print(f"🧠 Memory: Enabled with enhanced prompting")
        return True

    async def run_interaction(self, message: str, context: str = "") -> Dict[str, Any]:
        """Run a single interaction with memory analysis."""
        print(f"\n💬 {context}")
        print(f"User: {message}")

        # Get memories before interaction
        memories_before = self.memory.get_user_memories(user_id=self.user_id)

        # Run the interaction
        response = await self.agent.arun(message)

        # Get memories after interaction
        memories_after = self.memory.get_user_memories(user_id=self.user_id)

        # Analyze memory changes
        new_memories = [m for m in memories_after if m not in memories_before]

        print(f"Assistant: {response}")

        if new_memories:
            print(f"\n🧠 New Memories Created ({len(new_memories)}):")
            for i, memory in enumerate(new_memories, 1):
                print(f"  {i}. {memory.memory}")
                if memory.topics:
                    print(f"     Topics: {', '.join(memory.topics)}")

        print(f"\n📊 Total Memories: {len(memories_after)}")

        return {
            "message": message,
            "response": response,
            "memories_before": len(memories_before),
            "memories_after": len(memories_after),
            "new_memories": len(new_memories),
            "new_memory_details": [m.memory for m in new_memories],
        }

    async def demonstrate_memory_optimization(self):
        """Demonstrate the memory optimization capabilities."""
        print("\n🎯 DEMONSTRATION: Memory-Optimized Ollama Agent")
        print("=" * 70)

        # Test scenarios designed to showcase improved memory granularity
        test_scenarios = [
            {
                "message": "Hi! My name is Eric and I'm a software engineer at TechCorp.",
                "context": "Professional Introduction",
                "expected": "Should create separate memories for name and job",
            },
            {
                "message": "I love programming in Python and JavaScript, and I enjoy hiking on weekends.",
                "context": "Interests and Hobbies",
                "expected": "Should create separate memories for each programming language and hobby",
            },
            {
                "message": "I have a cat named Whiskers who is 3 years old, and I live in San Francisco.",
                "context": "Personal Details",
                "expected": "Should create separate memories for pet, pet details, and location",
            },
            {
                "message": "Actually, Whiskers just turned 4 last week! And I got promoted to Senior Software Engineer.",
                "context": "Information Updates",
                "expected": "Should update existing memories rather than create duplicates",
            },
            {
                "message": "I'm thinking about learning Rust programming and maybe getting a second cat.",
                "context": "Future Plans",
                "expected": "Should create memories for future interests and plans",
            },
        ]

        results = []

        for scenario in test_scenarios:
            print(f"\n📝 Expected: {scenario['expected']}")
            result = await self.run_interaction(
                scenario["message"], scenario["context"]
            )
            results.append(result)

            # Small delay to ensure proper processing
            await asyncio.sleep(1)

        # Final memory analysis
        await self.analyze_final_memories()

        return results

    async def analyze_final_memories(self):
        """Analyze the final state of memories for quality assessment."""
        print("\n📊 FINAL MEMORY ANALYSIS")
        print("=" * 50)

        all_memories = self.memory.get_user_memories(user_id=self.user_id)

        print(f"Total Memories Created: {len(all_memories)}")
        print("\n🧠 All Memories:")

        for i, memory in enumerate(all_memories, 1):
            print(f"\n{i}. Memory: {memory.memory}")
            if memory.topics:
                print(f"   Topics: {', '.join(memory.topics)}")
            if hasattr(memory, "created_at") and memory.created_at:
                print(f"   Created: {memory.created_at}")

        # Quality assessment
        print(f"\n📈 QUALITY ASSESSMENT:")
        print(
            f"- Memory Count: {len(all_memories)} (Higher count suggests better granularity)"
        )
        print(
            f"- Average Memory Length: {sum(len(m.memory) for m in all_memories) / len(all_memories):.1f} chars"
        )

        # Check for potential issues
        combined_memories = [
            m for m in all_memories if " and " in m.memory and len(m.memory) > 50
        ]
        if combined_memories:
            print(f"- ⚠️  Potential Combined Memories: {len(combined_memories)}")
            for cm in combined_memories:
                print(f"    • {cm.memory}")
        else:
            print(f"- ✅ No obvious combined memories detected")

    async def cleanup(self):
        """Clean up resources."""
        if hasattr(self.agent, "cleanup"):
            await self.agent.cleanup()


async def main():
    """Run the memory optimization demonstration."""
    agent = MemoryOptimizedOllamaAgent()

    try:
        # Initialize the agent
        await agent.initialize_agent()

        # Run the demonstration
        results = await agent.demonstrate_memory_optimization()

        # Print summary
        print("\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 50)
        print("Key Improvements Demonstrated:")
        print("✅ Enhanced prompting for memory granularity")
        print("✅ Explicit instructions for memory separation")
        print("✅ Update vs. creation guidance")
        print("✅ Quality assessment and monitoring")

        total_memories = sum(r["new_memories"] for r in results)
        print(f"\n📊 Total New Memories Created: {total_memories}")

        if total_memories >= 8:  # Expecting ~8-10 separate memories
            print("🎯 SUCCESS: Good memory granularity achieved!")
        elif total_memories >= 5:
            print("⚠️  PARTIAL: Some improvement, but could be more granular")
        else:
            print("❌ ISSUE: Still creating combined memories")

    except KeyboardInterrupt:
        print("\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n💥 Error during demonstration: {e}")
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
