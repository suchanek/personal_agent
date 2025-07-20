#!/usr/bin/env python3
"""
Test script to verify the memory clearing fix.

This script tests the semantic memory clearing functionality to ensure that:
1. Memories are properly cleared from the SQLite database
2. The clearing script and CLI show consistent results
3. Database connections are properly managed
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent
sys.path.insert(0, str(project_root / "src"))

from personal_agent.tools.memory_cleaner import MemoryClearingManager
from personal_agent.core.semantic_memory_manager import create_semantic_memory_manager
from agno.memory.v2.db.sqlite import SqliteMemoryDb


async def test_memory_clearing_fix():
    """Test the memory clearing fix to ensure it works correctly."""
    print("🧪 Testing Memory Clearing Fix")
    print("=" * 50)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_user_id = "test_user"
        
        print(f"📁 Test directory: {temp_path}")
        print(f"👤 Test user ID: {test_user_id}")
        
        # Step 1: Create and populate a test database
        print("\n1️⃣ Creating test database with sample memories...")
        
        db_path = temp_path / "semantic_memory.db"
        memory_db = SqliteMemoryDb(
            table_name="semantic_memory",
            db_file=str(db_path),
        )
        
        memory_manager = create_semantic_memory_manager(
            similarity_threshold=0.8,
            debug_mode=True,
        )
        
        # Add some test memories
        test_memories = [
            "I work as a software engineer at Google",
            "My favorite programming language is Python",
            "I live in San Francisco",
            "I have a dog named Max",
            "I enjoy hiking on weekends"
        ]
        
        for memory_text in test_memories:
            result = memory_manager.add_memory(
                memory_text=memory_text,
                db=memory_db,
                user_id=test_user_id
            )
            if result.is_success:
                print(f"   ✅ Added: {memory_text}")
            else:
                print(f"   ❌ Failed to add: {memory_text} - {result.message}")
        
        # Step 2: Verify memories were added
        print("\n2️⃣ Verifying memories were added...")
        stats = memory_manager.get_memory_stats(db=memory_db, user_id=test_user_id)
        initial_count = stats.get("total_memories", 0)
        print(f"   📊 Initial memory count: {initial_count}")
        
        if initial_count == 0:
            print("   ❌ No memories were added - test cannot continue")
            return False
        
        # Step 3: Test the clearing functionality
        print("\n3️⃣ Testing memory clearing with improved manager...")
        
        # Create the memory clearing manager
        manager = MemoryClearingManager(
            user_id=test_user_id,
            storage_dir=str(temp_path),
            lightrag_memory_url="http://localhost:9622",  # Won't be used in this test
            verbose=True
        )
        
        # Clear memories
        results = await manager.clear_all_memories(
            dry_run=False,
            semantic_only=True,  # Only test semantic clearing
            lightrag_only=False
        )
        
        print(f"   📋 Clearing results: {results}")
        
        # Step 4: Verify clearing was successful
        print("\n4️⃣ Verifying memories were cleared...")
        
        # Reinitialize components to simulate CLI behavior
        fresh_memory_db = SqliteMemoryDb(
            table_name="semantic_memory",
            db_file=str(db_path),
        )
        
        fresh_memory_manager = create_semantic_memory_manager(
            similarity_threshold=0.8,
            debug_mode=True,
        )
        
        # Check memory count with fresh connection
        fresh_stats = fresh_memory_manager.get_memory_stats(
            db=fresh_memory_db, 
            user_id=test_user_id
        )
        final_count = fresh_stats.get("total_memories", 0)
        print(f"   📊 Final memory count: {final_count}")
        
        # Step 5: Test verification
        print("\n5️⃣ Testing verification functionality...")
        verification = await manager.verify_clearing()
        print(f"   🔍 Verification results: {verification}")
        
        # Step 6: Determine test result
        print("\n6️⃣ Test Results:")
        print("=" * 30)
        
        success = True
        
        if not results["semantic_memory"]["success"]:
            print("   ❌ Memory clearing reported failure")
            success = False
        
        if final_count > 0:
            print(f"   ❌ Memories still remain: {final_count}")
            success = False
        
        if not verification["semantic_memory"]["cleared"]:
            print("   ❌ Verification indicates memories not cleared")
            success = False
        
        if success:
            print("   ✅ All tests passed!")
            print("   ✅ Memory clearing fix is working correctly")
            print("   ✅ Database connections are properly managed")
            print("   ✅ Verification is working correctly")
        else:
            print("   ❌ Some tests failed")
            print("   ❌ Memory clearing fix needs more work")
        
        return success


async def main():
    """Main test function."""
    try:
        success = await test_memory_clearing_fix()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
