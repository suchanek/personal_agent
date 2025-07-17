# ADR 001: Unified Memory Management & Document Management Tools

*   **Status:** Implemented
*   **Date:** 2025-01-09

## Context and Problem Statement

The agent's memory and document handling capabilities had several critical gaps:

1.  **No Unified Memory Clearing**: The system lacked a comprehensive way to clear both semantic memories (local SQLite) and LightRAG graph memories simultaneously, leading to potential drift between the two memory systems.
2.  **Limited Document Management Tools**: Existing LightRAG document management was fragmented and lacked modern API-based operations, requiring manual intervention and server restarts.
3.  **Memory System Maintenance**: No systematic approach to prevent memory drift between local semantic storage and graph-based knowledge storage systems.
4.  **Legacy Script Cleanup**: Old fix scripts (`fix_lightrag_data.py`, `fix_lightrag_persistent_storage.py`) were outdated and needed removal in favor of modern tools.

## Decision Drivers

*   The need to ensure data consistency between the local and graph-based memory systems.
*   The requirement to modernize and stabilize document management by moving to API-based operations.
*   The goal of improving developer and administrator experience by providing powerful, safe, and well-documented command-line tools.

## Considered Options

*   **Continue with separate scripts:** This was rejected as it would perpetuate the problem of memory drift and fragmented tooling.
*   **Build a monolithic tool:** A single script to manage everything was considered but rejected in favor of a more modular approach with a core library and separate CLI wrappers.
*   **Adopt a modular, library-first approach:** This was the chosen solution. It involved creating core Python classes for the logic (`MemoryClearingManager`, `LightRAGDocumentManager`) and then exposing that functionality through simple CLI scripts.

## Decision Outcome

The chosen solution was to implement a comprehensive, modular system for both memory and document management.

### 1. Unified Memory Management System

A `MemoryClearingManager` class was created to provide a single point of control for clearing both semantic and LightRAG memories.

*   **Core Module:** `src/personal_agent/tools/memory_cleaner.py`
*   **CLI Wrapper:** `tools/clear_all_memories.py`
*   **Key Features:**
    *   Dual-system clearing.
    *   Safety features: dry-run mode, confirmation prompts, and post-op verification.
    *   Selective clearing (`--semantic-only`, `--lightrag-only`).
    *   User isolation support.

### 2. Enhanced LightRAG Document Management

A `LightRAGDocumentManager` class was created to interact with the LightRAG server via its API, providing stable and powerful document management capabilities.

*   **Core Module:** `src/personal_agent/tools/lightrag_document_manager.py`
*   **CLI Wrapper:** `tools/docmgr.py`
*   **Key Features:**
    *   API-based operations (no server restarts needed).
    *   Batch operations, pattern-based deletion, and a retry mechanism for failed documents.
    *   Source file management.

### 3. Enhanced Memory Restatement

The `_restate_user_fact()` method in the core agent was improved to ensure that user facts are correctly transformed for optimal storage and entity recognition in the knowledge graph.

*   **Core Logic:** `src/personal_agent/core/agno_agent.py`
*   **Testing:** `tests/test_fact_restatement.py`

## Consequences

### Positive

*   **Improved System Reliability:** Unified memory management prevents data drift.
*   **Increased Operational Efficiency:** Modern, API-based document management reduces manual work and the need for server restarts.
*   **Enhanced Data Integrity:** The improved fact restatement process leads to a better-structured and more reliable knowledge graph.
*   **Better Maintainability:** The modular, library-first approach makes the system easier to understand, maintain, and extend.
*   **Improved User/Developer Experience:** The new CLI tools are powerful, intuitive, and well-documented.

### Negative

*   **Increased Complexity:** The introduction of new core libraries and modules adds to the overall size and complexity of the codebase. However, this is a necessary trade-off for the gain in reliability and maintainability.
