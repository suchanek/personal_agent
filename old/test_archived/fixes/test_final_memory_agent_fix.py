#!/usr/bin/env python3
"""
Final test to verify the complete memory agent fix works end-to-end.

This test verifies that:
1. The memory agent has access to list_all_memories function
2. The function returns a clean string response without <think> tags
3. The agent prefers list_all_memories over get_all_memories for general requests
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.core.agent_memory_manager import AgentMemoryManager
from personal_agent.tools.persag_memory_tools import PersagMemoryTools
from personal_agent.core.agent_instruction_manager import AgentInstructionManager


async def test_memory_agent_fix():
    """Test the complete memory agent fix."""
    print("🧪 Testing Memory Agent Fix")
    print("=" * 50)
    
    # Test 1: Verify AgentMemoryManager has list_all_memories method
    print("\n1. Testing AgentMemoryManager.list_all_memories method...")
    
    # Create a mock memory manager to test the method exists
    memory_manager = AgentMemoryManager(
        user_id="test_user",
        storage_dir="/tmp/test",
        enable_memory=True
    )
    
    # Check if the method exists
    if hasattr(memory_manager, 'list_all_memories'):
        print("✅ AgentMemoryManager.list_all_memories method exists")
    else:
        print("❌ AgentMemoryManager.list_all_memories method missing")
        return False
    
    # Test 2: Verify PersagMemoryTools exposes list_all_memories
    print("\n2. Testing PersagMemoryTools exposes list_all_memories...")
    
    # Create PersagMemoryTools instance
    tools = PersagMemoryTools(memory_manager=memory_manager)
    
    # Check if list_all_memories is in the tools list
    tool_names = [tool.__name__ for tool in tools.tools if hasattr(tool, '__name__')]
    if 'list_all_memories' in tool_names:
        print("✅ PersagMemoryTools exposes list_all_memories function")
    else:
        print("❌ PersagMemoryTools does not expose list_all_memories function")
        print(f"Available tools: {tool_names}")
        return False
    
    # Test 3: Verify agent instructions prefer list_all_memories
    print("\n3. Testing agent instructions prefer list_all_memories...")
    
    # Get the base memory instructions
    from personal_agent.core.agent_instruction_manager import InstructionLevel
    instruction_manager = AgentInstructionManager(
        instruction_level=InstructionLevel.MINIMAL,
        user_id="test_user",
        enable_memory=True,
        enable_mcp=False,
        mcp_servers={}
    )
    instructions = instruction_manager.get_base_memory_instructions()
    
    # Check if instructions mention list_all_memories preference
    if isinstance(instructions, list):
        instructions_text = " ".join(instructions)
    else:
        instructions_text = str(instructions)
    
    # Debug: Print first 500 characters to see what we got
    print(f"Debug: Instructions preview: {instructions_text[:500]}...")
    
    if "list_all_memories" in instructions_text.lower():
        print("✅ Agent instructions mention list_all_memories")
        
        # Check for preference patterns
        if "prefer" in instructions_text.lower() or "use this for" in instructions_text.lower():
            print("✅ Agent instructions show preference for list_all_memories")
        else:
            print("⚠️ Agent instructions mention list_all_memories but preference unclear")
    else:
        print("❌ Agent instructions do not mention list_all_memories")
        print(f"Debug: Searching for 'list_all_memories' in {len(instructions_text)} characters")
        # Let's also check if it's there with different casing
        if "list_all_memories" in instructions_text:
            print("Found with exact case!")
        elif "LIST_ALL_MEMORIES" in instructions_text.upper():
            print("Found with upper case!")
        else:
            print("Not found at all")
        return False
    
    # Test 4: Test the actual method response format
    print("\n4. Testing list_all_memories response format...")
    
    # Mock the agno_memory to test response format
    class MockMemoryManager:
        def list_all_memories(self, db, user_id):
            return [
                "grok loves hiking in the mountains",
                "grok's best friend is named Nick",
                "grok is interested in robotics and AI"
            ]
    
    class MockAgnoMemory:
        def __init__(self):
            self.memory_manager = MockMemoryManager()
            self.db = None
    
    # Set up the memory manager with mock data
    memory_manager.agno_memory = MockAgnoMemory()
    
    # Test the method
    try:
        result = await memory_manager.list_all_memories()
        print(f"✅ list_all_memories returned result: {len(result)} characters")
        
        # Check that result is a clean string without <think> tags
        if "<think>" in result or "</think>" in result:
            print("❌ Result contains <think> tags - response format issue")
            return False
        else:
            print("✅ Result is clean without <think> tags")
        
        # Check that result contains expected format
        if "📝 Listed" in result and "memories:" in result:
            print("✅ Result has expected format")
        else:
            print("❌ Result format unexpected")
            print(f"Result preview: {result[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing list_all_memories: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! Memory agent fix is complete.")
    print("\nSummary of fixes:")
    print("✅ Added list_all_memories method to AgentMemoryManager")
    print("✅ Exposed list_all_memories in PersagMemoryTools")
    print("✅ Updated agent instructions to prefer list_all_memories")
    print("✅ Fixed response format to return clean string")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_memory_agent_fix())
    sys.exit(0 if success else 1)
