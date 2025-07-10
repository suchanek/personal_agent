# ADR-007: Direct Knowledge Graph Construction

## Status

Accepted

## Context

The previous `store_graph_memory` tool relied on LightRAG's internal text processing to build the knowledge graph from a simple text file upload. This method was often imprecise, struggled with coreferences (e.g., resolving pronouns like "he," "she," "it"), and did not provide fine-grained control over the creation of entities and relationships. This resulted in an incomplete and often inaccurate knowledge graph, limiting the agent's ability to reason about the connections between different pieces of information.

## Decision

We will replace the passive file-upload approach with an active, direct graph construction method within the `store_graph_memory` tool. The new implementation directly manipulates the graph via API calls, guided by an NLP pipeline.

The new workflow is as follows:
1.  **Coreference Resolution**: Use `spacy` to perform advanced coreference resolution, replacing ambiguous pronouns in the user's statement with the specific entities they refer to.
2.  **Entity & Relationship Extraction**: Employ a custom NLP extractor (`extract_entities`, `extract_relationships`) to identify distinct entities and the relationships that connect them.
3.  **Direct Graph API Calls**: Instead of uploading text, the agent will now make direct, asynchronous API calls to the LightRAG memory server's dedicated graph endpoints:
    - `POST /graph/entity/edit`: To create or update individual entities.
    - `POST /graph/relation/edit`: To explicitly define relationships between entities.
4.  **Resilient Creation**: The process is designed to be robust. It performs entity and relationship creation in parallel using `asyncio.gather` and gracefully handles missing entities by creating them on-the-fly with a default type.

## Consequences

### Positive
- **Accuracy**: Produces significantly more accurate and detailed knowledge graphs by explicitly defining nodes and edges.
- **Clarity**: Relationships are created unambiguously, removing the guesswork from text interpretation.
- **Context**: Coreference resolution dramatically improves the agent's ability to retain context within a conversation.
- **Control**: Provides fine-grained control over the knowledge graph's structure.

### Negative
- **Increased Complexity**: The logic within `AgnoPersonalAgent` is now more complex due to the multi-step NLP and API interaction pipeline.
- **New Dependencies**: Adds a dependency on `spacy` and its associated language models.
- **Performance**: A single `store_graph_memory` call now triggers multiple API requests to the memory server. While these are executed asynchronously, it introduces a higher load on the memory server compared to the previous single-file upload.
