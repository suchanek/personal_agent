#!/usr/bin/env python3
"""
Simple test to verify file writing tool functionality.
This tests the specific scenario mentioned - writing scripts to ~/repos/random
"""

import os
import tempfile
import time
from datetime import datetime

import requests


def test_web_interface_file_creation():
    """Test file creation through the web interface by sending a request."""
    print("🧪 Testing file creation through web interface...")

    # Test query that should create a file
    test_query = """
    Create a simple Python script and save it to ~/repos/random/hello_script.py. 
    The script should print "Hello from Personal AI Agent!" and the current time.
    """

    try:
        # Make a POST request to the web interface (assuming it's running)
        url = "http://127.0.0.1:5001"
        data = {"query": test_query, "topic": "testing"}

        print(f"📤 Sending request to {url}")
        print(f"📝 Query: {test_query.strip()}")

        response = requests.post(url, data=data, timeout=60)

        if response.status_code == 200:
            print("✅ Web interface responded successfully")

            # Check if the file was actually created
            expected_file = os.path.expanduser("~/repos/random/hello_script.py")

            # Give it a moment for the file to be created
            time.sleep(2)

            if os.path.exists(expected_file):
                print(f"✅ File successfully created at: {expected_file}")

                # Read and display the file content
                with open(expected_file, "r") as f:
                    content = f.read()
                print(f"📄 File content:\n{content}")

                # Clean up
                os.remove(expected_file)

                # Try to remove the directory if it's empty
                try:
                    os.rmdir(os.path.dirname(expected_file))
                    print("🧹 Cleaned up test directory")
                except OSError:
                    print("📁 Directory not empty, leaving it")

                return True
            else:
                print(f"❌ File was not created at: {expected_file}")
                print(
                    "💡 This suggests the tool displayed the script but didn't actually save it"
                )
                return False
        else:
            print(f"❌ Web interface error: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(
            "❌ Could not connect to web interface. Is the agent running at http://127.0.0.1:5001?"
        )
        return False
    except Exception as e:
        print(f"❌ Error testing web interface: {e}")
        return False


def test_direct_tool_invocation():
    """Test the file writing tool directly."""
    print("\n🧪 Testing direct tool invocation...")

    # Create the test content
    test_content = f'''#!/usr/bin/env python3
"""
Test script created by Personal AI Agent
Generated at: {datetime.now()}
"""

def main():
    print("Hello from Personal AI Agent!")
    print(f"Current time: {{datetime.now()}}")

if __name__ == "__main__":
    from datetime import datetime
    main()
'''

    # Test file path
    test_file = "~/repos/random/direct_test_script.py"

    try:
        # First, let's test if we can import the tools
        import os
        import sys

        # Dynamically determine the project directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(current_dir)

        try:
            from personal_agent import USE_MCP, mcp_client, mcp_write_file

            print("✅ Successfully imported tools")
        except ImportError as e:
            print(f"❌ Failed to import tools: {e}")
            print("💡 Make sure the personal agent is set up correctly")
            return False

        if not USE_MCP or mcp_client is None:
            print("❌ MCP is not enabled or client not available")
            return False

        # Start the filesystem server if needed
        server_name = "filesystem-home"
        if server_name not in mcp_client.active_servers:
            print(f"🚀 Starting MCP server: {server_name}")
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                print(f"❌ Failed to start {server_name}")
                return False

        # Invoke the tool directly
        print(f"📝 Writing file to: {test_file}")
        result = mcp_write_file.invoke(
            {"file_path": test_file, "content": test_content}
        )

        print(f"🔧 Tool result: {result}")

        # Check if file was created
        expanded_path = os.path.expanduser(test_file)
        if os.path.exists(expanded_path):
            print(f"✅ File successfully created at: {expanded_path}")

            # Verify content
            with open(expanded_path, "r") as f:
                actual_content = f.read()

            if "Hello from Personal AI Agent!" in actual_content:
                print("✅ File content verified")
            else:
                print("❌ File content doesn't match expected")

            # Clean up
            os.remove(expanded_path)
            try:
                os.rmdir(os.path.dirname(expanded_path))
                print("🧹 Cleaned up test files")
            except OSError:
                pass

            return True
        else:
            print(f"❌ File was not created at: {expanded_path}")
            print(f"🔍 Tool returned: {result}")
            return False

    except Exception as e:
        print(f"❌ Error in direct tool test: {e}")
        return False


def main():
    """Run the file writing tests."""
    print("🚀 Testing Personal AI Agent File Writing Functionality")
    print("=" * 60)

    # Test 1: Direct tool invocation
    direct_success = test_direct_tool_invocation()

    print("\n" + "-" * 60)

    # Test 2: Web interface (only if direct tool works)
    if direct_success:
        web_success = test_web_interface_file_creation()
    else:
        print("⚠️ Skipping web interface test due to direct tool failure")
        web_success = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"  Direct Tool Test: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"  Web Interface Test: {'✅ PASS' if web_success else '❌ FAIL'}")

    if direct_success and web_success:
        print("\n🎉 All tests passed! File writing functionality is working correctly.")
    elif direct_success:
        print("\n⚠️ Direct tool works, but web interface may have issues.")
        print(
            "💡 The agent might be displaying scripts without actually invoking the tool."
        )
    else:
        print("\n❌ File writing functionality needs attention.")
        print("💡 Check MCP configuration and tool implementation.")


if __name__ == "__main__":
    main()
