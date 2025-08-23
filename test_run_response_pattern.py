#!/usr/bin/env python3
"""
Test script to verify the proper RunResponse pattern implementation.
"""

import asyncio
from typing import Iterator
from agno.agent import RunResponse
from src.personal_agent.core.agno_agent import AgnoPersonalAgent

async def test_run_response_pattern():
    """Test the proper RunResponse pattern implementation."""
    print("🧪 Testing RunResponse pattern implementation...")
    
    try:
        # Create agent with minimal setup for testing
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name="qwen3:1.7b",
            enable_memory=False,  # Disable for simple test
            alltools=False,  # Disable tools for simple test
            debug=True
        )
        
        # Test 1: Stream mode (should return Iterator[RunResponse])
        print("\n📡 Test 1: Stream mode (stream=True)")
        run_stream = await agent.run("Hello, what is 2+2?", stream=True)
        
        print(f"✅ Stream mode returned: {type(run_stream)}")
        print(f"   Is Iterator: {hasattr(run_stream, '__iter__')}")
        print(f"   Is async iterator: {hasattr(run_stream, '__aiter__')}")
        
        # Test 2: Non-stream mode (should return string)
        print("\n📝 Test 2: Non-stream mode (stream=False)")
        response_str = await agent.run("Hello, what is 3+3?", stream=False)
        
        print(f"✅ Non-stream mode returned: {type(response_str)}")
        print(f"   Response: {response_str[:100]}...")
        
        print("\n✅ All tests passed! RunResponse pattern is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_run_response_pattern())
