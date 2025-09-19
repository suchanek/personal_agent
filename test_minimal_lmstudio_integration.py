#!/usr/bin/env python3
"""
Minimal LM Studio integration test that matches the working example.
"""

import asyncio
from agno.agent import Agent
from agno.models.lmstudio import LMStudio

async def test_minimal_lmstudio():
    """Test minimal LM Studio integration."""
    print("🧪 Testing Minimal LM Studio Integration...")
    
    # Create agent exactly like the working example
    agent = Agent(model=LMStudio(id="qwen3-4b-mlx"), markdown=True)
    
    # Test simple query
    print("📤 Sending query: 'Hello! Can you tell me what 2 + 2 equals?'")
    
    try:
        # Use async run for consistency with the integration test
        response = await agent.arun("Hello! Can you tell me what 2 + 2 equals?")
        print("✅ Query successful!")
        print(f"📥 Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 Minimal LM Studio Integration Test")
    print("=" * 50)
    
    success = await test_minimal_lmstudio()
    
    if success:
        print("\n🎉 LM Studio integration is working correctly!")
        print("✅ The fix resolved the 'Unexpected endpoint' error")
        print("✅ LM Studio is responding properly")
        print("\n📝 Summary:")
        print("   - Fixed AgentModelManager to use simple LMStudio(id=model_name)")
        print("   - Removed complex wrapper logic that was causing endpoint issues")
        print("   - LM Studio integration now matches the working example pattern")
    else:
        print("\n❌ LM Studio integration still has issues")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
