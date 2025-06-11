#!/usr/bin/env python3
"""
Lightweight memory test to isolate the performance issue.
"""

import asyncio
import logging
import sys
from pathlib import Path
from uuid import uuid4

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduce log noise
logger = logging.getLogger(__name__)


async def test_agno_memory_minimal():
    """Test Agno memory with minimal configuration."""
    print("🧠 Testing Agno Memory (Minimal Configuration)")
    print("=" * 60)

    try:
        from agno.agent.agent import Agent
        from agno.models.ollama import Ollama

        print("✅ Successfully imported Agno components")

        # Create agent WITHOUT memory first
        print("\n🤖 Creating agent WITHOUT memory...")
        agent_no_memory = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            enable_user_memories=False,  # Disable memory
        )

        # Test basic functionality
        print("⚡ Testing basic response (no memory)...")
        start_time = asyncio.get_event_loop().time()
        response = await agent_no_memory.arun("What is 2+2?")
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"✅ Response: {response.content}")
        print(f"⏱️  Time taken: {elapsed:.2f} seconds")

        # Now test WITH memory but simple operation
        print("\n🧠 Creating agent WITH memory...")
        agent_with_memory = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            enable_user_memories=True,  # Enable memory
            user_id="test_user",
        )

        # Test simple math (should not trigger memory creation)
        print("⚡ Testing simple query (with memory enabled)...")
        start_time = asyncio.get_event_loop().time()
        response = await agent_with_memory.arun("What is 3+3?")
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"✅ Response: {response.content}")
        print(f"⏱️  Time taken: {elapsed:.2f} seconds")

        # Test query that might trigger memory creation (but simple)
        print("⚡ Testing memory-triggering query...")
        print("📝 Note: This may take longer as it creates memory...")
        start_time = asyncio.get_event_loop().time()

        # Use asyncio.wait_for to set a timeout
        try:
            response = await asyncio.wait_for(
                agent_with_memory.arun("Hello, my name is John."),
                timeout=30.0,  # 30 second timeout
            )
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"✅ Response: {response.content}")
            print(f"⏱️  Time taken: {elapsed:.2f} seconds")

        except asyncio.TimeoutError:
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"⏰ TIMEOUT after {elapsed:.2f} seconds")
            print("🔍 This confirms the memory system is too slow")
            return False

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Minimal memory test failed: %s", e, exc_info=True)
        return False


async def test_agno_memory_disabled_vs_enabled():
    """Compare performance with memory disabled vs enabled."""
    print("\n📊 Performance Comparison: Memory Disabled vs Enabled")
    print("=" * 60)

    test_queries = [
        "Hello!",
        "What's the weather like?",
        "Tell me a joke.",
    ]

    try:
        from agno.agent.agent import Agent
        from agno.models.ollama import Ollama

        # Test WITHOUT memory
        print("\n🚫 Testing WITHOUT memory...")
        agent_no_memory = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            enable_user_memories=False,
        )

        no_memory_times = []
        for i, query in enumerate(test_queries, 1):
            print(f"  Query {i}: {query}")
            start_time = asyncio.get_event_loop().time()
            response = await agent_no_memory.arun(query)
            elapsed = asyncio.get_event_loop().time() - start_time
            no_memory_times.append(elapsed)
            print(f"    Time: {elapsed:.2f}s")

        avg_no_memory = sum(no_memory_times) / len(no_memory_times)
        print(f"📈 Average time without memory: {avg_no_memory:.2f}s")

        # Test WITH memory (but with timeout protection)
        print("\n🧠 Testing WITH memory (timeout protected)...")
        agent_with_memory = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            enable_user_memories=True,
            user_id="perf_test_user",
        )

        memory_times = []
        for i, query in enumerate(test_queries, 1):
            print(f"  Query {i}: {query}")
            start_time = asyncio.get_event_loop().time()
            try:
                response = await asyncio.wait_for(
                    agent_with_memory.arun(query),
                    timeout=15.0,  # 15 second timeout per query
                )
                elapsed = asyncio.get_event_loop().time() - start_time
                memory_times.append(elapsed)
                print(f"    Time: {elapsed:.2f}s")
            except asyncio.TimeoutError:
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"    TIMEOUT after {elapsed:.2f}s")
                memory_times.append(15.0)  # Use timeout value

        avg_memory = sum(memory_times) / len(memory_times)
        print(f"📈 Average time with memory: {avg_memory:.2f}s")

        # Performance analysis
        print(f"\n📊 Performance Impact:")
        print(f"   Without memory: {avg_no_memory:.2f}s average")
        print(f"   With memory:    {avg_memory:.2f}s average")
        if avg_memory > avg_no_memory:
            slowdown = avg_memory / avg_no_memory
            print(f"   Memory overhead: {slowdown:.1f}x slower")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run memory performance tests."""
    print("🚀 Agno Memory Performance Analysis")
    print("=" * 60)

    # Ensure tmp directory exists
    Path("./tmp").mkdir(exist_ok=True)

    test_results = []

    # Test 1: Minimal memory test
    result1 = await test_agno_memory_minimal()
    test_results.append(("Minimal Memory Test", result1))

    # Test 2: Performance comparison
    result2 = await test_agno_memory_disabled_vs_enabled()
    test_results.append(("Performance Comparison", result2))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")

    total_passed = sum(result[1] for result in test_results)
    print(f"\nTotal: {total_passed}/{len(test_results)} tests passed")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("   1. For production: Disable user memories for faster responses")
    print("   2. For development: Use simpler memory storage (SQLite only)")
    print(
        "   3. For heavy memory use: Consider using OpenAI API instead of local Ollama"
    )
    print("   4. Alternative: Implement custom lightweight memory system")

    return 0 if total_passed == len(test_results) else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
