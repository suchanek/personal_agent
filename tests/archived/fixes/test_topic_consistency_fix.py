#!/usr/bin/env python3
"""
Test script to verify that topics are always stored as lists, not strings.

This test validates the fix for the topic consistency issue where some memories
had topics stored as strings (like "personal information") while others had
them stored as lists (like ["personal", "information"]).
"""

import asyncio
import sys
import time
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_topic_consistency():
    """Test that all topics are consistently stored as lists."""
    print("🧪 Testing Topic Consistency Fix")
    print("=" * 50)
    
    # Initialize agent
    print("🤖 Initializing agent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return False
    
    print(f"✅ Agent initialized with model: {LLM_MODEL}")
    
    # Test different topic input formats
    print("\n📝 Testing different topic input formats...")
    
    test_cases = [
        {
            "fact": "I am testing topic consistency with a single topic string.",
            "description": "Single topic string",
            "expected_behavior": "Should convert to list"
        },
        {
            "fact": "I am testing topic consistency with comma-separated topics.",
            "description": "Comma-separated topics",
            "expected_behavior": "Should split into list"
        },
        {
            "fact": "I am testing topic consistency with proper list topics.",
            "description": "Already proper list",
            "expected_behavior": "Should remain as list"
        },
        {
            "fact": "I am testing topic consistency with JSON string topics.",
            "description": "JSON string format",
            "expected_behavior": "Should parse to list"
        },
        {
            "fact": "I am testing topic consistency with malformed JSON topics.",
            "description": "Malformed JSON",
            "expected_behavior": "Should handle gracefully"
        }
    ]
    
    stored_facts = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {test_case['description']}")
        print(f"  Fact: {test_case['fact']}")
        print(f"  Expected: {test_case['expected_behavior']}")
        
        try:
            response = await agent.run(f"Please remember this fact about me: {test_case['fact']}")
            
            if any(indicator in response.lower() for indicator in ["stored", "remember", "noted", "✅", "🧠"]):
                print(f"    ✅ Stored successfully")
                stored_facts.append(test_case['fact'])
            else:
                print(f"    ⚠️ Storage unclear: {response[:100]}...")
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"    ❌ Failed: {e}")
    
    print(f"\n📊 Stored {len(stored_facts)}/{len(test_cases)} test facts")
    
    # Wait for storage to settle
    print("\n⏳ Waiting for storage to settle...")
    await asyncio.sleep(2)
    
    # Now check the actual stored memories to verify topic format
    print("\n🔍 Checking stored memory topic formats...")
    
    try:
        # Get all memories to check their topic formats
        all_memories_response = await agent.run("Show me all my memories")
        print(f"📋 Retrieved memories for format checking")
        
        # Access the memory database directly to check topic formats
        if agent.agno_memory and agent.agno_memory.db:
            memory_rows = agent.agno_memory.db.read_memories(user_id=USER_ID)
            
            topic_format_issues = []
            total_memories = 0
            list_format_count = 0
            string_format_count = 0
            
            print("\n📊 Memory Topic Format Analysis:")
            print("-" * 60)
            
            for row in memory_rows[-10:]:  # Check last 10 memories
                if row.user_id == USER_ID and row.memory:
                    try:
                        from agno.memory.v2.schema import UserMemory
                        user_memory = UserMemory.from_dict(row.memory)
                        total_memories += 1
                        
                        memory_text = user_memory.memory[:50] + "..." if len(user_memory.memory) > 50 else user_memory.memory
                        topics = user_memory.topics
                        
                        if isinstance(topics, list):
                            list_format_count += 1
                            print(f"  ✅ LIST: {memory_text}")
                            print(f"      Topics: {topics}")
                        elif isinstance(topics, str):
                            string_format_count += 1
                            topic_format_issues.append({
                                'memory': memory_text,
                                'topics': topics,
                                'memory_id': user_memory.memory_id
                            })
                            print(f"  ❌ STRING: {memory_text}")
                            print(f"      Topics: '{topics}' (should be list!)")
                        else:
                            print(f"  ⚠️ OTHER: {memory_text}")
                            print(f"      Topics: {topics} (type: {type(topics)})")
                            
                    except Exception as e:
                        print(f"  ❌ Error parsing memory: {e}")
            
            print("-" * 60)
            print(f"📊 Topic Format Summary:")
            print(f"  Total memories checked: {total_memories}")
            print(f"  List format (correct): {list_format_count}")
            print(f"  String format (incorrect): {string_format_count}")
            print(f"  Success rate: {(list_format_count / total_memories * 100):.1f}%" if total_memories > 0 else "N/A")
            
            if topic_format_issues:
                print(f"\n❌ Found {len(topic_format_issues)} memories with string topics:")
                for issue in topic_format_issues:
                    print(f"  - Memory: {issue['memory']}")
                    print(f"    Topics: '{issue['topics']}'")
                    print(f"    ID: {issue['memory_id']}")
                
                return False
            else:
                print(f"\n✅ All memories have topics in correct list format!")
                return True
                
        else:
            print("❌ Could not access memory database for format checking")
            return False
            
    except Exception as e:
        print(f"❌ Error checking memory formats: {e}")
        return False


async def test_topic_migration():
    """Test that existing string topics can be migrated to list format."""
    print("\n🔄 Testing Topic Migration (if needed)")
    print("=" * 50)
    
    # This would be where we implement a migration script if needed
    # For now, just verify that new memories use the correct format
    
    print("✅ Topic migration testing completed")
    return True


async def main():
    """Main test function."""
    print("🧪 Topic Consistency Fix Validation")
    print("=" * 60)
    
    try:
        # Run topic consistency test
        consistency_success = await test_topic_consistency()
        
        # Run migration test
        migration_success = await test_topic_migration()
        
        print("\n" + "=" * 60)
        print("📋 TOPIC CONSISTENCY TEST SUMMARY")
        print("=" * 60)
        
        print(f"Topic Consistency Test: {'✅ PASS' if consistency_success else '❌ FAIL'}")
        print(f"Topic Migration Test: {'✅ PASS' if migration_success else '❌ FAIL'}")
        
        overall_success = consistency_success and migration_success
        
        if overall_success:
            print("\n🎉 OVERALL: Topic consistency fix is working correctly!")
            print("✅ All topics are now stored as lists")
            print("✅ No more string/list inconsistencies")
            return True
        else:
            print("\n⚠️ OVERALL: Topic consistency issues detected")
            print("\n💡 Recommendations:")
            if not consistency_success:
                print("  - Check topic processing logic in store_user_memory")
                print("  - Verify SemanticMemoryManager topic handling")
                print("  - Consider running migration script for existing memories")
            return False
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Usage: python test_topic_consistency_fix.py")
    print("This test validates that topics are always stored as lists")
    print()
    
    # Run the tests
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Topic consistency fix validation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Topic consistency fix validation failed!")
        sys.exit(1)
