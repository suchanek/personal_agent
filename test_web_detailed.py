#!/usr/bin/env python3
"""
Detailed web interface test to see what the agent is actually doing.
"""

import os
import time

import requests


def test_web_interface_detailed():
    """Test what the agent actually returns when asked to create a file."""
    print("🧪 Testing web interface response in detail...")

    test_query = """Please use the mcp_write_file tool to create a Python script at ~/repos/random/web_test.py with this content:

#!/usr/bin/env python3
print("Hello from web interface test!")
print("File created successfully!")

Make sure to actually invoke the mcp_write_file tool, don't just show me the code."""

    try:
        url = "http://127.0.0.1:5001"
        data = {"query": test_query, "topic": "testing"}

        print(f"📤 Sending request to {url}")
        print(f"📝 Query: {test_query}")

        response = requests.post(url, data=data, timeout=120)

        if response.status_code == 200:
            print("✅ Web interface responded successfully")

            # Parse the HTML response to extract the agent's response
            content = response.text

            # Look for the response section
            if "response-content" in content:
                # Extract just the agent response part
                start = content.find('<div class="response-content">')
                end = content.find("</div>", start)
                if start != -1 and end != -1:
                    agent_response = content[start:end]
                    # Remove HTML tags for cleaner output
                    import re

                    clean_response = re.sub(r"<[^>]+>", "", agent_response)
                    print(f"\n📋 Agent Response:\n{clean_response}")
                else:
                    print("Could not extract agent response from HTML")

            # Check if the file was actually created
            expected_file = os.path.expanduser("~/repos/random/web_test.py")
            time.sleep(3)  # Give more time for file creation

            if os.path.exists(expected_file):
                print(f"✅ File successfully created at: {expected_file}")
                with open(expected_file, "r") as f:
                    content = f.read()
                print(f"📄 File content:\n{content}")

                # Clean up
                os.remove(expected_file)
                try:
                    os.rmdir(os.path.dirname(expected_file))
                except OSError:
                    pass

                return True
            else:
                print(f"❌ File was not created at: {expected_file}")
                print(
                    "💡 The agent responded but didn't actually invoke the file writing tool"
                )
                return False
        else:
            print(f"❌ Web interface error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error testing web interface: {e}")
        return False


def test_explicit_tool_request():
    """Test with very explicit tool invocation request."""
    print("\n🧪 Testing with explicit tool invocation request...")

    test_query = """I need you to call the mcp_write_file tool right now. Please execute this exact tool call:

Action: mcp_write_file
Action Input: {"file_path": "~/repos/random/explicit_test.py", "content": "#!/usr/bin/env python3\\nprint('Explicit tool test worked!')\\n"}

Do not just show me code - actually execute the mcp_write_file tool."""

    try:
        url = "http://127.0.0.1:5001"
        data = {"query": test_query, "topic": "testing"}

        print(f"📤 Sending explicit tool request to {url}")

        response = requests.post(url, data=data, timeout=120)

        if response.status_code == 200:
            print("✅ Web interface responded")

            # Check if the file was created
            expected_file = os.path.expanduser("~/repos/random/explicit_test.py")
            time.sleep(3)

            if os.path.exists(expected_file):
                print(f"✅ File successfully created at: {expected_file}")
                os.remove(expected_file)
                try:
                    os.rmdir(os.path.dirname(expected_file))
                except OSError:
                    pass
                return True
            else:
                print(f"❌ File was not created at: {expected_file}")
                return False
        else:
            print(f"❌ Web interface error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error in explicit tool test: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Detailed Web Interface Testing")
    print("=" * 50)

    test1_result = test_web_interface_detailed()
    test2_result = test_explicit_tool_request()

    print("\n" + "=" * 50)
    print("📊 DETAILED TEST SUMMARY:")
    print(f"  Detailed Response Test: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"  Explicit Tool Test: {'✅ PASS' if test2_result else '❌ FAIL'}")

    if not test1_result and not test2_result:
        print("\n🔍 DIAGNOSIS:")
        print(
            "The agent is likely generating responses without actually invoking tools."
        )
        print("This could be due to:")
        print("1. Agent prompt not encouraging tool use")
        print("2. Agent stopping before tool invocation")
        print("3. Tool invocation happening but failing silently")
