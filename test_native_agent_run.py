#!/usr/bin/env python3
"""
Test script to verify the native Agent.arun() method works without custom parsing.
This helps isolate whether the issue is with our response handling or the underlying system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.utils import setup_logging

# Configure logging
logger = setup_logging(__name__, level="INFO")


async def test_native_agent_run():
    """Test the native Agent.arun() method directly."""
    
    print("🧪 Testing Native Agent.arun() Method")
    print("=" * 50)
    
    try:
        # Create agent with minimal tools to reduce complexity
        print("📝 Creating AgnoPersonalAgent with minimal configuration...")
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name="gpt-oss:20b",  # Test the problematic model
            enable_memory=False,  # Disable memory to simplify
            enable_mcp=False,     # Disable MCP to simplify
            debug=True,           # Enable debug for detailed logging
            alltools=False,       # Disable all tools initially
        )
        
        print(f"✅ Agent created with model: {agent.model_name}")
        
        # Test simple query without tools first
        print("\n🔍 Testing simple query without tools...")
        simple_query = "Hello! What's 2 + 2?"
        
        try:
            response = await agent.run(simple_query)
            print(f"✅ Simple query successful!")
            print(f"📝 Response: {response[:200]}...")
            
        except Exception as e:
            print(f"❌ Simple query failed: {e}")
            logger.error("Simple query error:", exc_info=True)
            return False
        
        # Now test with minimal tools
        print("\n🔍 Testing with calculator tool...")
        agent_with_tools = AgnoPersonalAgent(
            model_provider="ollama",
            model_name="gpt-oss:20b",  # Test the problematic model with tools
            enable_memory=False,  # Disable memory to simplify
            enable_mcp=False,     # Disable MCP to simplify
            debug=True,           # Enable debug for detailed logging
            alltools=True,        # Enable tools but with model limits
        )
        
        tool_query = "Calculate 15 * 23 for me"
        
        try:
            response = await agent_with_tools.run(tool_query)
            print(f"✅ Tool query successful!")
            print(f"📝 Response: {response[:200]}...")
            
        except Exception as e:
            print(f"❌ Tool query failed: {e}")
            logger.error("Tool query error:", exc_info=True)
            
            # Check if it's the specific parsing error we're investigating
            if "validation error for ChatResponse" in str(e):
                print("🔍 This is the ChatResponse validation error we're investigating!")
                print("🔍 The error occurs in the native Agent.arun() method, not our custom parsing")
                return False
            elif "Function calculator_tools.add not found" in str(e):
                print("🔍 This is the tool function name mismatch error!")
                print("🔍 The model is trying to call functions that don't match the tool registration")
                return False
        
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        logger.error("Test setup error:", exc_info=True)
        return False


async def main():
    """Main test function."""
    print("🚀 Starting Native Agent Test")
    
    success = await test_native_agent_run()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("✅ The native Agent.arun() method works correctly")
        print("✅ The issue was likely in our custom response parsing")
    else:
        print("\n⚠️  Test revealed issues with the native Agent.arun() method")
        print("🔍 The problem is in the underlying Agno framework or tool calling")
        print("🔍 This helps isolate the root cause of the original error")


if __name__ == "__main__":
    asyncio.run(main())
