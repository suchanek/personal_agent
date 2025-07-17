# ADR 011: Enum-Based Memory Storage Status

## Status

Accepted

## Context

The `store_user_memory` tool and its underlying `SemanticMemoryManager.add_memory` method had an ambiguous return contract. Specifically, when a memory was rejected (e.g., as a duplicate), the method could return `None` or a simple string message. This made it difficult for calling code to programmatically determine the outcome of a storage operation, leading to fragile logic and unclear user feedback.

The key issues were:
- **Ambiguous `None` returns**: A `None` return for a rejected memory was not explicit and could be confused with other failure modes.
- **Unstructured string messages**: Relying on parsing string messages like "Duplicate memory" is brittle.
- **Lack of detailed metadata**: The system did not provide rich information about *why* a memory was rejected (e.g., exact vs. semantic duplicate) or metadata like similarity scores.
- **Poor dual-storage awareness**: With the introduction of a dual-storage system (local SQLite and LightRAG graph), it was difficult to determine the success status for each system individually.

## Decision

To address these issues, we decided to implement a more robust, explicit, and type-safe system for handling memory storage outcomes. The core of this decision is the introduction of an `Enum` for status codes and a `dataclass` for structured results.

### 1. `MemoryStorageStatus` Enum

We created a new `MemoryStorageStatus` enum to represent all possible outcomes of a memory storage operation. This provides a clear, explicit, and type-safe way to represent the status.

```python
from enum import Enum, auto

class MemoryStorageStatus(Enum):
    """Enum for memory storage operation results."""
    SUCCESS = auto()
    SUCCESS_LOCAL_ONLY = auto()
    DUPLICATE_EXACT = auto()
    DUPLICATE_SEMANTIC = auto()
    CONTENT_EMPTY = auto()
    CONTENT_TOO_LONG = auto()
    STORAGE_ERROR = auto()
    VALIDATION_ERROR = auto()
```

### 2. `MemoryStorageResult` Dataclass

We introduced a `MemoryStorageResult` dataclass to encapsulate the result of a storage operation. This object contains the status enum, a human-readable message, and other relevant metadata.

```python
from dataclasses import dataclass
from typing import List, Optional

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
        return self.status in [MemoryStorageStatus.SUCCESS, MemoryStorageStatus.SUCCESS_LOCAL_ONLY]

    @property
    def is_rejected(self) -> bool:
        """True if memory was rejected."""
        return self.status in [
            MemoryStorageStatus.DUPLICATE_EXACT,
            MemoryStorageStatus.DUPLICATE_SEMANTIC,
            MemoryStorageStatus.CONTENT_EMPTY,
            MemoryStorageStatus.CONTENT_TOO_LONG,
            MemoryStorageStatus.VALIDATION_ERROR
        ]
```

### 3. Refactoring Core Methods

The following methods were refactored to use the new enum and dataclass:

- **`SemanticMemoryManager.add_memory()`**:
    - **Before**: Returned `Tuple[bool, str, Optional[str], Optional[List[str]]]`
    - **After**: Returns a `MemoryStorageResult` object.
    - The logic was updated to perform validation (content empty, too long) and duplicate checks (exact, semantic) and return the appropriate structured result.

- **`AgnoPersonalAgent.store_user_memory()`**:
    - **Before**: Returned a `str`.
    - **After**: Returns a `MemoryStorageResult` object.
    - This method now orchestrates the dual storage (local and graph) and sets the final status (`SUCCESS` or `SUCCESS_LOCAL_ONLY`) based on the outcome of each storage attempt.

- **Tool Wrapper (`_store_user_memory_tool`)**:
    - The tool wrapper was updated to consume the `MemoryStorageResult` object and format it into a user-friendly string with appropriate emojis (✅, ⚠️, 🔄, ❌) to provide clear feedback.

## Consequences

### Positive

- **Clarity and Type Safety**: The new system is explicit and type-safe, eliminating the ambiguity of `None` returns.
- **Rich Metadata**: The `MemoryStorageResult` provides valuable metadata, such as `similarity_score` for duplicates and separate flags for `local_success` and `graph_success`.
- **Improved User Feedback**: The tool can now provide much clearer and more consistent feedback to the user.
- **Robustness**: The code is less brittle as it no longer relies on string parsing to determine outcomes.
- **Extensibility**: The enum and dataclass can be easily extended with new statuses and fields as the system evolves.
- **Better Debugging**: The structured result makes logging and debugging memory operations much easier.

### Negative

- **Increased Complexity**: The new system introduces more code (an enum and a dataclass) and requires more effort to handle the structured result compared to a simple string or boolean. However, this is a worthwhile trade-off for the benefits gained.
- **Internal API Change**: This is a breaking change for the internal API of `SemanticMemoryManager.add_memory` and `AgnoPersonalAgent.store_user_memory`. All internal calls to these methods had to be updated. The external-facing tool interface remains a string, so user interaction is unaffected.
