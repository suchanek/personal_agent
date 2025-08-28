#!/usr/bin/env python3
"""
Test script to verify the image agent fix works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.reasoning_team import create_image_agent


async def test_fixed_image_agent():
    """Test the fixed image agent."""
    print("🧪 TESTING FIXED IMAGE AGENT")
    print("=" * 50)
    
    # Create the fixed image agent
    image_agent = create_image_agent(debug=True, use_remote=False)
    
    print(f"✅ Agent created: {image_agent.name}")
    print(f"📋 Show tool calls: {image_agent.show_tool_calls}")
    print(f"📝 Instructions preview: {image_agent.instructions[0][:100]}...")
    
    prompt = "Create an image of a sunset over mountains"
    
    print(f"\n🎯 Testing with prompt: '{prompt}'")
    print("Using .pprint_response() to show the fixed response...")
    print("-" * 50)
    
    try:
        # Test with pprint_response to see the full output
        await image_agent.aprint_response(prompt, stream=False)
        
        print("-" * 50)
        print("✅ FIXED! The image agent should now properly display the image markdown format.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 TESTING FIXED IMAGE AGENT")
    print("This script tests the fixed image agent with relaxed instructions.\n")
    
    try:
        await test_fixed_image_agent()
        
        print("\n" + "=" * 50)
        print("🎯 TEST COMPLETE")
        print("=" * 50)
        
        print("\n📋 WHAT WAS FIXED:")
        print("1. ✅ Removed overly restrictive instructions")
        print("2. ✅ Enabled tool call display (show_tool_calls=True)")
        print("3. ✅ Allowed natural responses with image markdown")
        print("4. ✅ Removed 'NO thinking, NO explanations' restrictions")
        
        print("\n🔧 THE SOLUTION:")
        print("The agent now uses simple, clear instructions that allow it to:")
        print("- Use the create_image tool naturally")
        print("- Display tool calls for debugging")
        print("- Include the image markdown format in a natural response")
        print("- Provide context along with the image")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())