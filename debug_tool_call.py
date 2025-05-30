#!/usr/bin/env python3
"""
Debug script to understand what's happening with tool calls.
"""

import sys

sys.path.append(".")

from personal_agent import agent_executor, llm, mcp_write_file


def test_direct_tool_call():
    """Test calling the tool directly."""
    print("🔧 Testing direct tool call...")

    try:
        result = mcp_write_file.invoke(
            {
                "file_path": "~/repos/random/debug_test.py",
                "content": "#!/usr/bin/env python3\nprint('Direct tool call worked!')\n",
            }
        )
        print(f"✅ Direct tool call result: {result}")
        return True
    except Exception as e:
        print(f"❌ Direct tool call failed: {e}")
        return False


def test_agent_tool_call():
    """Test calling the tool through the agent."""
    print("\n🤖 Testing agent tool call...")

    try:
        # Test with a very simple, explicit request
        query = """
Use the mcp_write_file tool to create a file at ~/repos/random/agent_test.py with this content:

#!/usr/bin/env python3
print("Agent tool call worked!")

Format the action as:
Action: mcp_write_file  
Action Input: {"file_path": "~/repos/random/agent_test.py", "content": "#!/usr/bin/env python3\\nprint(\\"Agent tool call worked!\\")\\n"}
"""

        result = agent_executor.invoke(
            {"input": query, "context": "No previous context."}
        )
        print(f"✅ Agent result: {result}")
        return True
    except Exception as e:
        print(f"❌ Agent tool call failed: {e}")
        return False


def test_llm_parsing():
    """Test what the LLM actually generates."""
    print("\n🧠 Testing LLM output parsing...")

    try:
        query = """
You need to call the mcp_write_file tool. Generate the exact format:

Thought: I need to create a file using mcp_write_file
Action: mcp_write_file
Action Input: {"file_path": "~/test.py", "content": "print('hello')"}

Generate this format now.
"""

        response = llm.invoke(query)
        print(f"📝 LLM response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False


if __name__ == "__main__":
    print("🐛 Debugging Tool Call Issues")
    print("=" * 50)

    test_direct_tool_call()
    test_agent_tool_call()
    test_llm_parsing()

    print("\n" + "=" * 50)
    print("🏁 Debug complete")
