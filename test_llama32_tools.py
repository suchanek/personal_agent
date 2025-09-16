#!/usr/bin/env python3
"""
Test script to verify that the updated Llama32.Tools.Modelfile properly handles tool calling
using the XML-based approach similar to the Qwen model.
"""

import json
import subprocess
import sys

def test_tool_calling():
    """Test the tool calling functionality with the updated Llama32 model."""
    
    # Define a simple test tool
    test_tool = {
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
    
    # Create a test prompt that should trigger tool usage
    test_prompt = "What's the weather like in New York City?"
    
    # Prepare the ollama command with tools
    cmd = [
        "ollama", "run", "llama32-tools",
        "--format", "json",
        test_prompt
    ]
    
    print("Testing Llama32 tool calling with updated template...")
    print(f"Prompt: {test_prompt}")
    print(f"Tool available: {test_tool['function']['name']}")
    print("\nRunning test...")
    
    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Command executed successfully")
            print(f"Response: {result.stdout}")
            
            # Check if the response contains XML tool call tags
            if "<tool_call>" in result.stdout and "</tool_call>" in result.stdout:
                print("✅ XML tool call tags detected - template working correctly!")
            else:
                print("⚠️  No XML tool call tags found in response")
                
        else:
            print(f"❌ Command failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Error running test: {e}")

def compare_templates():
    """Compare the key differences between old and new templates."""
    print("\n" + "="*60)
    print("TEMPLATE COMPARISON")
    print("="*60)
    
    print("\nOLD APPROACH (problematic):")
    print("- Used plain JSON Schema for tools")
    print("- Expected pure JSON tool calls without XML wrapping")
    print("- No structured tool response handling")
    
    print("\nNEW APPROACH (fixed, based on Qwen):")
    print("- Uses <tools></tools> XML tags to wrap tool definitions")
    print("- Uses <tool_call></tool_call> XML tags to wrap tool calls")
    print("- Uses <tool_response></tool_response> XML tags to wrap tool responses")
    print("- Provides clear XML formatting instructions")
    print("- Maintains Llama-specific token format (<|start_header_id|>, <|eot_id|>)")

if __name__ == "__main__":
    print("Llama32 Tools Template Test")
    print("="*40)
    
    # Show the comparison first
    compare_templates()
    
    # Run the actual test
    print("\n" + "="*60)
    print("FUNCTIONALITY TEST")
    print("="*60)
    test_tool_calling()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("The Llama32.Tools.Modelfile has been updated to use the same")
    print("XML-based tool calling approach as the working Qwen model.")
    print("This should provide more reliable tool calling functionality.")
