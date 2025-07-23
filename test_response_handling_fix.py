#!/usr/bin/env python3
"""
Test script to verify the response handling fixes for the personal agent.

This script tests the specific issues identified:
1. Empty response handling
2. SmolLM2 instruction optimization
3. Response stream processing
4. Greeting handling
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.core.agent_instruction_manager import InstructionLevel

# Configure logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_response_handling():
    """Test the response handling fixes."""
    print("🧪 Testing Response Handling Fixes")
    print("=" * 50)
    
    # Test with SmolLM2 model (the problematic one from your logs)
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="smollm2:1.7B",
        enable_memory=False,  # Disable memory for simpler testing
        enable_mcp=False,     # Disable MCP for simpler testing
        debug=True,           # Enable debug logging
        instruction_level=InstructionLevel.CONCISE
    )
    
    print("🚀 Initializing agent...")
    success = await agent.initialize()
    
    if not success:
        print("❌ Failed to initialize agent")
        return False
    
    print("✅ Agent initialized successfully")
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Greeting",
            "query": "hello",
            "expected_pattern": "Hello charlie!"
        },
        {
            "name": "Greeting with Punctuation",
            "query": "hello!",
            "expected_pattern": "Hello charlie!"
        },
        {
            "name": "Hi Greeting",
            "query": "hi",
            "expected_pattern": "Hello charlie!"
        },
        {
            "name": "Simple Question",
            "query": "How are you?",
            "expected_pattern": None  # Just check it's not empty
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"Query: '{test_case['query']}'")
        
        try:
            response = await agent.run(test_case['query'])
            
            print(f"Response: '{response}'")
            print(f"Response length: {len(response)}")
            
            # Check if response is empty
            if not response or not response.strip():
                print("❌ FAIL: Empty response")
                results.append(False)
                continue
            
            # Check expected pattern if provided
            if test_case['expected_pattern']:
                if test_case['expected_pattern'].lower() in response.lower():
                    print("✅ PASS: Expected pattern found")
                    results.append(True)
                else:
                    print(f"❌ FAIL: Expected '{test_case['expected_pattern']}' not found in response")
                    results.append(False)
            else:
                print("✅ PASS: Non-empty response received")
                results.append(True)
                
            # Check tool calls
            tool_calls = agent.get_last_tool_calls()
            print(f"Tool calls made: {len(tool_calls)}")
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = getattr(tool_call, 'tool_name', 'unknown')
                    print(f"  - {tool_name}")
            
        except Exception as e:
            print(f"❌ FAIL: Exception occurred: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_case, result) in enumerate(zip(test_cases, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"Test {i} ({test_case['name']}): {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Response handling fixes are working.")
        return True
    else:
        print("⚠️  Some tests failed. Response handling needs more work.")
        return False

async def test_instruction_optimization():
    """Test that SmolLM2 gets optimized instructions."""
    print("\n🧪 Testing Instruction Optimization")
    print("=" * 50)
    
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="smollm2:1.7B",
        enable_memory=False,
        enable_mcp=False,
        debug=True,
        instruction_level=InstructionLevel.STANDARD  # This should trigger optimization
    )
    
    # Get the instructions without initializing the full agent
    instructions = agent.instruction_manager.create_instructions()
    
    print(f"Generated instructions length: {len(instructions)} characters")
    print(f"Instructions preview:\n{instructions[:300]}...")
    
    # Check if instructions are optimized (should be much shorter for SmolLM2)
    if len(instructions) < 500:  # Optimized instructions should be much shorter
        print("✅ PASS: Instructions appear to be optimized for SmolLM2")
        return True
    else:
        print("❌ FAIL: Instructions are too long, optimization may not be working")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Response Handling Fix Tests")
    print("=" * 60)
    
    try:
        # Test instruction optimization first (doesn't require full initialization)
        instruction_test = await test_instruction_optimization()
        
        # Test response handling
        response_test = await test_response_handling()
        
        print("\n" + "=" * 60)
        print("🏁 Final Results")
        print("=" * 60)
        
        if instruction_test and response_test:
            print("🎉 ALL TESTS PASSED! The response handling fixes are working correctly.")
            return 0
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            return 1
            
    except Exception as e:
        print(f"❌ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
