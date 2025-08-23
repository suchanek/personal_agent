#!/usr/bin/env python3
"""
Test script to diagnose and validate writer agent response handling.

This script tests the writer agent both in isolation and within the team context
to identify where the tool call execution vs content return issue occurs.
"""

import asyncio
import logging
from src.personal_agent.team.personal_agent_team import create_personal_agent_team
from src.personal_agent.team.specialized_agents import create_writer_agent

# Set up logging to see diagnostic messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_writer_agent_standalone():
    """Test the writer agent in standalone mode."""
    print("\n" + "="*80)
    print("TEST 1: Writer Agent Standalone")
    print("="*80)
    
    try:
        # Create standalone writer agent
        writer_agent = create_writer_agent(
            model_provider="ollama",
            model_name="llama3.1:8b",
            debug=True
        )
        
        print(f"✅ Writer agent created: {writer_agent.name}")
        print(f"   Model: {writer_agent.model.id}")
        print(f"   Tools: {len(writer_agent.tools)}")
        print(f"   Show tool calls: {writer_agent.show_tool_calls}")
        
        # Test a simple writing request
        query = "Write a short limerick about debugging code"
        print(f"\n📝 Testing query: {query}")
        
        response = await writer_agent.arun(query)
        
        print(f"\n📋 Response type: {type(response)}")
        print(f"📋 Response content length: {len(response.content) if hasattr(response, 'content') else 'No content attr'}")
        print(f"📋 Response preview: {(response.content[:300] + '...') if hasattr(response, 'content') and len(response.content) > 300 else (response.content if hasattr(response, 'content') else str(response))}")
        
        # Check for tool call syntax in response
        if hasattr(response, 'content') and "write_original_content(" in response.content:
            print("⚠️  WARNING: Response contains tool call syntax instead of executed content!")
        else:
            print("✅ Response appears to contain actual content, not tool call syntax")
            
        return response
        
    except Exception as e:
        print(f"❌ Error in standalone writer agent test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_writer_agent_in_team():
    """Test the writer agent within the team context."""
    print("\n" + "="*80)
    print("TEST 2: Writer Agent in Team Context")
    print("="*80)
    
    try:
        # Create team
        team = create_personal_agent_team(
            model_provider="ollama",
            model_name="qwen3:1.7b",  # Use smaller model for coordinator
            debug=True
        )
        
        print(f"✅ Team created: {team.name}")
        print(f"   Mode: {team.mode}")
        print(f"   Members: {len(team.members)}")
        
        # Find writer agent in team
        writer_agent = None
        for member in team.members:
            if "Writer" in member.name:
                writer_agent = member
                break
        
        if writer_agent:
            print(f"✅ Found writer agent in team: {writer_agent.name}")
            print(f"   Model: {writer_agent.model.id}")
            print(f"   Show tool calls: {writer_agent.show_tool_calls}")
        else:
            print("❌ Writer agent not found in team!")
            return None
        
        # Test a writing request through team coordination
        query = "Write a short limerick about debugging code"
        print(f"\n📝 Testing team query: {query}")
        
        response = await team.arun(query)
        
        print(f"\n📋 Team response type: {type(response)}")
        print(f"📋 Team response content length: {len(response.content) if hasattr(response, 'content') else 'No content attr'}")
        print(f"📋 Team response preview: {(response.content[:300] + '...') if hasattr(response, 'content') and len(response.content) > 300 else (response.content if hasattr(response, 'content') else str(response))}")
        
        # Check for tool call syntax in response
        if hasattr(response, 'content') and "write_original_content(" in response.content:
            print("⚠️  WARNING: Team response contains tool call syntax instead of executed content!")
            
            # Check member responses for actual content
            if hasattr(response, 'member_responses') and response.member_responses:
                print(f"🔍 Checking {len(response.member_responses)} member responses...")
                for i, member_resp in enumerate(response.member_responses):
                    if hasattr(member_resp, 'messages') and member_resp.messages:
                        for j, msg in enumerate(member_resp.messages):
                            if hasattr(msg, 'content') and msg.content and "write_original_content(" not in msg.content:
                                print(f"✅ Found actual content in member {i} message {j}:")
                                print(f"   Content: {msg.content[:200]}...")
                                return msg.content
        else:
            print("✅ Team response appears to contain actual content, not tool call syntax")
            
        return response
        
    except Exception as e:
        print(f"❌ Error in team writer agent test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run all writer agent tests."""
    print("🚀 Starting Writer Agent Response Diagnostic Tests")
    
    # Test 1: Standalone writer agent
    standalone_response = await test_writer_agent_standalone()
    
    # Test 2: Writer agent in team
    team_response = await test_writer_agent_in_team()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    if standalone_response:
        standalone_has_tool_syntax = hasattr(standalone_response, 'content') and "write_original_content(" in standalone_response.content
        print(f"📝 Standalone writer agent: {'❌ Tool call syntax' if standalone_has_tool_syntax else '✅ Actual content'}")
    else:
        print("📝 Standalone writer agent: ❌ Failed to test")
    
    if team_response:
        team_has_tool_syntax = hasattr(team_response, 'content') and "write_original_content(" in team_response.content
        print(f"🤖 Team writer agent: {'❌ Tool call syntax' if team_has_tool_syntax else '✅ Actual content'}")
    else:
        print("🤖 Team writer agent: ❌ Failed to test")
    
    print("\n✅ Diagnostic tests completed!")

if __name__ == "__main__":
    asyncio.run(main())