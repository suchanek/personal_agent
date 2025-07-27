#!/usr/bin/env python3
"""
Diagnostic script to test Qwen3 tool calling capabilities with OllamaTools
"""

import json
from agno.models.ollama import OllamaTools
from agno.models.message import Message
from agno.tools.duckduckgo import DuckDuckGoTools

def test_qwen3_tool_calling():
    """Test Qwen3 model's ability to generate proper tool calls"""
    
    print("=== Qwen3 Tool Calling Diagnostic ===\n")
    
    # Initialize OllamaTools with Qwen3
    model = OllamaTools(
        id="qwen3:8b"
    )
    
    # Create a simple tool
    search_tool = DuckDuckGoTools()
    tools = [search_tool.to_dict()]
    
    print("1. Testing Tool Call Prompt Generation:")
    tool_prompt = model.get_tool_call_prompt(tools)
    print(f"Tool prompt length: {len(tool_prompt) if tool_prompt else 0}")
    if tool_prompt:
        print("✓ Tool prompt generated successfully")
        print(f"First 200 chars: {tool_prompt[:200]}...")
    else:
        print("✗ No tool prompt generated")
    
    print("\n2. Testing System Message Generation:")
    system_msg = model.get_system_message_for_model(tools)
    print(f"System message exists: {system_msg is not None}")
    
    print("\n3. Testing Tool Call Instructions:")
    instructions = model.get_instructions_for_model(tools)
    print(f"Instructions: {instructions}")
    
    print("\n4. Testing Direct Model Response:")
    messages = [
        Message(role="user", content="Search for 'Python programming tutorials' using the search tool")
    ]
    
    try:
        # Test raw response
        response = model.invoke(messages=messages, tools=tools)
        print(f"Raw response type: {type(response)}")
        print(f"Response keys: {list(response.keys()) if hasattr(response, 'keys') else 'Not a dict'}")
        
        if 'message' in response:
            content = response['message'].get('content', '')
            print(f"Response content length: {len(content)}")
            print(f"Contains <tool_call>: {'<tool_call>' in content}")
            print(f"Contains </tool_call>: {'</tool_call>' in content}")
            print(f"First 300 chars of response:\n{content[:300]}")
            
            # Test parsing
            model_response = model.parse_provider_response(response)
            print(f"\nParsed tool calls: {model_response.tool_calls}")
            print(f"Parsed content: {model_response.content[:100] if model_response.content else 'None'}...")
        
    except Exception as e:
        print(f"Error during model invocation: {e}")
    
    print("\n5. Testing Expected Tool Call Format:")
    expected_format = """<tool_call>
{"name": "duckduckgo_search", "arguments": {"query": "Python programming tutorials"}}
</tool_call>"""
    print("Expected format:")
    print(expected_format)
    
    print("\n=== Diagnostic Complete ===")

if __name__ == "__main__":
    test_qwen3_tool_calling()