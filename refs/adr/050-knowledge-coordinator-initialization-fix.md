# 50. Knowledge Coordinator Initialization Fix

- **Date**: 2025-08-06
- **Status**: Accepted

## Context

The `KnowledgeTools` class, responsible for all knowledge base interactions, uses a `KnowledgeCoordinator` to route queries between the local semantic knowledge base (`agno_knowledge`) and the global LightRAG server.

A bug was discovered where the `KnowledgeCoordinator` was not being properly initialized within the `KnowledgeTools` class. The `self.knowledge_coordinator` attribute was initialized to `None` in the constructor, but the `create_knowledge_coordinator` function was only called within the `query_knowledge_base` method. This lazy initialization approach is fragile and led to a situation where the coordinator was not available when other methods in the class might have needed it.

Furthermore, the `AgnoPersonalAgent` was not passing the `agno_knowledge` object to the `KnowledgeTools` constructor, meaning that even when the coordinator was created, it lacked a reference to the local knowledge base, making it unable to perform local or hybrid queries.

## Decision

1.  **Fix `AgnoPersonalAgent` Initialization**: The `AgnoPersonalAgent`'s `_do_initialization` method will be modified to correctly pass the `self.agno_knowledge` instance to the `KnowledgeTools` constructor.

2.  **Fix `KnowledgeTools` Initialization**: The `KnowledgeTools` constructor will be refactored to initialize the `KnowledgeCoordinator` immediately, ensuring it is always available. The `create_knowledge_coordinator` function will be called directly in the `__init__` method, using the `agno_knowledge` object passed in.

This ensures that the `KnowledgeCoordinator` is instantiated correctly with all its dependencies as soon as `KnowledgeTools` is created, resolving the bug and making the class more robust.

## Consequences

- **Bug Fix**: The immediate and correct initialization of the `KnowledgeCoordinator` ensures that all knowledge queries will be routed correctly, restoring full functionality to the knowledge base tools.
- **Improved Robustness**: Eagerly initializing the coordinator in the constructor makes the `KnowledgeTools` class more reliable and less prone to initialization-related errors.
- **Code Clarity**: The initialization logic is now more straightforward and easier to understand.
