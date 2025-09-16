#!/usr/bin/env python3
"""
Proper test script to verify that the updated Llama32.Tools.Modelfile handles tool calling
with actual tools provided to the model.
"""

import json
import subprocess
import tempfile
import os

def create_test_with_tools():
    """Create a test that actually provides tools to the model."""
    
    # Create a temporary file with a tool-enabled conversation
    test_data = {
        "model": "llama32-tools",
        "messages": [
            {
                "role": "user",
                "content": "What's the weather like in New York City? Please use the weather tool."
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ],
        "stream": False
    }
    
    print("Testing Llama32 tool calling with actual tools provided...")
    print(f"Tool available: {test_data['tools'][0]['function']['name']}")
    print(f"User prompt: {test_data['messages'][0]['content']}")
    print("\nSending request to ollama API...")
    
    try:
        # Use ollama's API endpoint
        cmd = [
            "curl", "-X", "POST", "http://localhost:11434/api/chat",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(test_data)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ API call successful")
            try:
                response_data = json.loads(result.stdout)
                response_content = response_data.get('message', {}).get('content', '')
                
                print(f"Response content: {response_content}")
                
                # Check for XML tool call tags
                if "<tool_call>" in response_content and "</tool_call>" in response_content:
                    print("✅ XML tool call tags found - template working correctly!")
                    
                    # Extract the tool call content
                    start_tag = response_content.find("<tool_call>")
                    end_tag = response_content.find("</tool_call>")
                    if start_tag != -1 and end_tag != -1:
                        tool_call_content = response_content[start_tag+11:end_tag].strip()
                        print(f"Tool call content: {tool_call_content}")
                        
                        # Try to parse as JSON
                        try:
                            tool_call_json = json.loads(tool_call_content)
                            print("✅ Tool call content is valid JSON")
                            print(f"Function name: {tool_call_json.get('name')}")
                            print(f"Arguments: {tool_call_json.get('arguments')}")
                        except json.JSONDecodeError:
                            print("⚠️  Tool call content is not valid JSON")
                            
                else:
                    print("❌ No XML tool call tags found in response")
                    print("This suggests the template may not be working as expected")
                    
            except json.JSONDecodeError:
                print("❌ Failed to parse response as JSON")
                print(f"Raw response: {result.stdout}")
                
        else:
            print(f"❌ API call failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ API call timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Error during test: {e}")

def test_template_directly():
    """Test the template by examining the model directly."""
    print("\n" + "="*60)
    print("DIRECT TEMPLATE TEST")
    print("="*60)
    
    try:
        # Show the model info with --modelfile to verify our template is loaded
        cmd = ["ollama", "show", "llama32-tools", "--modelfile"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Model exists and template loaded")
            
            # Check if our XML-based template is present
            if "<tools>" in result.stdout and "<tool_call>" in result.stdout and "<tool_response>" in result.stdout:
                print("✅ XML-based template detected in model")
                print("✅ Template includes <tools>, <tool_call>, and <tool_response> tags")
            else:
                print("❌ XML-based template not found in model")
                print("The model may not have been updated properly")
                
        else:
            print(f"❌ Failed to show model info: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error checking model: {e}")

if __name__ == "__main__":
    print("Llama32 Tools XML Template Test")
    print("="*40)
    
    # First check the template directly
    test_template_directly()
    
    # Then test with actual tool calling
    print("\n" + "="*60)
    print("TOOL CALLING TEST")
    print("="*60)
    create_test_with_tools()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("This test verifies that the Llama32.Tools.Modelfile properly")
    print("uses XML tags for tool calling, matching the Qwen approach.")
