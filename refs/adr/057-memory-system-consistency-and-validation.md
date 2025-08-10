# ADR-057: Memory System Consistency, Validation, and Cleanup

## Status

Accepted

## Context

The agent's memory system exhibited several inconsistencies. The `show-config` tool was not synchronized with the `AgentMemoryManager`, the `clear_all_memories` function was incomplete, and the Streamlit UIs (`agno` and `team`) used incorrect deletion logic. This led to user confusion, orphaned data in the LightRAG graph memory system, and an inconsistent user experience when managing memories.

## Decision

To address these issues, a multi-faceted solution was implemented:

1.  **Comprehensive Memory Clearing**: The `clear_all_memories` method in `AgentMemoryManager` has been refactored to clear data from both the local SQLite database and the LightRAG graph memory server.

2.  **Consolidated UI Deletion Logic**: The memory deletion functionality in both the single-agent (`paga_streamlit_agno.py`) and team (`paga_streamlit_team.py`) Streamlit interfaces has been refactored to use the single, authoritative `AgentMemoryManager.delete_memory` method. This ensures all deletions correctly remove data from both local and graph storage systems.

3.  **Synchronized Tool Listing**: The memory tools list in `src/personal_agent/tools/show_config.py` is now updated to accurately match the public methods of `AgentMemoryManager`.

4.  **Clarify Dependencies and Dynamic User ID**: Tools that require the LightRAG memory server are now explicitly annotated, and the `show-config` tool now uses the dynamic `settings.get_userid()` function.

5.  **Introduce a Validation Script**: A new debug script, `scripts/debug_memory_tools.py`, has been created to programmatically validate memory tool consistency.

## Consequences

### Positive

- The `clear_all_memories` tool is now reliable and prevents data inconsistencies between the two memory systems.
- The `show-config` output is now an accurate and reliable source of information for available memory tools.
- Users can clearly see which tools depend on the LightRAG memory server.
- The displayed configuration is consistent with the dynamic multi-user system.
- The new validation script provides a mechanism for automated regression testing.

### Negative

- None.

### Neutral

- A new script has been added to the project for maintenance and validation purposes.