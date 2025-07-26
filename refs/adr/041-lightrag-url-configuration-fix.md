# ADR 041: LightRAG URL Configuration Fix

## Status

**Accepted**

## Context

The agent was experiencing issues communicating with the LightRAG server, specifically when attempting to query the knowledge base. Analysis revealed that the `query_lightrag_knowledge_direct` method in `agno_agent.py` was incorrectly configured, and there was a lack of clarity regarding which LightRAG instance (knowledge or memory) should be used for different types of queries. The `KnowledgeCoordinator` was also not explicitly designed to differentiate between these two LightRAG instances.

## Decision

To resolve these communication issues and ensure proper routing of LightRAG queries, the following clarifications and changes will be implemented:

1.  **`agno_agent.py` - `query_lightrag_knowledge_direct`**: This method will consistently use `LIGHTRAG_URL` for general knowledge queries. Its purpose is to query the main LightRAG knowledge server.
2.  **`knowledge_coordinator.py`**: This module will import both `LIGHTRAG_URL` (for knowledge queries) and `LIGHTRAG_MEMORY_URL` (for memory queries). The `KnowledgeCoordinator`'s role is to route queries to the appropriate LightRAG instance based on the query type. It will use `LIGHTRAG_URL` when routing to the knowledge base and delegate memory-specific LightRAG interactions to the `memory_manager` which uses `LIGHTRAG_MEMORY_URL`.
3.  **`memory_manager`**: The `memory_manager` will be explicitly responsible for all interactions with the LightRAG memory server, ensuring it consistently uses `LIGHTRAG_MEMORY_URL` for memory-related operations (e.g., storing graph memories, querying graph memories).

## Consequences

### Positive

-   **Improved LightRAG Communication**: The agent will now correctly communicate with both the main LightRAG server and the LightRAG memory server, resolving previous communication failures.
-   **Accurate Query Routing**: Queries will be accurately routed to the intended LightRAG instance, ensuring that knowledge base and memory queries are handled by the correct services.
-   **Enhanced Stability**: The fix will contribute to the overall stability and reliability of the agent's LightRAG integration.

### Negative

-   None anticipated.
