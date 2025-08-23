#!/usr/bin/env python3
"""
Test script to verify the tool call extraction fix.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the fixed function
sys.path.insert(0, str(Path(__file__).parent / "tools"))
from paga_streamlit_agno import extract_tool_calls_and_metrics, format_tool_call_for_debug

# Mock tool call objects to test different scenarios
class MockToolCallWithName:
    def __init__(self, name, arguments=None):
        self.name = name
        self.arguments = arguments or {}
        self.result = "Mock result"

class MockToolCallWithToolName:
    def __init__(self, tool_name, tool_args=None):
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.result = "Mock result"

class MockToolCallWithFunction:
    def __init__(self, function_name, function_args=None):
        self.function = MockFunction(function_name, function_args)
        self.result = "Mock result"

class MockFunction:
    def __init__(self, name, arguments=None):
        self.name = name
        self.arguments = arguments or {}

class MockToolCallWithInput:
    def __init__(self, name, input_data=None):
        self.name = name
        self.input = input_data or {}
        self.result = "Mock result"

class MockMessage:
    def __init__(self, role, tool_calls=None):
        self.role = role
        self.tool_calls = tool_calls or []
        self.metrics = {"response_time": 1.5, "tokens": 100}

class MockResponse:
    def __init__(self, messages=None):
        self.messages = messages or []

def test_tool_call_extraction():
    """Test the improved tool call extraction logic."""
    print("🧪 Testing tool call extraction logic...")
    
    # Test Case 1: Tool call with 'name' attribute
    tool_call_1 = MockToolCallWithName("search_google", {"query": "cats"})
    
    # Test Case 2: Tool call with 'tool_name' attribute (ToolExecution style)
    tool_call_2 = MockToolCallWithToolName("calculate", {"expression": "5 + 7"})
    
    # Test Case 3: Tool call with function.name (OpenAI style)
    tool_call_3 = MockToolCallWithFunction("get_weather", {"location": "New York"})
    
    # Test Case 4: Tool call with 'input' attribute (agno style)
    tool_call_4 = MockToolCallWithInput("write_poem", {"topic": "cats", "style": "haiku"})
    
    # Create mock messages and response
    message = MockMessage("assistant", [tool_call_1, tool_call_2, tool_call_3, tool_call_4])
    response = MockResponse([message])
    
    # Test the extraction function
    tool_calls_made, tool_call_details, metrics_data = extract_tool_calls_and_metrics(response)
    
    print(f"✅ Tool calls made: {tool_calls_made}")
    print(f"✅ Metrics extracted: {metrics_data}")
    print(f"✅ Tool call details:")
    
    for i, tool_info in enumerate(tool_call_details, 1):
        print(f"   Tool {i}: {tool_info['name']} - {tool_info['arguments']}")
    
    # Test the legacy function as well
    print("\n🧪 Testing legacy format_tool_call_for_debug function...")
    
    for i, tool_call in enumerate([tool_call_1, tool_call_2, tool_call_3, tool_call_4], 1):
        formatted = format_tool_call_for_debug(tool_call)
        print(f"   Tool {i}: {formatted['name']} - {formatted['arguments']}")
    
    # Verify results
    expected_names = ["search_google", "calculate", "get_weather", "write_poem"]
    actual_names = [tool['name'] for tool in tool_call_details]
    
    if actual_names == expected_names:
        print("\n✅ SUCCESS: All tool names extracted correctly!")
        return True
    else:
        print(f"\n❌ FAILURE: Expected {expected_names}, got {actual_names}")
        return False

if __name__ == "__main__":
    success = test_tool_call_extraction()
    sys.exit(0 if success else 1)