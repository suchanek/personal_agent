"""Unified Response Types

This module defines type-safe response objects for all query handlers.
It provides a unified interface for responses from different sources
(fast paths, team inference, etc.) with consistent metadata.

Classes:
    ResponseType: Enum of response source types
    Message: Individual message in response
    UnifiedResponse: Main response object
    ResponseBuilder: Helper to create responses

Author: Claude Code
Date: 2025-11-18
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ResponseType(Enum):
    """Source/type of response."""

    TEAM_INFERENCE = "team_inference"
    MEMORY_FAST_PATH = "memory_fast_path"
    MEMORY_SEARCH_FAST_PATH = "memory_search_fast_path"
    KNOWLEDGE_FAST_PATH = "knowledge_fast_path"
    ERROR = "error"


@dataclass
class Message:
    """Individual message in a response.

    :param role: Message role (user, assistant, system)
    :param content: Message content
    :param tool_calls: Optional list of tool calls made
    """

    role: str
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UnifiedResponse:
    """Unified response object for all response types.

    Provides a consistent interface regardless of whether the response came
    from a fast path or full team inference.

    :param content: Main response content
    :param response_type: Source/type of response
    :param messages: List of messages (empty for fast paths)
    :param metadata: Additional metadata (execution time, path, etc.)
    :param error: Error message if response_type is ERROR
    """

    content: str
    response_type: ResponseType
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self):
        """Ensure messages is always a list."""
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_error(self) -> bool:
        """Check if this is an error response.

        :return: True if response_type is ERROR
        """
        return self.response_type == ResponseType.ERROR

    @property
    def is_fast_path(self) -> bool:
        """Check if this came from a fast path.

        :return: True if response came from fast path
        """
        return self.response_type != ResponseType.TEAM_INFERENCE and not self.is_error

    @property
    def execution_time_ms(self) -> float:
        """Get execution time from metadata.

        :return: Execution time in milliseconds, or 0 if not set
        """
        return self.metadata.get("execution_time_ms", 0.0)


class ResponseBuilder:
    """Helper builder for creating typed responses."""

    @staticmethod
    def memory_fast_path(
        content: str,
        execution_time_sec: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UnifiedResponse:
        """Create a memory fast path response.

        :param content: Response content
        :param execution_time_sec: Execution time in seconds
        :param metadata: Additional metadata
        :return: UnifiedResponse object
        """
        return UnifiedResponse(
            content=content,
            response_type=ResponseType.MEMORY_FAST_PATH,
            messages=[],
            metadata={
                **(metadata or {}),
                "execution_time_ms": execution_time_sec * 1000,
                "path": "fast_path_memory",
            },
        )

    @staticmethod
    def memory_search_fast_path(
        content: str,
        execution_time_sec: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UnifiedResponse:
        """Create a memory search fast path response.

        :param content: Response content
        :param execution_time_sec: Execution time in seconds
        :param metadata: Additional metadata
        :return: UnifiedResponse object
        """
        return UnifiedResponse(
            content=content,
            response_type=ResponseType.MEMORY_SEARCH_FAST_PATH,
            messages=[],
            metadata={
                **(metadata or {}),
                "execution_time_ms": execution_time_sec * 1000,
                "path": "fast_path_memory_search",
            },
        )

    @staticmethod
    def knowledge_fast_path(
        content: str,
        execution_time_sec: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UnifiedResponse:
        """Create a knowledge fast path response.

        :param content: Response content
        :param execution_time_sec: Execution time in seconds
        :param metadata: Additional metadata
        :return: UnifiedResponse object
        """
        return UnifiedResponse(
            content=content,
            response_type=ResponseType.KNOWLEDGE_FAST_PATH,
            messages=[],
            metadata={
                **(metadata or {}),
                "execution_time_ms": execution_time_sec * 1000,
                "path": "fast_path_knowledge",
            },
        )

    @staticmethod
    def team_inference(
        content: str,
        execution_time_sec: float,
        messages: Optional[List[Message]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UnifiedResponse:
        """Create a team inference response.

        :param content: Response content
        :param execution_time_sec: Execution time in seconds
        :param messages: List of messages (optional)
        :param metadata: Additional metadata
        :return: UnifiedResponse object
        """
        return UnifiedResponse(
            content=content,
            response_type=ResponseType.TEAM_INFERENCE,
            messages=messages or [],
            metadata={
                **(metadata or {}),
                "execution_time_ms": execution_time_sec * 1000,
                "path": "team_inference",
            },
        )

    @staticmethod
    def error(error_message: str, original_error: Optional[Exception] = None) -> UnifiedResponse:
        """Create an error response.

        :param error_message: Error message
        :param original_error: Original exception (for logging)
        :return: UnifiedResponse object with ERROR type
        """
        return UnifiedResponse(
            content=f"Error: {error_message}",
            response_type=ResponseType.ERROR,
            messages=[],
            metadata={"error_type": type(original_error).__name__ if original_error else "unknown"},
            error=error_message,
        )
