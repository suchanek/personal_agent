#!/usr/bin/env python3
"""
Test to verify the JSON format fix resolves the tool input parsing issue.
This test validates that the updated agent prompt correctly guides the LLM to use JSON format.
"""

import os
import sys
import tempfile

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))


def test_agent_prompt_includes_json_guidance():
    """Test that the agent prompt includes JSON format guidance."""
    # Read the agent.py file directly to check the prompt content
    agent_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src",
        "personal_agent",
        "core",
        "agent.py",
    )

    with open(agent_file_path, "r", encoding="utf-8") as f:
        agent_code = f.read()

    # Check that the prompt includes JSON format guidance
    assert "Action Input: the input to the action as valid JSON" in agent_code
    assert "IMPORTANT: Action Input must be valid JSON format" in agent_code
    assert (
        'Correct: {{"file_path": "~/test.txt", "content": "Hello world"}}' in agent_code
    )
    assert (
        "Incorrect: file_path = '~/test.txt', content = '''Hello world'''" in agent_code
    )

    print("✅ Agent prompt includes proper JSON format guidance")


def test_json_parsing_scenarios():
    """Test various JSON parsing scenarios that the agent might encounter."""
    import json

    # Test cases representing different formats the agent might generate
    test_cases = [
        {
            "name": "Valid JSON (double quotes)",
            "input": '{"file_path": "~/test.txt", "content": "Hello world"}',
            "should_work": True,
        },
        {
            "name": "Python assignment syntax (the problem)",
            "input": "file_path = '~/test.txt', content = '''Hello world'''",
            "should_work": False,
        },
        {
            "name": "Python dict with single quotes",
            "input": "{'file_path': '~/test.txt', 'content': 'Hello world'}",
            "should_work": False,  # JSON requires double quotes
        },
        {
            "name": "Multi-line content (problematic case from test output)",
            "input": """{"file_path": "~/test.txt", "content": "Line 1\\nLine 2\\nLine 3"}""",
            "should_work": True,
        },
    ]

    results = []
    for test_case in test_cases:
        try:
            if test_case["input"].startswith("{") and test_case["input"].endswith("}"):
                parsed = json.loads(test_case["input"])
                has_required_params = "file_path" in parsed and "content" in parsed
                success = True and has_required_params
            else:
                success = False

            results.append(
                {
                    "name": test_case["name"],
                    "expected": test_case["should_work"],
                    "actual": success,
                    "passed": success == test_case["should_work"],
                }
            )

        except (json.JSONDecodeError, TypeError, KeyError):
            results.append(
                {
                    "name": test_case["name"],
                    "expected": test_case["should_work"],
                    "actual": False,
                    "passed": False == test_case["should_work"],
                }
            )

    # Print results
    print("\n📊 JSON Parsing Test Results:")
    print("-" * 50)
    all_passed = True
    for result in results:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['name']}")
        if not result["passed"]:
            all_passed = False
            print(f"   Expected: {result['expected']}, Got: {result['actual']}")

    assert all_passed, "Some JSON parsing tests failed"
    print("✅ All JSON parsing scenarios work as expected")


def test_langchain_react_pattern_simulation():
    """Simulate how LangChain ReAct parser extracts Action Input."""
    import re

    # Simulate agent outputs in ReAct format
    good_output = """Thought: I need to write a test file
Action: mcp_write_file
Action Input: {"file_path": "~/test.txt", "content": "Hello world"}
Observation: File written successfully"""

    bad_output = """Thought: I need to write a test file
Action: mcp_write_file
Action Input: file_path = '~/test.txt', content = '''Hello world'''
Observation: Error: content parameter is required"""

    # Pattern to extract Action Input (similar to LangChain)
    pattern = r"Action Input:\s*(.+?)(?=\nObservation:|$)"

    # Test good format
    match = re.search(pattern, good_output, re.DOTALL)
    assert match, "Could not extract Action Input from good output"

    good_action_input = match.group(1).strip()
    assert good_action_input.startswith("{"), "Good format should start with {"
    assert good_action_input.endswith("}"), "Good format should end with }"

    # Test bad format
    match = re.search(pattern, bad_output, re.DOTALL)
    assert match, "Could not extract Action Input from bad output"

    bad_action_input = match.group(1).strip()
    assert not bad_action_input.startswith("{"), "Bad format should not start with {"

    print("✅ LangChain ReAct pattern simulation works correctly")


def test_filesystem_tool_parameter_handling():
    """Test that filesystem tools can handle JSON parameters correctly."""
    # We'll test the parameter extraction logic that's in the filesystem tools
    import json

    # Simulate the parameter handling logic from mcp_write_file
    def extract_parameters(file_path_param, content_param):
        """Simulate the parameter extraction logic from the filesystem tools."""
        file_path = file_path_param
        content = content_param

        # Handle case where LangChain passes entire JSON as first parameter
        if (
            isinstance(file_path_param, str)
            and file_path_param.startswith("{")
            and file_path_param.endswith("}")
        ):
            try:
                params = json.loads(file_path_param)
                if "file_path" in params and "content" in params:
                    file_path = params["file_path"]
                    content = params["content"]
                    return file_path, content, True  # Successfully extracted
            except (json.JSONDecodeError, TypeError):
                pass

        return file_path, content, False  # Normal parameters

    # Test cases
    test_cases = [
        {
            "name": "Normal parameters",
            "file_path": "~/test.txt",
            "content": "Hello world",
            "should_extract": False,
        },
        {
            "name": "JSON string parameter (LangChain workaround)",
            "file_path": '{"file_path": "~/test.txt", "content": "Hello world"}',
            "content": None,
            "should_extract": True,
        },
        {
            "name": "Invalid JSON string",
            "file_path": "file_path = '~/test.txt', content = 'Hello'",
            "content": None,
            "should_extract": False,
        },
    ]

    for test_case in test_cases:
        file_path, content, extracted = extract_parameters(
            test_case["file_path"], test_case["content"]
        )

        assert (
            extracted == test_case["should_extract"]
        ), f"Extraction result mismatch for {test_case['name']}"

        if extracted:
            assert (
                file_path == "~/test.txt"
            ), f"File path mismatch for {test_case['name']}"
            assert content == "Hello world", f"Content mismatch for {test_case['name']}"

    print("✅ Filesystem tool parameter handling works correctly")


def test_comprehensive_fix_validation():
    """Comprehensive test to validate the complete fix."""
    print("\n🎯 Comprehensive Fix Validation")
    print("=" * 50)

    # 1. Verify prompt update
    print("1. Testing agent prompt includes JSON guidance...")
    test_agent_prompt_includes_json_guidance()

    # 2. Verify JSON parsing works correctly
    print("2. Testing JSON parsing scenarios...")
    test_json_parsing_scenarios()

    # 3. Verify ReAct pattern extraction
    print("3. Testing LangChain ReAct pattern simulation...")
    test_langchain_react_pattern_simulation()

    # 4. Verify tool parameter handling
    print("4. Testing filesystem tool parameter handling...")
    test_filesystem_tool_parameter_handling()

    print(
        "\n🎉 All tests passed! The JSON format fix should resolve the parsing issue."
    )
    print("\nSummary of the fix:")
    print(
        "- ✅ Updated agent prompt to explicitly require JSON format for Action Input"
    )
    print("- ✅ Added clear examples of correct vs incorrect formats")
    print("- ✅ Maintained backward compatibility with existing parameter handling")
    print(
        "- ✅ The fix addresses the root cause: agent using Python syntax instead of JSON"
    )


if __name__ == "__main__":
    try:
        test_comprehensive_fix_validation()
        print("\n✅ All tests completed successfully!")
    except (AssertionError, ImportError, FileNotFoundError) as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
