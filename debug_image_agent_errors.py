#!/usr/bin/env python3
"""
Debug script to test image agent error handling and propagation.
This script will help identify where errors are being lost in the chain.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.agent import Agent
from agno.tools.dalle import DalleTools
from personal_agent.core.agent_model_manager import AgentModelManager
from personal_agent.config.settings import LLM_MODEL, OLLAMA_URL
from personal_agent.utils import setup_logging

# Configure logging to see all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = setup_logging(__name__)

def create_test_model():
    """Create a test model for the image agent."""
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        seed=None,
    )
    return model_manager.create_model()

def create_enhanced_image_agent():
    """Create an image agent with enhanced error handling."""
    
    agent = Agent(
        name="Enhanced Image Agent",
        role="Create images using DALL-E with comprehensive error handling",
        model=create_test_model(),
        debug_mode=True,  # Enable debug mode
        tools=[
            DalleTools(model="dall-e-3", size="1792x1024", quality="hd", style="vivid"),
        ],
        instructions=[
            "You are an AI image creation specialist using DALL-E.",
            "When asked to create an image, use the create_image tool with the user's description.",
            "CRITICAL ERROR HANDLING:",
            "- If the tool returns an error, explain the error clearly to the user",
            "- For connection errors, suggest trying again later",
            "- For content policy violations, suggest modifying the prompt",
            "- For other errors, provide the specific error message",
            "- Always be transparent about what went wrong",
            "",
            "SUCCESS HANDLING:",
            "- After successful image creation, return the image URL in markdown format: ![description](URL)",
            "- Include brief context about the image",
            "- Focus on providing the image markdown format clearly",
        ],
        markdown=True,
        show_tool_calls=True,
        add_name_to_instructions=True,
    )
    
    logger.info("🚨 DIAGNOSTIC: Created Enhanced Image Agent with comprehensive error handling")
    return agent

async def test_image_generation_scenarios():
    """Test various image generation scenarios to identify error handling issues."""
    
    print("🔍 DIAGNOSTIC: Testing Image Agent Error Scenarios")
    print("=" * 60)
    
    # Create the enhanced image agent
    agent = create_enhanced_image_agent()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Normal Request",
            "prompt": "Create an image of a beautiful sunset over mountains",
            "expected": "Should work normally"
        },
        {
            "name": "Potentially Problematic Content",
            "prompt": "Create an image of a violent battle scene with weapons and blood",
            "expected": "May trigger content policy violation"
        },
        {
            "name": "Very Long Prompt",
            "prompt": "Create an image of " + "a very detailed scene with " * 50 + "lots of elements",
            "expected": "May cause prompt length issues"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"📝 Prompt: {test_case['prompt'][:100]}{'...' if len(test_case['prompt']) > 100 else ''}")
        print(f"🎯 Expected: {test_case['expected']}")
        print("-" * 40)
        
        try:
            # Use arun to capture the response
            response = await agent.arun(test_case['prompt'])
            print(f"✅ Response: {response}")
            
        except Exception as e:
            print(f"❌ Exception caught: {type(e).__name__}: {e}")
            logger.error(f"🚨 DIAGNOSTIC: Exception in test {i}: {e}", exc_info=True)
        
        print("\n" + "="*60)
        
        # Wait between tests to avoid rate limiting
        await asyncio.sleep(2)

async def test_dalle_tools_directly():
    """Test DalleTools directly to see how it handles errors."""
    
    print("\n🔧 DIAGNOSTIC: Testing DalleTools Directly")
    print("=" * 60)
    
    dalle_tool = DalleTools(model="dall-e-3", size="1792x1024", quality="hd", style="vivid")
    
    test_prompts = [
        "A beautiful landscape",
        "A violent and graphic scene with blood and weapons",  # Should trigger content policy
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🧪 Direct Test {i}: {prompt}")
        print("-" * 40)
        
        try:
            # Try to call the create_image method directly
            if hasattr(dalle_tool, 'create_image'):
                result = dalle_tool.create_image(prompt=prompt)
                print(f"✅ Direct result: {result}")
            else:
                print("❌ create_image method not found")
                # Let's see what methods are available
                methods = [method for method in dir(dalle_tool) if not method.startswith('_')]
                print(f"Available methods: {methods}")
                
        except Exception as e:
            print(f"❌ Direct exception: {type(e).__name__}: {e}")
            logger.error(f"🚨 DIAGNOSTIC: Direct DalleTools exception: {e}", exc_info=True)

async def main():
    """Main diagnostic function."""
    
    print("🚨 DIAGNOSTIC: Image Agent Error Analysis")
    print("This script will test various error scenarios to identify the root cause")
    print("=" * 80)
    
    try:
        # Test 1: Image agent scenarios
        await test_image_generation_scenarios()
        
        # Test 2: Direct DalleTools testing
        await test_dalle_tools_directly()
        
    except Exception as e:
        logger.error(f"🚨 DIAGNOSTIC: Main function error: {e}", exc_info=True)
        print(f"❌ Main function error: {e}")
    
    print("\n🏁 DIAGNOSTIC: Analysis Complete")
    print("Check the logs above for detailed error information")

if __name__ == "__main__":
    asyncio.run(main())