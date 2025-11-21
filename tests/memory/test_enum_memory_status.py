#!/usr/bin/env python3
"""
Test script to verify the new enum-based memory storage status system.
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.semantic_memory_manager import (
    MemoryStorageStatus,
    MemoryStorageResult,
    create_semantic_memory_manager,
)
from agno.memory.v2.db.sqlite import SqliteMemoryDb


@pytest.mark.asyncio
async def test_enum_memory_status():
    """Test the new enum-based memory storage status system."""
    print("🧪 Testing Enum-Based Memory Storage Status System")
    print("=" * 60)

    # Create a unique temporary database for testing
    import time
    import os
    db_path = f"/tmp/test_enum_memory_{int(time.time())}.db"
    
    # Clean up any existing database file
    if os.path.exists(db_path):
        os.remove(db_path)
    
    memory_db = SqliteMemoryDb(
        table_name="test_memory",
        db_file=db_path,
    )
    
    print(f"📂 Using clean database: {db_path}")

    # Create memory manager
    manager = create_semantic_memory_manager(
        similarity_threshold=0.7,  # Lower threshold for better semantic detection
        debug_mode=True,
    )

    test_user_id = "test_user"

    # Test 1: Successful memory storage
    print("\n📝 Test 1: Successful Memory Storage")
    result = manager.add_memory(
        memory_text="I love programming in Python",
        db=memory_db,
        user_id=test_user_id,
        topics=["programming", "preferences"]
    )
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Memory ID: {result.memory_id}")
    print(f"Topics: {result.topics}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")
    assert result.status == MemoryStorageStatus.SUCCESS
    assert result.is_success
    assert not result.is_rejected
    assert result.memory_id is not None

    # Test 2: Exact duplicate rejection
    print("\n🔄 Test 2: Exact Duplicate Rejection")
    result = manager.add_memory(
        memory_text="I love programming in Python",  # Exact same content
        db=memory_db,
        user_id=test_user_id,
    )
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Similarity Score: {result.similarity_score}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")
    assert result.status == MemoryStorageStatus.DUPLICATE_EXACT
    assert not result.is_success
    assert result.is_rejected
    assert result.similarity_score == 1.0

    # Test 3: Empty content rejection
    print("\n❌ Test 3: Empty Content Rejection")
    result = manager.add_memory(
        memory_text="",  # Empty content
        db=memory_db,
        user_id=test_user_id,
    )
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")
    assert result.status == MemoryStorageStatus.CONTENT_EMPTY
    assert not result.is_success
    assert result.is_rejected

    # Test 4: Content too long rejection
    print("\n📏 Test 4: Content Too Long Rejection")
    long_content = "x" * 1000  # Exceeds default max length of 500
    result = manager.add_memory(
        memory_text=long_content,
        db=memory_db,
        user_id=test_user_id,
    )
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")
    assert result.status == MemoryStorageStatus.CONTENT_TOO_LONG
    assert not result.is_success
    assert result.is_rejected

    # Test 5: Semantic duplicate rejection
    print("\n🔍 Test 5: Semantic Duplicate Rejection")
    result = manager.add_memory(
        memory_text="I love programming with Python",  # Very similar (love vs love, programming vs programming)
        db=memory_db,
        user_id=test_user_id,
    )
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Similarity Score: {result.similarity_score}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")
    
    # Check if it's either semantic or exact duplicate (both are valid rejections)
    assert result.status in [MemoryStorageStatus.DUPLICATE_SEMANTIC, MemoryStorageStatus.DUPLICATE_EXACT]
    assert not result.is_success
    assert result.is_rejected
    assert result.similarity_score is not None and result.similarity_score > 0.7

    # Test 6: Another successful memory
    print("\n✅ Test 6: Another Successful Memory")
    result = manager.add_memory(
        memory_text="I work as a software engineer at Google",
        db=memory_db,
        user_id=test_user_id,
        topics=["work", "career"]
    )
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Memory ID: {result.memory_id}")
    print(f"Topics: {result.topics}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")
    assert result.status == MemoryStorageStatus.SUCCESS
    assert result.is_success
    assert not result.is_rejected

    print("\n🎉 All tests passed! The enum-based memory storage status system is working correctly.")
    
    # Clean up
    try:
        import os
        os.remove(db_path)
        print(f"🧹 Cleaned up test database: {db_path}")
    except:
        pass


if __name__ == "__main__":
    asyncio.run(test_enum_memory_status())
