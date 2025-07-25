# ADR 038: Standardized Memory Clearing

## Status

**Accepted**

## Context

The agent utilizes a dual-memory system: a local SQLite database for semantic search and a LightRAG server for graph-based memory. Previously, the mechanisms for clearing these two stores were not synchronized, leading to inconsistencies. The `clear_all_memories.py` script and the agent's `--recreate` flag did not reliably clear both memory systems, resulting in data persistence issues and unpredictable behavior. This was caused by disparate database connection handling and a lack of a unified clearing process.

## Decision

We will implement a standardized, unified approach to memory clearing that ensures atomicity and consistency across both local and graph memory systems. This will be achieved through the following:

1.  **Centralized Clearing Logic**: A single, authoritative `MemoryClearingManager` will be responsible for orchestrating the clearing of both memory systems.
2.  **Standardized Connection Handling**: All components will use a standardized method for database connections to ensure consistency.
3.  **Agent Integration**: The `MemoryClearingManager` will be integrated into the agent's startup sequence, ensuring the `--recreate` flag is handled correctly and consistently.
4.  **Script Unification**: The `clear_all_memories.py` script will be updated to use the new `MemoryClearingManager`, ensuring a single, reliable method for manual memory clearing.

## Consequences

### Positive
- **Consistency**: Guarantees a consistent and clean state when clearing memories.
- **Reliability**: Reduces the risk of data-related bugs and unpredictable agent behavior.
- **Simplicity**: Simplifies the memory management architecture by centralizing clearing logic.

### Negative
- None anticipated.
