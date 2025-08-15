# ADR-064: Optimized Semantic Knowledge Base Recreate

- Status: accepted
- Date: 2025-08-15
- Deciders: Personal Agent Development Team

## Context and Problem Statement

The semantic knowledge base (Agno/LanceDB) required a full recreate of its vector embeddings after any new document ingestion. While this ensures immediate availability of new information, it is inefficient for batch operations. Ingesting multiple documents (e.g., from a directory) would trigger N recreates for N documents, leading to significant performance degradation and potential race conditions where the knowledge base is queried mid-recreate. We needed a more efficient approach for batch ingestions while preserving the immediate-availability behavior for single ingestions.

## Decision Drivers

- **Performance:** Reduce the time and computational cost of batch ingesting documents.
- **Reliability:** Ensure the knowledge base is in a consistent state and avoid query failures or incomplete results during batch operations.
- **User Experience:** Maintain the intuitive behavior of having a single ingested document be immediately available for querying.

## Considered Options

1.  **Always Defer Recreate:** Defer the recreate for all ingestions and require a manual trigger to update the knowledge base. This would be the most performant but would degrade the user experience for single ingestions.
2.  **Selective Recreate with a Parameter:** Introduce a parameter to control the recreate behavior. This would allow for both immediate and deferred recreates, providing flexibility for different use cases.
3.  **Heuristic-Based Recreate:** Automatically defer recreates if multiple ingestions happen within a short time window. This would be more complex to implement and could be less predictable.

## Decision Outcome

Chosen option: **Selective Recreate with a Parameter**.

We have introduced a `defer_reload: bool` parameter to the `ingest_semantic_file` and `ingest_semantic_text` methods in `KnowledgeTools`.

- By default, `defer_reload` is `False`, so single ingestions will trigger an immediate recreate of the knowledge base, preserving the existing behavior.
- The `batch_ingest_semantic_directory` method now calls the ingestion methods with `defer_reload=True` and then performs a single, explicit recreate at the end of the batch operation.

This approach provides the best of both worlds: it optimizes batch ingestions by reducing N recreates to 1, while maintaining the immediate-availability guarantee for single ingestions.

### Positive Consequences

- Significant performance improvement for batch ingestions.
- Reduced risk of race conditions and inconsistent states.
- Clear and predictable behavior for both single and batch ingestions.
- The change is backward-compatible, as the default behavior for single ingestions is unchanged.

### Negative Consequences

- Slightly more complex implementation due to the new parameter.

## Implementation

- **`src/personal_agent/tools/knowledge_tools.py`**:
    - Added `defer_reload: bool = False` to `ingest_semantic_file` and `ingest_semantic_text`.
    - Updated `batch_ingest_semantic_directory` to use `defer_reload=True` and perform a single recreate at the end.
- **`tests/test_semantic_kb_recreate.py`**:
    - Added a new test script to validate the recreate behavior for both single and batch ingestions.

## Validation

The new behavior is validated by the `tests/test_semantic_kb_recreate.py` script, which checks the number of recreate calls for single and batch ingestions.
