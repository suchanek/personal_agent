"""
Enhanced Memory Schema for Personal Agent

This module provides EnhancedUserMemory, a wrapper around Agno's UserMemory
that adds proxy tracking and confidence scoring capabilities.

Author: Eric G. Suchanek, PhD
Created: 2025-11-06
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from agno.memory.v2.schema import UserMemory


@dataclass
class EnhancedUserMemory:
    """
    Enhanced memory wrapper with proxy tracking and confidence scoring.

    This class wraps Agno's UserMemory and adds additional fields needed
    for team/proxy agent functionality without modifying the base class.

    Attributes:
        base_memory: The underlying UserMemory object
        confidence: Confidence score for the memory (0.0-1.0)
        is_proxy: Flag indicating if memory was created by a proxy agent
        proxy_agent: Name of the proxy agent that created this memory
    """

    base_memory: UserMemory
    confidence: float = 1.0
    is_proxy: bool = False
    proxy_agent: Optional[str] = None

    # Delegate properties to base_memory for transparent access
    @property
    def memory(self) -> str:
        """Get the memory text."""
        return self.base_memory.memory

    @memory.setter
    def memory(self, value: str):
        """Set the memory text."""
        self.base_memory.memory = value

    @property
    def topics(self) -> Optional[List[str]]:
        """Get the memory topics."""
        return self.base_memory.topics

    @topics.setter
    def topics(self, value: Optional[List[str]]):
        """Set the memory topics."""
        self.base_memory.topics = value

    @property
    def input(self) -> Optional[str]:
        """Get the input text."""
        return self.base_memory.input

    @input.setter
    def input(self, value: Optional[str]):
        """Set the input text."""
        self.base_memory.input = value

    @property
    def last_updated(self) -> Optional[datetime]:
        """Get the last updated timestamp."""
        return self.base_memory.last_updated

    @last_updated.setter
    def last_updated(self, value: Optional[datetime]):
        """Set the last updated timestamp."""
        self.base_memory.last_updated = value

    @property
    def memory_id(self) -> Optional[str]:
        """Get the memory ID."""
        return self.base_memory.memory_id

    @memory_id.setter
    def memory_id(self, value: Optional[str]):
        """Set the memory ID."""
        self.base_memory.memory_id = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary with all fields.

        Returns:
            Dictionary containing all memory data including enhanced fields
        """
        result = self.base_memory.to_dict()
        result.update(
            {
                "confidence": self.confidence,
                "is_proxy": self.is_proxy,
                "proxy_agent": self.proxy_agent,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedUserMemory":
        """
        Deserialize from dictionary with backward compatibility.

        Args:
            data: Dictionary containing memory data

        Returns:
            EnhancedUserMemory instance
        """
        # Extract enhanced fields (with defaults for backward compatibility)
        confidence = data.pop("confidence", 1.0)
        is_proxy = data.pop("is_proxy", False)
        proxy_agent = data.pop("proxy_agent", None)

        # Create base UserMemory from remaining data
        base_memory = UserMemory.from_dict(data)

        return cls(
            base_memory=base_memory,
            confidence=confidence,
            is_proxy=is_proxy,
            proxy_agent=proxy_agent,
        )

    @classmethod
    def from_user_memory(
        cls,
        user_memory: UserMemory,
        confidence: float = 1.0,
        is_proxy: bool = False,
        proxy_agent: Optional[str] = None,
    ) -> "EnhancedUserMemory":
        """
        Create EnhancedUserMemory from an existing UserMemory.

        Args:
            user_memory: Base UserMemory object
            confidence: Confidence score (default: 1.0)
            is_proxy: Whether created by proxy (default: False)
            proxy_agent: Name of proxy agent (default: None)

        Returns:
            EnhancedUserMemory wrapping the UserMemory
        """
        return cls(
            base_memory=user_memory,
            confidence=confidence,
            is_proxy=is_proxy,
            proxy_agent=proxy_agent,
        )

    def to_user_memory(self) -> UserMemory:
        """
        Extract the base UserMemory object.

        Returns:
            The underlying UserMemory object
        """
        return self.base_memory

    def __repr__(self) -> str:
        """String representation."""
        proxy_info = f" (proxy: {self.proxy_agent})" if self.is_proxy else ""
        conf_info = f" conf={self.confidence:.2f}" if self.confidence != 1.0 else ""
        return f"EnhancedUserMemory(id={self.memory_id}, memory='{self.memory[:50]}...'{proxy_info}{conf_info})"


def ensure_enhanced_memory(
    memory: Any,
    confidence: float = 1.0,
    is_proxy: bool = False,
    proxy_agent: Optional[str] = None,
) -> EnhancedUserMemory:
    """
    Ensure a memory object is an EnhancedUserMemory.

    Args:
        memory: UserMemory or EnhancedUserMemory object
        confidence: Confidence score to use if creating new enhanced memory
        is_proxy: Proxy flag to use if creating new enhanced memory
        proxy_agent: Proxy agent name to use if creating new enhanced memory

    Returns:
        EnhancedUserMemory object
    """
    if isinstance(memory, EnhancedUserMemory):
        return memory
    elif isinstance(memory, UserMemory):
        return EnhancedUserMemory.from_user_memory(
            memory, confidence=confidence, is_proxy=is_proxy, proxy_agent=proxy_agent
        )
    else:
        raise TypeError(
            f"Expected UserMemory or EnhancedUserMemory, got {type(memory)}"
        )


def extract_user_memory(memory: Any) -> UserMemory:
    """
    Extract UserMemory from either UserMemory or EnhancedUserMemory.

    Args:
        memory: UserMemory or EnhancedUserMemory object

    Returns:
        UserMemory object
    """
    if isinstance(memory, EnhancedUserMemory):
        return memory.to_user_memory()
    elif isinstance(memory, UserMemory):
        return memory
    else:
        raise TypeError(
            f"Expected UserMemory or EnhancedUserMemory, got {type(memory)}"
        )
