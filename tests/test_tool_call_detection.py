#!/usr/bin/env python3
"""
Test script to verify tool call detection in AgnoPersonalAgent.

This script tests the new get_last_tool_calls() method to ensure that
tool calls are properly detected and reported by the agent.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_tool_call_detection():
    """Test tool call detection with various queries."""
    print("🧪 Testing Tool Call Detection in AgnoPersonalAgent")
    print("=" * 60)
    
    # Initialize agent
    print("🔧 Initializing AgnoPersonalAgent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return
    
    print("✅ Agent initialized successfully")
    print(f"📊 Agent info: {agent.get_agent_info()['tool_counts']}")
    print()
    
    # Test cases that should trigger tool calls
    test_cases = [
        {
            "name": "Memory Storage Test",
            "query": "Remember that I like pizza and my favorite color is blue",
            "expected_tools": ["store_user_memory"],
            "should_have_tools": True
        },
        {
            "name": "Memory Retrieval Test", 
            "query": "What do you remember about me?",
            "expected_tools": ["get_recent_memories"],
            "should_have_tools": True
        },
        {
            "name": "Finance Tool Test",
            "query": "What's the current price of AAPL stock?",
            "expected_tools": ["get_current_stock_price"],
            "should_have_tools": True
        },
        {
            "name": "Web Search Test",
            "query": "Search for the latest news about artificial intelligence",
            "expected_tools": ["duckduckgo_search"],
            "should_have_tools": True
        },
        {
            "name": "Python Calculation Test",
            "query": "Calculate 15 * 23 + 47",
            "expected_tools": ["python_run"],
            "should_have_tools": True
        },
        {
            "name": "Simple Chat Test",
            "query": "Hello, how are you today?",
            "expected_tools": [],
            "should_have_tools": False
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}: {test_case['name']}")
        print(f"📝 Query: {test_case['query']}")
        
        try:
            # Run the query
            response = await agent.run(test_case['query'])
            
            # Get tool call information
            tool_info = agent.get_last_tool_calls()
            
            # Analyze results
            tool_count = tool_info.get("tool_calls_count", 0)
            tool_details = tool_info.get("tool_call_details", [])
            has_tools = tool_info.get("has_tool_calls", False)
            debug_info = tool_info.get("debug_info", {})
            
            print(f"🔧 Tool calls detected: {tool_count}")
            print(f"🛠️ Has tool calls: {has_tools}")
            
            if tool_details:
                print("📋 Tool details:")
                for j, tool in enumerate(tool_details, 1):
                    if isinstance(tool, dict):
                        func_name = tool.get('function_name', 'unknown')
                        tool_type = tool.get('type', 'function')
                        print(f"  {j}. {func_name} ({tool_type})")
                    else:
                        print(f"  {j}. {str(tool)}")
            
            # Check if results match expectations
            expected_has_tools = test_case['should_have_tools']
            actual_has_tools = has_tools
            
            if expected_has_tools == actual_has_tools:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            print(f"📊 Expected tools: {expected_has_tools}, Got tools: {actual_has_tools} - {status}")
            
            # Store results
            results.append({
                "test": test_case['name'],
                "query": test_case['query'],
                "expected_tools": expected_has_tools,
                "actual_tools": actual_has_tools,
                "tool_count": tool_count,
                "tool_details": tool_details,
                "debug_info": debug_info,
                "passed": expected_has_tools == actual_has_tools,
                "response_preview": response[:100] + "..." if len(response) > 100 else response
            })
            
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            results.append({
                "test": test_case['name'],
                "query": test_case['query'],
                "error": str(e),
                "passed": False
            })
        
        print("-" * 40)
        print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for r in results if r.get('passed', False))
    total_tests = len(results)
    
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
    print()
    
    # Detailed results
    for result in results:
        status = "✅" if result.get('passed', False) else "❌"
        print(f"{status} {result['test']}")
        
        if 'error' in result:
            print(f"   Error: {result['error']}")
        else:
            print(f"   Tool calls: {result.get('tool_count', 0)}")
            if result.get('tool_details'):
                tool_names = []
                for tool in result['tool_details']:
                    if isinstance(tool, dict):
                        tool_names.append(tool.get('function_name', 'unknown'))
                    else:
                        tool_names.append(str(tool))
                print(f"   Tools used: {', '.join(tool_names)}")
    
    print()
    
    # Debug information
    print("🔍 DEBUG INFORMATION")
    print("=" * 60)
    
    # Show debug info from last test
    if results and 'debug_info' in results[-1]:
        debug = results[-1]['debug_info']
        print("Last response debug info:")
        print(f"  - Has messages: {debug.get('has_messages', False)}")
        print(f"  - Messages count: {debug.get('messages_count', 0)}")
        print(f"  - Has tool_calls attr: {debug.get('has_tool_calls_attr', False)}")
        print(f"  - Response attributes: {debug.get('response_attributes', [])}")
    
    # Test the get_last_tool_calls method directly
    print("\n🔧 Testing get_last_tool_calls() method directly:")
    tool_info = agent.get_last_tool_calls()
    print(f"  - Tool calls count: {tool_info.get('tool_calls_count', 0)}")
    print(f"  - Has tool calls: {tool_info.get('has_tool_calls', False)}")
    print(f"  - Response type: {tool_info.get('response_type', 'unknown')}")
    
    if 'error' in tool_info:
        print(f"  - Error: {tool_info['error']}")
    
    print("\n🎉 Tool call detection test completed!")
    
    return results


async def test_memory_functionality():
    """Test memory-specific functionality to ensure tools are called."""
    print("\n🧠 Testing Memory Functionality")
    print("=" * 60)
    
    # Initialize agent
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    await agent.initialize()
    
    # Test memory storage
    print("📝 Testing memory storage...")
    response1 = await agent.run("Remember that I work as a software engineer and I love coffee")
    tool_info1 = agent.get_last_tool_calls()
    
    print(f"Response: {response1[:100]}...")
    print(f"Tool calls: {tool_info1.get('tool_calls_count', 0)}")
    
    # Test memory retrieval
    print("\n🔍 Testing memory retrieval...")
    response2 = await agent.run("What do you remember about my job and preferences?")
    tool_info2 = agent.get_last_tool_calls()
    
    print(f"Response: {response2[:100]}...")
    print(f"Tool calls: {tool_info2.get('tool_calls_count', 0)}")
    
    return tool_info1, tool_info2


def main():
    """Main test function."""
    print("🚀 Starting Tool Call Detection Tests")
    print("=" * 60)
    
    try:
        # Run main tests
        results = asyncio.run(test_tool_call_detection())
        
        # Run memory-specific tests
        memory_results = asyncio.run(test_memory_functionality())
        
        print("\n✅ All tests completed successfully!")
        
        # Final summary
        passed = sum(1 for r in results if r.get('passed', False))
        total = len(results)
        
        if passed == total:
            print(f"🎉 Perfect score: {passed}/{total} tests passed!")
        else:
            print(f"⚠️ Some tests failed: {passed}/{total} tests passed")
            print("Check the detailed results above for more information.")
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
