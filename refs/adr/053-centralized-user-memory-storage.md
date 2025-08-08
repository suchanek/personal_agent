# ADR-053: Centralized User Memory Storage

## Status

**Proposed**

## Context

The project contains multiple agent implementations (e.g., `BasicMemoryAgent`, `PersonalAgentTeam`, `SpecializedAgent`). Previously, each of these implementations had its own logic for handling user memory storage, particularly the `store_user_memory` tool. This led to significant code duplication and inconsistencies, especially regarding complex features like:

*   **Memory Restatement**: Converting first-person user facts into a third-person format for accurate knowledge graph ingestion.
*   **Dual Storage**: Persisting memories to both the local SQLite database and the LightRAG graph memory system.
*   **Duplicate Detection**: Handling duplicate memories consistently.
*   **Topic Parsing**: Processing topic strings from the LLM.

This decentralized approach made the system difficult to maintain and created a risk of divergent behavior between different agents.

## Decision

We will centralize all user memory storage operations within the `AgentMemoryManager`. All agent implementations that require memory storage capabilities will now instantiate and delegate to the `AgentMemoryManager` instead of implementing their own `store_user_memory` logic.

This involves refactoring the `store_user_memory` tool in `BasicMemoryAgent`, `PersonalAgentTeam`, and `SpecializedAgent` to use `AgentMemoryManager.store_user_memory()`.

## Consequences

### Pros

*   **Consistency & Reliability**: Guarantees that all agents use the exact same, battle-tested logic for storing memories, including restatement, dual storage, and error handling.
*   **Maintainability**: Radically simplifies maintenance. Changes or bug fixes to memory storage logic only need to be made in the `AgentMemoryManager`, eliminating code duplication and reducing the surface area for errors.
*   **Code Simplification**: Removes redundant and complex memory storage code from multiple agent and team definitions, making them cleaner and more focused on their primary roles.

### Cons

*   **Tighter Coupling**: Introduces a direct dependency on `AgentMemoryManager` for any agent that needs to store memories. However, given that this is a core, cross-cutting concern, this coupling is justified for the benefits gained.
