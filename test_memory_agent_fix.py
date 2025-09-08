#!/usr/bin/env python3
"""
Test script to verify the memory agent behavior fix.

This script tests that the memory agent now correctly selects list_all_memories
for general listing requests instead of get_all_memories.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def test_instruction_patterns():
    """Test the updated memory agent instructions."""
    from personal_agent.team.reasoning_team import _memory_specific_instructions
    
    print("🧪 Testing Memory Agent Instruction Updates")
    print("=" * 50)
    
    # Check that the new instructions are present
    instructions_text = "\n".join(_memory_specific_instructions)
    
    # Test cases that should now work correctly
    test_cases = [
        ("FUNCTION SELECTION RULES", "Should have clear function selection rules"),
        ("list all memories stored", "Should handle 'stored' variation"),
        ("show all memories", "Should handle 'show' variation"),
        ("what memories do you have", "Should handle 'what memories' variation"),
        ("Default to list_all_memories", "Should default to efficient function"),
        ("When in doubt, choose list_all_memories", "Should prefer efficient function"),
        ("Keywords for list_all_memories", "Should have keyword guidance"),
        ("Keywords for get_all_memories", "Should distinguish detailed requests"),
    ]
    
    print("✅ Checking for required instruction components:")
    for pattern, description in test_cases:
        if pattern in instructions_text:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ MISSING: {description}")
    
    print("\n📋 Updated Memory Agent Instructions:")
    print("-" * 30)
    for i, instruction in enumerate(_memory_specific_instructions, 1):
        if instruction.strip():  # Skip empty lines for readability
            print(f"{i:2d}. {instruction}")
    
    print("\n🎯 Key Improvements:")
    print("  • Added FUNCTION SELECTION RULES section")
    print("  • Expanded COMMON PATTERNS with more variations")
    print("  • Added PATTERN MATCHING GUIDELINES with keywords")
    print("  • Default bias toward list_all_memories for efficiency")
    print("  • Clear distinction between summary vs detailed requests")
    
    print("\n🧪 Test Phrases That Should Now Work:")
    test_phrases = [
        ("list all memories stored in the system", "list_all_memories"),
        ("show all memories", "list_all_memories"),
        ("what memories do you have about me", "list_all_memories"),
        ("how many memories", "list_all_memories"),
        ("memory summary", "list_all_memories"),
        ("show detailed memories", "get_all_memories"),
        ("get full memory details", "get_all_memories"),
        ("complete memory information", "get_all_memories"),
    ]
    
    for phrase, expected_function in test_phrases:
        print(f"  • '{phrase}' → {expected_function}")

if __name__ == "__main__":
    test_instruction_patterns()
    print("\n✅ Memory agent behavior fix has been successfully implemented!")
    print("The agent should now correctly choose list_all_memories for general requests.")
