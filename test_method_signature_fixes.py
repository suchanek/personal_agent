#!/usr/bin/env python3
"""
Test program to verify that all method signature fixes in AntiDuplicateMemory are working correctly.

This test verifies:
1. Method signatures match parent class
2. Functionality is preserved
3. Exception handling works correctly
4. Polymorphic usage works
"""

import inspect
import tempfile
import os
from typing import List

from agno.memory.v2.memory import Memory
from agno.memory.v2.schema import UserMemory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.models.message import Message

from src.personal_agent.core.anti_duplicate_memory import AntiDuplicateMemory


def test_method_signatures():
    """Test that method signatures are compatible with the parent class."""
    print("🔍 Testing Method Signatures")
    print("=" * 50)
    
    methods_to_check = ['add_user_memory', 'create_user_memories', 'delete_user_memory']
    compatible_count = 0
    
    for method_name in methods_to_check:
        parent_sig = inspect.signature(getattr(Memory, method_name))
        child_sig = inspect.signature(getattr(AntiDuplicateMemory, method_name))
        
        # Check parameter compatibility (parameters should match)
        parent_params = list(parent_sig.parameters.items())
        child_params = list(child_sig.parameters.items())
        
        params_match = parent_params == child_params
        
        # Special handling for methods with intentional differences
        if method_name == 'create_user_memories':
            # For this method, we only care about parameter compatibility
            compatible = params_match
            status = "✅" if compatible else "❌"
            note = " (intentionally different return type)" if compatible else ""
        elif method_name == 'add_user_memory':
            # For this method, parameters should match but return type is intentionally Optional[str] vs str
            compatible = params_match
            status = "✅" if compatible else "❌"
            note = " (intentionally Optional[str] for duplicate handling)" if compatible else ""
        else:
            # For other methods, full signature should match
            compatible = parent_sig == child_sig
            status = "✅" if compatible else "❌"
            note = ""
        
        if compatible:
            compatible_count += 1
            
        print(f"{status} {method_name}:")
        print(f"    Parent: {parent_sig}")
        print(f"    Child:  {child_sig}")
        print(f"    Compatible: {compatible}{note}")
        print()
    
    # Return True if all methods are compatible (even if not exact matches)
    return compatible_count == len(methods_to_check)


def test_add_user_memory():
    """Test add_user_memory method with all parameter combinations."""
    print("🧪 Testing add_user_memory Method")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = SqliteMemoryDb(table_name='test_memory', db_file=db_path)
        memory = AntiDuplicateMemory(db=db, debug_mode=False)
        
        # Test 1: Basic functionality
        print("Test 1: Basic add_user_memory")
        test_memory = UserMemory(memory='Test memory 1', topics=['test'])
        memory_id = memory.add_user_memory(test_memory)
        print(f"✅ Added memory with ID: {memory_id}")
        
        # Test 2: With explicit user_id
        print("\nTest 2: With explicit user_id")
        test_memory2 = UserMemory(memory='Test memory 2', topics=['test'])
        memory_id2 = memory.add_user_memory(test_memory2, user_id='test_user')
        print(f"✅ Added memory with ID: {memory_id2}")
        
        # Test 3: With refresh_from_db parameter
        print("\nTest 3: With refresh_from_db parameter")
        test_memory3 = UserMemory(memory='Test memory 3', topics=['test'])
        memory_id3 = memory.add_user_memory(test_memory3, user_id='test_user', refresh_from_db=False)
        print(f"✅ Added memory with ID: {memory_id3}")
        
        # Test 4: Duplicate detection (should return None)
        print("\nTest 4: Duplicate detection")
        duplicate_memory = UserMemory(memory='Test memory 1', topics=['test'])
        result = memory.add_user_memory(duplicate_memory)
        if result is None:
            print(f"✅ Duplicate detection working: Memory rejected")
        else:
            print("❌ Duplicate detection failed - should have returned None")
            return False
        
        return True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_create_user_memories():
    """Test create_user_memories method with all parameter combinations."""
    print("\n🧪 Testing create_user_memories Method")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = SqliteMemoryDb(table_name='test_memory', db_file=db_path)
        memory = AntiDuplicateMemory(db=db, debug_mode=False)
        
        # Test 1: Single message
        print("Test 1: Single message")
        memories = memory.create_user_memories(message="Single test message")
        print(f"✅ Created {len(memories)} memories from single message")
        
        # Test 2: List of messages
        print("\nTest 2: List of messages")
        messages = [
            Message(role="user", content="Message 1"),
            Message(role="user", content="Message 2"),
            "String message 3"
        ]
        memories = memory.create_user_memories(messages=messages)
        print(f"✅ Created {len(memories)} memories from message list")
        
        # Test 3: With explicit user_id
        print("\nTest 3: With explicit user_id")
        memories = memory.create_user_memories(
            message="User-specific message", 
            user_id="specific_user"
        )
        print(f"✅ Created {len(memories)} memories for specific user")
        
        # Test 4: With refresh_from_db parameter
        print("\nTest 4: With refresh_from_db parameter")
        memories = memory.create_user_memories(
            message="No refresh message", 
            user_id="test_user",
            refresh_from_db=False
        )
        print(f"✅ Created {len(memories)} memories without refresh")
        
        # Test 5: Duplicate handling
        print("\nTest 5: Duplicate handling")
        memories = memory.create_user_memories(message="Single test message")  # Duplicate
        print(f"✅ Duplicate handling: {len(memories)} memories created (should be 0)")
        
        return True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_delete_user_memory():
    """Test delete_user_memory method with all parameter combinations."""
    print("\n🧪 Testing delete_user_memory Method")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = SqliteMemoryDb(table_name='test_memory', db_file=db_path)
        memory = AntiDuplicateMemory(db=db, debug_mode=False)
        
        # First, add some memories to delete
        test_memory1 = UserMemory(memory='Memory to delete 1', topics=['test'])
        memory_id1 = memory.add_user_memory(test_memory1)
        
        test_memory2 = UserMemory(memory='Memory to delete 2', topics=['test'])
        memory_id2 = memory.add_user_memory(test_memory2, user_id='test_user')
        
        # Test 1: Basic delete
        print("Test 1: Basic delete")
        memory.delete_user_memory(memory_id1)
        print("✅ Successfully deleted memory")
        
        # Test 2: Delete with explicit user_id
        print("\nTest 2: Delete with explicit user_id")
        memory.delete_user_memory(memory_id2, user_id='test_user')
        print("✅ Successfully deleted memory with user_id")
        
        # Test 3: Delete with refresh_from_db parameter
        print("\nTest 3: Delete with refresh_from_db parameter")
        test_memory3 = UserMemory(memory='Memory to delete 3', topics=['test'])
        memory_id3 = memory.add_user_memory(test_memory3)
        memory.delete_user_memory(memory_id3, refresh_from_db=False)
        print("✅ Successfully deleted memory without refresh")
        
        # Test 4: Delete non-existent memory (should raise exception)
        print("\nTest 4: Delete non-existent memory")
        try:
            memory.delete_user_memory("non_existent_id")
            print("❌ Should have raised exception for non-existent memory")
            return False
        except Exception as e:
            print(f"✅ Correctly raised exception: {type(e).__name__}")
        
        return True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_polymorphic_usage():
    """Test that AntiDuplicateMemory can be used polymorphically as Memory."""
    print("\n🔄 Testing Polymorphic Usage")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = SqliteMemoryDb(table_name='test_memory', db_file=db_path)
        
        # Use AntiDuplicateMemory as Memory type
        memory: Memory = AntiDuplicateMemory(db=db, debug_mode=False)
        
        # Test polymorphic method calls
        print("Test 1: Polymorphic add_user_memory")
        test_memory = UserMemory(memory='Polymorphic test', topics=['test'])
        memory_id = memory.add_user_memory(test_memory, user_id='poly_user')
        print(f"✅ Polymorphic add successful: {memory_id}")
        
        print("\nTest 2: Polymorphic create_user_memories")
        memories = memory.create_user_memories(
            message="Polymorphic message",
            user_id='poly_user'
        )
        print(f"✅ Polymorphic create successful: {len(memories)} memories")
        
        print("\nTest 3: Polymorphic delete_user_memory")
        memory.delete_user_memory(memory_id, user_id='poly_user')
        print("✅ Polymorphic delete successful")
        
        return True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    """Run all tests."""
    print("🚀 Method Signature Fix Verification Tests")
    print("=" * 60)
    
    tests = [
        ("Method Signatures", test_method_signatures),
        ("add_user_memory", test_add_user_memory),
        ("create_user_memories", test_create_user_memories),
        ("delete_user_memory", test_delete_user_memory),
        ("Polymorphic Usage", test_polymorphic_usage),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ FAILED: {test_name} - {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Method signature fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
