#!/usr/bin/env python3
"""
Test script to verify that list_all_memories function only returns memory content without topics.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.core.agent_memory_manager import AgentMemoryManager

# Mock memory object for testing
class MockMemory:
    def __init__(self, memory_id, memory, topics=None, timestamp=None):
        self.memory_id = memory_id
        self.memory = memory
        self.topics = topics or []
        self.timestamp = timestamp or 1234567890

class MockMemoryManager:
    def get_all_memories(self, db, user_id):
        # Return some test memories
        return [
            MockMemory("1", "grok's friend Alex's girlfriend is named Susan.", ["friends"], 1234567890),
            MockMemory("2", "grok likes to eat pizza on Fridays.", ["food", "preferences"], 1234567891),
            MockMemory("3", "grok works as a software engineer.", ["work"], 1234567892),
        ]

class MockAgnoMemory:
    def __init__(self):
        self.memory_manager = MockMemoryManager()
        self.db = None

async def test_list_all_memories():
    """Test that list_all_memories only shows memory content, not topics."""
    
    # Create a memory manager with mock data
    memory_manager = AgentMemoryManager(
        user_id="test_user",
        storage_dir="/tmp",
        enable_memory=True
    )
    
    # Initialize with mock agno memory
    memory_manager.agno_memory = MockAgnoMemory()
    
    # Call list_all_memories
    result = await memory_manager.list_all_memories()
    
    print("=== TEST RESULT ===")
    print(result)
    print("===================")
    
    # Verify that topics are not included
    if "Topics:" in result:
        print("❌ FAIL: Topics are still being displayed")
        return False
    else:
        print("✅ PASS: Topics are not displayed")
        
    # Verify that memory content is still included
    if "grok's friend Alex's girlfriend is named Susan." in result:
        print("✅ PASS: Memory content is displayed")
        return True
    else:
        print("❌ FAIL: Memory content is missing")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_list_all_memories())
    if success:
        print("\n🎉 All tests passed! The list_all_memories function now only shows memory content without topics.")
    else:
        print("\n❌ Tests failed!")
    sys.exit(0 if success else 1)
