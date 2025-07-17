# ADR-016: Standardized Memory Clearing Logic

**Date**: 2025-07-16

**Status**: Accepted

## Context

The agent's memory system, which uses SQLite, was exhibiting inconsistent behavior. When memories were cleared via the `memory_cleaner.py` script or the `clear_all_memories` tool, the changes were not always reflected immediately or correctly in the CLI or other parts of the system.

The root cause was traced to a synchronization issue between different components accessing the memory database. The `memory_cleaner.py` script and the main agent were using slightly different database initialization patterns and connection management, leading to situations where one component would not see the changes made by another.

## Decision

To resolve this, we will standardize the memory clearing and database access logic across the entire application.

1.  **Unified Database Initialization**: All components that interact with the SQLite memory database, including the main agent, CLI tools, and utility scripts like `memory_cleaner.py`, will use the exact same database initialization logic. This ensures every part of the system connects to the correct database file with consistent settings.

2.  **Force Connection Closure**: The memory clearing process will now explicitly close all database connections after the operation is complete.

3.  **SQLite VACUUM**: A `VACUUM` operation will be performed after clearing the tables. This rebuilds the database file, which helps in reducing the file size and ensures that the deletion is fully committed and visible to all subsequent connections.

4.  **Verification**: The updated `memory_cleaner.py` script now includes a verification step to confirm that the memory tables are empty after the clearing operation, providing immediate feedback on the success of the operation.

## Consequences

**Positive**:
-   **Data Consistency**: Memory clearing is now reliable and consistent across all parts of the system.
-   **Improved Stability**: Eliminates a source of bugs and unpredictable behavior related to memory management.
-   **Testability**: The fix is validated by a new test script, `test_memory_clearing_fix.py`, ensuring the solution remains robust.

**Negative**:
-   None identified. This change is a strict improvement to system reliability.
