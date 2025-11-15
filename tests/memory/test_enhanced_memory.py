#!/usr/bin/env python3
"""
Tests for EnhancedUserMemory wrapper class.

This test suite verifies that the EnhancedUserMemory wrapper correctly
extends UserMemory with proxy tracking and confidence scoring while
maintaining backward compatibility.
"""

from datetime import datetime

import pytest
from agno.memory.v2.schema import UserMemory

from personal_agent.core.enhanced_memory import (
    EnhancedUserMemory,
    ensure_enhanced_memory,
    extract_user_memory,
)


def test_enhanced_memory_creation():
    """Test creating an EnhancedUserMemory from scratch."""
    base_memory = UserMemory(
        memory="Test memory content",
        topics=["test", "memory"],
        memory_id="test-123",
    )

    enhanced = EnhancedUserMemory(
        base_memory=base_memory,
        confidence=0.85,
        is_proxy=True,
        proxy_agent="TestAgent",
    )

    assert enhanced.memory == "Test memory content"
    assert enhanced.topics == ["test", "memory"]
    assert enhanced.memory_id == "test-123"
    assert enhanced.confidence == 0.85
    assert enhanced.is_proxy is True
    assert enhanced.proxy_agent == "TestAgent"


def test_enhanced_memory_from_user_memory():
    """Test creating EnhancedUserMemory from existing UserMemory."""
    user_memory = UserMemory(
        memory="Another test",
        topics=["conversion"],
        memory_id="test-456",
    )

    enhanced = EnhancedUserMemory.from_user_memory(
        user_memory,
        confidence=0.95,
        is_proxy=False,
    )

    assert enhanced.memory == "Another test"
    assert enhanced.topics == ["conversion"]
    assert enhanced.confidence == 0.95
    assert enhanced.is_proxy is False
    assert enhanced.proxy_agent is None


def test_enhanced_memory_serialization():
    """Test to_dict() includes enhanced fields."""
    base_memory = UserMemory(
        memory="Serialization test",
        topics=["serialization"],
        memory_id="ser-123",
    )

    enhanced = EnhancedUserMemory(
        base_memory=base_memory,
        confidence=0.75,
        is_proxy=True,
        proxy_agent="ProxyBot",
    )

    data = enhanced.to_dict()

    assert "memory" in data
    assert data["memory"] == "Serialization test"
    assert "topics" in data
    assert data["topics"] == ["serialization"]
    assert "memory_id" in data
    assert data["memory_id"] == "ser-123"
    assert "confidence" in data
    assert data["confidence"] == 0.75
    assert "is_proxy" in data
    assert data["is_proxy"] is True
    assert "proxy_agent" in data
    assert data["proxy_agent"] == "ProxyBot"


def test_enhanced_memory_deserialization():
    """Test from_dict() correctly reconstructs EnhancedUserMemory."""
    data = {
        "memory": "Deserialization test",
        "topics": ["deser"],
        "memory_id": "deser-789",
        "confidence": 0.90,
        "is_proxy": False,
        "proxy_agent": None,
    }

    enhanced = EnhancedUserMemory.from_dict(data)

    assert enhanced.memory == "Deserialization test"
    assert enhanced.topics == ["deser"]
    assert enhanced.memory_id == "deser-789"
    assert enhanced.confidence == 0.90
    assert enhanced.is_proxy is False
    assert enhanced.proxy_agent is None


def test_enhanced_memory_backward_compatibility():
    """Test that from_dict() works with old UserMemory data (no enhanced fields)."""
    # Old format without enhanced fields
    data = {
        "memory": "Old format memory",
        "topics": ["legacy"],
        "memory_id": "old-123",
    }

    enhanced = EnhancedUserMemory.from_dict(data)

    assert enhanced.memory == "Old format memory"
    assert enhanced.topics == ["legacy"]
    assert enhanced.memory_id == "old-123"
    # Check default values for enhanced fields
    assert enhanced.confidence == 1.0
    assert enhanced.is_proxy is False
    assert enhanced.proxy_agent is None


def test_extract_user_memory():
    """Test extracting base UserMemory from EnhancedUserMemory."""
    base_memory = UserMemory(
        memory="Extract test",
        topics=["extract"],
        memory_id="ext-123",
    )

    enhanced = EnhancedUserMemory(
        base_memory=base_memory,
        confidence=0.80,
        is_proxy=True,
        proxy_agent="ExtractBot",
    )

    extracted = extract_user_memory(enhanced)

    assert isinstance(extracted, UserMemory)
    assert extracted.memory == "Extract test"
    assert extracted.topics == ["extract"]
    assert extracted.memory_id == "ext-123"
    # Enhanced fields should not be in base UserMemory
    assert not hasattr(extracted, "confidence")
    assert not hasattr(extracted, "is_proxy")
    assert not hasattr(extracted, "proxy_agent")


def test_extract_user_memory_passthrough():
    """Test that extract_user_memory passes through plain UserMemory."""
    user_memory = UserMemory(
        memory="Passthrough test",
        topics=["pass"],
        memory_id="pass-123",
    )

    extracted = extract_user_memory(user_memory)

    assert extracted is user_memory  # Should be the same object
    assert isinstance(extracted, UserMemory)


def test_ensure_enhanced_memory_with_user_memory():
    """Test ensure_enhanced_memory converts UserMemory to EnhancedUserMemory."""
    user_memory = UserMemory(
        memory="Ensure test",
        topics=["ensure"],
        memory_id="ens-123",
    )

    enhanced = ensure_enhanced_memory(
        user_memory, confidence=0.88, is_proxy=True, proxy_agent="EnsureBot"
    )

    assert isinstance(enhanced, EnhancedUserMemory)
    assert enhanced.memory == "Ensure test"
    assert enhanced.confidence == 0.88
    assert enhanced.is_proxy is True
    assert enhanced.proxy_agent == "EnsureBot"


def test_ensure_enhanced_memory_with_enhanced_memory():
    """Test ensure_enhanced_memory passes through EnhancedUserMemory."""
    base_memory = UserMemory(
        memory="Already enhanced",
        topics=["enhanced"],
        memory_id="enh-123",
    )

    enhanced = EnhancedUserMemory(
        base_memory=base_memory,
        confidence=0.92,
        is_proxy=False,
    )

    result = ensure_enhanced_memory(enhanced)

    assert result is enhanced  # Should be the same object
    assert isinstance(result, EnhancedUserMemory)


def test_property_setters():
    """Test that property setters work correctly."""
    base_memory = UserMemory(
        memory="Original",
        topics=["original"],
        memory_id="orig-123",
    )

    enhanced = EnhancedUserMemory(base_memory=base_memory)

    # Test setters
    enhanced.memory = "Modified"
    enhanced.topics = ["modified", "updated"]
    enhanced.memory_id = "mod-456"

    assert enhanced.memory == "Modified"
    assert enhanced.topics == ["modified", "updated"]
    assert enhanced.memory_id == "mod-456"
    assert enhanced.base_memory.memory == "Modified"
    assert enhanced.base_memory.topics == ["modified", "updated"]
    assert enhanced.base_memory.memory_id == "mod-456"


def test_roundtrip_serialization():
    """Test that serialize->deserialize preserves all data."""
    original = EnhancedUserMemory(
        base_memory=UserMemory(
            memory="Roundtrip test",
            topics=["roundtrip", "test"],
            memory_id="rt-123",
            last_updated=datetime.now(),
        ),
        confidence=0.77,
        is_proxy=True,
        proxy_agent="RoundtripBot",
    )

    # Serialize
    data = original.to_dict()

    # Deserialize
    restored = EnhancedUserMemory.from_dict(data)

    # Compare
    assert restored.memory == original.memory
    assert restored.topics == original.topics
    assert restored.memory_id == original.memory_id
    assert restored.confidence == original.confidence
    assert restored.is_proxy == original.is_proxy
    assert restored.proxy_agent == original.proxy_agent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
