#!/usr/bin/env python3
"""
Bare-bones LM Studio test that matches the working example exactly.
This bypasses all our configuration and uses the minimal approach.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.agent import Agent
from agno.models.lmstudio import LMStudio
from personal_agent.core.agno_agent import AgnoPersonalAgent

async def test_bare_lmstudio():
    """Test bare LM Studio approach exactly like working example."""
    print("🧪 Testing Bare LM Studio Integration...")
    
    # Test 1: Exact working example approach
    print("\n📤 Test 1: Exact working example approach")
    try:
        # This is EXACTLY the working example
        agent = Agent(model=LMStudio(id="qwen3-4b-mlx"), markdown=True)
        
        response = await agent.arun("What is 2 + 2?")
        print("✅ Bare LM Studio works!")
        print(f"📥 Response: {response}")
        
    except Exception as e:
        print(f"❌ Bare LM Studio failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: AgnoPersonalAgent with absolute minimal config
    print("\n📤 Test 2: AgnoPersonalAgent with absolute minimal config")
    try:
        # Create the most minimal AgnoPersonalAgent possible
        agent = await AgnoPersonalAgent.create_with_init(
            model_provider="lm-studio",
            model_name="qwen3-4b-mlx",
            enable_memory=False,
            enable_mcp=False,
            alltools=False,  # No tools at all
            debug=False,     # No debug output
        )
        
        response = await agent.arun("What is 2 + 2?")
        print("✅ Minimal AgnoPersonalAgent works!")
        print(f"📥 Response: {response}")
        
    except Exception as e:
        print(f"❌ Minimal AgnoPersonalAgent failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bare_lmstudio())
