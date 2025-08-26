# Memory Subsystem Schemas Documentation

This document provides a comprehensive overview of the memory schemas and types used in the Personal Agent memory subsystem.

## Overview

The Personal Agent uses the Agno library for memory management, which provides a layered architecture with different schema types for various memory operations. The memory subsystem supports both user memories and session summaries with different representations at different layers.

## Core Memory Types

### 1. UserMemory (Application Layer)

**Location**: `agno.memory.v2.schema.UserMemory`

The primary memory type for storing user-specific information and facts.

```python
@dataclass
class UserMemory:
    """Model for User Memories"""
    
    memory: str                           # The actual memory content/text
    topics: Optional[List[str]] = None    # Associated topics for categorization
    input: Optional[str] = None           # Original input that generated this memory
    last_updated: Optional[datetime] = None  # Timestamp of last update
    memory_id: Optional[str] = None       # Unique identifier for the memory
```

**Key Features:**
- Uses `memory_id` as the unique identifier (NOT `id`)
- Supports topic-based categorization
- Tracks original input context
- Includes timestamp tracking
- Provides `to_dict()` and `from_dict()` methods for serialization

### 2. SessionSummary (Application Layer)

**Location**: `agno.memory.v2.schema.SessionSummary`

Used for storing summaries of conversation sessions.

```python
@dataclass
class SessionSummary:
    """Model for Session Summary."""
    
    summary: str                          # Summary text of the session
    topics: Optional[List[str]] = None    # Topics discussed in the session
    last_updated: Optional[datetime] = None  # Timestamp of last update
```

**Key Features:**
- Focuses on session-level information
- Topic-based organization
- Timestamp tracking
- Serialization support

## Database Layer Schemas

### 3. MemoryRow (Database Layer)

**Location**: `agno.memory.v2.db.schema.MemoryRow`

The database representation of memories, used for persistence.

```python
class MemoryRow(BaseModel):
    """Memory Row that is stored in the database"""
    
    id: Optional[str] = None              # Auto-generated UUID if not provided
    memory: Dict[str, Any]                # Serialized memory data
    user_id: Optional[str] = None         # User identifier
    last_updated: Optional[datetime] = None  # Timestamp
```

**Key Features:**
- Uses Pydantic BaseModel
- Auto-generates UUID for `id` field
- Stores memory as serialized dictionary
- Multi-user support via `user_id`

### 4. SummaryRow (Database Layer)

**Location**: `agno.memory.v2.db.schema.SummaryRow`

Database representation for session summaries.

```python
class SummaryRow(BaseModel):
    """Session Summary Row that is stored in the database"""
    
    id: Optional[str] = None              # Auto-generated UUID
    summary: Dict[str, Any]               # Serialized summary data
    user_id: Optional[str] = None         # User identifier
    last_updated: Optional[datetime] = None  # Timestamp
```

## Legacy Memory Types

### 5. Memory (Legacy)

**Location**: `agno.memory.memory.Memory`

The original memory model, still used in some contexts.

```python
class Memory(BaseModel):
    """Model for Agent Memories"""
    
    memory: str                           # Memory content
    id: Optional[str] = None              # Identifier (note: uses 'id', not 'memory_id')
    topic: Optional[str] = None           # Single topic (not a list)
    input: Optional[str] = None           # Original input
```

**Key Differences from UserMemory:**
- Uses `id` instead of `memory_id`
- Single `topic` instead of `topics` list
- No timestamp tracking
- Simpler structure

### 6. SessionSummary (Legacy)

**Location**: `agno.memory.summary.SessionSummary`

Legacy session summary model.

```python
class SessionSummary(BaseModel):
    """Model for Session Summary."""
    
    summary: str                          # Summary content with field description
    topics: Optional[List[str]] = None    # Topics list
```

## Memory Retrieval Types

### 7. MemoryRetrieval Enum

**Location**: `agno.memory.memory.MemoryRetrieval`

Defines different memory retrieval strategies.

```python
class MemoryRetrieval(str, Enum):
    last_n = "last_n"        # Retrieve last N memories
    first_n = "first_n"      # Retrieve first N memories  
    semantic = "semantic"    # Semantic similarity-based retrieval
```

## Personal Agent Extensions

### 8. MemoryStorageResult

**Location**: `src/personal_agent/core/semantic_memory_manager.py`

Enhanced result type for memory operations.

```python
@dataclass
class MemoryStorageResult:
    """Structured result for memory storage operations."""
    
    status: MemoryStorageStatus          # Success/failure status
    memory_id: Optional[str] = None      # ID of stored memory
    message: str = ""                    # Status message
    duplicate_of: Optional[str] = None   # ID of duplicate memory if rejected
```

### 9. MemoryStorageStatus Enum

```python
class MemoryStorageStatus(Enum):
    """Enum for memory storage operation results."""
    
    SUCCESS = "success"
    REJECTED_DUPLICATE = "rejected_duplicate"
    REJECTED_INVALID = "rejected_invalid"
    ERROR = "error"
```

## Key Architecture Points

### Schema Evolution
- **v1 (Legacy)**: Simple `Memory` and `SessionSummary` models
- **v2 (Current)**: Enhanced `UserMemory` and `SessionSummary` with better structure

### Identifier Naming
- **Legacy Memory**: Uses `id` field
- **Current UserMemory**: Uses `memory_id` field
- **Database Layer**: Uses `id` field (auto-generated UUID)

### Multi-User Support
- Database layer includes `user_id` for multi-tenant support
- Application layer memories are user-scoped through the database layer

### Topic Management
- **Legacy**: Single `topic` string
- **Current**: `topics` list for multiple categorizations

### Serialization
- All models provide `to_dict()` methods
- Database models use Pydantic for validation
- Application models use dataclasses with custom serialization

## Usage in Diagnostic Script

The diagnostic script error was caused by attempting to access `test_memory.id` on a `UserMemory` object, which uses `memory_id` instead. This highlights the importance of understanding the schema differences between legacy and current memory types.

**Correct Usage:**
```python
# For UserMemory objects (v2)
memory_id = test_memory.memory_id

# For legacy Memory objects (v1)  
memory_id = test_memory.id
```

## Database Operations

The memory subsystem uses the `MemoryDb` abstract base class for database operations:

- `create()`: Initialize database tables
- `memory_exists()`: Check for memory existence
- `read_memories()`: Retrieve memories with filtering
- `upsert_memory()`: Insert or update memories
- `delete_memory()`: Remove memories by ID
- `clear()`: Clear all memories

This layered approach provides flexibility while maintaining data consistency across the memory subsystem.
