#!/usr/bin/env python3
"""
Enhanced Memory Management for Ollama Models using Agno's Native Memory Class.

This scr        # Create memory with enhanced model configuration
        self.memory = Memory(
            db=memory_db,
            model=Ollama(
                id=self.model_name,
                # Enhanced system prompt for memory operations
                instructions=self.get_memory_creation_prompt()
            )
        )trates how to use Agno's native Memory class with enhanced
prompting and explicit tool specifications to achieve better memory management
with Ollama models, addressing the memory duplication and granularity issues.

Key Features:
1. Uses agno.memory.v2.memory.Memory directly
2. Enhanced memory creation prompts
3. Explicit memory management tools
4. Granular memory creation guidance
5. Local privacy maintained
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.memory.v2.schema import UserMemory
from agno.models.ollama import Ollama
from rich import print
from rich.console import Console
from rich.pretty import pprint

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID


class EnhancedMemoryManager:
    """Enhanced memory manager using Agno's native Memory class with optimized prompting."""

    def __init__(self, user_id: str = USER_ID, model_name: str = LLM_MODEL):
        self.user_id = user_id
        self.model_name = model_name
        self.memory = None
        self.console = Console()

    def get_memory_creation_prompt(self) -> str:
        """Get enhanced prompt for better memory creation with Ollama models."""
        return """
You are analyzing user input to create high-quality, granular memories. Follow these strict guidelines:

## MEMORY CREATION RULES:

### 1. GRANULARITY - Create Separate Memories for Each Fact
- ONE memory per distinct piece of information
- Never combine multiple facts into a single memory
- Break down complex information into atomic components

### 2. STRUCTURE - Use Clear, Specific Language
- Start with clear subject identification
- Use factual, searchable language
- Include relevant context when needed
- Keep each memory focused and specific

### 3. EXAMPLES OF PROPER SEPARATION:

Input: "My name is Eric and I work as a software engineer at TechCorp"
❌ WRONG: "User is Eric who works as a software engineer at TechCorp"
✅ CORRECT: 
- "User's name is Eric"
- "User works as a software engineer"
- "User is employed at TechCorp"

Input: "I love Python programming and hiking on weekends"
❌ WRONG: "User loves Python programming and hiking on weekends"
✅ CORRECT:
- "User enjoys programming in Python"
- "User likes hiking"
- "User hikes on weekends"

### 4. CATEGORIES TO SEPARATE:
- Personal identity (name, age, location)
- Professional information (job, company, skills)
- Preferences and interests
- Relationships (family, friends, pets)
- Activities and hobbies
- Goals and plans
- Physical characteristics
- Experiences and events

### 5. UPDATE VS CREATE:
- Check for existing similar memories
- Update existing memories when information changes
- Only create new memories for truly new information

### 6. QUALITY STANDARDS:
- Be specific and concrete
- Use searchable keywords
- Avoid vague language
- Include relevant temporal context
- Maintain factual accuracy

Remember: Better memory granularity leads to better personalization and retrieval.
"""

    async def initialize_memory(self) -> bool:
        """Initialize the enhanced memory system."""
        print("🧠 Initializing Enhanced Memory Manager")
        print("=" * 60)

        # Create memory database
        memory_db = SqliteMemoryDb(
            table_name="enhanced_memory_manager",
            db_file=f"{AGNO_STORAGE_DIR}/enhanced_memory.db",
        )

        # Create memory with enhanced model configuration
        self.memory = Memory(
            db=memory_db,
            model=Ollama(
                id=self.model_name,
                # Enhanced system prompt for memory operations
                instructions=self.get_memory_creation_prompt(),
            ),
        )

        print(f"✅ Memory system initialized")
        print(f"📊 Model: {self.model_name}")
        print(f"💾 Database: enhanced_memory.db")
        return True

    async def create_memories_from_text(
        self, text: str, context: str = ""
    ) -> List[UserMemory]:
        """Create memories from text with enhanced analysis."""
        print(f"\n💭 Processing: {context}")
        print(f"📝 Input: {text}")

        # Get existing memories for comparison
        existing_memories = self.memory.get_user_memories(user_id=self.user_id)
        existing_count = len(existing_memories)

        # Use the memory system to create memories with enhanced prompting
        enhanced_prompt = f"""
        {self.get_memory_creation_prompt()}
        
        Current user input to process: "{text}"
        Context: {context}
        
        Create appropriate granular memories for this information.
        """

        # Create memories using the enhanced system
        self.memory.create_user_memories(message=text, user_id=self.user_id)

        # Get new memories
        updated_memories = self.memory.get_user_memories(user_id=self.user_id)
        new_memories = updated_memories[existing_count:]  # Get only new memories

        print(f"🧠 Created {len(new_memories)} new memories")
        for i, memory in enumerate(new_memories, 1):
            print(f"  {i}. {memory.memory}")
            if memory.topics:
                print(f"     Topics: {', '.join(memory.topics)}")

        return new_memories

    async def demonstrate_granular_memory_creation(self):
        """Demonstrate improved memory creation with various input types."""
        print("\n🎯 DEMONSTRATION: Enhanced Memory Creation")
        print("=" * 70)

        # Test scenarios to demonstrate improved granularity
        test_scenarios = [
            {
                "text": "Hi there! My name is Eric and I'm 28 years old.",
                "context": "Basic Introduction",
                "expected_memories": ["name", "age"],
            },
            {
                "text": "I work as a senior software engineer at TechCorp and I specialize in Python development.",
                "context": "Professional Information",
                "expected_memories": [
                    "job title",
                    "company",
                    "programming language specialty",
                ],
            },
            {
                "text": "I love hiking, reading science fiction novels, and playing chess with friends.",
                "context": "Hobbies and Interests",
                "expected_memories": [
                    "hiking",
                    "reading",
                    "sci-fi preference",
                    "chess",
                    "social activities",
                ],
            },
            {
                "text": "I have a cat named Whiskers who is 3 years old and loves to play with toy mice.",
                "context": "Pet Information",
                "expected_memories": ["has cat", "cat name", "cat age", "cat behavior"],
            },
            {
                "text": "I live in San Francisco, California and I've been there for 5 years now.",
                "context": "Location Details",
                "expected_memories": ["location", "duration of residence"],
            },
            {
                "text": "Actually, I just got promoted to lead engineer and Whiskers turned 4 last month!",
                "context": "Updates to Existing Information",
                "expected_memories": ["job title update", "cat age update"],
            },
        ]

        all_results = []

        for scenario in test_scenarios:
            print(f"\n📋 Expected memories: {', '.join(scenario['expected_memories'])}")

            memories = await self.create_memories_from_text(
                scenario["text"], scenario["context"]
            )

            all_results.append(
                {
                    "context": scenario["context"],
                    "input": scenario["text"],
                    "expected": scenario["expected_memories"],
                    "created": len(memories),
                    "memory_details": [m.memory for m in memories],
                }
            )

            # Small delay for processing
            await asyncio.sleep(1)

        return all_results

    async def analyze_memory_quality(self):
        """Analyze the quality and granularity of created memories."""
        print("\n📊 MEMORY QUALITY ANALYSIS")
        print("=" * 50)

        all_memories = self.memory.get_user_memories(user_id=self.user_id)

        print(f"📈 Total Memories: {len(all_memories)}")
        print(f"👤 User ID: {self.user_id}")

        if not all_memories:
            print("❌ No memories found!")
            return

        # Display all memories
        print(f"\n🧠 All Memories:")
        for i, memory in enumerate(all_memories, 1):
            print(f"\n{i:2d}. {memory.memory}")
            if memory.topics:
                print(f"     Topics: {', '.join(memory.topics)}")
            if hasattr(memory, "created_at") and memory.created_at:
                print(f"     Created: {memory.created_at}")

        # Quality metrics
        avg_length = sum(len(m.memory) for m in all_memories) / len(all_memories)
        print(f"\n📊 QUALITY METRICS:")
        print(f"- Average memory length: {avg_length:.1f} characters")
        print(f"- Memories with topics: {sum(1 for m in all_memories if m.topics)}")

        # Check for combined memories (potential quality issues)
        combined_indicators = [" and ", ", and", " & ", " + "]
        potential_combined = []

        for memory in all_memories:
            for indicator in combined_indicators:
                if indicator in memory.memory and len(memory.memory) > 40:
                    potential_combined.append(memory)
                    break

        if potential_combined:
            print(f"- ⚠️  Potential combined memories: {len(potential_combined)}")
            for mem in potential_combined:
                print(f"    • {mem.memory}")
        else:
            print(f"- ✅ No obvious combined memories detected")

        # Memory categories
        categories = {}
        for memory in all_memories:
            if memory.topics:
                for topic in memory.topics:
                    categories[topic] = categories.get(topic, 0) + 1

        if categories:
            print(f"\n📂 MEMORY CATEGORIES:")
            for category, count in sorted(categories.items()):
                print(f"- {category}: {count} memories")

    async def search_memories_demo(self):
        """Demonstrate memory search capabilities."""
        print("\n🔍 MEMORY SEARCH DEMONSTRATION")
        print("=" * 50)

        search_queries = [
            "What is the user's name?",
            "Where does the user work?",
            "What programming languages does the user know?",
            "Tell me about the user's pets",
            "What are the user's hobbies?",
            "How old is the user?",
        ]

        for query in search_queries:
            print(f"\n❓ Query: {query}")

            # Search using different methods
            try:
                # Semantic search
                semantic_results = self.memory.search_user_memories(
                    user_id=self.user_id, query=query, limit=3
                )

                if semantic_results:
                    print(f"📋 Found {len(semantic_results)} relevant memories:")
                    for i, result in enumerate(semantic_results, 1):
                        print(f"  {i}. {result.memory}")
                else:
                    print("   No relevant memories found")

            except Exception as e:
                print(f"   Error searching: {e}")

    def clear_memories(self):
        """Clear all memories for fresh testing."""
        print("\n🗑️  Clearing all memories for fresh test...")
        self.memory.clear()
        print("✅ Memories cleared")


async def main():
    """Run the enhanced memory management demonstration."""
    manager = EnhancedMemoryManager()

    try:
        # Initialize the memory system
        await manager.initialize_memory()

        # Optional: Clear previous memories for clean test
        manager.clear_memories()

        # Demonstrate enhanced memory creation
        results = await manager.demonstrate_granular_memory_creation()

        # Analyze the quality of created memories
        await manager.analyze_memory_quality()

        # Demonstrate search capabilities
        await manager.search_memories_demo()

        # Print final summary
        print("\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 50)

        total_scenarios = len(results)
        total_memories_created = sum(r["created"] for r in results)

        print(f"📊 SUMMARY:")
        print(f"- Test scenarios: {total_scenarios}")
        print(f"- Total memories created: {total_memories_created}")
        print(
            f"- Average memories per scenario: {total_memories_created/total_scenarios:.1f}"
        )

        # Success criteria
        if total_memories_created >= 12:  # Expecting good granularity
            print("\n🎯 SUCCESS: Excellent memory granularity achieved!")
            print("   Ollama model is creating separate, focused memories.")
        elif total_memories_created >= 8:
            print("\n⚠️  GOOD: Improved granularity, some combined memories may remain.")
        else:
            print("\n❌ NEEDS IMPROVEMENT: Still creating too many combined memories.")

        print("\n💡 Key Improvements Demonstrated:")
        print("✅ Enhanced prompting for memory granularity")
        print("✅ Direct use of Agno's native Memory class")
        print("✅ Explicit memory creation guidance")
        print("✅ Quality assessment and monitoring")
        print("✅ Local privacy maintained (no OpenAI dependency)")

    except KeyboardInterrupt:
        print("\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n💥 Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
