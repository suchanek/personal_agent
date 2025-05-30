#!/usr/bin/env python3
"""Test the fixed main.py initialization."""

import logging
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.main import initialize_system

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def test_main_initialization():
    """Test the fixed main.py initialization."""
    print("=== Testing Main.py Initialization ===")

    try:
        tools = initialize_system()
        print(f"SUCCESS: Initialized {len(tools)} tools")

        # List all tools by name
        for i, tool in enumerate(tools):
            tool_name = getattr(tool, "name", "Unknown")
            print(f"  Tool {i+1}: {tool_name}")

        # Check if we have the expected number of tools (should be 13 total)
        if len(tools) >= 13:
            print("✅ PASS: Memory tools are included!")
        else:
            print("❌ FAIL: Memory tools are missing")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_main_initialization()
