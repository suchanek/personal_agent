# ADR-035: Unified Memory and Knowledge Tools

**Date**: 2025-07-24
**Status**: Accepted

## Context

The agent's initialization process had become overly complex. Memory and knowledge-related tools were generated as a flat list of functions from different managers (`AgentMemoryManager`, `AgentKnowledgeManager`). This approach, while functional, resulted in scattered logic, made the agent's setup difficult to follow, and increased the overhead for maintenance and extension. The core agent class (`AgnoPersonalAgent`) was responsible for orchestrating the collection of these disparate tools, violating the Single Responsibility Principle.

This complexity was in stark contrast to the cleaner, more modular design patterns advocated by the underlying `agno` framework, as seen in reference examples like `persag`.

## Decision

We decided to refactor the tool management system by encapsulating all memory and knowledge-related functionalities into a single, cohesive class: `MemoryAndKnowledgeTools`.

This new class, inheriting from `agno.tools.Toolkit`, acts as a unified toolset. It is initialized with the necessary managers (`SemanticMemoryManager` and `KnowledgeManager`) and exposes all memory and knowledge operations (e.g., `store_user_memory`, `query_knowledge_base`) as its methods.

The agent's initialization is now significantly simplified. Instead of collecting and registering numerous individual tool functions, the agent now just needs to be provided with an instance of the `MemoryAndKnowledgeTools` class.

## Consequences

### Positive

-   **Improved Modularity & Cohesion**: All memory and knowledge tools are now located in a single, dedicated module (`src/personal_agent/tools/memory_and_knowledge_tools.py`), making the system easier to understand and navigate.
-   **Simplified Agent Initialization**: The `AgnoPersonalAgent`'s setup logic is much cleaner and more concise. It no longer needs to know the details of how memory or knowledge tools are created.
-   **Enhanced Maintainability**: Changes to memory or knowledge tools are now localized to the `MemoryAndKnowledgeTools` class, reducing the risk of side effects in other parts of the application.
-   **Better Alignment with `agno`**: The new architecture more closely follows the idiomatic use of the `agno` framework, which favors organizing tools into `Toolkit` classes.

### Negative

-   **Initial Refactoring Effort**: Migrating all existing tool functions into the new class required a one-time refactoring effort.
-   **Slight Indirection**: Tool calls now go through the `MemoryAndKnowledgeTools` instance, which then delegates to the appropriate manager. This is a minor and acceptable level of indirection for the significant architectural benefits gained.
