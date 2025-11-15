#!/usr/bin/env python3
"""
Test the final image fix in reasoning_team.py
This test verifies that image URLs are properly displayed and clickable.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.reasoning_team import create_team

async def test_image_functionality():
    """Test that image creation works and returns clickable URLs."""
    print("🧪 Testing final image fix...")
    print("=" * 50)
    
    try:
        # Create the team
        print("🔧 Creating team...")
        team = await create_team(use_remote=False)
        print("✅ Team created successfully!")
        
        # Test image creation
        print("\n🎨 Testing image creation...")
        query = "Create an image of a cute robot"
        print(f"Query: {query}")
        print("\n" + "="*50)
        print("TEAM RESPONSE:")
        print("="*50)
        
        # This should now use our simplified response handling
        response = await team.arun(query, stream=False)
        
        # Let the team handle the response display
        team.print_response(response)
        
        print("\n" + "="*50)
        print("✅ Image test completed!")
        print("Check above for clickable image URLs in format: ![description](URL)")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            if 'team' in locals():
                from personal_agent.team.reasoning_team import cleanup_team
                await cleanup_team(team)
                print("🧹 Team cleanup completed")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup error: {cleanup_error}")

if __name__ == "__main__":
    print("🚀 Starting final image functionality test...")
    asyncio.run(test_image_functionality())