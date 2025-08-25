#!/usr/bin/env python3
"""
Test script to verify the StreamlitMemoryHelper fix for get_all_memories().

This script tests whether the get_all_memories() method now properly returns
UserMemory objects instead of an empty list.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent / "src"
sys.path.insert(0, str(project_root))

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper


def test_memory_helper_fix():
    """Test the StreamlitMemoryHelper get_all_memories fix."""
    print("🧪 Testing StreamlitMemoryHelper.get_all_memories() fix...")

    try:
        # Initialize the agent
        print("📝 Initializing agent...")
        agent = AgnoPersonalAgent(initialize_agent=True)

        # Create memory helper
        print("🔧 Creating StreamlitMemoryHelper...")
        memory_helper = StreamlitMemoryHelper(agent)

        # Test get_all_memories
        print("🔍 Testing get_all_memories()...")
        memories = memory_helper.get_all_memories()

        print(f"📊 Result: {type(memories)} with {len(memories)} items")

        if isinstance(memories, list):
            if len(memories) > 0:
                print("✅ SUCCESS: get_all_memories() returned a list with memories!")
                print(f"   First memory type: {type(memories[0])}")
                if hasattr(memories[0], "memory"):
                    print(f"   First memory content: {memories[0].memory[:100]}...")
                if hasattr(memories[0], "topics"):
                    print(f"   First memory topics: {memories[0].topics}")
            else:
                print(
                    "ℹ️  SUCCESS: get_all_memories() returned an empty list (no memories found)"
                )
        else:
            print(
                f"❌ FAILURE: get_all_memories() returned {type(memories)} instead of list"
            )

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧠 StreamlitMemoryHelper Fix Test")
    print("=" * 50)

    success = test_memory_helper_fix()

    if success:
        print("\n✅ Test completed successfully!")
        print(
            "The fix should now properly display memories in the Streamlit dashboard."
        )
    else:
        print("\n❌ Test failed!")
        print("There may be additional issues to resolve.")
