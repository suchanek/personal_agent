#!/usr/bin/env python3
"""
Test the Image Agent directly to confirm it works properly.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.reasoning_team import create_image_agent

async def test_direct_image_agent():
    """Test the Image Agent directly."""
    print("🧪 Testing Image Agent directly...")
    print("=" * 50)
    
    try:
        # Create just the image agent
        print("🔧 Creating Image Agent...")
        image_agent = create_image_agent(use_remote=False)
        print("✅ Image Agent created successfully!")
        
        # Test image creation directly
        print("\n🎨 Testing direct image creation...")
        query = "Create an image of a cute robot"
        print(f"Query: {query}")
        print("\n" + "="*50)
        print("IMAGE AGENT RESPONSE:")
        print("="*50)
        
        # Call the image agent directly
        response = await image_agent.arun(query, stream=False)
        
        # Print the response using the agent's built-in method
        image_agent.print_response(response)
        
        print("\n" + "="*50)
        print("✅ Direct Image Agent test completed!")
        print("Check above for clickable image URLs in format: ![description](URL)")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting direct Image Agent test...")
    asyncio.run(test_direct_image_agent())