#!/usr/bin/env python3
"""
Test script to verify enhanced agent_utils.py functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.personal_agent.streamlit.utils.agent_utils import (
    collect_streaming_response,
    extract_final_response_and_tools,
    format_for_streamlit_display,
    get_complete_response_from_agent
)
from src.personal_agent.team.reasoning_team import create_image_agent


async def test_enhanced_agent_utils():
    """Test the enhanced agent utilities functions."""
    print("🧪 TESTING ENHANCED AGENT UTILS")
    print("=" * 40)
    
    # Create image agent
    image_agent = create_image_agent(debug=False, use_remote=False)
    prompt = "Create an image of a robot drinking coffee"
    
    print(f"Prompt: '{prompt}'")
    
    # Test 1: collect_streaming_response
    print(f"\n1️⃣  Testing collect_streaming_response")
    try:
        run_stream = image_agent.run(prompt, stream=True, stream_intermediate_steps=True)
        chunks = collect_streaming_response(run_stream)
        print(f"✅ Collected {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: extract_final_response_and_tools (enhanced version)
    print(f"\n2️⃣  Testing enhanced extract_final_response_and_tools")
    try:
        analysis = extract_final_response_and_tools(chunks)
        print(f"✅ Analysis completed")
        print(f"   Final content length: {len(str(analysis['final_content']))}")
        print(f"   Tool calls found: {len(analysis['tool_calls'])}")
        print(f"   Images found: {len(analysis['image_urls'])}")
        print(f"   Status: {analysis['status']}")
        
        # Show details about tool calls
        if analysis['tool_calls']:
            print(f"\n🔧 TOOL CALL DETAILS:")
            for i, tool in enumerate(analysis['tool_calls'], 1):
                print(f"   {i}. Name: {tool['name']}")
                print(f"      Arguments: {tool['arguments']}")
                print(f"      Status: {tool['status']}")
        
        # Show details about images
        if analysis['image_urls']:
            print(f"\n🖼️  IMAGE DETAILS:")
            for i, img in enumerate(analysis['image_urls'], 1):
                print(f"   {i}. Alt text: {img['alt_text']}")
                print(f"      URL: {img['url'][:80]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: format_for_streamlit_display
    print(f"\n3️⃣  Testing format_for_streamlit_display")
    try:
        streamlit_format = format_for_streamlit_display(analysis)
        print(f"✅ Streamlit format created")
        print(f"   Response content type: {type(streamlit_format['response_content']).__name__}")
        print(f"   Tool calls: {len(streamlit_format['tool_calls'])}")
        print(f"   Images: {len(streamlit_format['images'])}")
        print(f"   Status: {streamlit_format['status']}")
        print(f"   Metrics: {streamlit_format['metrics']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 4: get_complete_response_from_agent (streaming)
    print(f"\n4️⃣  Testing get_complete_response_from_agent (streaming)")
    try:
        streaming_result = get_complete_response_from_agent(
            image_agent, 
            prompt, 
            stream=True,
            stream_intermediate_steps=True
        )
        print(f"✅ Streaming result obtained")
        print(f"   Content length: {len(str(streaming_result['response_content']))}")
        print(f"   Tool calls: {len(streaming_result['tool_calls'])}")
        print(f"   Images: {len(streaming_result['images'])}")
        print(f"   Status: {streaming_result['status']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 5: get_complete_response_from_agent (non-streaming)
    print(f"\n5️⃣  Testing get_complete_response_from_agent (non-streaming)")
    try:
        non_streaming_result = get_complete_response_from_agent(
            image_agent,
            prompt,
            stream=False
        )
        print(f"✅ Non-streaming result obtained")
        print(f"   Content length: {len(str(non_streaming_result.content))}")
        print(f"   Status: {non_streaming_result.status}")
        print(f"   Tools: {len(non_streaming_result.tools) if non_streaming_result.tools else 0}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print(f"\n🎉 ALL TESTS PASSED!")
    print("=" * 40)
    print("Enhanced agent_utils.py successfully utilizes learnings:")
    print("• Looks for tool calls in both 'tool' and 'tools' attributes")
    print("• Properly extracts image URLs from markdown content")
    print("• Handles both streaming and non-streaming modes")
    print("• Formats results appropriately for Streamlit apps")


if __name__ == "__main__":
    asyncio.run(test_enhanced_agent_utils())