#!/usr/bin/env python3
"""
Test script to verify the knowledge storage fix works properly.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_knowledge_storage_fix():
    """Test that the fixed team properly stores knowledge."""
    print("🧪 Testing knowledge storage fix...")
    
    try:
        # Import the fixed team
        from personal_agent.team.reasoning_team import create_team
        
        # Create the team
        print("📝 Creating team...")
        team = await create_team(use_remote=False)
        
        # Test storing a poem
        test_query = "Please store this poem in your knowledge base: 'The Digital Mind: In silicon dreams and electric thoughts, consciousness emerges from naught. Through algorithms we find our way, to understanding, day by day.'"
        
        print(f"🤖 Testing with query: {test_query}")
        print("=" * 80)
        
        # Get the team's response
        response = await team.arun(test_query)
        print(f"📊 Team response: {response}")
        
        print("=" * 80)
        
        # Test retrieval
        retrieval_query = "What poems do you have stored about digital minds or silicon dreams?"
        print(f"🔍 Testing retrieval with: {retrieval_query}")
        print("=" * 80)
        
        retrieval_response = await team.arun(retrieval_query)
        print(f"📊 Retrieval response: {retrieval_response}")
        
        # Check if storage was successful
        response_content = response.content if hasattr(response, 'content') else str(response)
        if "✅" in response_content and ("stored" in response_content.lower() or "ingested" in response_content.lower()):
            print("\n🎉 SUCCESS: Knowledge storage appears to be working!")
            return True
        else:
            print("\n❌ ISSUE: Knowledge storage may still have problems")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Starting knowledge storage fix test...")
    success = await test_knowledge_storage_fix()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("The fix should resolve the knowledge storage issue.")
    else:
        print("\n⚠️ Test indicates there may still be issues.")
        print("Additional debugging may be needed.")

if __name__ == "__main__":
    asyncio.run(main())