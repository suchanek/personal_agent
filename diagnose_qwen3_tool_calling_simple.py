#!/usr/bin/env python3
"""
Simple diagnostic script to test Qwen3 tool calling capabilities with OllamaTools
"""

import json
from agno.models.ollama import OllamaTools
from agno.models.message import Message
from agno.tools.duckduckgo import DuckDuckGoTools

def test_qwen3_tool_calling():
    """Test Qwen3 model's ability to generate proper tool calls"""
    
    print("=== Qwen3 Tool Calling Diagnostic ===\n")
    
    # Initialize OllamaTools with Qwen3
    model = OllamaTools(id="qwen3:8b")
    
    # Create a simple tool (same as in working example)
    search_tool = DuckDuckGoTools(cache_results=True)
    
    print("1. Testing Tool Call Prompt Generation:")
    # Get tools in the format expected by the model
    tools = search_tool.to_dict()
    tool_prompt = model.get_tool_call_prompt(tools)
    
    if tool_prompt:
        print("✓ Tool prompt generated successfully")
        print(f"Tool prompt length: {len(tool_prompt)}")
        print(f"Contains <tool_call> instructions: {'<tool_call>' in tool_prompt}")
        print(f"Contains XML format: {'</tool_call>' in tool_prompt}")
        print("\nFirst 500 chars of tool prompt:")
        print("-" * 50)
        print(tool_prompt[:500])
        print("-" * 50)
    else:
        print("✗ No tool prompt generated")
    
    print("\n2. Testing Direct Model Response:")
    messages = [
        Message(role="user", content="Search for 'Python programming tutorials' using the search tool")
    ]
    
    try:
        # Test raw response with tools
        response = model.invoke(messages=messages, tools=tools)
        print(f"✓ Model responded successfully")
        print(f"Response type: {type(response)}")
        
        if 'message' in response:
            content = response['message'].get('content', '')
            print(f"Response content length: {len(content)}")
            print(f"Contains <tool_call>: {'<tool_call>' in content}")
            print(f"Contains </tool_call>: {'</tool_call>' in content}")
            
            print(f"\nFull response content:")
            print("-" * 50)
            print(content)
            print("-" * 50)
            
            # Test parsing
            model_response = model.parse_provider_response(response)
            print(f"\nParsed tool calls: {model_response.tool_calls}")
            print(f"Number of tool calls: {len(model_response.tool_calls) if model_response.tool_calls else 0}")
            
            if model_response.tool_calls:
                print("✓ Tool calls were parsed successfully!")
                for i, tool_call in enumerate(model_response.tool_calls):
                    print(f"  Tool call {i+1}: {tool_call}")
            else:
                print("✗ No tool calls were parsed from the response")
        
    except Exception as e:
        print(f"✗ Error during model invocation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n3. Testing Expected vs Actual Format:")
    expected_format = """<tool_call>
{"name": "duckduckgo_search", "arguments": {"query": "Python programming tutorials"}}
</tool_call>"""
    print("Expected XML format:")
    print(expected_format)
    
    print("\n=== Diagnostic Complete ===")

if __name__ == "__main__":
    test_qwen3_tool_calling()