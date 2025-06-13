#!/usr/bin/env python3
"""
Debug tool output to see what's actually being returned.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentSystemTools,
)


def debug_tools():
    """Debug what the tools are actually returning."""

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="debug_test_")
    print(f"Test directory: {temp_dir}")

    try:
        # Test filesystem tools
        print("\n=== FILESYSTEM TOOLS DEBUG ===")
        fs_tools = PersonalAgentFilesystemTools()

        # Test write_file
        print("\n1. Testing write_file:")
        test_file = os.path.join(temp_dir, "test.txt")
        result = fs_tools.write_file(test_file, "test content")
        print(f"Result: {repr(result)}")
        print(f"Type: {type(result)}")

        # Test list_directory
        print("\n2. Testing list_directory:")
        result = fs_tools.list_directory(temp_dir)
        print(f"Result: {repr(result)}")
        print(f"Type: {type(result)}")

        # Test system tools
        print("\n=== SYSTEM TOOLS DEBUG ===")
        sys_tools = PersonalAgentSystemTools()

        # Test shell_command
        print("\n3. Testing shell_command:")
        result = sys_tools.shell_command("echo 'hello'", temp_dir)
        print(f"Result: {repr(result)}")
        print(f"Type: {type(result)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    debug_tools()
