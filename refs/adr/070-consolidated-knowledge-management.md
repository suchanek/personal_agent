# 070-consolidated-knowledge-management

## Consolidated Knowledge Management

**Status:** Accepted

**Context:**
Previously, the agent's knowledge management was distributed across multiple components, leading to redundancy, increased complexity, and inconsistent handling of semantic (LanceDB) and graph (LightRAG) knowledge bases. While ADR-063 addressed the consolidation of knowledge *ingestion*, the management and querying aspects still suffered from a fragmented architecture. This resulted in duplicated logic for querying, updating, and maintaining the two distinct knowledge stores, making it challenging to ensure data consistency and optimize retrieval.

**Decision:**
We have refactored and enhanced the `KnowledgeManager` to serve as the single, authoritative interface for all knowledge-related operations, encompassing both semantic and graph knowledge bases. This refactoring involves:

1.  **Centralizing Query Logic:** All knowledge queries, regardless of whether they target the semantic or graph store, will now be routed through the `KnowledgeManager`. This manager will intelligently determine the appropriate backend based on the query mode (e.g., "local", "global", "hybrid") and delegate to the respective `SemanticMemoryManager` or `LightRAGManager`.
2.  **Unified Interface for Tools:** The `KnowledgeTools` toolkit will now exclusively interact with the `KnowledgeManager`, abstracting away the complexities of the underlying knowledge stores. This simplifies tool implementation and ensures consistent behavior.
3.  **Streamlined Knowledge Operations:** The `KnowledgeManager` will encapsulate logic for operations such as retrieving, updating, and potentially deleting knowledge entries, providing a cohesive API for the rest of the agent.

**Consequences:**

*   **Improved Modularity and Maintainability:** By centralizing knowledge logic, we reduce code duplication and create a clearer separation of concerns, making the codebase easier to understand, test, and maintain.
*   **Enhanced Consistency:** A single point of control for knowledge operations ensures consistent data handling and retrieval across the entire agent.
*   **Simplified Agent Development:** Developers can interact with a unified `KnowledgeManager` API without needing to understand the intricacies of each underlying knowledge store.
*   **Future Extensibility:** The centralized `KnowledgeManager` provides a robust foundation for integrating new knowledge sources or retrieval techniques in the future with minimal impact on the existing agent architecture.
*   **Potential Performance Optimizations:** Centralized control allows for better optimization strategies, such as caching or intelligent query routing, to improve knowledge retrieval performance.
