# 076. Formalize Memory Schemas and Diagnostics

- **Status**: Accepted
- **Date**: 2025-08-26

## Context and Problem Statement

The agent's memory subsystem has evolved, resulting in multiple, similar-but-distinct memory object schemas (e.g., legacy `agno.memory.memory.Memory` vs. the current `agno.memory.v2.schema.UserMemory`). A key difference is the unique identifier field (`id` in the legacy version vs. `memory_id` in the current version). This distinction was not formally documented, leading to developer confusion and causing subtle bugs where code would attempt to access the wrong attribute.

Furthermore, system health checks were fragmented across numerous scripts in the `tests/` and `memory_tests/` directories. This made it difficult and inefficient to perform a quick, comprehensive diagnostic of the agent's core functionalities.

## Decision

To address these issues, we will implement a two-part solution:

1.  **Formalize Schemas**: Create a definitive documentation file, `refs/MEMORY_SUBSYSTEM_SCHEMAS.md`, to serve as the single source of truth for all memory-related data structures. This document will clearly outline the different schemas, their fields, and their intended use.
2.  **Unify Diagnostics**: Implement a new, unified diagnostic script at `scripts/run_diagnostics.py`. This script will provide a modular, easy-to-use interface for testing the health of all major subsystems (Configuration, Memory, Tools, etc.) and will correctly implement the newly documented schemas, resolving existing bugs.

## Consequences

-   **Positive**:
    -   **Reduced Ambiguity**: Provides a single source of truth for memory schemas, reducing developer confusion and onboarding time.
    -   **Improved Stability**: Eliminates a class of bugs related to schema mismatches. The new diagnostic script correctly uses `memory_id`, preventing recurrence.
    -   **Efficient Testing**: A single, easy-to-run script (`python scripts/run_diagnostics.py`) for verifying system health improves developer workflow and maintainability.
    -   **Centralized Logic**: Consolidates testing logic into a single, extensible framework.

-   **Negative**:
    -   **Maintenance Overhead**: The new documentation and diagnostic script will require maintenance as the agent evolves.
