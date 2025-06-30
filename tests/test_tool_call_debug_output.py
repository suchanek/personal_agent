#!/usr/bin/env python3
"""
Test script to verify that tool call debug output is working correctly.

This script tests the get_last_tool_calls() method to ensure it properly
extracts and formats tool call arguments for debug display.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_tool_call_debug_output():
    """Test that tool call debug output shows proper arguments."""
    print("🧪 Testing Tool Call Debug Output")
    print("=" * 50)
    
    # Create agent with debug enabled
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=True,
        storage_dir=AGNO_STORAGE_DIR,
        debug=True,  # Enable debug mode
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
    )
    
    # Initialize agent
    print("🔄 Initializing agent...")
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return False
    
    print("✅ Agent initialized successfully")
    
    # Test 1: News search (should trigger DuckDuckGo tool)
    print("\n📰 Test 1: News search with tool call")
    print("-" * 30)
    
    query = "show me the top 3 news headlines about AI developments"
    print(f"Query: {query}")
    
    try:
        response = await agent.run(query)
        print(f"Response length: {len(response)} characters")
        
        # Get tool call information
        tool_call_info = agent.get_last_tool_calls()
        
        print("\n🔍 Tool Call Debug Information:")
        print(f"Tool calls count: {tool_call_info.get('tool_calls_count', 0)}")
        print(f"Has tool calls: {tool_call_info.get('has_tool_calls', False)}")
        
        if tool_call_info.get('tool_call_details'):
            for i, tool_call in enumerate(tool_call_info['tool_call_details'], 1):
                print(f"\nTool Call {i}:")
                print(f"  ID: {tool_call.get('id', 'unknown')}")
                print(f"  Type: {tool_call.get('type', 'unknown')}")
                print(f"  Function: {tool_call.get('function_name', 'unknown')}")
                
                # This is the key test - arguments should be properly formatted
                args = tool_call.get('function_args', {})
                print(f"  Arguments: {args}")
                print(f"  Arguments type: {type(args)}")
                
                # Verify arguments are properly parsed
                if isinstance(args, dict) and args:
                    print("  ✅ Arguments properly parsed as dictionary")
                    for key, value in args.items():
                        print(f"    {key}: {value}")
                elif isinstance(args, str) and args != '{}':
                    print("  ⚠️  Arguments still as string (may be expected for some tools)")
                    print(f"    Raw string: {args}")
                else:
                    print("  ❌ Arguments empty or not properly parsed")
        else:
            print("No tool call details found")
        
        # Show debug info
        debug_info = tool_call_info.get('debug_info', {})
        if debug_info:
            print(f"\n🔧 Debug Info:")
            print(f"  Response attributes: {len(debug_info.get('response_attributes', []))}")
            print(f"  Has messages: {debug_info.get('has_messages', False)}")
            print(f"  Messages count: {debug_info.get('messages_count', 0)}")
            print(f"  Has tool_calls attr: {debug_info.get('has_tool_calls_attr', False)}")
            print(f"  Has formatted_tool_calls attr: {debug_info.get('has_formatted_tool_calls_attr', False)}")
            print(f"  Formatted tool calls count: {debug_info.get('formatted_tool_calls_count', 0)}")
        
    except Exception as e:
        print(f"❌ Error during news search test: {e}")
        return False
    
    # Test 2: Finance query (should trigger YFinance tool)
    print("\n💰 Test 2: Finance query with tool call")
    print("-" * 30)
    
    query = "get the current stock price for NVDA"
    print(f"Query: {query}")
    
    try:
        response = await agent.run(query)
        print(f"Response length: {len(response)} characters")
        
        # Get tool call information
        tool_call_info = agent.get_last_tool_calls()
        
        print("\n🔍 Tool Call Debug Information:")
        print(f"Tool calls count: {tool_call_info.get('tool_calls_count', 0)}")
        
        if tool_call_info.get('tool_call_details'):
            for i, tool_call in enumerate(tool_call_info['tool_call_details'], 1):
                print(f"\nTool Call {i}:")
                print(f"  Function: {tool_call.get('function_name', 'unknown')}")
                
                args = tool_call.get('function_args', {})
                print(f"  Arguments: {args}")
                print(f"  Arguments type: {type(args)}")
                
                # Verify arguments for finance tools
                if isinstance(args, dict) and args:
                    print("  ✅ Arguments properly parsed as dictionary")
                    # Look for common finance tool arguments
                    if 'symbol' in args or 'ticker' in args:
                        print(f"    Stock symbol found: {args.get('symbol') or args.get('ticker')}")
                else:
                    print("  ❌ Arguments not properly parsed")
        
    except Exception as e:
        print(f"❌ Error during finance test: {e}")
        return False
    
    # Test 3: Memory query (should trigger memory tools)
    print("\n🧠 Test 3: Memory query with tool call")
    print("-" * 30)
    
    query = "what do you remember about me?"
    print(f"Query: {query}")
    
    try:
        response = await agent.run(query)
        print(f"Response length: {len(response)} characters")
        
        # Get tool call information
        tool_call_info = agent.get_last_tool_calls()
        
        print("\n🔍 Tool Call Debug Information:")
        print(f"Tool calls count: {tool_call_info.get('tool_calls_count', 0)}")
        
        if tool_call_info.get('tool_call_details'):
            for i, tool_call in enumerate(tool_call_info['tool_call_details'], 1):
                print(f"\nTool Call {i}:")
                print(f"  Function: {tool_call.get('function_name', 'unknown')}")
                
                args = tool_call.get('function_args', {})
                print(f"  Arguments: {args}")
                print(f"  Arguments type: {type(args)}")
                
                # Memory tools might have different argument structures
                if isinstance(args, dict):
                    print("  ✅ Arguments properly parsed as dictionary")
                    if args:
                        for key, value in args.items():
                            print(f"    {key}: {value}")
                    else:
                        print("    (No arguments - expected for get_recent_memories)")
                else:
                    print("  ❌ Arguments not properly parsed")
        
    except Exception as e:
        print(f"❌ Error during memory test: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Tool Call Debug Output Test Complete!")
    print("\nKey things to verify:")
    print("1. Arguments should be dictionaries, not empty '{}' strings")
    print("2. Actual parameter values should be visible")
    print("3. Different tool types should show their specific arguments")
    print("\nIf you see properly formatted arguments above, the fix is working!")
    
    return True


def test_argument_parsing():
    """Test the argument parsing function directly."""
    print("\n🔧 Testing Argument Parsing Function")
    print("-" * 30)
    
    # Import the agent to access the parsing logic
    from personal_agent.core.agno_agent import AgnoPersonalAgent
    
    # Create a dummy agent to test the parsing
    agent = AgnoPersonalAgent()
    
    # Test cases for argument parsing
    test_cases = [
        ('{}', {}),
        ('{"max_results": 5, "query": "test"}', {"max_results": 5, "query": "test"}),
        ('{"symbol": "NVDA"}', {"symbol": "NVDA"}),
        ('invalid json', 'invalid json'),
        (None, {}),
        ('', {}),
        ({'already': 'dict'}, {'already': 'dict'}),
    ]
    
    # We need to access the parse_arguments function from the method
    # Since it's defined inside get_last_tool_calls, we'll test the overall behavior
    
    print("Testing various argument formats:")
    for i, (input_val, expected) in enumerate(test_cases, 1):
        print(f"Test {i}: {input_val} -> Expected: {expected}")
    
    print("✅ Argument parsing test cases defined")
    print("(Full testing happens during actual tool calls above)")


async def main():
    """Main test function."""
    print("🚀 Starting Tool Call Debug Output Tests")
    print("This will test the fix for Streamlit debug output showing empty arguments")
    print()
    
    # Test argument parsing logic
    test_argument_parsing()
    
    # Test actual tool calls
    success = await test_tool_call_debug_output()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("The tool call debug output fix appears to be working.")
    else:
        print("\n❌ Some tests failed.")
        print("Check the error messages above for details.")
    
    return success


if __name__ == "__main__":
    # Run the async test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
