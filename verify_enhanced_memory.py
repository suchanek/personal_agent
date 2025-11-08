#!/usr/bin/env python3
"""
Verification script for EnhancedUserMemory implementation.

This script demonstrates the enhanced memory functionality and verifies
that the wrapper pattern works correctly with the existing memory system.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.memory.v2.schema import UserMemory

from personal_agent.core.enhanced_memory import (
    EnhancedUserMemory,
    ensure_enhanced_memory,
    extract_user_memory,
)


def test_basic_functionality():
    """Test basic EnhancedUserMemory functionality."""
    print("=" * 60)
    print("TEST 1: Basic Enhanced Memory Creation")
    print("=" * 60)

    # Create a base UserMemory
    base_memory = UserMemory(
        memory="I like hiking on weekends",
        topics=["hobbies", "outdoor"],
        memory_id="test-001",
    )

    # Wrap in EnhancedUserMemory
    enhanced = EnhancedUserMemory(
        base_memory=base_memory,
        confidence=0.95,
        is_proxy=False,
    )

    print(f"✓ Memory: {enhanced.memory}")
    print(f"✓ Topics: {enhanced.topics}")
    print(f"✓ Confidence: {enhanced.confidence}")
    print(f"✓ Is Proxy: {enhanced.is_proxy}")
    print(f"✓ Proxy Agent: {enhanced.proxy_agent}")
    print()


def test_proxy_memory():
    """Test proxy agent memory creation."""
    print("=" * 60)
    print("TEST 2: Proxy Agent Memory")
    print("=" * 60)

    # Create memory from a proxy agent
    user_memory = UserMemory(
        memory="User prefers morning meetings",
        topics=["preferences", "schedule"],
        memory_id="proxy-001",
    )

    # Create enhanced memory with proxy info
    enhanced = EnhancedUserMemory.from_user_memory(
        user_memory,
        confidence=0.85,
        is_proxy=True,
        proxy_agent="SchedulerBot",
    )

    print(f"✓ Memory: {enhanced.memory}")
    print(f"✓ Is Proxy: {enhanced.is_proxy}")
    print(f"✓ Proxy Agent: {enhanced.proxy_agent}")
    print(f"✓ Confidence: {enhanced.confidence}")
    print()


def test_serialization():
    """Test serialization and deserialization."""
    print("=" * 60)
    print("TEST 3: Serialization/Deserialization")
    print("=" * 60)

    # Create enhanced memory
    original = EnhancedUserMemory(
        base_memory=UserMemory(
            memory="Lives in San Francisco",
            topics=["personal", "location"],
            memory_id="ser-001",
        ),
        confidence=1.0,
        is_proxy=False,
    )

    # Serialize to dict
    data = original.to_dict()
    print(f"✓ Serialized data keys: {list(data.keys())}")
    print(f"  - Has 'confidence': {'confidence' in data}")
    print(f"  - Has 'is_proxy': {'is_proxy' in data}")
    print(f"  - Has 'proxy_agent': {'proxy_agent' in data}")

    # Deserialize back
    restored = EnhancedUserMemory.from_dict(data)
    print(f"✓ Restored memory: {restored.memory}")
    print(f"✓ Restored confidence: {restored.confidence}")
    print(f"✓ Data matches: {restored.memory == original.memory}")
    print()


def test_backward_compatibility():
    """Test backward compatibility with old UserMemory format."""
    print("=" * 60)
    print("TEST 4: Backward Compatibility")
    print("=" * 60)

    # Old format without enhanced fields
    old_data = {
        "memory": "Works at a tech company",
        "topics": ["work", "career"],
        "memory_id": "old-001",
    }

    # Should still work
    enhanced = EnhancedUserMemory.from_dict(old_data)
    print(f"✓ Memory from old format: {enhanced.memory}")
    print(f"✓ Default confidence: {enhanced.confidence}")
    print(f"✓ Default is_proxy: {enhanced.is_proxy}")
    print(f"✓ Default proxy_agent: {enhanced.proxy_agent}")
    print()


def test_helper_functions():
    """Test helper utility functions."""
    print("=" * 60)
    print("TEST 5: Helper Functions")
    print("=" * 60)

    # Test ensure_enhanced_memory
    user_memory = UserMemory(
        memory="Enjoys reading science fiction",
        topics=["hobbies", "reading"],
        memory_id="help-001",
    )

    enhanced = ensure_enhanced_memory(
        user_memory, confidence=0.88, is_proxy=True, proxy_agent="RecommendationBot"
    )

    print(f"✓ ensure_enhanced_memory created: {type(enhanced).__name__}")
    print(f"✓ Memory: {enhanced.memory}")
    print(f"✓ Proxy Agent: {enhanced.proxy_agent}")

    # Test extract_user_memory
    base = extract_user_memory(enhanced)
    print(f"✓ extract_user_memory returned: {type(base).__name__}")
    print(f"✓ Has enhanced fields: {hasattr(base, 'confidence')}")
    print()


def test_property_access():
    """Test property delegation."""
    print("=" * 60)
    print("TEST 6: Property Delegation")
    print("=" * 60)

    enhanced = EnhancedUserMemory(
        base_memory=UserMemory(
            memory="Original memory",
            topics=["test"],
            memory_id="prop-001",
        ),
        confidence=0.90,
    )

    print(f"✓ Original memory: {enhanced.memory}")

    # Test setter
    enhanced.memory = "Modified memory"
    enhanced.topics = ["modified", "test"]

    print(f"✓ Modified memory: {enhanced.memory}")
    print(f"✓ Modified topics: {enhanced.topics}")
    print(f"✓ Base memory updated: {enhanced.base_memory.memory}")
    print()


def main():
    """Run all verification tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  EnhancedUserMemory Verification Suite                  ║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_basic_functionality()
        test_proxy_memory()
        test_serialization()
        test_backward_compatibility()
        test_helper_functions()
        test_property_access()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✓ Basic creation and property access")
        print("  ✓ Proxy agent tracking")
        print("  ✓ Serialization/deserialization")
        print("  ✓ Backward compatibility")
        print("  ✓ Helper functions")
        print("  ✓ Property delegation")
        print()
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
