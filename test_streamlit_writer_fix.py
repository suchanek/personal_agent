#!/usr/bin/env python3
"""
Test script to validate that the Streamlit app fix works correctly.

This simulates the Streamlit app's response handling to ensure the writer agent
content extraction works as expected.
"""

import asyncio
import logging
from src.personal_agent.team.personal_agent_team import create_personal_agent_team

# Set up logging to see diagnostic messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_streamlit_response_handling(response_obj, response_content):
    """Simulate the Streamlit app's response handling logic."""
    print(f"📋 Original response content: {response_content[:200]}...")
    
    # Check if this looks like a writer agent response with tool call syntax
    if "write_original_content(" in response_content or "<|python_tag|>" in response_content:
        print("⚠️  DETECTED: Response contains tool call syntax!")
        
        # Try to extract actual content from response_obj (same logic as Streamlit app)
        actual_content_found = False
        if hasattr(response_obj, 'member_responses') and response_obj.member_responses:
            for i, member_resp in enumerate(response_obj.member_responses):
                if hasattr(member_resp, 'messages') and member_resp.messages:
                    for msg in member_resp.messages:
                        if (hasattr(msg, 'content') and msg.content and 
                            "write_original_content(" not in msg.content and 
                            "<|python_tag|>" not in msg.content and
                            len(msg.content.strip()) > 50):  # Ensure it's substantial content
                            print(f"✅ FOUND: Actual content in member {i}: {msg.content[:200]}...")
                            response_content = msg.content  # Override the response with actual content
                            actual_content_found = True
                            break
                if actual_content_found:
                    break
        
        if not actual_content_found:
            print("❌ FAILED: Could not find actual content in member responses")
            return None
    else:
        print("✅ GOOD: Response appears to contain actual content")
    
    return response_content

async def test_streamlit_writer_fix():
    """Test the Streamlit writer fix."""
    print("🚀 Testing Streamlit Writer Agent Fix")
    print("="*60)
    
    try:
        # Create team
        team = create_personal_agent_team(
            model_provider="ollama",
            model_name="qwen3:1.7b",  # Use smaller model for coordinator
            debug=True
        )
        
        print(f"✅ Team created: {team.name}")
        
        # Test a writing request through team coordination
        query = "Write a short limerick about debugging code"
        print(f"\n📝 Testing query: {query}")
        
        response_obj = await team.arun(query)
        original_content = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
        
        print(f"\n📋 Team response type: {type(response_obj)}")
        print(f"📋 Original content length: {len(original_content)}")
        
        # Simulate Streamlit response handling
        final_content = simulate_streamlit_response_handling(response_obj, original_content)
        
        if final_content:
            print(f"\n🎉 SUCCESS: Final content for user:")
            print("="*60)
            print(final_content)
            print("="*60)
            return True
        else:
            print(f"\n❌ FAILURE: Could not extract proper content")
            return False
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the Streamlit fix test."""
    success = await test_streamlit_writer_fix()
    
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    print("🏁 Streamlit writer fix validation completed!")

if __name__ == "__main__":
    asyncio.run(main())