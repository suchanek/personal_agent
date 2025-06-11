#!/usr/bin/env python3
"""
Improved Enhanced Memory Demo that prevents agent-level memory duplication.
"""

import time

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.personal_agent.config import LLM_MODEL, OLLAMA_URL
from src.personal_agent.core.agno_storage import (
    EnhancedMemory,
    analyze_memory_quality,
    clear_agno_database_completely,
    create_agno_memory,
    create_agno_storage,
)
from src.personal_agent.utils import setup_logging

logger = setup_logging(__name__)


class AgentMemoryInterceptor:
    """Wrapper that intercepts agent memory creation to prevent duplicates."""

    def __init__(self, enhanced_memory: EnhancedMemory, user_id: str):
        """Initialize the interceptor.

        :param enhanced_memory: Enhanced memory instance with duplicate detection
        :param user_id: User ID for memory operations
        """
        self.enhanced_memory = enhanced_memory
        self.user_id = user_id
        self.original_create_memory = None

    def intercept_memory_creation(self, agent: Agent):
        """Intercept the agent's memory creation to add duplicate checking."""
        # Store reference to original memory instance
        original_memory = agent.memory

        # Create a wrapper that checks for duplicates before storing
        class MemoryWrapper:
            def __init__(self, original_memory, enhanced_memory, user_id):
                self._original = original_memory
                self._enhanced = enhanced_memory
                self._user_id = user_id

            def create_memory(self, memory_text: str, **kwargs):
                """Intercept memory creation to check for duplicates."""
                # Check if this would be a duplicate
                if self._enhanced.should_create_memory(self._user_id, memory_text):
                    logger.info(f"✅ Creating unique memory: '{memory_text[:50]}...'")
                    return self._original.create_memory(memory_text, **kwargs)
                else:
                    logger.info(
                        f"⏭️  Skipping duplicate memory: '{memory_text[:50]}...'"
                    )
                    return None

            def __getattr__(self, name):
                """Delegate all other methods to original memory."""
                return getattr(self._original, name)

        # Replace agent's memory with our wrapper
        agent.memory = MemoryWrapper(
            original_memory, self.enhanced_memory, self.user_id
        )

        return agent


def demo_improved_enhanced_memory():
    """Demonstrate improved enhanced memory with agent-level duplicate prevention."""
    print("🚀 Improved Enhanced Agno Memory Demo")
    print("=" * 60)

    # Clear existing data for clean demo
    print("\n🗑️  Clearing existing data...")
    clear_agno_database_completely()

    # Create standard memory and storage for agent
    print("\n📦 Creating Agno memory and storage...")
    base_memory = create_agno_memory()
    storage = create_agno_storage()

    # Create enhanced memory wrapper for duplicate checking
    enhanced_memory = EnhancedMemory(base_memory, similarity_threshold=0.8)
    logger.info(
        "Created Enhanced Memory wrapper with duplicate prevention (threshold: 0.8)"
    )

    # Create agent with standard memory
    agent = Agent(
        model=OpenAIChat(
            id=LLM_MODEL,
            api_key="ollama",
            base_url=f"{OLLAMA_URL}/v1",
        ),
        memory=base_memory,
        enable_user_memories=True,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        markdown=True,
    )

    user_id = "demo_user"

    # Create memory interceptor
    interceptor = AgentMemoryInterceptor(enhanced_memory, user_id)
    agent = interceptor.intercept_memory_creation(agent)

    # Test facts (some duplicates intentionally included)
    test_facts = [
        "My name is Alice and I work as a data scientist.",
        "I live in Seattle, Washington.",
        "My favorite programming language is Python.",
        "I have a cat named Whiskers.",
        "My name is Alice and I am a data scientist.",  # Similar to first
        "I live in Seattle, WA.",  # Similar to second
        "I enjoy hiking in the mountains on weekends.",
        "I have a pet cat called Whiskers.",  # Similar to fourth
        "My birthday is on July 15th.",
        "I love reading science fiction novels.",
    ]

    print(
        f"\n🔄 Processing {len(test_facts)} facts with agent-level duplicate prevention..."
    )
    print("=" * 80)

    processed_count = 0

    for i, fact in enumerate(test_facts, 1):
        print(f"\n📝 Fact {i}: {fact}")

        # Show current memory count for debugging
        current_memories = enhanced_memory.get_user_memories(user_id=user_id)
        print(f"   📊 Current memories in database: {len(current_memories)}")

        # Process through agent (memory creation will be intercepted)
        print("   🤖 Processing with agent (duplicate checking enabled)...")

        agent.print_response(
            fact,
            user_id=user_id,
            stream=False,
            stream_intermediate_steps=False,
        )
        processed_count += 1

        # Small delay for processing and verify memory was stored
        time.sleep(1)

        # Check if memory was actually stored
        updated_memories = enhanced_memory.get_user_memories(user_id=user_id)
        print(f"   💾 Memories after processing: {len(updated_memories)}")

        # Show any new memories that were created
        if len(updated_memories) > len(current_memories):
            new_memories = updated_memories[len(current_memories) :]
            print(f"   ✨ New memories created:")
            for j, mem in enumerate(new_memories):
                print(f"     {j+1}. '{mem.memory}'")
        else:
            print(f"   ⏭️  No new memories created (likely duplicates)")

    print(f"\n📊 Processing Summary:")
    print(f"   Total facts processed: {len(test_facts)}")
    print(f"   Facts sent to agent: {processed_count}")

    # Analyze memory quality
    print(f"\n🔍 Memory Quality Analysis:")
    analysis = analyze_memory_quality(enhanced_memory, user_id)

    print(f"   Quality Score: {analysis['quality_score']}/100")
    print(f"   Total Memories: {analysis['analysis_summary']['total_memories']}")
    print(f"   Efficiency: {analysis['analysis_summary']['efficiency']}")
    print(f"   Topic Coverage: {analysis['analysis_summary']['topic_coverage']}")

    if analysis["analysis_summary"]["top_topics"]:
        print(f"   Top Topics:")
        for topic, count in analysis["analysis_summary"]["top_topics"]:
            print(f"     - {topic}: {count} memories")

    if analysis["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in analysis["recommendations"]:
            print(f"   - {rec}")

    # Show all stored memories
    print(f"\n🧠 Stored Memories:")
    memories = enhanced_memory.get_user_memories(user_id=user_id)
    for i, memory in enumerate(memories, 1):
        topics_str = str(memory.topics) if memory.topics else "[No Topics]"
        print(f"   {i}. '{memory.memory}' [topics: {topics_str}]")

    # Calculate efficiency improvement
    expected_without_duplicates = len(set(test_facts))  # Unique input facts
    actual_stored = len(memories)

    print(f"\n📈 Efficiency Metrics:")
    print(f"   Input facts: {len(test_facts)}")
    print(f"   Unique input facts: {expected_without_duplicates}")
    print(f"   Actual memories stored: {actual_stored}")
    print(
        f"   Storage ratio: {actual_stored}/{len(test_facts)} = {actual_stored/len(test_facts)*100:.1f}%"
    )
    print(
        f"   Efficiency vs unique: {actual_stored}/{expected_without_duplicates} = {actual_stored/expected_without_duplicates*100:.1f}%"
    )

    # Test agent interaction with memories
    print(f"\n🤖 Testing Agent Interaction:")
    try:
        response = agent.run(
            "Tell me what you know about the user. Be specific about their details.",
            user_id=user_id,
        )
        print(f"Agent Response: {response.content}")
    except Exception as e:
        print(f"Agent interaction failed: {e}")

    print(f"\n✅ Improved enhanced memory demo completed!")


if __name__ == "__main__":
    demo_improved_enhanced_memory()
