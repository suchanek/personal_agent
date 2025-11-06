"""Test cognitive state mapping to confidence scores."""

import tempfile
from unittest.mock import MagicMock, Mock

import pytest

from personal_agent.core.agent_memory_manager import AgentMemoryManager
from personal_agent.core.enhanced_memory import EnhancedUserMemory
from personal_agent.core.semantic_memory_manager import (
    MemoryStorageResult,
    MemoryStorageStatus,
)
from personal_agent.core.user_model import User


class TestCognitiveStateConfidence:
    """Test that cognitive state is properly mapped to confidence scores."""

    @pytest.fixture
    def mock_agno_memory(self):
        """Create mock Agno memory system."""
        mock_mem = MagicMock()
        mock_mem.memory_manager = MagicMock()
        mock_mem.db = MagicMock()
        return mock_mem

    @pytest.fixture
    def memory_manager(self, mock_agno_memory):
        """Create memory manager with mocked dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AgentMemoryManager(
                user_id="test_user",
                storage_dir=tmpdir,
                agno_memory=mock_agno_memory,
                lightrag_url="http://localhost:9621",
                lightrag_memory_url="http://localhost:9622",
                enable_memory=True,
            )
            yield manager

    @pytest.mark.anyio
    async def test_proxy_memory_full_confidence(self, memory_manager, mock_agno_memory):
        """Test that proxy memories always get confidence=1.0."""
        # Mock successful storage
        mock_agno_memory.memory_manager.add_memory.return_value = MemoryStorageResult(
            status=MemoryStorageStatus.SUCCESS,
            message="Stored",
            memory_id="test_id",
            topics=["test"],
            local_success=True,
            graph_success=True,
        )

        # Create user with low cognitive state
        user = User(
            user_id="test",
            user_name="Test User",
            cognitive_state=25,  # 25/100 = 0.25
        )

        # Store proxy memory
        _ = await memory_manager.store_user_memory(
            content="Test proxy memory",
            topics=["test"],
            user=user,
            is_proxy=True,
            proxy_agent="TestAgent",
        )

        # Verify add_memory was called with confidence=1.0
        call_args = mock_agno_memory.memory_manager.add_memory.call_args
        assert call_args is not None
        assert call_args.kwargs["confidence"] == 1.0
        assert call_args.kwargs["is_proxy"] is True
        assert call_args.kwargs["proxy_agent"] == "TestAgent"

    @pytest.mark.anyio
    async def test_user_memory_cognitive_state_mapping(
        self, memory_manager, mock_agno_memory
    ):
        """Test that user memories map cognitive state to confidence."""
        # Mock successful storage
        mock_agno_memory.memory_manager.add_memory.return_value = MemoryStorageResult(
            status=MemoryStorageStatus.SUCCESS,
            message="Stored",
            memory_id="test_id",
            topics=["test"],
            local_success=True,
            graph_success=True,
        )

        test_cases = [
            (0, 0.0),  # cognitive_state=0 -> confidence=0.0
            (25, 0.25),  # cognitive_state=25 -> confidence=0.25
            (50, 0.5),  # cognitive_state=50 -> confidence=0.5
            (75, 0.75),  # cognitive_state=75 -> confidence=0.75
            (100, 1.0),  # cognitive_state=100 -> confidence=1.0
        ]

        for cognitive_state, expected_confidence in test_cases:
            # Create user with specific cognitive state
            user = User(
                user_id="test",
                user_name="Test User",
                cognitive_state=cognitive_state,
            )

            # Store user memory (not proxy, default confidence)
            await memory_manager.store_user_memory(
                content=f"Test memory with cognitive_state={cognitive_state}",
                topics=["test"],
                user=user,
                is_proxy=False,
            )

            # Verify add_memory was called with mapped confidence
            call_args = mock_agno_memory.memory_manager.add_memory.call_args
            assert call_args is not None
            assert (
                call_args.kwargs["confidence"] == expected_confidence
            ), f"Expected confidence={expected_confidence} for cognitive_state={cognitive_state}"
            assert call_args.kwargs["is_proxy"] is False

    @pytest.mark.anyio
    async def test_explicit_confidence_preserved(
        self, memory_manager, mock_agno_memory
    ):
        """Test that explicitly set confidence values are preserved."""
        # Mock successful storage
        mock_agno_memory.memory_manager.add_memory.return_value = MemoryStorageResult(
            status=MemoryStorageStatus.SUCCESS,
            message="Stored",
            memory_id="test_id",
            topics=["test"],
            local_success=True,
            graph_success=True,
        )

        # Create user with cognitive state that would map to 0.5
        user = User(
            user_id="test",
            user_name="Test User",
            cognitive_state=50,
        )

        # Store memory with explicit confidence=0.75
        await memory_manager.store_user_memory(
            content="Test memory with explicit confidence",
            topics=["test"],
            user=user,
            confidence=0.75,  # Explicitly set, should override cognitive state
            is_proxy=False,
        )

        # Verify add_memory was called with explicit confidence
        call_args = mock_agno_memory.memory_manager.add_memory.call_args
        assert call_args is not None
        assert (
            call_args.kwargs["confidence"] == 0.75
        ), "Explicit confidence should be preserved"
        assert call_args.kwargs["is_proxy"] is False

    @pytest.mark.anyio
    async def test_no_user_defaults_to_full_confidence(
        self, memory_manager, mock_agno_memory
    ):
        """Test that missing user defaults to confidence=1.0."""
        # Mock successful storage
        mock_agno_memory.memory_manager.add_memory.return_value = MemoryStorageResult(
            status=MemoryStorageStatus.SUCCESS,
            message="Stored",
            memory_id="test_id",
            topics=["test"],
            local_success=True,
            graph_success=True,
        )

        # Store memory without user
        await memory_manager.store_user_memory(
            content="Test memory without user",
            topics=["test"],
            user=None,  # No user provided
            is_proxy=False,
        )

        # Verify add_memory was called with confidence=1.0
        call_args = mock_agno_memory.memory_manager.add_memory.call_args
        assert call_args is not None
        assert (
            call_args.kwargs["confidence"] == 1.0
        ), "Missing user should default to confidence=1.0"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-k", "asyncio"])
