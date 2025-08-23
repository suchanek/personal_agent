#!/usr/bin/env python3
"""
Test script to verify the File Operations Agent fix for overthinking behavior.

This script tests that the agent can handle simple directory listing requests
without excessive deliberation or confusion about which tools to use.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.specialized_agents import create_file_operations_agent
from personal_agent.config import LLM_MODEL, OLLAMA_URL


async def test_file_operations_agent():
    """Test the File Operations Agent with a simple directory listing request."""
    
    print("🔧 Creating File Operations Agent...")
    
    # Create the agent
    agent = create_file_operations_agent(
        model_provider="ollama",
        model_name="qwen3:1.7b",  # Use smaller model for faster testing
        ollama_base_url=OLLAMA_URL,
        debug=True
    )
    
    print(f"✅ Agent created: {agent.name}")
    print(f"📋 Agent role: {agent.role}")
    print(f"🛠️  Available tools: {[tool.__class__.__name__ for tool in agent.tools] if agent.tools else 'None'}")
    
    # Test simple directory listing request
    print("\n" + "="*60)
    print("🧪 Testing directory listing request: 'list ~/repos'")
    print("="*60)
    
    try:
        # This should be handled efficiently without overthinking
        response = await agent.arun("list ~/repos")
        
        print("\n📤 Agent Response:")
        print("-" * 40)
        print(response.content)
        print("-" * 40)
        
        # Check if the response is concise and direct
        if len(response.content) > 2000:
            print("⚠️  WARNING: Response seems verbose (>2000 chars)")
        else:
            print("✅ Response length looks good")
            
        # Check if it contains overthinking patterns
        overthinking_indicators = [
            "Let me see which agent should handle",
            "Looking at the team members",
            "Wait, the function",
            "Alternatively, perhaps",
            "Therefore, the correct step is"
        ]
        
        has_overthinking = any(indicator in response.content for indicator in overthinking_indicators)
        
        if has_overthinking:
            print("❌ ISSUE: Response contains overthinking patterns")
        else:
            print("✅ No overthinking patterns detected")
            
        return response
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return None


async def test_simple_file_read():
    """Test reading a simple file."""
    
    print("\n" + "="*60)
    print("🧪 Testing file reading request: 'read .env.minimal'")
    print("="*60)
    
    agent = create_file_operations_agent(
        model_provider="ollama",
        model_name="qwen3:1.7b",
        ollama_base_url=OLLAMA_URL,
        debug=False  # Less verbose for this test
    )
    
    try:
        response = await agent.arun("read .env.minimal")
        
        print("\n📤 Agent Response:")
        print("-" * 40)
        print(response.content)
        print("-" * 40)
        
        return response
        
    except Exception as e:
        print(f"❌ Error during file read test: {e}")
        return None


async def main():
    """Run all tests."""
    
    print("🚀 Testing File Operations Agent Fix")
    print("=" * 60)
    
    # Test 1: Directory listing
    result1 = await test_file_operations_agent()
    
    # Test 2: File reading
    result2 = await test_simple_file_read()
    
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    if result1:
        print("✅ Directory listing test completed")
    else:
        print("❌ Directory listing test failed")
        
    if result2:
        print("✅ File reading test completed")
    else:
        print("❌ File reading test failed")
    
    print("\n🎯 Expected behavior:")
    print("- Agent should use list_directory tool directly")
    print("- No excessive explanation or confirmation for safe operations")
    print("- Clear, concise responses")
    print("- No confusion about which tool to use")


if __name__ == "__main__":
    asyncio.run(main())
