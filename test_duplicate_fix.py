#!/usr/bin/env python3
"""
Test script to verify the duplicate tool call fix in reasoning_team.py

This script tests that the team coordinator properly recognizes when a memory
storage task has been completed successfully and doesn't make duplicate calls.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.team.reasoning_team import create_team


async def test_memory_storage_fix():
    """Test that memory storage doesn't result in duplicate tool calls."""
    
    print("🧪 Testing duplicate tool call fix...")
    print("=" * 50)
    
    try:
        # Create the team
        print("Creating team...")
        team = await create_team(use_remote=False)
        print("✅ Team created successfully")
        
        # Test query that should store a memory
        test_query = "store new memory: I love hiking in the mountains"
        
        print(f"\n🔍 Testing query: '{test_query}'")
        print("This should result in ONE tool call, not multiple duplicates")
        print("-" * 50)
        
        # Run the query and capture the response
        response = await team.arun(test_query)
        
        print("\n📊 Response Analysis:")
        print(f"Response type: {type(response)}")
        print(f"Response content length: {len(response.content) if hasattr(response, 'content') and response.content else 0}")
        
        # Check for tool calls in the response
        tool_calls_found = 0
        if hasattr(response, 'messages') and response.messages:
            for message in response.messages:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls_found += len(message.tool_calls)
                    print(f"Found {len(message.tool_calls)} tool calls in message")
                    for i, tool_call in enumerate(message.tool_calls):
                        tool_name = getattr(tool_call, 'name', 'unknown')
                        print(f"  Tool call {i+1}: {tool_name}")
        
        # Check member responses for tool calls
        if hasattr(response, 'member_responses') and response.member_responses:
            print(f"Found {len(response.member_responses)} member responses")
            for i, member_resp in enumerate(response.member_responses):
                if hasattr(member_resp, 'messages') and member_resp.messages:
                    for message in member_resp.messages:
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            tool_calls_found += len(message.tool_calls)
                            print(f"Member {i} has {len(message.tool_calls)} tool calls")
        
        print(f"\n📈 Total tool calls found: {tool_calls_found}")
        
        # Analyze the response content for success indicators
        response_text = response.content if hasattr(response, 'content') else str(response)
        success_indicators = [
            'Added memory for user',
            'ACCEPTED:',
            'Memory stored successfully',
            '✅'
        ]
        
        found_success = False
        for indicator in success_indicators:
            if indicator in response_text:
                print(f"✅ Found success indicator: '{indicator}'")
                found_success = True
                break
        
        if not found_success:
            print("⚠️ No clear success indicators found in response")
        
        # Check for duplicate patterns
        duplicate_patterns = [
            'transfer_task_to_member',
            'Store new memory:',
            'asteroid fragment'
        ]
        
        duplicate_found = False
        for pattern in duplicate_patterns:
            count = response_text.count(pattern)
            if count > 1:
                print(f"⚠️ Potential duplicate found: '{pattern}' appears {count} times")
                duplicate_found = True
        
        if not duplicate_found:
            print("✅ No obvious duplicate patterns found")
        
        print(f"\n📝 Response preview (first 500 chars):")
        print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
        
        # Cleanup
        from personal_agent.team.reasoning_team import cleanup_team
        await cleanup_team(team)
        print("\n🧹 Team cleanup completed")
        
        # Summary
        print("\n" + "=" * 50)
        print("🎯 TEST SUMMARY:")
        print(f"   Tool calls found: {tool_calls_found}")
        print(f"   Success indicators: {'✅ Found' if found_success else '❌ Not found'}")
        print(f"   Duplicate patterns: {'❌ Found' if duplicate_found else '✅ None found'}")
        
        if tool_calls_found <= 2 and found_success and not duplicate_found:
            print("🎉 TEST PASSED: Fix appears to be working correctly!")
            return True
        else:
            print("❌ TEST FAILED: Issues detected")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Duplicate Tool Call Fix Test")
    print("Testing the fix for duplicate memory storage calls in reasoning_team.py")
    print()
    
    success = await test_memory_storage_fix()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
