# ADR-019: Modular Agent Architecture Refactoring

**Date**: 2025-07-16

**Status**: Accepted

## Context

The `AgnoPersonalAgent` class had become a monolithic entity exceeding 2,800 lines of code. It violated the Single Responsibility Principle by managing a wide range of concerns, including:

*   LLM model creation and configuration
*   Dynamic instruction generation
*   Dual-system memory management (SQLite and LightRAG)
*   Knowledge base operations
*   Tool creation and management (including MCP tools)

This complexity made the class difficult to understand, maintain, and test. Changes in one area carried a high risk of unintentionally breaking another.

## Decision

To address this technical debt and improve the long-term health of the codebase, we have refactored the `AgnoPersonalAgent` into a modular, coordinator-based architecture. The original class has been broken down into a set of specialized manager classes, each with a single, well-defined responsibility.

The new architecture is as follows:

```
AgnoPersonalAgent (Coordinator)
├── AgentModelManager
├── AgentInstructionManager
├── AgentMemoryManager
├── AgentKnowledgeManager
└── AgentToolManager
```

1.  **`AgentModelManager`**: Handles the creation and configuration of LLM models (Ollama, OpenAI, etc.).
2.  **`AgentInstructionManager`**: Manages the dynamic generation of agent instructions based on different sophistication levels.
3.  **`AgentMemoryManager`**: Encapsulates all logic for memory operations, including the dual-storage system (SQLite and LightRAG).
4.  **`AgentKnowledgeManager`**: Manages the local knowledge base (facts, preferences, entities, relationships).
5.  **`AgentToolManager`**: Handles the registration, validation, and execution of all agent tools.
6.  **`AgnoPersonalAgent` (Refactored)**: The main class now acts as a high-level coordinator. It initializes the manager components and delegates all operational logic to them, while maintaining its original public API for backward compatibility.

## Consequences

### Positive

*   **Improved Maintainability**: The codebase is now significantly easier to navigate and understand. Each manager class is small, focused, and self-contained.
*   **Enhanced Testability**: Each manager can be unit-tested in isolation, leading to more robust and reliable tests.
*   **Single Responsibility Principle**: The new architecture adheres to SOLID principles, making the system more robust and less prone to errors.
*   **Reduced Complexity**: The cognitive load required to work on any single component is drastically reduced.
*   **Greater Extensibility**: Adding new features or modifying existing ones is now much safer and more straightforward. For example, adding a new type of memory system would only require changes to the `AgentMemoryManager`.

### Negative

*   **Increased Number of Files**: The refactoring has increased the number of files in the `core` directory. This is a minor trade-off for the significant gains in clarity and maintainability.
*   **Indirection**: There is now a layer of indirection, as the main agent class delegates to the managers. However, this is a standard and beneficial pattern in well-structured software.