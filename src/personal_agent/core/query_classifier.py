"""Query Intent Classification System

This module provides intelligent query classification to route user queries to
appropriate handlers (fast paths vs full team inference). It supports multiple
classification strategies and is easily extensible.

Classes:
    QueryIntent: Enum of query intent types
    ClassifierResult: Result of query classification
    QueryClassifier: Main classifier engine

Author: Claude Code
Date: 2025-11-18
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Query intent types for routing decisions."""

    MEMORY_LIST = "memory_list"
    MEMORY_SEARCH = "memory_search"
    KNOWLEDGE_SEARCH = "knowledge_search"
    GENERAL = "general"


@dataclass
class ClassifierResult:
    """Result of query classification.

    :param intent: The classified intent
    :param confidence: Confidence score (0.0-1.0)
    :param reason: Human-readable reason for classification
    :param matched_pattern: Pattern that matched (if any)
    """

    intent: QueryIntent
    confidence: float
    reason: str
    matched_pattern: Optional[str] = None


class QueryClassifier:
    """Intelligent query classifier with multiple strategies.

    Classifies user queries into intent categories using:
    - Regex pattern matching
    - Compound query detection
    - Fallback strategies

    The classifier is configurable and extensible for new query types.

    :param patterns: Optional dict of custom patterns
    :param strict_mode: If True, require high confidence for fast paths
    """

    # Default regex patterns for memory list queries
    MEMORY_LIST_PATTERNS = [
        r"^list\s+(all\s+)?memories",  # list memories, list all memories
        r"^list\s+(my\s+)?memories",  # list memories, list my memories
        r"^show\s+(all\s+)?memories",  # show memories, show all memories
        r"^show\s+(my\s+)?memories",  # show memories, show my memories
        r"^what\s+memories",  # what memories
        r"^my\s+memories",  # my memories
        r"^all\s+my\s+memories",  # all my memories
        r"^memories\s+list",  # memories list
    ]

    # Default regex patterns for memory search queries
    MEMORY_SEARCH_PATTERNS = [
        r"do\s+you\s+remember",  # do you remember
        r"what\s+do\s+you\s+know\s+about",  # what do you know about
        r"search\s+memories",  # search memories
        r"find\s+memories",  # find memories
    ]

    # Compound query indicators (multiple topics)
    COMPOUND_CONNECTORS = [
        " and ",
        " but ",
        " also ",
        ", then ",
        ", also ",
        " plus ",
    ]

    def __init__(
        self,
        patterns: Optional[Dict[str, List[str]]] = None,
        strict_mode: bool = True,
    ):
        """Initialize the query classifier.

        :param patterns: Custom patterns dict with keys like 'memory_list'
        :param strict_mode: If True, require high confidence (>0.9) for fast paths
        """
        self.strict_mode = strict_mode
        self.confidence_threshold = 0.9 if strict_mode else 0.85

        # Set up patterns
        self.memory_list_patterns = (
            patterns.get("memory_list", self.MEMORY_LIST_PATTERNS)
            if patterns
            else self.MEMORY_LIST_PATTERNS
        )
        self.memory_search_patterns = (
            patterns.get("memory_search", self.MEMORY_SEARCH_PATTERNS)
            if patterns
            else self.MEMORY_SEARCH_PATTERNS
        )

        # Compile regex patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        self.compiled_memory_list = [re.compile(p, re.IGNORECASE) for p in self.memory_list_patterns]
        self.compiled_memory_search = [re.compile(p, re.IGNORECASE) for p in self.memory_search_patterns]

    def classify(self, query: str) -> ClassifierResult:
        """Classify a query into an intent category.

        Uses multiple strategies:
        1. Check for compound queries (multi-topic)
        2. Check for memory list patterns
        3. Check for memory search patterns
        4. Default to general

        :param query: User query text
        :return: ClassifierResult with intent and confidence
        """
        query_lower = query.lower().strip()

        # Strategy 1: Detect compound queries (should not use fast paths)
        if self._is_compound_query(query_lower):
            return ClassifierResult(
                intent=QueryIntent.GENERAL,
                confidence=0.95,
                reason="Compound query detected (multiple topics)",
            )

        # Strategy 2: Check for memory list intent
        matched_pattern = self._matches_patterns(query_lower, self.compiled_memory_list)
        if matched_pattern:
            return ClassifierResult(
                intent=QueryIntent.MEMORY_LIST,
                confidence=0.95,
                reason="Matched memory list pattern",
                matched_pattern=matched_pattern,
            )

        # Strategy 3: Check for memory search intent
        matched_pattern = self._matches_patterns(query_lower, self.compiled_memory_search)
        if matched_pattern:
            return ClassifierResult(
                intent=QueryIntent.MEMORY_SEARCH,
                confidence=0.85,
                reason="Matched memory search pattern",
                matched_pattern=matched_pattern,
            )

        # Strategy 4: Default to general
        return ClassifierResult(
            intent=QueryIntent.GENERAL,
            confidence=0.5,
            reason="No specific pattern matched",
        )

    def should_use_fast_path(self, query: str) -> bool:
        """Check if a query should use a fast path.

        :param query: User query text
        :return: True if query should use fast path
        """
        result = self.classify(query)

        # Use fast path for high-confidence memory list queries
        if result.intent == QueryIntent.MEMORY_LIST and result.confidence >= self.confidence_threshold:
            return True

        return False

    def _is_compound_query(self, query: str) -> bool:
        """Check if query requests multiple things.

        :param query: Lowercased query string
        :return: True if compound query detected
        """
        return any(connector in query for connector in self.COMPOUND_CONNECTORS)

    @staticmethod
    def _matches_patterns(query: str, compiled_patterns: List[re.Pattern]) -> Optional[str]:
        """Check if query matches any compiled pattern.

        :param query: Query string to check
        :param compiled_patterns: List of compiled regex patterns
        :return: Matched pattern string if match found, None otherwise
        """
        for pattern in compiled_patterns:
            if pattern.search(query):
                return pattern.pattern

        return None
