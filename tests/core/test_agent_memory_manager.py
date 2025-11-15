"""
Unit tests for AgentMemoryManager.

This module tests the memory management functionality
extracted from the AgnoPersonalAgent class using Python's built-in unittest framework.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from src.personal_agent.core.agent_memory_manager import AgentMemoryManager
from src.personal_agent.core.semantic_memory_manager import (
    MemoryStorageResult,
    MemoryStorageStatus,
)


class TestAgentMemoryManager(unittest.TestCase):
    """Test cases for AgentMemoryManager."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.user_id = "test_user"
        self.storage_dir = "/tmp/test_storage"
        self.lightrag_url = "http://localhost:8020"
        self.lightrag_memory_url = "http://localhost:8021"

        self.manager = AgentMemoryManager(
            user_id=self.user_id,
            storage_dir=self.storage_dir,
            lightrag_url=self.lightrag_url,
            lightrag_memory_url=self.lightrag_memory_url,
            enable_memory=True,
        )

    def test_init(self):
        """Test AgentMemoryManager initialization."""
        self.assertEqual(self.manager.user_id, self.user_id)
        self.assertEqual(self.manager.storage_dir, self.storage_dir)
        self.assertEqual(self.manager.lightrag_url, self.lightrag_url)
        self.assertEqual(self.manager.lightrag_memory_url, self.lightrag_memory_url)
        self.assertTrue(self.manager.enable_memory)
        self.assertIsNone(self.manager.agno_memory)

    def test_init_with_disabled_memory(self):
        """Test initialization with memory disabled."""
        manager = AgentMemoryManager(
            user_id="test_user", storage_dir="/tmp/test", enable_memory=False
        )

        self.assertFalse(manager.enable_memory)
        self.assertIsNone(manager.lightrag_url)
        self.assertIsNone(manager.lightrag_memory_url)

    def test_initialize(self):
        """Test memory manager initialization with agno_memory."""
        mock_agno_memory = Mock()

        self.manager.initialize(mock_agno_memory)

        self.assertEqual(self.manager.agno_memory, mock_agno_memory)

    def test_direct_search_memories_no_agno_memory(self):
        """Test direct search when agno_memory is not initialized."""
        result = self.manager.direct_search_memories("test query")

        self.assertEqual(result, [])

    def test_direct_search_memories_with_agno_memory(self):
        """Test direct search with initialized agno_memory."""
        # Mock agno_memory and its components
        mock_agno_memory = Mock()
        mock_memory_manager = Mock()
        mock_db = Mock()

        mock_agno_memory.memory_manager = mock_memory_manager
        mock_agno_memory.db = mock_db

        # Mock search results
        mock_results = [("memory1", 0.8), ("memory2", 0.6)]
        mock_memory_manager.search_memories.return_value = mock_results

        self.manager.initialize(mock_agno_memory)

        result = self.manager.direct_search_memories(
            "test query", limit=5, similarity_threshold=0.5
        )

        # Verify the search was called correctly
        mock_memory_manager.search_memories.assert_called_once_with(
            query="test query",
            db=mock_db,
            user_id=self.user_id,
            limit=5,
            similarity_threshold=0.5,
            search_topics=True,
            topic_boost=0.5,
        )

        self.assertEqual(result, mock_results)

    def test_direct_search_memories_exception(self):
        """Test direct search when an exception occurs."""
        # Mock agno_memory that raises an exception
        mock_agno_memory = Mock()
        mock_memory_manager = Mock()
        mock_memory_manager.search_memories.side_effect = Exception("Search failed")
        mock_agno_memory.memory_manager = mock_memory_manager
        mock_agno_memory.db = Mock()

        self.manager.initialize(mock_agno_memory)

        result = self.manager.direct_search_memories("test query")

        self.assertEqual(result, [])

    def test_restate_user_fact(self):
        """Test restating user facts from first to third person (for graph storage)."""
        test_cases = [
            ("I am a developer", "test_user is a developer"),
            ("I have a dog", "test_user has a dog"),
            ("I'm working on a project", "test_user is working on a project"),
            ("I've completed the task", "test_user has completed the task"),
            ("My favorite color is blue", "test_user's favorite color is blue"),
            ("This is mine", "This is test_user's"),
            ("I did it myself", "test_user did it test_user"),
            # New tests for verb conjugation
            ("I love programming", "test_user loves programming"),
            ("I work at Google", "test_user works at Google"),
            ("I enjoy hiking", "test_user enjoys hiking"),
            ("I go running every day", "test_user goes running every day"),
            ("I do yoga in the morning", "test_user does yoga in the morning"),
            ("I study machine learning", "test_user studies machine learning"),
            ("I play guitar", "test_user plays guitar"),
            ("I watch movies", "test_user watches movies"),
            ("I teach programming", "test_user teaches programming"),
            ("I carry a backpack", "test_user carries a backpack"),
        ]

        for input_text, expected_output in test_cases:
            with self.subTest(input_text=input_text):
                result = self.manager.restate_user_fact(input_text)
                self.assertEqual(result, expected_output)

    def test_restate_to_second_person(self):
        """Test restating user facts from first to second person (for local storage)."""
        test_cases = [
            ("I am a developer", "you are a developer"),
            ("I have a dog", "you have a dog"),
            ("I was happy", "you were happy"),
            ("I'm working on a project", "you're working on a project"),
            ("I've completed the task", "you've completed the task"),
            ("I'll finish tomorrow", "you'll finish tomorrow"),
            ("I'd like to help", "you'd like to help"),
            ("My favorite color is blue", "your favorite color is blue"),
            ("This is mine", "This is yours"),
            ("I did it myself", "you did it yourself"),
            ("Tell me about it", "Tell you about it"),
        ]

        for input_text, expected_output in test_cases:
            with self.subTest(input_text=input_text):
                result = self.manager.restate_to_second_person(input_text)
                self.assertEqual(result, expected_output)

    def test_restate_user_fact_case_insensitive(self):
        """Test that restatement works with different cases."""
        test_cases = [
            ("i am happy", "test_user is happy"),
            ("I AM HAPPY", "test_user is HAPPY"),
            ("My dog is cute", "test_user's dog is cute"),
            ("MY DOG IS CUTE", "test_user's DOG IS CUTE"),
        ]

        for input_text, expected_output in test_cases:
            with self.subTest(input_text=input_text):
                result = self.manager.restate_user_fact(input_text)
                self.assertEqual(result, expected_output)

    def test_restate_user_fact_word_boundaries(self):
        """Test that restatement respects word boundaries."""
        # These should NOT be changed because they're not complete words
        test_cases = [
            ("mining is fun", "mining is fun"),  # "mine" in "mining" should not change
            (
                "imagination is key",
                "imagination is key",
            ),  # "I" in "imagination" should not change
        ]

        for input_text, expected_output in test_cases:
            with self.subTest(input_text=input_text):
                result = self.manager.restate_user_fact(input_text)
                self.assertEqual(result, expected_output)


class TestAgentMemoryManagerAsync(unittest.IsolatedAsyncioTestCase):
    """Async test cases for AgentMemoryManager."""

    async def asyncSetUp(self):
        """Set up async test fixtures."""
        self.user_id = "test_user"
        self.storage_dir = "/tmp/test_storage"
        self.lightrag_url = "http://localhost:8020"
        self.lightrag_memory_url = "http://localhost:8021"

        self.manager = AgentMemoryManager(
            user_id=self.user_id,
            storage_dir=self.storage_dir,
            lightrag_url=self.lightrag_url,
            lightrag_memory_url=self.lightrag_memory_url,
            enable_memory=True,
        )

        # Mock agno_memory
        self.mock_agno_memory = Mock()
        self.mock_memory_manager = Mock()
        self.mock_db = Mock()

        self.mock_agno_memory.memory_manager = self.mock_memory_manager
        self.mock_agno_memory.db = self.mock_db

        self.manager.initialize(self.mock_agno_memory)

    async def test_store_user_memory_empty_content(self):
        """Test storing memory with empty content."""
        result = await self.manager.store_user_memory("")

        self.assertEqual(result.status, MemoryStorageStatus.CONTENT_EMPTY)
        self.assertFalse(result.is_success)
        self.assertIn("Content is required", result.message)

    async def test_store_user_memory_success(self):
        """Test successful memory storage."""
        # Mock successful local storage
        mock_local_result = MemoryStorageResult(
            status=MemoryStorageStatus.SUCCESS,
            message="Memory stored successfully",
            memory_id="mem_123",
            topics=["test"],
            local_success=True,
            graph_success=False,
        )
        self.mock_memory_manager.add_memory.return_value = mock_local_result

        # Mock successful graph storage
        with patch.object(
            self.manager, "store_graph_memory", new_callable=AsyncMock
        ) as mock_store_graph:
            mock_store_graph.return_value = "✅ Graph memory synced successfully"

            result = await self.manager.store_user_memory(
                "I love programming", ["test"]
            )

            # Verify local storage was called with enhanced parameters (second-person)
            self.mock_memory_manager.add_memory.assert_called_once_with(
                memory_text="you love programming",  # Second-person restatement
                db=self.mock_db,
                user_id=self.user_id,
                topics=["test"],
                custom_timestamp=None,
                confidence=1.0,
                is_proxy=False,
                proxy_agent=None,
            )

            # Verify graph storage was called with third-person restatement
            mock_store_graph.assert_called_once_with(
                "test_user loves programming",
                ["test"],
                "mem_123",  # Proper verb conjugation!
            )

            # Verify result
            self.assertEqual(result.status, MemoryStorageStatus.SUCCESS)
            self.assertTrue(result.is_success)
            self.assertTrue(result.local_success)
            self.assertTrue(result.graph_success)

    async def test_store_user_memory_local_only(self):
        """Test memory storage when graph storage fails."""
        # Mock successful local storage
        mock_local_result = MemoryStorageResult(
            status=MemoryStorageStatus.SUCCESS,
            message="Memory stored successfully",
            memory_id="mem_123",
            topics=["test"],
            local_success=True,
            graph_success=False,
        )
        self.mock_memory_manager.add_memory.return_value = mock_local_result

        # Mock failed graph storage
        with patch.object(
            self.manager, "store_graph_memory", new_callable=AsyncMock
        ) as mock_store_graph:
            mock_store_graph.return_value = "❌ Graph storage failed"

            result = await self.manager.store_user_memory("Test memory content")

            # Verify result
            self.assertEqual(result.status, MemoryStorageStatus.SUCCESS_LOCAL_ONLY)
            self.assertTrue(result.is_success)
            self.assertTrue(result.local_success)
            self.assertFalse(result.graph_success)

    async def test_store_user_memory_duplicate_rejection(self):
        """Test memory storage when duplicate is detected."""
        # Mock duplicate rejection from local storage
        mock_local_result = MemoryStorageResult(
            status=MemoryStorageStatus.DUPLICATE_EXACT,
            message="Duplicate memory detected",
            local_success=False,
            graph_success=False,
            similarity_score=1.0,
        )
        self.mock_memory_manager.add_memory.return_value = mock_local_result

        result = await self.manager.store_user_memory("Duplicate content")

        # Should return the rejection directly
        self.assertEqual(result.status, MemoryStorageStatus.DUPLICATE_EXACT)
        self.assertFalse(result.is_success)
        self.assertEqual(result.similarity_score, 1.0)

    async def test_store_user_memory_topic_handling(self):
        """Test different topic input formats."""
        mock_local_result = MemoryStorageResult(
            status=MemoryStorageStatus.SUCCESS,
            message="Memory stored successfully",
            memory_id="mem_123",
            topics=["topic1", "topic2"],
            local_success=True,
            graph_success=False,
        )
        self.mock_memory_manager.add_memory.return_value = mock_local_result

        with patch.object(self.manager, "store_graph_memory", new_callable=AsyncMock):
            # Test string with commas
            await self.manager.store_user_memory(
                "Test content", "topic1, topic2, topic3"
            )
            call_args = self.mock_memory_manager.add_memory.call_args
            self.assertEqual(call_args[1]["topics"], ["topic1", "topic2", "topic3"])

            # Reset mock
            self.mock_memory_manager.add_memory.reset_mock()

            # Test single string
            await self.manager.store_user_memory("Test content", "single_topic")
            call_args = self.mock_memory_manager.add_memory.call_args
            self.assertEqual(call_args[1]["topics"], ["single_topic"])

            # Reset mock
            self.mock_memory_manager.add_memory.reset_mock()

            # Test list
            await self.manager.store_user_memory(
                "Test content", ["list_topic1", "list_topic2"]
            )
            call_args = self.mock_memory_manager.add_memory.call_args
            self.assertEqual(call_args[1]["topics"], ["list_topic1", "list_topic2"])

    async def test_query_memory_empty_query(self):
        """Test querying memory with empty query."""
        result = await self.manager.query_memory("")

        self.assertIn("Query cannot be empty", result)
        self.assertIn("❌", result)

    async def test_query_memory_generic_queries(self):
        """Test that generic queries delegate to list_all_memories."""
        with patch.object(
            self.manager, "list_all_memories", new_callable=AsyncMock
        ) as mock_list_all:
            mock_list_all.return_value = "All memories result"

            generic_queries = ["all", "everything", "what do you know about me"]

            for query in generic_queries:
                with self.subTest(query=query):
                    result = await self.manager.query_memory(query)
                    mock_list_all.assert_called()
                    self.assertEqual(result, "All memories result")
                    mock_list_all.reset_mock()

    async def test_query_memory_specific_search(self):
        """Test querying memory with specific search terms."""
        # Mock search results
        mock_memory = Mock()
        mock_memory.memory = "I like programming"
        mock_memory.topics = ["programming", "interests"]

        mock_results = [(mock_memory, 0.8)]
        self.mock_memory_manager.search_memories.return_value = mock_results

        result = await self.manager.query_memory("programming interests")

        # Verify search was called correctly
        self.mock_memory_manager.search_memories.assert_called_once_with(
            query="programming interests",
            db=self.mock_db,
            user_id=self.user_id,
            limit=None,
            similarity_threshold=0.3,
            search_topics=True,
            topic_boost=0.5,
        )

        # Verify result format
        self.assertIn("MEMORY RETRIEVAL", result)
        self.assertIn("I like programming", result)
        self.assertIn("similarity: 0.80", result)
        self.assertIn("programming, interests", result)

    async def test_query_memory_no_results(self):
        """Test querying memory when no results are found."""
        self.mock_memory_manager.search_memories.return_value = []

        result = await self.manager.query_memory("nonexistent topic")

        self.assertIn("No memories found", result)
        self.assertIn("🔍", result)

    async def test_get_all_memories(self):
        """Test getting all memories."""
        # Mock memory objects
        mock_memory1 = Mock()
        mock_memory1.memory = "First memory"
        mock_memory1.topics = ["topic1"]
        mock_memory1.timestamp = 1640995200  # 2022-01-01
        mock_memory1.memory_id = "mem_1"  # Changed from id to memory_id

        mock_memory2 = Mock()
        mock_memory2.memory = "Second memory"
        mock_memory2.topics = ["topic2"]
        mock_memory2.timestamp = 1641081600  # 2022-01-02
        mock_memory2.memory_id = "mem_2"  # Changed from id to memory_id

        self.mock_memory_manager.get_all_memories.return_value = [
            mock_memory1,
            mock_memory2,
        ]

        result = await self.manager.get_all_memories()

        # Verify the call
        self.mock_memory_manager.get_all_memories.assert_called_once_with(
            db=self.mock_db, user_id=self.user_id
        )

        # Verify result format
        self.assertIn("ALL MEMORIES (2 total)", result)
        self.assertIn("Second memory", result)  # Should be first (newest)
        self.assertIn("First memory", result)
        self.assertIn("topic1", result)
        self.assertIn("topic2", result)
        self.assertIn("mem_1", result)
        self.assertIn("mem_2", result)

    async def test_get_all_memories_empty(self):
        """Test getting all memories when none exist."""
        self.mock_memory_manager.get_all_memories.return_value = []

        result = await self.manager.get_all_memories()

        self.assertIn("No memories found", result)
        self.assertIn("🔍", result)

    async def test_update_memory(self):
        """Test updating an existing memory."""
        self.mock_memory_manager.update_memory.return_value = (
            True,
            "Memory updated successfully",
        )

        result = await self.manager.update_memory(
            "mem_123", "Updated content", ["new_topic"]
        )

        # Verify the call
        self.mock_memory_manager.update_memory.assert_called_once_with(
            memory_id="mem_123",
            memory_text="Updated content",
            db=self.mock_db,
            user_id=self.user_id,
            topics=["new_topic"],
        )

        # Verify result
        self.assertIn("✅", result)
        self.assertIn("Successfully updated memory", result)

    async def test_update_memory_failure(self):
        """Test updating memory when it fails."""
        self.mock_memory_manager.update_memory.return_value = (
            False,
            "Memory not found",
        )

        result = await self.manager.update_memory("mem_123", "Updated content")

        self.assertIn("❌", result)
        self.assertIn("Error updating memory", result)
        self.assertIn("Memory not found", result)

    @patch("aiohttp.ClientSession")
    async def test_clear_all_memories(self, mock_session_class):
        """Test clearing all memories from both systems."""
        # Mock local memory clearing
        self.mock_memory_manager.clear_memories.return_value = (
            True,
            "Local memories cleared",
        )

        # Mock HTTP session for LightRAG operations
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        # Mock getting documents response
        mock_get_response = AsyncMock()
        mock_get_response.status = 200
        mock_get_response.json = AsyncMock(
            return_value={"statuses": {"indexed": [{"id": "doc1"}, {"id": "doc2"}]}}
        )

        # Mock deleting documents response
        mock_delete_response = AsyncMock()
        mock_delete_response.status = 200

        # Set up the async context manager properly
        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__ = AsyncMock(return_value=mock_get_response)
        mock_get_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_delete_ctx = AsyncMock()
        mock_delete_ctx.__aenter__ = AsyncMock(return_value=mock_delete_response)
        mock_delete_ctx.__aexit__ = AsyncMock(return_value=None)

        # Configure session.get and session.delete to return the context managers
        mock_session.get = Mock(return_value=mock_get_ctx)
        mock_session.delete = Mock(return_value=mock_delete_ctx)

        result = await self.manager.clear_all_memories()

        # Verify local clearing was called
        self.mock_memory_manager.clear_memories.assert_called_once_with(
            db=self.mock_db, user_id=self.user_id
        )

        # Verify result contains both operations
        self.assertIn("Local memory: All memories cleared successfully", result)
        self.assertIn("Graph memory: All memories cleared successfully", result)


class TestAgentMemoryManagerIntegration(unittest.TestCase):
    """Integration tests for AgentMemoryManager."""

    def test_memory_manager_with_realistic_config(self):
        """Test memory manager with realistic configuration."""
        manager = AgentMemoryManager(
            user_id="john_doe",
            storage_dir="/home/john_doe/.personal_agent",
            lightrag_url="http://localhost:8020",
            lightrag_memory_url="http://localhost:8021",
            enable_memory=True,
        )

        self.assertEqual(manager.user_id, "john_doe")
        self.assertEqual(manager.storage_dir, "/home/john_doe/.personal_agent")
        self.assertTrue(manager.enable_memory)

    def test_memory_manager_minimal_config(self):
        """Test memory manager with minimal configuration."""
        manager = AgentMemoryManager(
            user_id="test_user", storage_dir="/tmp/test", enable_memory=False
        )

        self.assertEqual(manager.user_id, "test_user")
        self.assertFalse(manager.enable_memory)
        self.assertIsNone(manager.lightrag_url)
        self.assertIsNone(manager.lightrag_memory_url)


if __name__ == "__main__":
    unittest.main()
