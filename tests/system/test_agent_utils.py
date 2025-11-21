#!/usr/bin/env python3
"""
Test script for agent_utils.py module

This test is skipped by default because it's slow (requires image generation).
Run manually with: python tests/system/test_agent_utils.py
Or with pytest: pytest tests/system/test_agent_utils.py -v
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.personal_agent.streamlit.utils.agent_utils import (
    collect_streaming_response,
    extract_final_response_and_tools,
    format_for_streamlit_display,
    get_complete_response_from_agent
)
from src.personal_agent.team.reasoning_team import create_image_agent


@pytest.mark.skip(reason="Slow test - requires image generation. Run manually if needed.")
async def test_agent_utils():
    """Test the agent utilities functions.
    
    This test is skipped by default because it's slow (requires DALL-E image generation).
    To run manually: python tests/system/test_agent_utils.py
    """
    print("🧪 TESTING AGENT UTILS MODULE")
    print("=" * 40)
    
    # Create image agent
    image_agent = create_image_agent(debug=False)
    prompt = "Create an image of a cat wearing sunglasses"
    
    print(f"Prompt: '{prompt}'")
    
    # Test 1: collect_streaming_response
    print(f"\n1️⃣  Testing collect_streaming_response")
    try:
        run_stream = image_agent.run(prompt, stream=True, stream_intermediate_steps=True)
        chunks = list(collect_streaming_response(run_stream))
        print(f"✅ Collected {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: extract_final_response_and_tools
    print(f"\n2️⃣  Testing extract_final_response_and_tools")
    try:
        analysis = extract_final_response_and_tools(chunks)
        print(f"✅ Analysis completed")
        print(f"   Final content length: {len(str(analysis['final_content']))}")
        print(f"   Tool calls found: {len(analysis['tool_calls'])}")
        print(f"   Images found: {len(analysis['image_urls'])}")
        print(f"   Status: {analysis['status']}")
    except Exception as e:
        print(f"❌ Error: {e}")
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
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 4: get_complete_response_from_agent (streaming)
    print(f"\n4️⃣  Testing get_complete_response_from_agent (streaming)")
    try:
        # When stream=True, returns Dict[str, Any] with Streamlit-formatted data
        streaming_result = await asyncio.to_thread(
            get_complete_response_from_agent,
            image_agent,
            prompt,
            stream=True,
            stream_intermediate_steps=True
        )
        print(f"✅ Streaming result obtained")
        # Type guard: streaming_result is Dict[str, Any] when stream=True
        if isinstance(streaming_result, dict):
            print(f"   Content length: {len(str(streaming_result['response_content']))}")
            print(f"   Tool calls: {len(streaming_result['tool_calls'])}")
            print(f"   Images: {len(streaming_result['images'])}")
        else:
            print(f"   ⚠️ Unexpected result type: {type(streaming_result)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 5: get_complete_response_from_agent (non-streaming)
    print(f"\n5️⃣  Testing get_complete_response_from_agent (non-streaming)")
    try:
        # When stream=False, returns RunResponse object
        non_streaming_result = await asyncio.to_thread(
            get_complete_response_from_agent,
            image_agent,
            prompt,
            stream=False
        )
        print(f"✅ Non-streaming result obtained")
        # Type guard: non_streaming_result is RunResponse when stream=False
        if not isinstance(non_streaming_result, dict):
            print(f"   Content length: {len(str(non_streaming_result.content))}")
            print(f"   Status: {non_streaming_result.status}")
            print(f"   Tools: {len(non_streaming_result.tools) if non_streaming_result.tools else 0}")
        else:
            print(f"   ⚠️ Unexpected result type: {type(non_streaming_result)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print(f"\n🎉 ALL TESTS PASSED!")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(test_agent_utils())