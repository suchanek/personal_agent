# ADR-044: Semantic Knowledge Ingestion and Unified Querying

**Date**: 2025-07-30
**Status**: Proposed

## Context

The personal agent architecture featured three distinct knowledge and memory systems:

1.  **LightRAG Knowledge Base (Graph-based):** For factual knowledge, with a robust `KnowledgeIngestionTools` toolkit.
2.  **LightRAG Memory System (Graph-based):** For personal memories, with its own ingestion methods.
3.  **Semantic Knowledge Base (Local LanceDB):** For fast, local vector search, but it critically lacked a dedicated, user-friendly ingestion toolkit. Users could query it, but could not easily add new information.

Furthermore, the `query_knowledge_base` tool directly queried the LightRAG server, and a bug prevented the `mode="local"` parameter from correctly routing queries to the local semantic search. This created an inconsistent and incomplete knowledge management experience.

## Decision

To address these gaps, we have implemented a two-part solution:

1.  **Introduce `SemanticKnowledgeIngestionTools`**: A new, dedicated toolkit has been created (`src/personal_agent/tools/semantic_knowledge_ingestion_tools.py`) that mirrors the functionality of the existing `KnowledgeIngestionTools`. It provides a complete set of tools (`ingest_semantic_file`, `ingest_semantic_text`, `ingest_semantic_from_url`, `batch_ingest_semantic_directory`, and `query_semantic_knowledge`) for managing the local LanceDB semantic knowledge base.

2.  **Unify Knowledge Querying**: The primary `query_knowledge_base` tool within `KnowledgeTools` has been refactored. Instead of directly calling the LightRAG server, it now leverages the existing `KnowledgeCoordinator`. The coordinator intelligently routes the user's query to the appropriate backend (local semantic search or LightRAG) based on the specified `mode`, thus fixing the `mode="local"` bug and creating a single, reliable entry point for all knowledge queries.

## Consequences

### Positive

*   **Feature Parity:** All three knowledge/memory systems now have complete, parallel ingestion and querying capabilities.
*   **Improved User Experience:** Users can now seamlessly add knowledge to the fast, local semantic store using natural language and familiar tool patterns.
*   **Architectural Consistency:** The knowledge querying mechanism is now centralized in the `KnowledgeCoordinator`, simplifying the logic within the tools and ensuring consistent behavior.
*   **Bug Fix:** The long-standing issue where `query_knowledge_base(mode="local")` failed is now resolved.
*   **Enhanced Modularity:** The separation of concerns between LightRAG ingestion and semantic ingestion into distinct toolkits improves code clarity and maintainability.

### Negative

*   **Increased Complexity:** The addition of a new toolkit slightly increases the number of tools available to the agent, which could marginally increase complexity if not managed well. However, the clear naming convention (`semantic_...`) mitigates this.

## Technical Details

*   **New Toolkit:** `src/personal_agent/tools/semantic_knowledge_ingestion_tools.py`
*   **Refactored Tool:** `query_knowledge_base` in `src/personal_agent/tools/knowledge_tools.py` now uses `create_knowledge_coordinator`.
*   **Agent Integration:** The `AgnoPersonalAgent` in `src/personal_agent/core/agno_agent.py` now loads the `SemanticKnowledgeIngestionTools` alongside the other toolkits.
