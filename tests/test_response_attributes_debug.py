#!/usr/bin/env python3
"""
Test script to examine all response attributes from AgnoPersonalAgent
and understand how to properly extract tool call information.
"""

import asyncio
import json
import sys
from pathlib import Path
from pprint import pprint

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_response_attributes():
    """Test and display all response attributes from AgnoPersonalAgent."""
    print("🔍 Testing AgnoPersonalAgent Response Attributes")
    print("=" * 60)
    
    # Create agent
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=True,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    # Initialize agent
    print("🚀 Initializing agent...")
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return
    
    print("✅ Agent initialized successfully")
    print()
    
    # Test query that should trigger a tool call
    test_query = "search for the latest news about artificial intelligence"
    print(f"📝 Test Query: {test_query}")
    print()
    
    # Run the query
    print("🔄 Running query...")
    response_content = await agent.run(test_query)
    
    print("✅ Query completed")
    print()
    
    # Get the last response object
    if hasattr(agent, '_last_response') and agent._last_response:
        response = agent._last_response
        print("🔍 RESPONSE OBJECT ANALYSIS")
        print("=" * 40)
        
        # Display all attributes
        print("📋 All Response Attributes:")
        all_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
        for attr in sorted(all_attrs):
            print(f"  - {attr}")
        print()
        
        # Examine key attributes in detail
        print("🔍 DETAILED ATTRIBUTE EXAMINATION")
        print("=" * 40)
        
        # Basic info
        print("📊 Basic Information:")
        print(f"  - Type: {type(response)}")
        print(f"  - Content length: {len(response.content) if hasattr(response, 'content') else 'N/A'}")
        print(f"  - Model: {getattr(response, 'model', 'N/A')}")
        print(f"  - Run ID: {getattr(response, 'run_id', 'N/A')}")
        print()
        
        # Messages
        if hasattr(response, 'messages') and response.messages:
            print(f"💬 Messages ({len(response.messages)}):")
            for i, msg in enumerate(response.messages):
                print(f"  Message {i+1}:")
                print(f"    - Type: {type(msg)}")
                print(f"    - Role: {getattr(msg, 'role', 'N/A')}")
                if hasattr(msg, 'content'):
                    content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
                    print(f"    - Content: {content_preview}")
                
                # Check for tool calls in messages
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"    - Tool calls: {len(msg.tool_calls)}")
                    for j, tool_call in enumerate(msg.tool_calls):
                        print(f"      Tool Call {j+1}:")
                        print(f"        - Type: {type(tool_call)}")
                        print(f"        - ID: {getattr(tool_call, 'id', 'N/A')}")
                        if hasattr(tool_call, 'function'):
                            print(f"        - Function name: {getattr(tool_call.function, 'name', 'N/A')}")
                            print(f"        - Function args: {getattr(tool_call.function, 'arguments', 'N/A')}")
                        elif hasattr(tool_call, 'name'):
                            print(f"        - Tool name: {tool_call.name}")
                            print(f"        - Tool input: {getattr(tool_call, 'input', 'N/A')}")
                        
                        # Show all tool call attributes
                        tool_attrs = [attr for attr in dir(tool_call) if not attr.startswith('_')]
                        print(f"        - All attributes: {tool_attrs}")
                print()
        
        # Formatted tool calls (agno-specific)
        if hasattr(response, 'formatted_tool_calls') and response.formatted_tool_calls:
            print(f"🛠️ Formatted Tool Calls ({len(response.formatted_tool_calls)}):")
            for i, tool_call in enumerate(response.formatted_tool_calls):
                print(f"  Formatted Tool Call {i+1}:")
                print(f"    - Type: {type(tool_call)}")
                print(f"    - ID: {getattr(tool_call, 'id', 'N/A')}")
                print(f"    - Call type: {getattr(tool_call, 'type', 'N/A')}")
                
                if hasattr(tool_call, 'function'):
                    print(f"    - Function name: {getattr(tool_call.function, 'name', 'N/A')}")
                    print(f"    - Function args: {getattr(tool_call.function, 'arguments', 'N/A')}")
                    print(f"    - Function args type: {type(getattr(tool_call.function, 'arguments', None))}")
                    
                    # Try to parse arguments if they're a string
                    args = getattr(tool_call.function, 'arguments', None)
                    if isinstance(args, str):
                        try:
                            parsed_args = json.loads(args)
                            print(f"    - Parsed args: {parsed_args}")
                            print(f"    - Parsed args type: {type(parsed_args)}")
                        except json.JSONDecodeError:
                            print(f"    - Args parsing failed: {args}")
                
                # Show all formatted tool call attributes
                formatted_attrs = [attr for attr in dir(tool_call) if not attr.startswith('_')]
                print(f"    - All attributes: {formatted_attrs}")
                print()
        
        # Tools
        if hasattr(response, 'tools') and response.tools:
            print(f"🔧 Tools ({len(response.tools)}):")
            for i, tool in enumerate(response.tools):
                print(f"  Tool {i+1}: {type(tool)} - {tool}")
            print()
        
        # Metrics
        if hasattr(response, 'metrics') and response.metrics:
            print("📊 Metrics:")
            print(f"  - Type: {type(response.metrics)}")
            print(f"  - Content: {response.metrics}")
            print()
        
        # Extra data
        if hasattr(response, 'extra_data') and response.extra_data:
            print("📦 Extra Data:")
            print(f"  - Type: {type(response.extra_data)}")
            print(f"  - Content: {response.extra_data}")
            print()
        
        # Thinking/reasoning
        if hasattr(response, 'thinking') and response.thinking:
            thinking_preview = response.thinking[:200] + "..." if len(response.thinking) > 200 else response.thinking
            print(f"🤔 Thinking: {thinking_preview}")
            print()
        
        if hasattr(response, 'reasoning_content') and response.reasoning_content:
            reasoning_preview = response.reasoning_content[:200] + "..." if len(response.reasoning_content) > 200 else response.reasoning_content
            print(f"🧠 Reasoning Content: {reasoning_preview}")
            print()
        
        # Raw response object for debugging
        print("🔍 RAW RESPONSE OBJECT:")
        print("=" * 30)
        print(f"Response: {response}")
        print()
        
        # Try to access response as dict if possible
        if hasattr(response, 'to_dict'):
            try:
                response_dict = response.to_dict()
                print("📋 Response as Dict:")
                pprint(response_dict, width=80, depth=3)
                print()
            except Exception as e:
                print(f"❌ Failed to convert to dict: {e}")
        
    else:
        print("❌ No last response found")
    
    # Test the get_last_tool_calls method
    print("🔍 GET_LAST_TOOL_CALLS METHOD ANALYSIS")
    print("=" * 40)
    
    tool_call_info = agent.get_last_tool_calls()
    print("📊 Tool Call Info from get_last_tool_calls():")
    pprint(tool_call_info, width=80, depth=3)
    print()
    
    print("✅ Analysis complete!")


def main():
    """Main function to run the test."""
    try:
        asyncio.run(test_response_attributes())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
