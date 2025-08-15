# ADR-063: Consolidated Knowledge Ingestion Architecture

## Context

The previous architecture for knowledge ingestion was fragmented and suffered from significant code duplication. Functionality was scattered across four different classes (`KnowledgeIngestionTools`, `KnowledgeTools`, `MemoryAndKnowledgeTools`, and `SemanticKnowledgeIngestionTools`), each with overlapping responsibilities. This proliferation led to a codebase that was difficult to maintain, extend, and reason about. Managing and initializing the agent's tools was unnecessarily complex due to this lack of a single, clear source of truth for knowledge operations.

## Decision

To address these issues, we have executed a major refactoring to consolidate all knowledge-related functionality into a single, authoritative class.

1.  **Single Source of Truth**: The `KnowledgeTools` class, located in `src/personal_agent/tools/knowledge_tools.py`, is now the sole owner of all knowledge ingestion and querying logic.
2.  **Unified Functionality**: It now handles operations for both the LightRAG (graph) and the local `LanceDB` (semantic) knowledge bases. This includes ingestion from files, text, and URLs, as well as querying and semantic KB management (e.g., `recreate_semantic_kb`).
3.  **Deprecate and Remove Redundancy**: The redundant classes (`KnowledgeIngestionTools`, `SemanticKnowledgeIngestionTools`) and their corresponding files have been deleted. Other classes that contained duplicated logic, like `MemoryAndKnowledgeTools`, have been streamlined.
4.  **Update Consumers**: The `AgnoPersonalAgent` and all user-facing interfaces (e.g., Streamlit apps) have been updated to use the consolidated `KnowledgeTools` exclusively.

## Consequences

### Positive
- **Massive Code Reduction**: Eliminated over 1000 lines of duplicated code, significantly reducing the repository's size and complexity.
- **Improved Maintainability**: With a single source of truth, future updates or bug fixes to knowledge handling need to be made in only one place.
- **Simplified Architecture**: The agent's tool configuration is now much simpler, improving architectural clarity and making the system easier to understand for new developers.
- **Clear Separation of Concerns**: This change reinforces a clean boundary between `KnowledgeTools` (handling factual, objective information) and `AgnoMemoryTools` (handling personal, user-specific information).

### Negative
- None have been identified. The refactoring was executed to be non-breaking.

### Neutral
- All external-facing tool method signatures and behaviors have been preserved, ensuring full backward compatibility for end-users and existing workflows.
