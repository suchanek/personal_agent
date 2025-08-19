# ADR-069: Personal Agent Team Refactoring for Separation of Concerns

**Date**: 2025-08-18
**Status**: Accepted

## Context

The `PersonalAgentTeam` coordinator was responsible for both routing tasks to specialized agents and managing memory/knowledge operations directly. This violated the Single Responsibility Principle (SRP), leading to a tightly coupled architecture, increased complexity, and a higher maintenance burden. Changes to the memory system could directly impact the core routing logic, and testing these intertwined functionalities was difficult.

The original architecture:
```
Coordinator Agent (Overloaded)
├── Routing Logic
├── Memory Tools (SRP violation)
├── Memory Storage/Retrieval
└── Team Member Delegation
    ├── Web Research Agent
    ├── Finance Agent
    └── ...
```

## Decision

To address this, we will refactor the `PersonalAgentTeam` to enforce a clean separation of concerns. The new architecture will be:

1.  **Simplify the Coordinator**: The coordinator agent will be stripped of all memory and knowledge tools. Its sole responsibility will be to route incoming queries to the appropriate specialist agent based on a clear set of rules. It will have no tools of its own.

2.  **Introduce a Dedicated Knowledge Agent**: A new agent, an instance of `AgnoPersonalAgent`, will be added to the team. This "Knowledge Agent" will be the exclusive handler for all memory and knowledge-related operations, including storage, retrieval, and querying.

3.  **Update Team Structure**: The Knowledge Agent will be the first member of the team to ensure it has priority for memory-related tasks.

The new, refactored architecture:
```
Coordinator Agent (Pure Router)
├── Routing Logic ONLY
└── Delegates to Specialized Agents:
    ├── Knowledge Agent (AgnoPersonalAgent)
    │   ├── Memory & Knowledge Tools
    │   └── All Memory/Knowledge Operations
    ├── Web Research Agent
    ├── Finance Agent
    └── ...
```

This decision also includes fixing two critical bugs discovered during the refactoring process:
-   An initialization bug where `AgnoPersonalAgent` would not load memory tools correctly when `alltools=False`.
-   An `UnboundLocalError` caused by a redundant, incorrectly scoped `asyncio` import.

## Consequences

### Positive
-   **Improved Maintainability**: The coordinator and memory systems can be modified independently.
-   **Adherence to SRP**: Each agent has a single, well-defined purpose.
-   **Simplified Testing**: Routing and memory functionality can be tested in isolation.
-   **Loose Coupling**: The coordinator is no longer tightly coupled to the implementation details of the memory system.
-   **Architectural Clarity**: The flow of information and delegation of tasks is more logical and easier to understand.

### Negative
-   **Slight Overhead**: Introduces one additional agent instance to the team, which may have a minimal impact on memory usage. The routing step adds a small amount of latency, though this is expected to be negligible.

### Backward Compatibility
-   The refactoring is designed to be fully backward compatible. All external interfaces, particularly for the Streamlit UI, are preserved. The `TeamWrapper` class was updated to access the memory system through the new Knowledge Agent, ensuring no breaking changes for consumers.