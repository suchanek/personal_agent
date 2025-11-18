"""Query Metrics Collection and Analysis

This module provides built-in observability for query handling with:
- Query metric recording (intent, execution time, response type)
- Analytics and statistics
- Performance tracking
- Usage patterns

Classes:
    QueryMetric: Individual query metric data
    QueryMetricsCollector: Thread-safe metrics collection

Author: Claude Code
Date: 2025-11-18
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from personal_agent.core.response_types import ResponseType


@dataclass
class QueryMetric:
    """Single query metric record.

    :param timestamp: When query was executed
    :param query: Query text (first 100 chars)
    :param intent: Classified intent
    :param confidence: Intent classification confidence
    :param execution_time_ms: Total execution time in milliseconds
    :param response_type: Source of response (fast path or team inference)
    :param success: Whether query succeeded
    :param error: Error message if failed
    """

    timestamp: datetime
    query: str
    intent: str
    confidence: float
    execution_time_ms: float
    response_type: str
    success: bool
    error: Optional[str] = None


@dataclass
class QueryMetricsCollector:
    """Thread-safe metrics collector for query analytics.

    Collects metrics about query execution including classification,
    performance, and response types. Provides analytics queries.

    :param max_records: Maximum metrics to keep in memory (default 1000)
    """

    max_records: int = 1000
    metrics: List[QueryMetric] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, metric: QueryMetric) -> None:
        """Record a query metric.

        Thread-safe operation that maintains max_records limit.

        :param metric: QueryMetric to record
        """
        with self._lock:
            self.metrics.append(metric)

            # Keep only most recent max_records
            if len(self.metrics) > self.max_records:
                self.metrics = self.metrics[-self.max_records :]

    def get_statistics(self, window_minutes: int = 60) -> Dict:
        """Get statistics for queries within time window.

        :param window_minutes: Time window in minutes (default 60)
        :return: Dictionary with statistics
        """
        with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=window_minutes)

            recent = [m for m in self.metrics if m.timestamp >= cutoff]

            if not recent:
                return self._empty_stats()

            # Calculate statistics
            total_queries = len(recent)
            successful_queries = len([m for m in recent if m.success])
            failed_queries = total_queries - successful_queries

            # Response type breakdown
            response_types = {}
            for m in recent:
                response_types[m.response_type] = response_types.get(m.response_type, 0) + 1

            # Fast path vs full inference
            fast_path_queries = len([m for m in recent if m.response_type != "team_inference"])

            # Timing statistics
            execution_times = [m.execution_time_ms for m in recent]
            avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
            min_time = min(execution_times) if execution_times else 0
            max_time = max(execution_times) if execution_times else 0

            # Intent breakdown
            intents = {}
            for m in recent:
                intents[m.intent] = intents.get(m.intent, 0) + 1

            # Average confidence
            confidences = [m.confidence for m in recent]
            avg_confidence = (
                sum(confidences) / len(confidences) if confidences else 0
            )

            return {
                "window_minutes": window_minutes,
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "failed_queries": failed_queries,
                "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                "fast_path_queries": fast_path_queries,
                "fast_path_percentage": (
                    fast_path_queries / total_queries * 100 if total_queries > 0 else 0
                ),
                "response_types": response_types,
                "intents": intents,
                "average_confidence": avg_confidence,
                "execution_time": {
                    "average_ms": avg_time,
                    "min_ms": min_time,
                    "max_ms": max_time,
                },
                "timestamp": now.isoformat(),
            }

    def get_fast_path_effectiveness(self) -> Dict:
        """Get effectiveness metrics for fast paths.

        Compares fast path performance vs full inference.

        :return: Dictionary with effectiveness metrics
        """
        with self._lock:
            fast_path_queries = [
                m
                for m in self.metrics
                if m.response_type != "team_inference" and m.success
            ]
            full_inference = [m for m in self.metrics if m.response_type == "team_inference"]

            if not fast_path_queries or not full_inference:
                return {}

            fast_times = [m.execution_time_ms for m in fast_path_queries]
            inference_times = [m.execution_time_ms for m in full_inference]

            avg_fast = sum(fast_times) / len(fast_times)
            avg_inference = sum(inference_times) / len(inference_times)

            speedup = avg_inference / avg_fast if avg_fast > 0 else 0
            time_saved_per_query = avg_inference - avg_fast

            return {
                "fast_path_queries": len(fast_path_queries),
                "full_inference_queries": len(full_inference),
                "average_fast_path_ms": avg_fast,
                "average_inference_ms": avg_inference,
                "speedup_factor": speedup,
                "time_saved_per_query_ms": time_saved_per_query,
            }

    def get_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent errors.

        :param limit: Maximum errors to return
        :return: List of error records
        """
        with self._lock:
            errors = [m for m in self.metrics if m.error]
            recent_errors = sorted(errors, key=lambda m: m.timestamp, reverse=True)[
                :limit
            ]

            return [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "query": m.query,
                    "error": m.error,
                    "intent": m.intent,
                }
                for m in recent_errors
            ]

    def get_slowest_queries(self, limit: int = 10) -> List[Dict]:
        """Get slowest queries (for performance investigation).

        :param limit: Maximum queries to return
        :return: List of slow query records
        """
        with self._lock:
            slowest = sorted(
                self.metrics,
                key=lambda m: m.execution_time_ms,
                reverse=True,
            )[:limit]

            return [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "query": m.query,
                    "execution_time_ms": m.execution_time_ms,
                    "response_type": m.response_type,
                    "intent": m.intent,
                }
                for m in slowest
            ]

    def get_intent_breakdown(self) -> Dict[str, int]:
        """Get breakdown of queries by intent.

        :return: Dictionary with intent counts
        """
        with self._lock:
            breakdown = {}
            for m in self.metrics:
                breakdown[m.intent] = breakdown.get(m.intent, 0) + 1

            return breakdown

    def clear(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self.metrics.clear()

    def _empty_stats(self) -> Dict:
        """Return empty statistics dictionary."""
        return {
            "window_minutes": 0,
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "success_rate": 0,
            "fast_path_queries": 0,
            "fast_path_percentage": 0,
            "response_types": {},
            "intents": {},
            "average_confidence": 0,
            "execution_time": {
                "average_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
            },
        }
