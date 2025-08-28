#!/usr/bin/env python3
"""
Diagnostic script to debug image agent response issues using .pprint_response()
This script creates the image agent exactly as in reasoning_team.py and tests it directly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.agent import Agent
from agno.tools.dalle import DalleTools

# Import the exact function from reasoning_team.py
from personal_agent.team.reasoning_team import create_image_agent, create_model
from personal_agent.config.settings import LLM_MODEL, OLLAMA_URL


async def test_image_agent_with_pprint():
    """Test the image agent using .pprint_response() to see the full response."""
    print("🔍 DIAGNOSTIC: Testing Image Agent with .pprint_response()")
    print("=" * 70)
    
    # Create the image agent exactly as in reasoning_team.py
    print("1️⃣  Creating image agent using reasoning_team.create_image_agent()...")
    image_agent = create_image_agent(debug=True, use_remote=False)
    
    print(f"   ✅ Agent created: {image_agent.name}")
    print(f"   📝 Agent role: {image_agent.role}")
    print(f"   🛠️  Tools: {[tool.__class__.__name__ for tool in image_agent.tools]}")
    print(f"   🧠 Model: {type(image_agent.model).__name__}")
    print(f"   🔧 Debug mode: {image_agent.debug_mode}")
    print(f"   📋 Show tool calls: {image_agent.show_tool_calls}")
    
    # Test prompt
    prompt = "Create an image of a futuristic robot in a cyberpunk city"
    
    print(f"\n2️⃣  Testing with prompt: '{prompt}'")
    print("   Using .pprint_response() to show full response details...")
    print("-" * 50)
    
    try:
        # Use pprint_response to see exactly what happens
        await image_agent.aprint_response(prompt, stream=False)
        
    except Exception as e:
        print(f"❌ Error during pprint_response: {e}")
        import traceback
        traceback.print_exc()
    
    print("-" * 50)
    print("3️⃣  Now testing with .arun() to compare response object...")
    
    try:
        response = await image_agent.arun(prompt)
        
        print(f"   Response type: {type(response)}")
        print(f"   Response status: {getattr(response, 'status', 'unknown')}")
        
        # Detailed response analysis
        if hasattr(response, 'content'):
            content = response.content
            print(f"   Content length: {len(content) if content else 0}")
            if content:
                print(f"   Content preview: '{content[:200]}...' " if len(content) > 200 else f"   Content: '{content}'")
                
                # Check for image markdown format
                if "![" in content and "](" in content:
                    print("   ✅ Contains image markdown format")
                    import re
                    image_match = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", content)
                    if image_match:
                        alt_text, url = image_match.groups()
                        print(f"   🖼️  Alt text: '{alt_text}'")
                        print(f"   🔗 URL: '{url}'")
                else:
                    print("   ❌ No image markdown format found")
            else:
                print("   ❌ Content is empty or None")
        else:
            print("   ❌ Response has no content attribute")
            
        # Check tool calls
        if hasattr(response, 'tools') and response.tools:
            print(f"   🛠️  Tool calls: {len(response.tools)}")
            for i, tool in enumerate(response.tools):
                print(f"      {i+1}. {tool.tool_name}")
                if hasattr(tool, 'result'):
                    result_preview = str(tool.result)[:100] + "..." if len(str(tool.result)) > 100 else str(tool.result)
                    print(f"         Result: {result_preview}")
        else:
            print("   ❌ No tool calls found")
            
        # Check messages
        if hasattr(response, 'messages') and response.messages:
            print(f"   💬 Messages: {len(response.messages)}")
            for i, msg in enumerate(response.messages):
                role = getattr(msg, 'role', 'unknown')
                content_preview = str(getattr(msg, 'content', ''))[:100]
                print(f"      {i+1}. {role}: {content_preview}...")
        else:
            print("   ❌ No messages found")
            
    except Exception as e:
        print(f"❌ Error during arun: {e}")
        import traceback
        traceback.print_exc()


async def test_simplified_image_agent():
    """Test a simplified version of the image agent to isolate issues."""
    print("\n\n🧪 DIAGNOSTIC: Testing Simplified Image Agent")
    print("=" * 70)
    
    # Create a simplified agent with minimal configuration
    simplified_agent = Agent(
        name="Simple Image Agent",
        role="Create images using DALL-E",
        model=create_model(provider="ollama", use_remote=False),
        debug_mode=True,
        tools=[DalleTools(model="dall-e-3", size="1024x1024", quality="hd")],
        instructions=[
            "You are an image creation agent.",
            "When asked to create an image, use the create_image tool.",
            "Return the image URL in markdown format: ![description](URL)",
        ],
        markdown=True,
        show_tool_calls=True,  # Enable tool call display for debugging
    )
    
    prompt = "Create an image of a sunset over mountains"
    
    print(f"Testing simplified agent with prompt: '{prompt}'")
    print("Using .pprint_response()...")
    print("-" * 50)
    
    try:
        await simplified_agent.aprint_response(prompt, stream=False)
        
    except Exception as e:
        print(f"❌ Error with simplified agent: {e}")
        import traceback
        traceback.print_exc()


async def test_direct_dalle_tool():
    """Test the DALL-E tool directly to isolate tool-specific issues."""
    print("\n\n🔧 DIAGNOSTIC: Testing DALL-E Tool Directly")
    print("=" * 70)
    
    try:
        dalle_tool = DalleTools(model="dall-e-3", size="1024x1024", quality="hd")
        
        print("Testing DALL-E tool directly...")
        result = dalle_tool.create_image(prompt="A futuristic robot in a cyberpunk city")
        
        print(f"Direct tool result type: {type(result)}")
        print(f"Direct tool result: {result}")
        
    except Exception as e:
        print(f"❌ Error testing DALL-E tool directly: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main diagnostic function."""
    print("🚀 IMAGE AGENT RESPONSE DIAGNOSTIC SCRIPT")
    print("This script will help identify the root cause of image agent response issues")
    print("by using .pprint_response() and detailed response analysis.\n")
    
    try:
        # Test 1: Original image agent with pprint_response
        await test_image_agent_with_pprint()
        
        # Test 2: Simplified image agent
        await test_simplified_image_agent()
        
        # Test 3: Direct DALL-E tool test
        await test_direct_dalle_tool()
        
        print("\n" + "=" * 70)
        print("🎯 DIAGNOSTIC COMPLETE")
        print("=" * 70)
        
        print("\n📋 ANALYSIS SUMMARY:")
        print("• Check the .pprint_response() output above for the complete response flow")
        print("• Compare the original agent vs simplified agent behavior")
        print("• Verify if the DALL-E tool is working correctly when called directly")
        print("• Look for differences in tool call execution and response formatting")
        
        print("\n🔍 KEY THINGS TO LOOK FOR:")
        print("1. Does the DALL-E tool get called successfully?")
        print("2. Is the tool result properly formatted?")
        print("3. Are the agent instructions causing response filtering?")
        print("4. Is the model properly processing the tool results?")
        print("5. Are there any errors in the response chain?")
        
    except Exception as e:
        print(f"\n❌ Diagnostic failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())