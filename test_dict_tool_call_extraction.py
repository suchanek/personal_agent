#!/usr/bin/env python3
"""
Test script to verify the dictionary-based tool call extraction fix.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the fixed function
sys.path.insert(0, str(Path(__file__).parent / "tools"))
from paga_streamlit_agno import extract_tool_calls_and_metrics, format_tool_call_for_debug

class MockMessage:
    def __init__(self, role, tool_calls=None):
        self.role = role
        self.tool_calls = tool_calls or []
        self.metrics = {"response_time": 1.5, "tokens": 100}

class MockResponse:
    def __init__(self, messages=None):
        self.messages = messages or []

def test_dict_tool_call_extraction():
    """Test the improved tool call extraction logic with dictionary-based tool calls."""
    print("🧪 Testing dictionary-based tool call extraction logic...")
    
    # Test Case 1: Dictionary with 'name' key
    dict_tool_call_1 = {
        "name": "write_poem",
        "arguments": {"topic": "robots", "style": "funny"},
        "result": "A funny poem about robots"
    }
    
    # Test Case 2: Dictionary with 'tool_name' key
    dict_tool_call_2 = {
        "tool_name": "search_google",
        "input": {"query": "funny robot jokes"},
        "result": "Search results"
    }
    
    # Test Case 3: Dictionary with function.name (OpenAI style)
    dict_tool_call_3 = {
        "function": {
            "name": "calculate",
            "arguments": {"expression": "2 + 2"}
        },
        "result": "4"
    }
    
    # Test Case 4: Dictionary with minimal structure
    dict_tool_call_4 = {
        "name": "get_weather",
        "arguments": {"location": "San Francisco"}
    }
    
    # Create mock messages and response
    message = MockMessage("assistant", [dict_tool_call_1, dict_tool_call_2, dict_tool_call_3, dict_tool_call_4])
    response = MockResponse([message])
    
    # Test the extraction function
    tool_calls_made, tool_call_details, metrics_data = extract_tool_calls_and_metrics(response)
    
    print(f"✅ Tool calls made: {tool_calls_made}")
    print(f"✅ Metrics extracted: {metrics_data}")
    print(f"✅ Tool call details:")
    
    for i, tool_info in enumerate(tool_call_details, 1):
        print(f"   Tool {i}: {tool_info['name']} - {tool_info['arguments']}")
    
    # Test the legacy function as well
    print("\n🧪 Testing legacy format_tool_call_for_debug function with dictionaries...")
    
    for i, tool_call in enumerate([dict_tool_call_1, dict_tool_call_2, dict_tool_call_3, dict_tool_call_4], 1):
        formatted = format_tool_call_for_debug(tool_call)
        print(f"   Tool {i}: {formatted['name']} - {formatted['arguments']}")
    
    # Verify results
    expected_names = ["write_poem", "search_google", "calculate", "get_weather"]
    actual_names = [tool['name'] for tool in tool_call_details]
    
    if actual_names == expected_names:
        print("\n✅ SUCCESS: All dictionary-based tool names extracted correctly!")
        return True
    else:
        print(f"\n❌ FAILURE: Expected {expected_names}, got {actual_names}")
        return False

if __name__ == "__main__":
    success = test_dict_tool_call_extraction()
    sys.exit(0 if success else 1)