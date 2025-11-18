"""Unit Tests for Query Classifier

Tests cover:
- Memory list query detection
- Memory search query detection
- Compound query detection
- Pattern matching accuracy
- Confidence scoring

Author: Claude Code
Date: 2025-11-18
"""

import pytest

from personal_agent.core.query_classifier import QueryClassifier, QueryIntent


class TestQueryClassifier:
    """Test suite for QueryClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        return QueryClassifier()

    # ========== Memory List Query Tests ==========

    def test_memory_list_exact_phrases(self, classifier):
        """Test exact memory list phrases."""
        queries = [
            "list memories",
            "list all memories",
            "list my memories",
            "show memories",
            "show all memories",
            "show my memories",
            "what memories",
            "my memories",
            "all my memories",
            "memories list",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert (
                result.intent == QueryIntent.MEMORY_LIST
            ), f"Failed to classify as memory list: '{query}'"
            assert result.confidence > 0.9, f"Low confidence for: '{query}'"

    def test_memory_list_case_insensitive(self, classifier):
        """Test case insensitivity."""
        queries = [
            "LIST MEMORIES",
            "List All Memories",
            "SHOW ALL MEMORIES",
            "My Memories",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result.intent == QueryIntent.MEMORY_LIST, f"Failed for: '{query}'"

    def test_memory_list_with_punctuation(self, classifier):
        """Test with punctuation."""
        queries = [
            "list memories!",
            "show all memories?",
            "what memories.",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result.intent == QueryIntent.MEMORY_LIST, f"Failed for: '{query}'"

    # ========== Memory Search Query Tests ==========

    def test_memory_search_detection(self, classifier):
        """Test memory search query detection."""
        queries = [
            "do you remember about python",
            "what do you know about cats",
            "search memories for python",
            "find memories about work",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert (
                result.intent == QueryIntent.MEMORY_SEARCH
            ), f"Failed to classify as memory search: '{query}'"

    # ========== Compound Query Tests ==========

    def test_compound_queries_rejected_from_fast_path(self, classifier):
        """Test that compound queries are not classified as memory list."""
        queries = [
            "list memories and search the web",
            "show my memories, then get weather",
            "memories but also news",
            "list all memories plus search wikipedia",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert (
                result.intent != QueryIntent.MEMORY_LIST
            ), f"Wrongly classified as memory list: '{query}'"

    def test_compound_query_detection(self, classifier):
        """Test compound query detection specifically."""
        compound_queries = [
            "memories and weather",
            "list memories, also search web",
            "memories but news too",
        ]

        for query in compound_queries:
            assert classifier._is_compound_query(
                query.lower()
            ), f"Failed to detect compound: '{query}'"

    # ========== General Query Tests ==========

    def test_general_queries(self, classifier):
        """Test that unrelated queries classify as general."""
        queries = [
            "what's the weather",
            "search the web for news",
            "calculate 2+2",
            "hello how are you",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result.intent == QueryIntent.GENERAL, f"Unexpected intent for: '{query}'"

    # ========== Fast Path Decision Tests ==========

    def test_should_use_fast_path_for_memory_list(self, classifier):
        """Test that memory list queries should use fast path."""
        queries = [
            "list memories",
            "show all memories",
            "what memories",
        ]

        for query in queries:
            assert (
                classifier.should_use_fast_path(query)
            ), f"Should use fast path for: '{query}'"

    def test_should_not_use_fast_path_for_compound(self, classifier):
        """Test that compound queries don't use fast path."""
        queries = [
            "list memories and search web",
            "memories, also news",
        ]

        for query in queries:
            assert not classifier.should_use_fast_path(
                query
            ), f"Should not use fast path for: '{query}'"

    def test_should_not_use_fast_path_for_general(self, classifier):
        """Test that general queries don't use fast path."""
        queries = [
            "what's the weather",
            "hello",
        ]

        for query in queries:
            assert not classifier.should_use_fast_path(
                query
            ), f"Should not use fast path for: '{query}'"

    # ========== Confidence Score Tests ==========

    def test_confidence_scores(self, classifier):
        """Test that confidence scores are reasonable."""
        # Memory list should have high confidence
        result = classifier.classify("list memories")
        assert result.confidence >= 0.9, "Memory list confidence too low"

        # General should have lower confidence
        result = classifier.classify("hello")
        assert result.confidence < 0.9, "General query confidence too high"

    # ========== Pattern Matching Tests ==========

    def test_matched_pattern_returned(self, classifier):
        """Test that matched pattern is returned."""
        result = classifier.classify("list all memories")
        assert result.matched_pattern is not None, "Pattern should be returned for match"

        result = classifier.classify("hello world")
        assert result.matched_pattern is None, "Pattern should be None for non-match"

    # ========== Edge Cases ==========

    def test_whitespace_handling(self, classifier):
        """Test handling of extra whitespace."""
        queries = [
            "  list memories  ",
            "list   all   memories",
            "\n show all memories \n",
        ]

        for query in queries:
            result = classifier.classify(query)
            # Should still classify correctly after stripping
            assert result.intent in [
                QueryIntent.MEMORY_LIST,
                QueryIntent.GENERAL,
            ], f"Failed for query with whitespace: '{query}'"

    def test_empty_query(self, classifier):
        """Test handling of empty query."""
        result = classifier.classify("")
        assert result.intent == QueryIntent.GENERAL, "Empty query should be general"

    def test_very_long_query(self, classifier):
        """Test handling of very long query."""
        long_query = "list memories " + "and ask something " * 50
        result = classifier.classify(long_query)
        # Should detect compound query
        assert result.intent == QueryIntent.GENERAL, "Long compound query should be general"

    # ========== Custom Patterns ==========

    def test_custom_patterns(self):
        """Test classifier with custom patterns."""
        custom_patterns = {
            "memory_list": [
                r"^show\s+my\s+stuff",
                r"^tell\s+me\s+what\s+you\s+know",
            ]
        }

        classifier = QueryClassifier(patterns=custom_patterns)

        result = classifier.classify("show my stuff")
        assert result.intent == QueryIntent.MEMORY_LIST

        result = classifier.classify("tell me what you know")
        assert result.intent == QueryIntent.MEMORY_LIST

    # ========== Strict Mode Tests ==========

    def test_strict_mode(self):
        """Test classifier in strict mode."""
        classifier_strict = QueryClassifier(strict_mode=True)
        classifier_loose = QueryClassifier(strict_mode=False)

        # Both should classify memory list queries
        result_strict = classifier_strict.classify("list memories")
        result_loose = classifier_loose.classify("list memories")

        assert result_strict.intent == QueryIntent.MEMORY_LIST
        assert result_loose.intent == QueryIntent.MEMORY_LIST

        # Strict mode should have higher confidence threshold
        assert classifier_strict.confidence_threshold > classifier_loose.confidence_threshold


class TestClassifierPerformance:
    """Test classifier performance characteristics."""

    def test_multiple_classifications_are_consistent(self):
        """Test that multiple classifications of same query are consistent."""
        classifier = QueryClassifier()
        query = "list all memories"

        results = [classifier.classify(query) for _ in range(10)]

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.intent == first_result.intent
            assert result.confidence == first_result.confidence

    def test_classification_speed(self):
        """Test that classification is fast."""
        import time

        classifier = QueryClassifier()

        start = time.time()
        for _ in range(1000):
            classifier.classify("list all memories")
        elapsed = time.time() - start

        # Should classify 1000 queries in less than 1 second
        assert elapsed < 1.0, f"Classification too slow: {elapsed:.3f}s for 1000 queries"
