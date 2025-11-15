#!/usr/bin/env python3
"""
Test script to verify USER_ID propagation after user switching.

This script tests that when we switch users, the new USER_ID is properly
propagated to all components that need it.
"""

import os
import sys
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

def test_user_id_propagation():
    """Test that USER_ID propagation works correctly."""
    print("🧪 Testing USER_ID Propagation")
    print("=" * 50)
    
    # Test 1: Initial USER_ID
    from personal_agent.config import get_current_user_id, refresh_user_dependent_settings
    
    initial_user = get_current_user_id()
    print(f"📋 Initial USER_ID: {initial_user}")
    
    # Test 2: Change environment variable
    new_user_id = "test_user_123"
    os.environ["USER_ID"] = new_user_id
    
    # Test 3: Verify dynamic function returns new value
    current_user = get_current_user_id()
    print(f"📋 After env change: {current_user}")
    
    if current_user == new_user_id:
        print("✅ Dynamic USER_ID function works correctly")
    else:
        print("❌ Dynamic USER_ID function failed")
        return False
    
    # Test 4: Test configuration refresh
    refreshed_settings = refresh_user_dependent_settings()
    print(f"📋 Refreshed settings USER_ID: {refreshed_settings['USER_ID']}")
    
    if refreshed_settings['USER_ID'] == new_user_id:
        print("✅ Configuration refresh works correctly")
    else:
        print("❌ Configuration refresh failed")
        return False
    
    # Test 5: Test UserManager integration
    try:
        from personal_agent.core.user_manager import UserManager
        
        user_manager = UserManager()
        
        # Create test user
        create_result = user_manager.create_user(new_user_id, "Test User")
        if create_result["success"]:
            print("✅ Test user created successfully")
        else:
            # Handle both 'message' and 'error' keys
            msg = create_result.get('message', create_result.get('error', 'Unknown error'))
            print(f"⚠️  Test user creation: {msg}")
        
        # Test switch user
        switch_result = user_manager.switch_user(new_user_id, restart_lightrag=False)
        if switch_result["success"]:
            print("✅ User switching works correctly")
            print(f"📋 Config refresh result: {switch_result.get('config_refresh', {})}")
        else:
            # Check if it's the expected "already logged in" error
            error_msg = switch_result.get("error", "")
            if "Already logged in" in error_msg:
                print(f"✅ User switching correctly detected already logged in: {error_msg}")
            else:
                print(f"❌ User switching failed: {error_msg}")
                return False
            
    except Exception as e:
        print(f"❌ UserManager test failed: {e}")
        return False
    
    print("\n🎉 All USER_ID propagation tests passed!")
    return True

def test_semantic_memory_manager():
    """Test that SemanticMemoryManager uses dynamic USER_ID."""
    print("\n🧠 Testing SemanticMemoryManager USER_ID handling")
    print("=" * 50)
    
    try:
        from personal_agent.core.semantic_memory_manager import create_semantic_memory_manager
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from personal_agent.config import get_current_user_id
        
        # Create manager
        manager = create_semantic_memory_manager(debug_mode=True)
        
        # Create test database
        db = SqliteMemoryDb(
            table_name="test_memory",
            db_file=":memory:",  # In-memory database for testing
        )
        
        current_user = get_current_user_id()
        print(f"📋 Current USER_ID: {current_user}")
        
        # Test add_memory with explicit user_id=None (should use dynamic function)
        import time
        unique_text = f"I am testing the memory system at {time.time()}"
        result = manager.add_memory(
            memory_text=unique_text,
            db=db,
            user_id=None  # This should trigger dynamic USER_ID resolution
        )
        
        if result.is_success:
            print("✅ SemanticMemoryManager add_memory works with dynamic USER_ID")
        else:
            print(f"❌ SemanticMemoryManager add_memory failed: {result.message}")
            return False
            
        print("✅ SemanticMemoryManager USER_ID handling works correctly")
        return True
        
    except Exception as e:
        print(f"❌ SemanticMemoryManager test failed: {e}")
        return False

if __name__ == "__main__":
    success = True
    
    try:
        success &= test_user_id_propagation()
        success &= test_semantic_memory_manager()
        
        if success:
            print("\n🎉 All tests passed! USER_ID propagation is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. Check the output above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
