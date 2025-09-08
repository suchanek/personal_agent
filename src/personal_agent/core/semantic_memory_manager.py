#!/usr/bin/env python3
"""
Semantic Memory Manager - LLM-free memory management with semantic search and duplicate detection.

This module provides a semantic search driven memory manager that does NOT invoke the LLM.
It combines the Pydantic Agno MemoryManager structure with our AntiDuplicate class capabilities
to build a classifier with a simpler method to determine the topic of the sentence and if the
statement/memory is a duplicate.
"""

import difflib
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from agno.memory.v2.db.base import MemoryDb, MemoryRow
from agno.memory.v2.schema import UserMemory
from agno.models.base import Model
from pydantic import BaseModel, Field

from ..config import get_current_user_id
from ..utils import setup_logging
from .topic_classifier import TopicClassifier

logger = setup_logging(__name__)


class MemoryStorageStatus(Enum):
    """Enum for memory storage operation results."""

    SUCCESS = auto()  # Memory stored successfully in both systems
    SUCCESS_LOCAL_ONLY = auto()  # Stored in local SQLite, graph sync failed
    DUPLICATE_EXACT = auto()  # Rejected: exact duplicate found
    DUPLICATE_SEMANTIC = auto()  # Rejected: semantic duplicate found
    CONTENT_EMPTY = auto()  # Rejected: empty or invalid content
    CONTENT_TOO_LONG = auto()  # Rejected: content exceeds max length
    STORAGE_ERROR = auto()  # Error: database/storage failure
    VALIDATION_ERROR = auto()  # Error: input validation failed


@dataclass
class MemoryStorageResult:
    """Structured result for memory storage operations."""

    status: MemoryStorageStatus
    message: str
    memory_id: Optional[str] = None
    topics: Optional[List[str]] = None
    local_success: bool = False
    graph_success: bool = False
    similarity_score: Optional[float] = None

    @property
    def is_success(self) -> bool:
        """True if memory was stored (fully or partially)."""
        return self.status in [
            MemoryStorageStatus.SUCCESS,
            MemoryStorageStatus.SUCCESS_LOCAL_ONLY,
        ]

    @property
    def is_rejected(self) -> bool:
        """True if memory was rejected (duplicate, validation, etc.)."""
        return self.status in [
            MemoryStorageStatus.DUPLICATE_EXACT,
            MemoryStorageStatus.DUPLICATE_SEMANTIC,
            MemoryStorageStatus.CONTENT_EMPTY,
            MemoryStorageStatus.CONTENT_TOO_LONG,
            MemoryStorageStatus.VALIDATION_ERROR,
        ]


class SemanticDuplicateDetector:
    """Semantic duplicate detection without LLM using advanced text similarity."""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower().strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common punctuation
        text = re.sub(r"[.,!?;:]", "", text)

        return text

    def _extract_key_terms(self, text: str) -> Set[str]:
        """Extract key terms from text for semantic comparison."""
        normalized = self._normalize_text(text)

        # Split into words
        words = normalized.split()

        # Remove common stop words
        stop_words = {
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "your",
            "yours",
            "yourself",
            "yourselves",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "her",
            "hers",
            "herself",
            "it",
            "its",
            "itself",
            "they",
            "them",
            "their",
            "theirs",
            "themselves",
            "what",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "these",
            "those",
            "am",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "having",
            "do",
            "does",
            "did",
            "doing",
            "a",
            "an",
            "the",
            "and",
            "but",
            "if",
            "or",
            "because",
            "as",
            "until",
            "while",
            "of",
            "at",
            "by",
            "for",
            "with",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "up",
            "down",
            "in",
            "out",
            "on",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
        }

        key_terms = {word for word in words if word not in stop_words and len(word) > 2}
        return key_terms

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts with improved exact word matching."""
        # Normalize texts
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)

        # Check for exact word matches (NEW: improved for search queries)
        words1 = set(re.findall(r"\b\w+\b", norm1))
        words2 = set(re.findall(r"\b\w+\b", norm2))
        exact_matches = words1.intersection(words2)

        # If we have exact word matches, boost the score significantly
        if exact_matches and len(words1) <= 3:  # For short queries (1-3 words)
            match_ratio = len(exact_matches) / len(words1)
            exact_word_score = 0.6 + (match_ratio * 0.4)  # 0.6 to 1.0 range

            # Also calculate traditional semantic similarity
            string_similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
            terms1 = self._extract_key_terms(text1)
            terms2 = self._extract_key_terms(text2)

            if not terms1 and not terms2:
                terms_similarity = 1.0
            elif not terms1 or not terms2:
                terms_similarity = 0.0
            else:
                intersection = len(terms1.intersection(terms2))
                union = len(terms1.union(terms2))
                terms_similarity = intersection / union if union > 0 else 0.0

            traditional_score = (string_similarity * 0.6) + (terms_similarity * 0.4)

            # Return the higher of exact word score or traditional score
            return max(exact_word_score, traditional_score)

        # For longer queries or no exact matches, use traditional method
        string_similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()

        # Key terms similarity
        terms1 = self._extract_key_terms(text1)
        terms2 = self._extract_key_terms(text2)

        if not terms1 and not terms2:
            terms_similarity = 1.0
        elif not terms1 or not terms2:
            terms_similarity = 0.0
        else:
            intersection = len(terms1.intersection(terms2))
            union = len(terms1.union(terms2))
            terms_similarity = intersection / union if union > 0 else 0.0

        # Weighted combination
        semantic_score = (string_similarity * 0.6) + (terms_similarity * 0.4)

        return semantic_score

    def is_duplicate(
        self, new_text: str, existing_texts: List[str]
    ) -> Tuple[bool, Optional[str], float]:
        """
        Check if new text is a duplicate of any existing texts.

        :param new_text: New text to check
        :param existing_texts: List of existing texts to compare against
        :return: Tuple of (is_duplicate, matching_text, similarity_score)
        """
        max_similarity = 0.0
        best_match = None

        for existing_text in existing_texts:
            similarity = self._calculate_semantic_similarity(new_text, existing_text)

            if similarity > max_similarity:
                max_similarity = similarity
                best_match = existing_text

        is_duplicate = max_similarity >= self.similarity_threshold

        return is_duplicate, best_match, max_similarity


class SemanticMemoryManagerConfig(BaseModel):
    """Configuration for the Semantic Memory Manager."""

    similarity_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Threshold for semantic similarity"
    )
    enable_semantic_dedup: bool = Field(
        default=True, description="Enable semantic duplicate detection"
    )
    enable_exact_dedup: bool = Field(
        default=True, description="Enable exact duplicate detection"
    )
    enable_topic_classification: bool = Field(
        default=True, description="Enable automatic topic classification"
    )
    max_memory_length: int = Field(
        default=500, description="Maximum length for a single memory"
    )
    recent_memory_limit: int = Field(
        default=100, description="Number of recent memories to check for duplicates"
    )
    debug_mode: bool = Field(default=False, description="Enable debug logging")


@dataclass
class SemanticMemoryManager:
    """
    Semantic Memory Manager that provides LLM-free memory management.

    This manager combines the structure of Agno's MemoryManager with semantic search
    and duplicate detection capabilities, without requiring LLM invocation.
    """

    # Required by Agno Memory class - model attribute
    model: Optional[Model] = Field(default=None)

    # Configuration
    config: SemanticMemoryManagerConfig = Field(
        default_factory=SemanticMemoryManagerConfig
    )

    # Components
    topic_classifier: TopicClassifier = Field(default_factory=TopicClassifier)
    duplicate_detector: SemanticDuplicateDetector = Field(default=None)

    # State tracking
    memories_updated: bool = Field(default=False)

    def __init__(
        self,
        model: Optional[Model] = None,
        config: Optional[SemanticMemoryManagerConfig] = None,
        similarity_threshold: float = 0.8,
        enable_semantic_dedup: bool = True,
        enable_exact_dedup: bool = True,
        enable_topic_classification: bool = True,
        debug_mode: bool = False,
    ):
        """Initialize the Semantic Memory Manager."""
        if config is None:
            config = SemanticMemoryManagerConfig(
                similarity_threshold=similarity_threshold,
                enable_semantic_dedup=enable_semantic_dedup,
                enable_exact_dedup=enable_exact_dedup,
                enable_topic_classification=enable_topic_classification,
                debug_mode=debug_mode,
            )

        self.model = model  # Required by Agno Memory class
        self.config = config

        # Get the correct path to topics.yaml
        current_dir = os.path.dirname(os.path.abspath(__file__))
        topics_yaml_path = os.path.join(current_dir, "topics.yaml")

        self.topic_classifier = TopicClassifier(config_path=topics_yaml_path)
        self.duplicate_detector = SemanticDuplicateDetector(
            similarity_threshold=config.similarity_threshold
        )
        self.memories_updated = False

        if self.config.debug_mode:
            logger.setLevel(logging.DEBUG)

        logger.info(
            "Initialized SemanticMemoryManager with similarity_threshold=%.2f",
            config.similarity_threshold,
        )

    def _is_exact_duplicate(
        self, new_memory: str, existing_memories: List[UserMemory]
    ) -> Optional[UserMemory]:
        """Check for exact duplicate memories."""
        if not self.config.enable_exact_dedup:
            return None

        new_memory_clean = new_memory.strip().lower()

        for existing in existing_memories:
            existing_clean = existing.memory.strip().lower()
            if new_memory_clean == existing_clean:
                logger.debug("Exact duplicate found: '%s'", new_memory)
                return existing

        return None

    def _is_semantic_duplicate(
        self, new_memory: str, existing_memories: List[UserMemory]
    ) -> Optional[UserMemory]:
        """Check for semantic duplicate memories."""
        if not self.config.enable_semantic_dedup:
            return None

        existing_texts = [mem.memory for mem in existing_memories]
        is_dup, best_match, similarity = self.duplicate_detector.is_duplicate(
            new_memory, existing_texts
        )

        if is_dup and best_match:
            # Find the matching memory object
            for existing in existing_memories:
                if existing.memory == best_match:
                    logger.debug(
                        "Semantic duplicate found (similarity: %.2f): '%s' ~ '%s'",
                        similarity,
                        new_memory,
                        existing.memory,
                    )
                    return existing

        return None

    def _should_reject_memory(
        self, new_memory: str, existing_memories: List[UserMemory]
    ) -> Tuple[bool, str]:
        """Determine if a memory should be rejected."""
        # Check memory length
        if len(new_memory) > self.config.max_memory_length:
            return (
                True,
                f"Memory too long ({len(new_memory)} > {self.config.max_memory_length} chars)",
            )

        # Check for exact duplicates
        exact_duplicate = self._is_exact_duplicate(new_memory, existing_memories)
        if exact_duplicate:
            return True, f"Exact duplicate of: '{exact_duplicate.memory}'"

        # Check for semantic duplicates
        semantic_duplicate = self._is_semantic_duplicate(new_memory, existing_memories)
        if semantic_duplicate:
            return True, f"Semantic duplicate of: '{semantic_duplicate.memory}'"

        return False, ""

    def _get_recent_memories(self, db: MemoryDb, user_id: str) -> List[UserMemory]:
        """Get recent memories for duplicate checking."""
        try:
            memory_rows = db.read_memories(
                user_id=user_id, limit=self.config.recent_memory_limit, sort="desc"
            )

            user_memories = []
            for row in memory_rows:
                if row.user_id == user_id and row.memory:
                    try:
                        user_memory = UserMemory.from_dict(row.memory)
                        user_memories.append(user_memory)
                    except (ValueError, KeyError, TypeError) as e:
                        logger.warning(
                            "Failed to convert memory row to UserMemory: %s", e
                        )

            return user_memories
        except Exception as e:
            logger.error("Error retrieving recent memories: %s", e)
            return []

    def add_memory(
        self,
        memory_text: str,
        db: MemoryDb,
        user_id: str = None,
        topics: Optional[List[str]] = None,
        input_text: Optional[str] = None,
    ) -> MemoryStorageResult:
        """
        Add a memory with duplicate detection and topic classification.

        :param memory_text: The memory text to add
        :param db: Memory database instance
        :param user_id: User ID for the memory
        :param topics: Optional list of topics (will be auto-classified if not provided)
        :param input_text: Optional input text that generated this memory
        :return: MemoryStorageResult with detailed status information
        """
        # Get current user ID if not provided
        if user_id is None:
            user_id = get_current_user_id()

        # Validate input
        if not memory_text or not memory_text.strip():
            return MemoryStorageResult(
                status=MemoryStorageStatus.CONTENT_EMPTY,
                message="Memory content cannot be empty",
                local_success=False,
                graph_success=False,
            )

        # Get recent memories for duplicate checking
        existing_memories = self._get_recent_memories(db, user_id)

        # Check memory length
        if len(memory_text) > self.config.max_memory_length:
            return MemoryStorageResult(
                status=MemoryStorageStatus.CONTENT_TOO_LONG,
                message=f"Memory too long ({len(memory_text)} > {self.config.max_memory_length} chars)",
                local_success=False,
                graph_success=False,
            )

        # Check for exact duplicates
        exact_duplicate = self._is_exact_duplicate(memory_text, existing_memories)
        if exact_duplicate:
            return MemoryStorageResult(
                status=MemoryStorageStatus.DUPLICATE_EXACT,
                message=f"Exact duplicate of: '{exact_duplicate.memory}'",
                local_success=False,
                graph_success=False,
                similarity_score=1.0,
            )

        # Check for semantic duplicates
        semantic_duplicate = self._is_semantic_duplicate(memory_text, existing_memories)
        if semantic_duplicate:
            # Get similarity score for the duplicate
            existing_texts = [mem.memory for mem in existing_memories]
            _, _, similarity_score = self.duplicate_detector.is_duplicate(
                memory_text, existing_texts
            )

            return MemoryStorageResult(
                status=MemoryStorageStatus.DUPLICATE_SEMANTIC,
                message=f"Semantic duplicate of: '{semantic_duplicate.memory}'",
                local_success=False,
                graph_success=False,
                similarity_score=similarity_score,
            )

        # Auto-classify topics if not provided
        if topics is None and self.config.enable_topic_classification:
            topics = self.topic_classifier.classify(memory_text)

        # Create the memory
        try:
            from uuid import uuid4

            memory_id = str(uuid4())
            last_updated = datetime.now()

            user_memory = UserMemory(
                memory_id=memory_id,
                memory=memory_text,
                topics=topics,
                last_updated=last_updated,
                input=input_text,
            )

            memory_row = MemoryRow(
                id=memory_id,
                user_id=user_id,
                memory=user_memory.to_dict(),
                last_updated=last_updated,
            )

            db.upsert_memory(memory_row)

            self.memories_updated = True

            logger.info(
                "Added memory for user %s: '%s' (topics: %s)",
                user_id,
                memory_text,
                topics,
            )
            if self.config.debug_mode:
                print(f"✅ ACCEPTED: '{memory_text}' (topics: {topics})")

            return MemoryStorageResult(
                status=MemoryStorageStatus.SUCCESS,
                message="Memory added successfully",
                memory_id=memory_id,
                topics=topics,
                local_success=True,
                graph_success=False,  # Will be updated by the caller for dual storage
            )

        except Exception as e:
            error_msg = f"Error adding memory: {e}"
            logger.error(error_msg)
            return MemoryStorageResult(
                status=MemoryStorageStatus.STORAGE_ERROR,
                message=error_msg,
                local_success=False,
                graph_success=False,
            )

    def update_memory(
        self,
        memory_id: str,
        memory_text: str,
        db: MemoryDb,
        user_id: str = None,
        topics: Optional[List[str]] = None,
        input_text: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Update an existing memory.

        :param memory_id: ID of the memory to update
        :param memory_text: New memory text
        :param db: Memory database instance
        :param user_id: User ID for the memory
        :param topics: Optional list of topics (will be auto-classified if not provided)
        :param input_text: Optional input text that generated this memory
        :return: Tuple of (success, message)
        """
        # Get current user ID if not provided
        if user_id is None:
            user_id = get_current_user_id()

        # Auto-classify topics if not provided
        if topics is None and self.config.enable_topic_classification:
            topics = self.topic_classifier.classify(memory_text)

        try:
            last_updated = datetime.now()

            user_memory = UserMemory(
                memory_id=memory_id,
                memory=memory_text,
                topics=topics,
                last_updated=last_updated,
                input=input_text,
            )

            memory_row = MemoryRow(
                id=memory_id,
                user_id=user_id,
                memory=user_memory.to_dict(),
                last_updated=last_updated,
            )

            db.upsert_memory(memory_row)

            self.memories_updated = True

            logger.info(
                "Updated memory %s for user %s: '%s'", memory_id, user_id, memory_text
            )
            if self.config.debug_mode:
                print(f"🔄 UPDATED: '{memory_text}' (topics: {topics})")

            return True, "Memory updated successfully"

        except Exception as e:
            error_msg = f"Error updating memory: {e}"
            logger.error(error_msg)
            return False, error_msg

    def delete_memory(
        self, memory_id: str, db: MemoryDb, user_id: str = None
    ) -> Tuple[bool, str]:
        """
        Delete a memory.

        :param memory_id: ID of the memory to delete
        :param db: Memory database instance
        :param user_id: User ID for the memory
        :return: Tuple of (success, message)
        """
        try:
            # Get current user ID if not provided
            if user_id is None:
                user_id = get_current_user_id()

            # First check if the memory exists
            memory_rows = db.read_memories(user_id=user_id)
            memory_exists = False
            for row in memory_rows:
                if row.id == memory_id and row.user_id == user_id:
                    memory_exists = True
                    break

            if not memory_exists:
                logger.warning("Memory %s not found for user %s", memory_id, user_id)
                return False, f"Memory {memory_id} not found"

            # Delete the memory
            db.delete_memory(memory_id)

            self.memories_updated = True

            logger.info("Deleted memory %s for user %s", memory_id, user_id)
            if self.config.debug_mode:
                print(f"🗑️ DELETED: {memory_id}")

            return True, f"Memory {memory_id} deleted successfully"

        except Exception as e:
            error_msg = f"Error deleting memory {memory_id}: {e}"
            logger.error(error_msg)
            return False, error_msg

    def delete_memories_by_topic(
        self, topics: List[str], db: MemoryDb, user_id: str = None
    ) -> Tuple[bool, str]:
        """
        Delete all memories associated with a specific topic or list of topics.

        :param topics: A list of topics to delete memories for.
        :param db: Memory database instance.
        :param user_id: User ID for the memories.
        :return: Tuple of (success, message).
        """
        # Get current user ID if not provided
        if user_id is None:
            user_id = get_current_user_id()

        if not topics:
            return False, "No topics provided for deletion."

        try:
            # Get all memories for the specified topics
            memories_to_delete = self.get_memories_by_topic(
                db=db, user_id=user_id, topics=topics
            )

            if not memories_to_delete:
                return (
                    True,
                    f"No memories found for topics: {', '.join(topics)}.",
                )

            deleted_count = 0
            for memory in memories_to_delete:
                success, _ = self.delete_memory(
                    memory_id=memory.memory_id, db=db, user_id=user_id
                )
                if success:
                    deleted_count += 1

            self.memories_updated = True

            logger.info(
                "Deleted %d memories for topics '%s' for user %s",
                deleted_count,
                ", ".join(topics),
                user_id,
            )
            if self.config.debug_mode:
                print(
                    f"🗑️ DELETED BY TOPIC: {deleted_count} memories for topics: {', '.join(topics)}"
                )

            return (
                True,
                f"Successfully deleted {deleted_count} memories for topics: {', '.join(topics)}.",
            )

        except Exception as e:
            error_msg = f"Error deleting memories by topic: {e}"
            logger.error(error_msg)
            return False, error_msg

    def clear_memories(self, db: MemoryDb, user_id: str = None) -> Tuple[bool, str]:
        """
        Clear all memories for a user.

        :param db: Memory database instance
        :param user_id: User ID for the memories
        :return: Tuple of (success, message)
        """
        # Get current user ID if not provided
        if user_id is None:
            user_id = get_current_user_id()

        try:
            # Get all memories for the user first
            memory_rows = db.read_memories(user_id=user_id)

            # Delete each memory
            for row in memory_rows:
                if row.user_id == user_id:
                    db.delete_memory(row.id)

            self.memories_updated = True

            logger.info("Cleared all memories for user %s", user_id)
            if self.config.debug_mode:
                print(f"🧹 CLEARED: All memories for user {user_id}")

            return True, f"Cleared {len(memory_rows)} memories successfully"

        except Exception as e:
            error_msg = f"Error clearing memories: {e}"
            logger.error(error_msg)
            return False, error_msg

    def search_memories(
        self,
        query: str,
        db: MemoryDb,
        user_id: str = None,
        limit: int = None,
        similarity_threshold: float = 0.3,
        search_topics: bool = True,
        topic_boost: float = 0.5,
    ) -> List[Tuple[UserMemory, float]]:
        """
        Search memories using semantic similarity and topic matching with enhanced query expansion.

        :param query: Search query
        :param db: Memory database instance
        :param user_id: User ID to search within
        :param limit: Maximum number of results
        :param similarity_threshold: Minimum similarity threshold for content
        :param search_topics: Whether to include topic search (default: True)
        :param topic_boost: Score boost for topic matches (default: 0.5)
        :return: List of (UserMemory, combined_score) tuples
        """
        import time

        # LATENCY DEBUG: Start timing memory search
        search_start_time = time.perf_counter()
        logger.info(
            "🔍 MEMORY LATENCY: Starting search_memories for query: %s", query[:50]
        )

        # Get current user ID if not provided
        if user_id is None:
            user_id = get_current_user_id()

        try:
            # LATENCY DEBUG: Time query expansion
            expand_start = time.perf_counter()
            expanded_queries = self._expand_query(query)
            expand_time = time.perf_counter() - expand_start
            logger.info(
                "🔍 MEMORY LATENCY: Query expansion took %.3f seconds (%d queries)",
                expand_time,
                len(expanded_queries),
            )

            # LATENCY DEBUG: Time database read
            db_start = time.perf_counter()
            memory_rows = db.read_memories(user_id=user_id)
            db_time = time.perf_counter() - db_start
            logger.info(
                "🔍 MEMORY LATENCY: Database read took %.3f seconds (%d rows)",
                db_time,
                len(memory_rows),
            )

            # LATENCY DEBUG: Time memory conversion
            convert_start = time.perf_counter()
            user_memories = []
            for row in memory_rows:
                if row.user_id == user_id and row.memory:
                    try:
                        user_memory = UserMemory.from_dict(row.memory)
                        user_memories.append(user_memory)
                    except (ValueError, KeyError, TypeError) as e:
                        logger.warning(
                            "Failed to convert memory row to UserMemory: %s", e
                        )
            convert_time = time.perf_counter() - convert_start
            logger.info(
                "🔍 MEMORY LATENCY: Memory conversion took %.3f seconds (%d memories)",
                convert_time,
                len(user_memories),
            )

            # LATENCY DEBUG: Time similarity calculations
            similarity_start = time.perf_counter()
            results = []
            query_lower = query.lower().strip()

            for memory in user_memories:
                max_similarity = 0.0
                best_query = query

                # Test original query and all expanded queries
                for test_query in expanded_queries:
                    content_similarity = (
                        self.duplicate_detector._calculate_semantic_similarity(
                            test_query, memory.memory
                        )
                    )
                    if content_similarity > max_similarity:
                        max_similarity = content_similarity
                        best_query = test_query

                # Topic matching with enhanced search
                topic_score = 0.0
                topic_matches = []

                if search_topics and memory.topics:
                    for topic in memory.topics:
                        # Check original query and expanded queries against topics
                        for test_query in expanded_queries:
                            test_query_lower = test_query.lower()
                            if (
                                test_query_lower in topic.lower()
                                or topic.lower() in test_query_lower
                            ):
                                if test_query_lower == topic.lower():
                                    topic_score = 1.0  # Exact topic match
                                    topic_matches.append(topic)
                                    break
                                else:
                                    topic_score = max(
                                        topic_score, 0.8
                                    )  # Partial topic match
                                    topic_matches.append(topic)

                # Enhanced keyword matching for work-related queries
                keyword_score = self._calculate_keyword_score(
                    expanded_queries, memory.memory
                )

                # Combined scoring: use the best of content similarity, topic match, or keyword match
                final_score = max(
                    max_similarity, topic_score * topic_boost, keyword_score
                )

                if (
                    final_score >= similarity_threshold
                    or topic_score > 0
                    or keyword_score > 0.4
                ):
                    results.append((memory, final_score))

                    if self.config.debug_mode and (
                        topic_matches or keyword_score > 0.4
                    ):
                        logger.debug(
                            "Enhanced match for query '%s': memory='%s', topics=%s, final_score=%.3f (content=%.3f, topic=%.3f, keyword=%.3f)",
                            query,
                            memory.memory[:50],
                            topic_matches,
                            final_score,
                            max_similarity,
                            topic_score,
                            keyword_score,
                        )

            similarity_time = time.perf_counter() - similarity_start
            logger.info(
                "🔍 MEMORY LATENCY: Similarity calculations took %.3f seconds (%d memories processed)",
                similarity_time,
                len(user_memories),
            )

            # LATENCY DEBUG: Time sorting
            sort_start = time.perf_counter()
            results.sort(key=lambda x: x[1], reverse=True)
            sort_time = time.perf_counter() - sort_start
            logger.info("🔍 MEMORY LATENCY: Sorting took %.3f seconds", sort_time)

            # LATENCY DEBUG: Total timing
            total_time = time.perf_counter() - search_start_time
            logger.info(
                "🔍 MEMORY LATENCY: Total search_memories time: %.3f seconds (expand: %.3f, db: %.3f, convert: %.3f, similarity: %.3f, sort: %.3f)",
                total_time,
                expand_time,
                db_time,
                convert_time,
                similarity_time,
                sort_time,
            )

            return results[:limit]

        except Exception as e:
            logger.error("Error searching memories: %s", e)
            return []

    def get_memories_by_topic(
        self,
        db: MemoryDb,
        user_id: str = None,
        topics: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[UserMemory]:
        """
        Get memories filtered by a list of topics, without similarity search.

        :param db: Memory database instance
        :param user_id: User ID to search within
        :param topics: Optional list of topics to filter by. If None, returns all memories.
        :param limit: Maximum number of results to return
        :return: List of UserMemory objects matching the topics.
        """
        # Get current user ID if not provided
        if user_id is None:
            user_id = get_current_user_id()

        try:
            # Get all memories for the user
            memory_rows = db.read_memories(user_id=user_id, sort="desc")

            user_memories = []
            for row in memory_rows:
                if row.user_id == user_id and row.memory:
                    try:
                        user_memory = UserMemory.from_dict(row.memory)
                        user_memories.append(user_memory)
                    except (ValueError, KeyError, TypeError) as e:
                        logger.warning(
                            "Failed to convert memory row to UserMemory: %s", e
                        )

            if not topics:
                # If no topics are specified, return all memories up to the limit
                return user_memories[:limit]

            # Filter memories by the given topics
            filtered_memories = []
            topic_set = {t.lower() for t in topics}
            for memory in user_memories:
                if memory.topics and any(t.lower() in topic_set for t in memory.topics):
                    filtered_memories.append(memory)

            # Sort by date (already sorted by read_memories) and limit
            return filtered_memories[:limit]

        except Exception as e:
            logger.error("Error getting memories by topic: %s", e)
            return []

    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms for better semantic matching.

        :param query: Original search query
        :return: List of expanded queries including the original
        """
        query_lower = query.lower().strip()
        expanded = [query]  # Always include original query

        # Work-related expansions
        work_synonyms = {
            "work": [
                "job",
                "employment",
                "career",
                "occupation",
                "position",
                "company",
                "employer",
                "workplace",
            ],
            "workplace": ["work", "job", "office", "company", "employer", "business"],
            "job": ["work", "employment", "career", "position", "occupation", "role"],
            "company": ["employer", "business", "organization", "workplace", "firm"],
            "career": ["job", "work", "profession", "occupation", "employment"],
        }

        # Education-related expansions
        education_synonyms = {
            "school": ["university", "college", "education", "academic", "institution"],
            "university": ["college", "school", "education", "academic", "institution"],
            "degree": ["education", "qualification", "diploma", "certification"],
            "study": ["education", "learning", "academic", "school", "university"],
        }

        # Personal-related expansions
        personal_synonyms = {
            "hobby": ["interest", "activity", "pastime", "recreation", "leisure"],
            "interest": ["hobby", "passion", "activity", "like", "enjoy"],
            "like": ["enjoy", "prefer", "love", "interest", "hobby"],
            "preference": ["like", "prefer", "choice", "favorite"],
        }

        # Combine all synonym dictionaries
        all_synonyms = {**work_synonyms, **education_synonyms, **personal_synonyms}

        # Add synonyms for words in the query
        query_words = query_lower.split()
        for word in query_words:
            if word in all_synonyms:
                for synonym in all_synonyms[word]:
                    # Create expanded queries by replacing the word with synonyms
                    expanded_query = query_lower.replace(word, synonym)
                    if expanded_query not in expanded:
                        expanded.append(expanded_query)

                    # Also add just the synonym
                    if synonym not in expanded:
                        expanded.append(synonym)

        return expanded

    def _calculate_keyword_score(self, queries: List[str], memory_text: str) -> float:
        """
        Calculate keyword-based similarity score for enhanced matching.

        :param queries: List of query variations to test
        :param memory_text: Memory text to search in
        :return: Keyword similarity score (0.0 to 1.0)
        """
        memory_lower = memory_text.lower()
        max_score = 0.0

        for query in queries:
            query_words = query.lower().split()
            if not query_words:
                continue

            matches = 0
            for word in query_words:
                if (
                    len(word) > 2 and word in memory_lower
                ):  # Only count words longer than 2 chars
                    matches += 1

            if query_words:
                score = matches / len(query_words)
                max_score = max(max_score, score)

        return max_score

    def get_all_memories(self, db: MemoryDb, user_id: str = None) -> List[UserMemory]:
        """
        Get all memories for a user.

        :param db: Memory database instance
        :param user_id: User ID to retrieve memories for
        :return: List of UserMemory objects
        """
        # Get current user ID if not provided
        if user_id is None:
            user_id = get_current_user_id()

        try:
            # Get all memories for the user
            memory_rows = db.read_memories(user_id=user_id, sort="desc")

            user_memories = []
            for row in memory_rows:
                if row.user_id == user_id and row.memory:
                    try:
                        user_memory = UserMemory.from_dict(row.memory)
                        user_memories.append(user_memory)
                    except (ValueError, KeyError, TypeError) as e:
                        logger.warning(
                            "Failed to convert memory row to UserMemory: %s", e
                        )

            logger.info(
                "Retrieved %d memories for user %s", len(user_memories), user_id
            )
            return user_memories

        except Exception as e:
            logger.error("Error retrieving all memories: %s", e)
            return []

    def list_all_memories(self, db: MemoryDb, user_id: str = None) -> List[str]:
        """
        Get all memory data as a simple list of strings.

        This function takes the result of get_all_memories and extracts the memory
        text (data field) from each memory object, returning a simple list of strings.

        :param db: Memory database instance
        :param user_id: User ID to retrieve memories for
        :return: List of memory text strings
        """
        # Get all memories using the existing method
        all_memories = self.get_all_memories(db, user_id)

        # Extract the memory text (data field) from each memory object
        memory_texts = []
        for memory in all_memories:
            if hasattr(memory, "memory") and memory.memory:
                memory_texts.append(memory.memory)

        logger.info(
            "Listed %d memory texts for user %s",
            len(memory_texts),
            user_id or get_current_user_id(),
        )
        return memory_texts

    def get_memory_stats(self, db: MemoryDb, user_id: str = None) -> Dict[str, Any]:
        """
        Get statistics about memories for a user.

        :param db: Memory database instance
        :param user_id: User ID to analyze
        :return: Dictionary with memory statistics
        """
        # Get current user ID if not provided
        if user_id is None:
            user_id = get_current_user_id()

        try:
            memories = self._get_recent_memories(db, user_id)

            if not memories:
                return {"total_memories": 0}

            # Topic distribution
            topic_counts = {}
            for memory in memories:
                if memory.topics:
                    for topic in memory.topics:
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # Average memory length
            avg_length = sum(len(m.memory) for m in memories) / len(memories)

            # Recent activity (memories in last 24 hours)
            recent_count = 0
            if memories:
                cutoff = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                for memory in memories:
                    if memory.last_updated and memory.last_updated >= cutoff:
                        recent_count += 1

            return {
                "total_memories": len(memories),
                "topic_distribution": topic_counts,
                "average_memory_length": avg_length,
                "recent_memories_24h": recent_count,
                "most_common_topic": (
                    max(topic_counts.items(), key=lambda x: x[1])[0]
                    if topic_counts
                    else None
                ),
            }

        except Exception as e:
            logger.error("Error getting memory stats: %s", e)
            return {"error": str(e)}

    def process_input(
        self,
        input_text: str,
        db: MemoryDb,
        user_id: str = None,
        extract_multiple: bool = True,
    ) -> Dict[str, Any]:
        """
        Process input text and extract memories without using LLM.

        This method uses simple heuristics to determine if the input contains
        memorable information and extracts it accordingly.

        :param input_text: Input text to process
        :param db: Memory database instance
        :param user_id: User ID for the memories
        :param extract_multiple: Whether to try extracting multiple memories from input
        :return: Dictionary with processing results
        """
        results = {
            "memories_added": [],
            "memories_rejected": [],
            "total_processed": 0,
            "success": True,
            "message": "Processing completed",
        }

        try:
            # Simple heuristics to extract memorable statements
            memorable_statements = self._extract_memorable_statements(input_text)

            for statement in memorable_statements:
                result = self.add_memory(
                    memory_text=statement,
                    db=db,
                    user_id=user_id,
                    input_text=input_text,
                )

                results["total_processed"] += 1

                if result.is_success:
                    results["memories_added"].append(
                        {
                            "memory_id": result.memory_id,
                            "memory": statement,
                            "topics": result.topics,
                        }
                    )
                else:
                    results["memories_rejected"].append(
                        {"memory": statement, "reason": result.message}
                    )

            if results["memories_added"]:
                self.memories_updated = True

        except Exception as e:
            results["success"] = False
            results["message"] = f"Error processing input: {e}"
            logger.error("Error processing input: %s", e)

        return results

    def create_or_update_memories(
        self,
        messages: List,  # List[Message] from agno.models.message
        existing_memories: List[Dict[str, Any]],
        user_id: str,
        db: MemoryDb,
        delete_memories: bool = True,
        clear_memories: bool = True,
    ) -> str:
        """
        Create or update memories based on messages - LLM-free implementation.

        This method provides the same interface as Agno's MemoryManager but uses
        semantic analysis instead of LLM calls for better performance and reliability.

        :param messages: List of Message objects to process
        :param existing_memories: List of existing memory dictionaries
        :param user_id: User ID for the memories
        :param db: Memory database instance
        :param delete_memories: Whether deletion is enabled (not used in our implementation)
        :param clear_memories: Whether clearing is enabled (not used in our implementation)
        :return: String describing the actions taken
        """
        logger.debug("SemanticMemoryManager.create_or_update_memories Start")

        # Create a simple memory class for duplicate checking
        class SimpleMemory:
            def __init__(self, memory_text: str, memory_id: str = ""):
                self.memory = memory_text
                self.memory_id = memory_id

        # Convert existing memories to UserMemory objects for our processing
        existing_user_memories = []
        for mem_dict in existing_memories:
            try:
                # Create a UserMemory-like object for our duplicate detection
                memory_text = mem_dict.get("memory", "")
                if memory_text:
                    existing_user_memories.append(
                        SimpleMemory(memory_text, mem_dict.get("memory_id", ""))
                    )
            except Exception as e:
                logger.warning(f"Failed to process existing memory: {e}")

        # Extract text content from messages
        message_texts = []
        for message in messages:
            if hasattr(message, "content") and message.content:
                if hasattr(message, "role") and message.role == "user":
                    # Only process user messages for memory extraction
                    message_texts.append(str(message.content))
            elif hasattr(message, "get_content_string"):
                # Use agno's method to get content
                content = message.get_content_string()
                if content and hasattr(message, "role") and message.role == "user":
                    message_texts.append(content)

        if not message_texts:
            logger.debug("No user messages found to process")
            return "No user messages to process for memory creation"

        # Combine all message texts
        combined_input = " ".join(message_texts)

        # Extract memorable statements
        memorable_statements = self._extract_memorable_statements(combined_input)

        if not memorable_statements:
            logger.debug("No memorable statements found in messages")
            return "No memorable information found in the messages"

        # Process each memorable statement
        actions_taken = []
        memories_added = 0
        memories_rejected = 0

        for statement in memorable_statements:
            # Check for duplicates against existing memories
            should_reject, reason = self._should_reject_memory(
                statement, existing_user_memories
            )

            if should_reject:
                memories_rejected += 1
                actions_taken.append(f"Rejected: '{statement[:50]}...' - {reason}")
                logger.debug(f"Rejected memory: {reason}")
                continue

            # Add the memory
            result = self.add_memory(
                memory_text=statement,
                db=db,
                user_id=user_id,
                input_text=combined_input,
            )

            if result.is_success:
                memories_added += 1
                actions_taken.append(f"Added: '{statement[:50]}...'")
                logger.debug(f"Added memory: {result.memory_id}")

                # Add to existing memories list for subsequent duplicate checking
                existing_user_memories.append(
                    SimpleMemory(statement, result.memory_id or "")
                )
            else:
                memories_rejected += 1
                actions_taken.append(
                    f"Failed to add: '{statement[:50]}...' - {result.message}"
                )
                logger.warning(f"Failed to add memory: {result.message}")

        # Set memories_updated flag if any memories were added
        if memories_added > 0:
            self.memories_updated = True

        # Create response summary
        response_parts = [
            f"Processed {len(memorable_statements)} memorable statements",
            f"Added {memories_added} new memories",
            f"Rejected {memories_rejected} duplicates/invalid memories",
        ]

        if self.config.debug_mode and actions_taken:
            response_parts.append("Actions taken:")
            response_parts.extend(actions_taken[:5])  # Limit to first 5 actions
            if len(actions_taken) > 5:
                response_parts.append(f"... and {len(actions_taken) - 5} more actions")

        response = ". ".join(response_parts)
        logger.debug("SemanticMemoryManager.create_or_update_memories End")

        return response

    async def acreate_or_update_memories(
        self,
        messages: List,  # List[Message] from agno.models.message
        existing_memories: List[Dict[str, Any]],
        user_id: str,
        db: MemoryDb,
        delete_memories: bool = True,
        clear_memories: bool = True,
    ) -> str:
        """
        Async version of create_or_update_memories.

        Since our implementation doesn't use async operations, this just calls
        the sync version. This maintains compatibility with Agno's async interface.
        """
        return self.create_or_update_memories(
            messages=messages,
            existing_memories=existing_memories,
            user_id=user_id,
            db=db,
            delete_memories=delete_memories,
            clear_memories=clear_memories,
        )

    def run_memory_task(
        self,
        task: str,
        existing_memories: List[Dict[str, Any]],
        user_id: str,
        db: MemoryDb,
        delete_memories: bool = True,
        clear_memories: bool = True,
    ) -> str:
        """
        Process a memory task without using LLM.

        This method provides the same interface as Agno's MemoryManager.run_memory_task
        but uses semantic analysis instead of LLM calls for better performance and reliability.

        :param task: The task/input text to process for memory extraction
        :param existing_memories: List of existing memory dictionaries
        :param user_id: User ID for the memories
        :param db: Memory database instance
        :param delete_memories: Whether deletion is enabled (not used in our implementation)
        :param clear_memories: Whether clearing is enabled (not used in our implementation)
        :return: String describing the actions taken
        """
        logger.debug("SemanticMemoryManager.run_memory_task Start")

        try:
            # Extract memorable statements from the task
            memorable_statements = self._extract_memorable_statements(task)

            if not memorable_statements:
                logger.debug("No memorable statements found in task")
                return "No memorable information found in the task"

            # Convert existing memories to UserMemory-like objects for duplicate checking
            class SimpleMemory:
                def __init__(self, memory_text: str, memory_id: str = ""):
                    self.memory = memory_text
                    self.memory_id = memory_id

            existing_user_memories = []
            for mem_dict in existing_memories:
                try:
                    memory_text = mem_dict.get("memory", "")
                    if memory_text:
                        existing_user_memories.append(
                            SimpleMemory(memory_text, mem_dict.get("memory_id", ""))
                        )
                except Exception as e:
                    logger.warning(f"Failed to process existing memory: {e}")

            # Process each memorable statement
            actions_taken = []
            memories_added = 0
            memories_rejected = 0

            for statement in memorable_statements:
                # Check for duplicates against existing memories
                should_reject, reason = self._should_reject_memory(
                    statement, existing_user_memories
                )

                if should_reject:
                    memories_rejected += 1
                    actions_taken.append(f"Rejected: '{statement[:50]}...' - {reason}")
                    logger.debug(f"Rejected memory: {reason}")
                    continue

                # Add the memory
                result = self.add_memory(
                    memory_text=statement,
                    db=db,
                    user_id=user_id,
                    input_text=task,
                )

                if result.is_success:
                    memories_added += 1
                    actions_taken.append(f"Added: '{statement[:50]}...'")
                    logger.debug(f"Added memory: {result.memory_id}")

                    # Add to existing memories list for subsequent duplicate checking
                    existing_user_memories.append(
                        SimpleMemory(statement, result.memory_id or "")
                    )
                else:
                    memories_rejected += 1
                    actions_taken.append(
                        f"Failed to add: '{statement[:50]}...' - {result.message}"
                    )
                    logger.warning(f"Failed to add memory: {result.message}")

            # Set memories_updated flag if any memories were added
            if memories_added > 0:
                self.memories_updated = True

            # Create response summary
            response_parts = [
                f"Processed {len(memorable_statements)} memorable statements",
                f"Added {memories_added} new memories",
                f"Rejected {memories_rejected} duplicates/invalid memories",
            ]

            if self.config.debug_mode and actions_taken:
                response_parts.append("Actions taken:")
                response_parts.extend(actions_taken[:5])  # Limit to first 5 actions
                if len(actions_taken) > 5:
                    response_parts.append(
                        f"... and {len(actions_taken) - 5} more actions"
                    )

            response = ". ".join(response_parts)
            logger.debug("SemanticMemoryManager.run_memory_task End")

            return response

        except Exception as e:
            error_msg = f"Error in run_memory_task: {e}"
            logger.error(error_msg)
            return error_msg

    async def arun_memory_task(
        self,
        task: str,
        existing_memories: List[Dict[str, Any]],
        user_id: str,
        db: MemoryDb,
        delete_memories: bool = True,
        clear_memories: bool = True,
    ) -> str:
        """
        Async version of run_memory_task.

        Since our implementation doesn't use async operations, this just calls
        the sync version. This maintains compatibility with Agno's async interface.

        :param task: The task/input text to process for memory extraction
        :param existing_memories: List of existing memory dictionaries
        :param user_id: User ID for the memories
        :param db: Memory database instance
        :param delete_memories: Whether deletion is enabled (not used in our implementation)
        :param clear_memories: Whether clearing is enabled (not used in our implementation)
        :return: String describing the actions taken
        """
        return self.run_memory_task(
            task=task,
            existing_memories=existing_memories,
            user_id=user_id,
            db=db,
            delete_memories=delete_memories,
            clear_memories=clear_memories,
        )

    def _extract_memorable_statements(self, text: str) -> List[str]:
        """
        Extract memorable statements from text using simple heuristics.

        :param text: Input text
        :return: List of memorable statements
        """
        statements = []

        # Split by sentences
        sentences = re.split(r"[.!?]+", text)

        # Patterns that indicate memorable information
        memorable_patterns = [
            r"\bi am\b",
            r"\bmy name is\b",
            r"\bi work\b",
            r"\bi live\b",
            r"\bi like\b",
            r"\bi love\b",
            r"\bi hate\b",
            r"\bi prefer\b",
            r"\bi have\b",
            r"\bi study\b",
            r"\bi graduated\b",
            r"\bmy favorite\b",
            r"\bmy goal\b",
            r"\bi want to\b",
            r"\bi plan to\b",
        ]

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue

            # Check if sentence contains memorable patterns
            for pattern in memorable_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    statements.append(sentence)
                    break

        return statements


# Convenience function for easy usage
def create_semantic_memory_manager(
    model: Optional[Model] = None,
    similarity_threshold: float = 0.8,
    enable_semantic_dedup: bool = True,
    enable_exact_dedup: bool = True,
    enable_topic_classification: bool = True,
    debug_mode: bool = False,
) -> SemanticMemoryManager:
    """
    Create a SemanticMemoryManager instance with sensible defaults.

    :param model: Optional model instance (required by Agno Memory class)
    :param similarity_threshold: Threshold for semantic similarity
    :param enable_semantic_dedup: Enable semantic duplicate detection
    :param enable_exact_dedup: Enable exact duplicate detection
    :param enable_topic_classification: Enable automatic topic classification
    :param debug_mode: Enable debug output
    :return: Configured SemanticMemoryManager instance
    """
    config = SemanticMemoryManagerConfig(
        similarity_threshold=similarity_threshold,
        enable_semantic_dedup=enable_semantic_dedup,
        enable_exact_dedup=enable_exact_dedup,
        enable_topic_classification=enable_topic_classification,
        debug_mode=debug_mode,
    )

    return SemanticMemoryManager(model=model, config=config)


def main():
    """
    Main function to demonstrate SemanticMemoryManager capabilities.
    """
    import sys
    from pathlib import Path

    # Add parent directories to path for imports
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    sys.path.insert(0, str(project_root / "src"))

    from agno.memory.v2.db.sqlite import SqliteMemoryDb

    from personal_agent.config import AGNO_STORAGE_DIR, get_userid

    print("🧠 Semantic Memory Manager Demo")
    print("=" * 50)

    # Create database connection
    db_path = Path(AGNO_STORAGE_DIR) / "semantic_memory.db"
    print(f"📂 Database: {db_path}")

    memory_db = SqliteMemoryDb(
        table_name="semantic_memory",
        db_file=str(db_path),
    )

    # Create SemanticMemoryManager instance
    manager = create_semantic_memory_manager(
        similarity_threshold=0.8,
        debug_mode=True,
    )

    # Demo input processing
    demo_inputs = [
        "My name is John Doe and I work as a software engineer.",
        "I live in San Francisco and I love hiking on weekends.",
        "My favorite programming language is Python.",
        "I have a dog named Max and I enjoy reading science fiction books.",
        "I prefer tea over coffee in the morning.",
    ]

    print("\n🔄 Processing demo inputs...")
    for i, input_text in enumerate(demo_inputs, 1):
        print(f"\n--- Input {i}: {input_text}")
        result = manager.process_input(input_text, memory_db, get_userid())

        if result["success"]:
            print(f"✅ Processed successfully:")
            print(f"   Added: {len(result['memories_added'])} memories")
            print(f"   Rejected: {len(result['memories_rejected'])} memories")

            for memory in result["memories_added"]:
                print(f"   📝 '{memory['memory']}' (topics: {memory['topics']})")

            for rejection in result["memories_rejected"]:
                print(f"   🚫 '{rejection['memory']}' - {rejection['reason']}")
        else:
            print(f"❌ Processing failed: {result['message']}")

    # Demo memory search
    print(f"\n🔍 Searching memories...")
    search_queries = ["software engineer", "San Francisco", "Python programming"]

    for query in search_queries:
        print(f"\n--- Search: '{query}'")
        results = manager.search_memories(query, memory_db, get_userid(), limit=3)

        if results:
            for memory, similarity in results:
                print(
                    f"   📋 {similarity:.2f}: '{memory.memory}' (topics: {memory.topics})"
                )
        else:
            print("   No results found")

    # Demo memory stats
    print(f"\n📊 Memory Statistics:")
    stats = manager.get_memory_stats(memory_db, get_userid())

    for key, value in stats.items():
        if key == "topic_distribution" and isinstance(value, dict):
            print(f"   {key}:")
            for topic, count in value.items():
                print(f"     - {topic}: {count}")
        else:
            print(f"   {key}: {value}")

    classifier = TopicClassifier()
    examples = [
        "My name is John and I work at Google.",
        "I love to play the piano and travel.",
        "I am 35 years old and live in Paris.",
        "I studied biology at university.",
        "Married to a wonderful woman with 2 kids.",
        "I prefer coffee over tea.",
        "I plan to climb Mount Everest.",
        "I have a peanut allergy.",
        "Completely unrelated sentence.",
    ]

    for text in examples:
        topics = classifier.classify(text)
        print(f"Input: {text}\nTopics: {topics}\n")
    print(f"\n✅ Demo completed!")


if __name__ == "__main__":
    main()
