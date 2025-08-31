#!/usr/bin/env python3
"""
Test script to verify that the team now properly displays image URLs from the Image Agent.
This script tests the fix for the streaming response issue.
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.personal_agent.team.reasoning_team import create_team


async def test_team_image_response():
    """Test that the team now properly captures and displays image URLs."""
    print("🧪 Testing Team Image Response Fix")
    print("=" * 50)

    try:
        # Create the team
        print("📦 Creating team...")
        team = await create_team(use_remote=False)
        print("✅ Team created successfully!")

        # Test image creation request
        print("\n🎨 Testing image creation request...")
        print("Request: 'Create an image of a robot riding a monkey'")
        print("\n🤖 Team Response:")
        print("-" * 30)

        # This should now capture the final chunk with the image URL
        response = await team.arun(
            "Create an image of a robot riding a monkey", stream=False
        )

        print(f"\n📊 Response Analysis:")
        print(
            f"Response length: {len(response.content) if response.content else 0} characters"
        )

        # Check if the response contains image markdown
        if (
            response.content
            and "![" in response.content
            and "](https://" in response.content
        ):
            print("✅ SUCCESS: Image URL found in response!")

            # Extract and display the image URL
            import re

            image_pattern = r"!\[([^\]]*)\]\((https://[^)]+)\)"
            matches = re.findall(image_pattern, response.content)

            if matches:
                for alt_text, url in matches:
                    print(f"🖼️  Alt text: '{alt_text}'")
                    print(f"🔗 URL: {url}")

            print(f"\n📝 Full Response:")
            print(response.content)

        else:
            print("❌ FAILED: No image URL found in response!")
            print(f"Response content: {response.content}")

        # Cleanup
        print("\n🧹 Cleaning up...")
        from src.personal_agent.team.reasoning_team import cleanup_team

        await cleanup_team(team)
        print("✅ Cleanup completed!")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Team Image Response Test")
    asyncio.run(test_team_image_response())
