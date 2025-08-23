#!/usr/bin/env python3
"""
Demonstration of the fixed RunResponse pattern implementation.

This script shows how to use the improved .run() method that properly handles
RunResponse parsing, tool calls, and the pprint_run_response functionality.
"""

import asyncio
from src.personal_agent.core.agno_agent import AgnoPersonalAgent

async def demo_run_response_pattern():
    """Demonstrate the proper RunResponse pattern implementation."""
    print("🚀 Demonstrating RunResponse pattern implementation...")
    
    # Create agent with minimal setup for demo
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="qwen3:1.7b",
        enable_memory=False,  # Disable for simple demo
        alltools=True,  # Enable tools to show tool call handling
        debug=True
    )
    
    print("\n" + "="*60)
    print("DEMO 1: Stream mode with pprint_run_response")
    print("="*60)
    
    # Test 1: Stream mode with pprint
    run_stream = await agent.run("What is 5 + 7?", stream=True)
    print("📡 Printing stream response using pprint_run_response:")
    agent.print_run_response(run_stream, markdown=True, show_time=True)
    
    print("\n" + "="*60)
    print("DEMO 2: Non-stream mode with metrics")
    print("="*60)
    
    # Test 2: Non-stream mode with metrics
    response_str = await agent.run("Calculate 10 * 15", stream=False)
    print(f"📝 String response: {response_str[:100]}...")
    
    # Show the pattern from your task description
    print("\n📊 Printing metrics per message (your requested pattern):")
    agent.print_run_response_with_metrics()
    
    print("\n" + "="*60)
    print("DEMO 3: Tool call extraction")
    print("="*60)
    
    # Test 3: Tool call extraction
    tool_calls = agent.get_last_tool_calls()
    print(f"🔧 Tool calls from last run: {len(tool_calls)} found")
    for i, tool_call in enumerate(tool_calls):
        print(f"   Tool {i+1}: {tool_call}")
    
    print("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    asyncio.run(demo_run_response_pattern())
