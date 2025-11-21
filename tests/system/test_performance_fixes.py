import asyncio
import logging
import sys
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.personal_agent.core.agent_instruction_manager import InstructionLevel
from src.personal_agent.core.agno_agent import AgnoPersonalAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceTimer:
    def __init__(self):
        self.timings = {}

    def start_timer(self, name):
        self.timings[name] = {"start": time.perf_counter()}
        logger.info(f"⏱️  Starting timer: {name}")

    def end_timer(self, name):
        if name in self.timings:
            self.timings[name]["end"] = time.perf_counter()
            duration = self.timings[name]["end"] - self.timings[name]["start"]
            self.timings[name]["duration"] = duration
            logger.info(f"⏱️  Timer {name}: {duration:.2f} seconds")
            return duration
        return 0

    def get_timing(self, name):
        return self.timings.get(name, {}).get("duration", 0)


@pytest.mark.asyncio
async def test_performance_fixes():
    """
    Test the performance fixes for AgnoPersonalAgent memory queries
    """
    print("=== PERFORMANCE FIXES VALIDATION TEST ===")

    timer = PerformanceTimer()

    # Test 1: Agent initialization
    print("\n1. Testing AgnoPersonalAgent initialization...")
    timer.start_timer("agent_init")

    try:
        agent = await AgnoPersonalAgent.create_with_init(
            enable_memory=True,
            debug=False,  # Disable debug to test performance without debug overhead
            instruction_level=InstructionLevel.EXPLICIT,
            alltools=True,
        )
        timer.end_timer("agent_init")
        print(
            f"✅ Agent initialized successfully in {timer.get_timing('agent_init'):.2f}s"
        )
    except Exception as e:
        timer.end_timer("agent_init")
        print(f"❌ Agent initialization failed: {e}")
        return

    # Test 2: Simple query (baseline)
    print("\n2. Testing simple query (baseline)...")
    timer.start_timer("simple_query")

    try:
        response = await agent.arun("Hello, who are you?")
        timer.end_timer("simple_query")

        print(f"✅ Simple query completed in {timer.get_timing('simple_query'):.2f}s")
        print(f"Response preview: {str(response)[:100]}...")

    except Exception as e:
        timer.end_timer("simple_query")
        print(f"❌ Simple query failed: {e}")
        return

    # Test 3: Memory listing query (the fixed query)
    print("\n3. Testing 'list all memories' query (PERFORMANCE FIX TEST)...")
    timer.start_timer("list_memories_query")

    try:
        # This is the exact query that was taking 320 seconds
        response = await agent.arun(
            "list all memories. do not interpret, just list them"
        )
        timer.end_timer("list_memories_query")

        print(
            f"✅ Memory listing completed in {timer.get_timing('list_memories_query'):.2f}s"
        )
        print(f"Response preview: {str(response)[:200]}...")

    except Exception as e:
        timer.end_timer("list_memories_query")
        print(f"❌ Memory listing failed: {e}")
        return

    # Test 4: Alternative memory query phrasing
    print("\n4. Testing alternative memory query phrasing...")
    timer.start_timer("alt_memory_query")

    try:
        response = await agent.arun("show me all my memories")
        timer.end_timer("alt_memory_query")

        print(
            f"✅ Alternative memory query completed in {timer.get_timing('alt_memory_query'):.2f}s"
        )
        print(f"Response preview: {str(response)[:200]}...")

    except Exception as e:
        timer.end_timer("alt_memory_query")
        print(f"❌ Alternative memory query failed: {e}")

    # Performance Analysis
    print("\n=== PERFORMANCE ANALYSIS ===")
    print(f"Agent initialization: {timer.get_timing('agent_init'):.2f}s")
    print(f"Simple query: {timer.get_timing('simple_query'):.2f}s")
    print(f"List memories query: {timer.get_timing('list_memories_query'):.2f}s")
    print(f"Alternative memory query: {timer.get_timing('alt_memory_query'):.2f}s")

    # Success criteria
    list_memories_time = timer.get_timing("list_memories_query")
    simple_query_time = timer.get_timing("simple_query")

    print("\n=== PERFORMANCE FIX VALIDATION ===")
    if list_memories_time < 10:  # Should be under 10 seconds now
        print(
            f"✅ SUCCESS: Memory listing query completed in {list_memories_time:.2f}s (target: <10s)"
        )

        if (
            list_memories_time <= simple_query_time * 3
        ):  # Should be similar to simple queries
            print(
                f"✅ EXCELLENT: Memory listing performance is comparable to simple queries"
            )
        else:
            print(f"⚠️  GOOD: Memory listing is fast but could be optimized further")

        improvement_factor = (
            320 / list_memories_time if list_memories_time > 0 else float("inf")
        )
        print(
            f"🚀 PERFORMANCE IMPROVEMENT: ~{improvement_factor:.1f}x faster than before (320s → {list_memories_time:.2f}s)"
        )

    elif list_memories_time < 30:
        print(
            f"⚠️  PARTIAL SUCCESS: Memory listing improved but still slow ({list_memories_time:.2f}s)"
        )
        print("   Additional optimization may be needed")
    else:
        print(
            f"❌ PERFORMANCE ISSUE PERSISTS: Memory listing still taking {list_memories_time:.2f}s"
        )
        print("   The fixes may not have addressed the root cause")

    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_performance_fixes())
    except KeyboardInterrupt:
        print("\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.exception("Test execution exception:")
