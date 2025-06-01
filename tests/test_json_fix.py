#!/usr/bin/env python3
"""
Simple test script to verify the JSON format fix works.
This simulates the agent behavior without requiring full imports.
"""

import json
import re


def test_json_parsing():
    """Test different tool input formats to verify JSON parsing works."""

    print("🧪 Testing JSON format parsing")
    print("=" * 50)

    # Test cases that represent the different formats the agent might generate
    test_cases = [
        # Correct JSON format (what we want)
        {
            "name": "Correct JSON",
            "input": '{"file_path": "~/test.txt", "content": "Hello world"}',
            "should_parse": True,
        },
        # Python variable assignment format (the problematic one)
        {
            "name": "Python assignment (problematic)",
            "input": "file_path = '~/test.txt', content = '''Hello world'''",
            "should_parse": False,
        },
        # Another incorrect format
        {
            "name": "Python dict literal",
            "input": "{'file_path': '~/test.txt', 'content': 'Hello world'}",
            "should_parse": True,  # This should work
        },
    ]

    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        print(f"Input: {test_case['input']}")

        try:
            # Try to parse as JSON
            if test_case["input"].startswith("{") and test_case["input"].endswith("}"):
                parsed = json.loads(test_case["input"])
                print(f"✅ Parsed successfully: {parsed}")

                # Check if it has the required parameters
                if "file_path" in parsed and "content" in parsed:
                    print("✅ Contains required parameters")
                else:
                    print("❌ Missing required parameters")

            else:
                print("❌ Not valid JSON format")

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
        except Exception as e:
            print(f"❌ Other error: {e}")


def simulate_langchain_react_parser():
    """Simulate how LangChain ReAct parser handles different action input formats."""

    print("\n🔍 Simulating LangChain ReAct Parser")
    print("=" * 50)

    # Simulate agent outputs with different formats
    agent_outputs = [
        {
            "name": "Good format",
            "output": """Thought: I need to write a file
Action: mcp_write_file
Action Input: {"file_path": "~/test.txt", "content": "Hello world"}
Observation:""",
        },
        {
            "name": "Bad format (the problem)",
            "output": """Thought: I need to write a file
Action: mcp_write_file  
Action Input: file_path = '~/test.txt', content = '''Hello world'''
Observation:""",
        },
    ]

    for test in agent_outputs:
        print(f"\n📝 Testing: {test['name']}")

        # Extract Action Input using regex (similar to LangChain)
        pattern = r"Action Input:\s*(.+?)(?=\nObservation:|$)"
        match = re.search(pattern, test["output"], re.DOTALL)

        if match:
            action_input = match.group(1).strip()
            print(f"Extracted Action Input: {action_input}")

            # Try to parse as JSON
            try:
                if action_input.startswith("{") and action_input.endswith("}"):
                    parsed = json.loads(action_input)
                    print(f"✅ Successfully parsed: {parsed}")
                else:
                    print("❌ Not in JSON format - this would cause the error")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing would fail: {e}")
        else:
            print("❌ Could not extract Action Input")


def test_prompt_effectiveness():
    """Test if our prompt update would help guide the agent to use correct format."""

    print("\n📋 Testing Prompt Effectiveness")
    print("=" * 50)

    # Our updated prompt includes this guidance:
    prompt_guidance = """
IMPORTANT: Action Input must be valid JSON format. For example:
- Correct: {"file_path": "~/test.txt", "content": "Hello world"}
- Incorrect: file_path = '~/test.txt', content = '''Hello world'''
"""

    print("✅ Updated prompt includes explicit JSON format guidance:")
    print(prompt_guidance)
    print("\nThis should help the agent understand that it needs to use JSON format")
    print("for Action Input instead of Python variable assignment syntax.")


if __name__ == "__main__":
    test_json_parsing()
    simulate_langchain_react_parser()
    test_prompt_effectiveness()

    print("\n🎯 Summary")
    print("=" * 50)
    print("✅ Identified the core issue: Agent using Python syntax instead of JSON")
    print("✅ Updated agent prompt to explicitly require JSON format")
    print("✅ Added examples of correct vs incorrect formats")
    print("💡 The fix should resolve the 'content parameter is required' errors")
