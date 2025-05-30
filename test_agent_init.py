#!/usr/bin/env python3
"""Test the agent initialization without starting the web server."""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_full_initialization():
    """Test the complete initialization process."""
    print("🚀 Testing full agent initialization...")

    try:
        from personal_agent.main import initialize_system

        # Set up logging to capture output
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

        print("\n📦 Initializing system components...")
        tools = initialize_system()

        print(f"\n✅ Initialization successful!")
        print(f"📊 Total tools loaded: {len(tools)}")

        # Show tool names
        if tools:
            print("\n🛠️  Available tools:")
            for tool in tools:
                tool_name = getattr(tool, "name", "Unknown")
                print(f"  - {tool_name}")

        return True

    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the initialization test."""
    success = test_full_initialization()

    if success:
        print("\n🎉 Agent system is ready! You can now run the web interface.")
        return 0
    else:
        print("\n⚠️  Agent initialization failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
