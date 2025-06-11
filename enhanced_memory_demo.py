#!/usr/bin/env python3
"""
Demo script showing how to use the enhanced Agno memory system with duplicate prevention.
"""

import asyncio
from pathlib import Path

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.personal_agent.config import LLM_MODEL, OLLAMA_URL
from src.personal_agent.core.agno_storage import (
    EnhancedMemory,
    analyze_memory_quality,
    clear_agno_database_completely,
    create_agno_memory,
    create_agno_storage,
    create_enhanced_agno_memory,
)
from src.personal_agent.utils import setup_logging

logger = setup_logging(__name__)


def demo_enhanced_memory():
    """Demonstrate enhanced memory with duplicate prevention."""
    print("🧠 Enhanced Agno Memory Demo")
    print("=" * 50)

    # Clear existing data for clean demo
    print("\n🗑️  Clearing existing data...")
    clear_agno_database_completely()

    # Create standard memory and storage for agent
    print("\n📦 Creating Agno memory and storage...")
    base_memory = create_agno_memory()
    storage = create_agno_storage()

    # Create enhanced memory wrapper separately for duplicate checking
    enhanced_memory = EnhancedMemory(base_memory, similarity_threshold=0.8)
    logger.info(
        "Created Enhanced Memory wrapper with duplicate prevention (threshold: 0.8)"
    )

    # Create agent with standard memory (avoiding session loading issues)
    agent = Agent(
        model=OpenAIChat(
            id=LLM_MODEL,
            api_key="ollama",
            base_url=f"{OLLAMA_URL}/v1",
        ),
        memory=base_memory,  # Use base memory to avoid session loading type errors
        enable_user_memories=True,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        markdown=True,
    )

    user_id = "demo_user"

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

    print(f"\n🔄 Processing {len(test_facts)} facts...")
    print("=" * 60)

    processed_count = 0
    would_skip_count = 0

    for i, fact in enumerate(test_facts, 1):
        print(f"\n📝 Fact {i}: {fact}")

        # Show current memory count for debugging
        current_memories = enhanced_memory.get_user_memories(user_id=user_id)
        print(f"   📊 Current memories in database: {len(current_memories)}")

        # Check if this would be a duplicate using our enhanced memory
        would_be_unique = enhanced_memory.should_create_memory(user_id, fact)

        if would_be_unique:
            print("   🔍 Checking for duplicates... ✅ Unique, processing with agent")

            # Process through agent (this will create memories automatically)
            agent.print_response(
                fact,
                user_id=user_id,
                stream=False,
                stream_intermediate_steps=False,
            )
            processed_count += 1

            # Small delay for processing and verify memory was stored
            import time

            time.sleep(1)

            # Check if memory was actually stored
            updated_memories = enhanced_memory.get_user_memories(user_id=user_id)
            print(f"   💾 Memories after processing: {len(updated_memories)}")

        else:
            print("   🔍 Checking for duplicates... ⏭️  Would skip (duplicate detected)")
            # Show which existing memory this is similar to
            existing_memories = enhanced_memory.get_user_memories(user_id=user_id)
            for existing_mem in existing_memories:
                # Check similarity
                fact_words = set(fact.lower().split())
                existing_words = set(existing_mem.memory.lower().split())
                if len(fact_words) > 0 and len(existing_words) > 0:
                    intersection = fact_words.intersection(existing_words)
                    union = fact_words.union(existing_words)
                    similarity = len(intersection) / len(union)
                    if similarity >= enhanced_memory.similarity_threshold:
                        print(
                            f"   🔗 Similar to: '{existing_mem.memory}' (similarity: {similarity:.2f})"
                        )
                        break
            would_skip_count += 1

    print(f"\n📊 Processing Summary:")
    print(f"   Total facts: {len(test_facts)}")
    print(f"   Processed: {processed_count}")
    print(f"   Would skip: {would_skip_count}")
    print(f"   Efficiency: {processed_count/len(test_facts)*100:.1f}%")

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

    print(f"\n✅ Enhanced memory demo completed!")


def demo_comparison():
    """Compare standard memory vs enhanced memory."""
    print("\n🔄 Comparison Demo: Standard vs Enhanced Memory")
    print("=" * 60)

    # Clear data first
    clear_agno_database_completely()

    # Test with duplicate facts
    duplicate_facts = [
        "I like pizza",
        "I enjoy pizza",
        "Pizza is my favorite food",
        "I love eating pizza",
        "My favorite food is pizza",
    ]

    user_id = "comparison_user"

    # Test 1: Standard Memory (through agent interactions)
    print("\n📝 Test 1: Standard Memory (allows duplicates)")
    standard_memory = create_agno_memory()

    # Create agent with standard memory
    standard_agent = Agent(
        model=OpenAIChat(
            id=LLM_MODEL,
            api_key="ollama",
            base_url=f"{OLLAMA_URL}/v1",
        ),
        memory=standard_memory,
        enable_user_memories=True,
        markdown=True,
    )

    for fact in duplicate_facts:
        standard_agent.print_response(fact, user_id=user_id, stream=False)
        import time

        time.sleep(0.5)  # Brief delay

    standard_memories = standard_memory.get_user_memories(user_id=user_id)
    print(f"   Memories stored: {len(standard_memories)}")

    # Test 2: Enhanced Memory (with duplicate checking)
    print("\n🔒 Test 2: Enhanced Memory (prevents duplicates)")
    base_memory_enhanced = create_agno_memory()
    enhanced_memory = EnhancedMemory(base_memory_enhanced, similarity_threshold=0.7)

    # Create agent with base memory
    enhanced_agent = Agent(
        model=OpenAIChat(
            id=LLM_MODEL,
            api_key="ollama",
            base_url=f"{OLLAMA_URL}/v1",
        ),
        memory=base_memory_enhanced,  # Use base memory to avoid type errors
        enable_user_memories=True,
        markdown=True,
    )

    processed = 0
    for fact in duplicate_facts:
        if enhanced_memory.should_create_memory(user_id, fact):
            enhanced_agent.print_response(fact, user_id=user_id, stream=False)
            processed += 1
            import time

            time.sleep(0.5)  # Brief delay
        else:
            print(f"   Skipping duplicate: '{fact}'")

    enhanced_memories = enhanced_memory.get_user_memories(user_id=user_id)
    print(f"   Memories stored: {len(enhanced_memories)}")
    print(f"   Duplicates prevented: {len(duplicate_facts) - processed}")

    print(f"\n📊 Comparison Results:")
    print(f"   Input facts: {len(duplicate_facts)}")
    print(f"   Standard memory: {len(standard_memories)} stored")
    print(f"   Enhanced memory: {len(enhanced_memories)} stored")
    if len(standard_memories) > 0:
        print(
            f"   Efficiency improvement: {(1 - len(enhanced_memories)/len(standard_memories))*100:.1f}% reduction"
        )


if __name__ == "__main__":
    demo_enhanced_memory()
    demo_comparison()
