#!/usr/bin/env python3
"""
Test script to reproduce the exact image agent CLI issue.
This tests the image agent as used in the reasoning_team.py context.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.dalle import DalleTools

from personal_agent.config.settings import LLM_MODEL, OLLAMA_URL


def create_reasoning_team_image_agent():
    """Create the image agent exactly as defined in reasoning_team.py."""
    return Agent(
        name="Image Agent",
        role="Create images using DALL-E based on text descriptions",
        model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
        debug_mode=True,
        tools=[
            DalleTools(model="dall-e-3", size="1024x1024", quality="hd", style="vivid"),
        ],
        instructions=[
            "When the user asks you to create an image, use the DALL-E tool to create an image.",
            "The DALL-E tool will return an image URL.",
            "Return the image URL in your response in the following format: `![image description](image URL)`",
        ],
        markdown=True,
        show_tool_calls=True,
        add_name_to_instructions=True,
    )


async def test_team_image_agent():
    """Test the image agent exactly as used in the team."""
    print("🧪 TESTING TEAM IMAGE AGENT (EXACT REPRODUCTION)")
    print("=" * 60)

    # Create the agent exactly as in reasoning_team.py
    image_agent = create_reasoning_team_image_agent()

    prompt = "Create an image of a futuristic robot"

    print(f"\nTesting prompt: '{prompt}'")
    print("🤖 Using Ollama model with DALL-E tools (as in reasoning_team.py)")

    try:
        # Test 1: Using arun() - this is what the team uses
        print("\n1️⃣  Testing agent.arun() (team method):")
        response = await image_agent.arun(prompt)

        print(f"Response type: {type(response)}")
        print(f"Response status: {getattr(response, 'status', 'unknown')}")

        # Check if response has content
        if hasattr(response, "content") and response.content:
            print("✅ Response has content:")
            print(
                response.content[:500] + "..."
                if len(response.content) > 500
                else response.content
            )
        else:
            print("❌ No content in response")

        # Check for tool calls
        if hasattr(response, "tools") and response.tools:
            print(f"✅ Tool calls found: {len(response.tools)}")
            for i, tool in enumerate(response.tools):
                print(
                    f"   {i+1}. {tool.tool_name}: {getattr(tool, 'result', 'no result')[:100]}..."
                )
        else:
            print("❌ No tool calls in response")

        # Check formatted tool calls
        if hasattr(response, "formatted_tool_calls") and response.formatted_tool_calls:
            print(f"✅ Formatted tool calls: {len(response.formatted_tool_calls)}")
            for i, tool_call in enumerate(response.formatted_tool_calls):
                print(f"   {i+1}. {tool_call}")

        # Test 2: Simulate CLI response handling
        print("\n2️⃣  Testing CLI-style response handling:")

        # This is how the CLI might be handling the response
        if hasattr(response, "content"):
            content = response.content.strip()
            if content:
                print(f"   CLI would display: '{content[:200]}...'")
            else:
                print("   CLI would display: (empty response)")
        else:
            print("   CLI would display: (no content attribute)")

        # Test 3: Check if response has the expected image URL format
        print("\n3️⃣  Testing for image URL format:")
        if hasattr(response, "content") and response.content:
            content = response.content
            if "![" in content and "](" in content and ")" in content:
                print("   ✅ Response contains image markdown format")
                # Extract the image URL
                import re

                image_match = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", content)
                if image_match:
                    alt_text, url = image_match.groups()
                    print(f"   📝 Alt text: '{alt_text}'")
                    print(f"   🔗 URL: '{url}'")
                else:
                    print("   ❌ Could not extract image URL")
            else:
                print("   ❌ Response does not contain image markdown format")
                print(f"   Content preview: '{content[:200]}...'")

    except Exception as e:
        print(f"❌ Error testing team image agent: {e}")
        import traceback

        traceback.print_exc()


async def test_working_example_comparison():
    """Compare with the working example from team_with_intermediate_steps.py."""
    print("\n\n📚 TESTING WORKING EXAMPLE COMPARISON")
    print("=" * 60)

    # Create agent similar to the working example
    working_agent = Agent(
        model=Ollama(id=LLM_MODEL, host=OLLAMA_URL),
        tools=[DalleTools()],
        description="You are an AI agent that can create images using DALL-E.",
        instructions=[
            "When the user asks you to create an image, use the DALL-E tool to create an image.",
            "The DALL-E tool will return an image URL.",
            "Return the image URL in your response in the following format: `![image description](image URL)`",
        ],
        markdown=True,
    )

    prompt = "Create an image of a yellow siamese cat"

    print(f"\nTesting prompt: '{prompt}'")
    print("🤖 Using working example pattern")

    try:
        # Test with streaming (as in the working example)
        print("\n1️⃣  Testing with streaming (working example method):")
        run_stream = working_agent.run(
            prompt, stream=True, stream_intermediate_steps=True
        )

        final_content = ""
        chunk_count = 0
        for chunk in run_stream:
            chunk_count += 1
            if hasattr(chunk, "content") and chunk.content:
                final_content += chunk.content

        print(f"   Collected content length: {len(final_content)}")
        if final_content:
            print(f"   Content preview: '{final_content[:200]}...'")
        else:
            print("   ❌ No content collected")

        # Test with arun()
        print("\n2️⃣  Testing with arun():")
        response = await working_agent.arun(prompt)

        if hasattr(response, "content") and response.content:
            print(f"   ✅ Response content: '{response.content[:200]}...'")
        else:
            print("   ❌ No content in response")

    except Exception as e:
        print(f"❌ Error testing working example: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 IMAGE AGENT CLI ISSUE REPRODUCTION")
    print("This script reproduces the exact issue you're experiencing")
    print("with the image agent in CLI mode.\n")

    try:
        # Test the team image agent (reproducing the issue)
        await test_team_image_agent()

        # Compare with working example
        await test_working_example_comparison()

        print("\n" + "=" * 60)
        print("🎯 REPRODUCTION COMPLETE")
        print("=" * 60)

        print("\n📋 ANALYSIS:")
        print(
            "• The team image agent uses the same DALL-E tools as the working examples"
        )
        print(
            "• If the working example succeeds but the team agent fails, the issue is in:"
        )
        print("  - Team coordination logic")
        print("  - Response handling in team context")
        print("  - Agent initialization differences")

        print("\n🔧 NEXT STEPS:")
        print(
            "1. Check if the issue occurs when calling the agent directly (not through team)"
        )
        print("2. Verify team member delegation is working correctly")
        print("3. Check if the agent is being initialized properly in team context")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
