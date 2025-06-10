#!/usr/bin/env python3
"""Quick validation test for filesystem tools."""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.config import HOME_DIR


def test_import():
    """Test that filesystem tools can be imported without syntax errors."""

    try:
        from personal_agent.tools.filesystem import (
            mcp_read_file,
            mcp_write_file,
            mcp_list_directory,
        )

        print("✓ Successfully imported filesystem tools")
        return True
    except Exception as e:
        print(f"✗ Failed to import filesystem tools: {e}")
        return False


def test_function_definitions():
    """Test that the functions are properly defined."""

    from personal_agent.tools.filesystem import (
        mcp_read_file,
        mcp_write_file,
        mcp_list_directory,
    )

    # Check if functions have proper attributes
    functions = [mcp_read_file, mcp_write_file, mcp_list_directory]
    for func in functions:
        if hasattr(func, "name"):
            print(f"✓ {func.name} is properly defined")
        else:
            print(f"✗ Function missing name attribute")

    return True


if __name__ == "__main__":
    print("FILESYSTEM TOOLS VALIDATION")
    print("=" * 40)
    print(f"HOME_DIR: {HOME_DIR}")
    print()

    success = True
    success &= test_import()
    success &= test_function_definitions()

    if success:
        print("\n✓ All validation tests passed!")
    else:
        print("\n✗ Some validation tests failed!")
        sys.exit(1)
