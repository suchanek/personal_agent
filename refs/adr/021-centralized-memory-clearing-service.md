# ADR-021: Centralized Memory Clearing Service

## Context

The previous memory clearing system had two major problems:
1.  **Incomplete Clearing**: It failed to clear the `memory_inputs` directory, which contains raw files for LightRAG processing. This could lead to unintended data reprocessing.
2.  **Code Duplication**: The logic for clearing different parts of the memory system (semantic memories, LightRAG documents, etc.) was scattered across multiple files, including `MemoryClearingManager` and `AgentMemoryManager`. This violated the DRY (Don't Repeat Yourself) principle, making the system difficult to maintain and prone to inconsistencies.

A unified, reliable, and maintainable solution was needed to ensure that all memory components are cleared consistently and completely from a single, authoritative source.

## Decision

We decided to implement a **Centralized Memory Clearing Service** to consolidate all memory deletion logic into a single, reusable class.

The key components of this decision are:
1.  **Create `MemoryClearingService`**: A new service class, located at `src/personal_agent/core/memory_clearing_service.py`, is now the single source of truth for all memory clearing operations. It includes methods to clear:
    - The `memory_inputs` directory (new functionality).
    - Local semantic memories (SQLite).
    - LightRAG documents.
    - LightRAG knowledge graph files.
    - LightRAG server cache.
2.  **Refactor Existing Managers**: All existing classes responsible for memory clearing (`MemoryClearingManager`, `AgentMemoryManager`) were refactored to be thin wrappers that delegate all clearing operations to the new `MemoryClearingService`.
3.  **Introduce Structured Results**: The service returns detailed result objects (`ClearingResult`) for each operation, providing clear status, counts, and error messages.
4.  **Add Comprehensive Testing**: A new, dedicated test suite (`memory_tests/test_centralized_memory_clearing.py`) was created to validate the functionality of the new service, including its integration with existing managers, error handling, and dry-run capabilities.

## Consequences

### Positive
- **Completeness**: The memory clearing process now correctly includes the `memory_inputs` directory, ensuring a full and clean reset.
- **Maintainability**: All clearing logic is now in one place, making it easy to update, debug, and extend. Code duplication has been eliminated.
- **Reliability**: The system behaves consistently across all entry points (CLI, agent tools), as they all use the same underlying service.
- **Testability**: The centralized service is easier to test in isolation, and the new test suite provides robust coverage.
- **Clarity**: The structured result objects provide clear and detailed feedback on what was cleared, improving transparency.

### Negative
- **Increased Abstraction**: The introduction of a new service layer adds a level of abstraction, which might require a slight learning curve for new developers. However, the benefits of centralization and clarity far outweigh this minor complexity.
