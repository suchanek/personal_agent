#!/usr/bin/env python3
"""
Test script to verify the file writing functionality of the Personal AI Agent.
This will test the enhanced mcp_write_file tool with path expansion and directory creation.
"""

import os
import shutil

# Import the tools from personal_agent
import sys
import tempfile
from datetime import datetime

from personal_agent.utils import add_src_to_path

add_src_to_path()

try:
    from personal_agent import (
        ROOT_DIR,
        USE_MCP,
        create_and_save_file,
        mcp_client,
        mcp_read_file,
        mcp_write_file,
    )

    print("✅ Successfully imported tools from personal_agent")
except ImportError as e:
    print(f"❌ Failed to import tools: {e}")
    sys.exit(1)


def test_basic_file_creation():
    """Test basic file creation in the home directory."""
    print("\n🧪 Testing basic file creation...")

    test_file = "~/test_basic_file.txt"
    test_content = f"This is a test file created at {datetime.now()}"

    try:
        # Test using mcp_write_file directly
        result = mcp_write_file.invoke(
            {"file_path": test_file, "content": test_content}
        )
        print(f"📝 Write result: {result}")

        # Verify the file was created
        expanded_path = os.path.expanduser(test_file)
        if os.path.exists(expanded_path):
            print(f"✅ File successfully created at: {expanded_path}")

            # Read back the content to verify
            read_result = mcp_read_file.invoke({"file_path": test_file})
            if test_content in read_result:
                print("✅ File content verified successfully")
            else:
                print(
                    f"❌ File content mismatch. Expected: {test_content[:50]}..., Got: {read_result[:50]}..."
                )
        else:
            print(f"❌ File was not created at: {expanded_path}")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

    finally:
        # Cleanup
        expanded_path = os.path.expanduser(test_file)
        if os.path.exists(expanded_path):
            os.remove(expanded_path)
            print("🧹 Cleaned up test file")


def test_directory_creation():
    """Test creating files in nested directories that don't exist."""
    print("\n🧪 Testing directory creation...")

    test_file = "~/repos/random/test_script.py"
    test_content = '''#!/usr/bin/env python3
"""
Test script created by Personal AI Agent
"""

def hello_world():
    print("Hello from the Personal AI Agent!")
    print("This file was created with automatic directory creation.")

if __name__ == "__main__":
    hello_world()
'''

    try:
        # Test using create_and_save_file which should create directories
        result = create_and_save_file.invoke(
            {"file_path": test_file, "content": test_content, "create_dirs": True}
        )
        print(f"📝 Create result: {result}")

        # Verify the file and directory were created
        expanded_path = os.path.expanduser(test_file)
        expanded_dir = os.path.dirname(expanded_path)

        if os.path.exists(expanded_dir):
            print(f"✅ Directory successfully created at: {expanded_dir}")
        else:
            print(f"❌ Directory was not created at: {expanded_dir}")

        if os.path.exists(expanded_path):
            print(f"✅ File successfully created at: {expanded_path}")

            # Read back the content to verify
            read_result = mcp_read_file.invoke({"file_path": test_file})
            if "hello_world" in read_result:
                print("✅ File content verified successfully")
            else:
                print(
                    f"❌ File content mismatch. Expected function 'hello_world', Got: {read_result[:100]}..."
                )
        else:
            print(f"❌ File was not created at: {expanded_path}")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

    finally:
        # Cleanup - remove the entire test directory tree
        expanded_path = os.path.expanduser(test_file)
        test_dir = os.path.expanduser("~/repos/random")
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print("🧹 Cleaned up test directory")


def test_path_conversion():
    """Test various path formats to ensure proper conversion."""
    print("\n🧪 Testing path conversion...")

    test_cases = [
        ("~/test_tilde.txt", "Tilde expansion test"),
        ("~/nested/deep/test.txt", "Nested directory test"),
    ]

    for test_path, test_content in test_cases:
        try:
            print(f"  Testing path: {test_path}")

            result = mcp_write_file.invoke(
                {"file_path": test_path, "content": test_content}
            )

            expanded_path = os.path.expanduser(test_path)
            if os.path.exists(expanded_path):
                print(f"  ✅ Successfully created: {expanded_path}")
                os.remove(expanded_path)

                # Also clean up directory if it was created
                expanded_dir = os.path.dirname(expanded_path)
                if expanded_dir != os.path.expanduser("~") and os.path.exists(
                    expanded_dir
                ):
                    try:
                        os.rmdir(expanded_dir)
                        # Try to remove parent dirs if empty
                        parent_dir = os.path.dirname(expanded_dir)
                        if parent_dir != os.path.expanduser("~"):
                            os.rmdir(parent_dir)
                    except OSError:
                        pass  # Directory not empty, that's fine
            else:
                print(f"  ❌ Failed to create: {expanded_path}")

        except Exception as e:
            print(f"  ❌ Error testing {test_path}: {e}")


def test_mcp_availability():
    """Test if MCP is properly configured and available."""
    print("\n🧪 Testing MCP availability...")

    if not USE_MCP:
        print("❌ MCP is disabled in configuration")
        return False

    if mcp_client is None:
        print("❌ MCP client is not initialized")
        return False

    print("✅ MCP is enabled and client is available")

    # Test starting filesystem server
    try:
        server_name = "filesystem-home"
        if server_name not in mcp_client.active_servers:
            print(f"🚀 Starting MCP server: {server_name}")
            result = mcp_client.start_server_sync(server_name)
            if result:
                print(f"✅ Successfully started {server_name}")
            else:
                print(f"❌ Failed to start {server_name}")
                return False
        else:
            print(f"✅ {server_name} already running")

        return True

    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False


def run_all_tests():
    """Run all file writing tests."""
    print("🚀 Starting File Writing Tool Tests")
    print("=" * 50)

    # Check MCP availability first
    if not test_mcp_availability():
        print("\n❌ MCP tests failed, skipping file writing tests")
        return

    # Run the tests
    test_basic_file_creation()
    test_directory_creation()
    test_path_conversion()

    print("\n" + "=" * 50)
    print("🏁 File Writing Tool Tests Completed")


if __name__ == "__main__":
    run_all_tests()
