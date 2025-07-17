# ADR-007: Enriched Graph Ingestion Pipeline

## Status

Accepted

## Context

The initial `store_graph_memory` tool relied on uploading raw text to LightRAG's document processing pipeline. This method was often imprecise, struggled with coreferences (e.g., resolving pronouns like "he," "she," "it"), and did not provide fine-grained control over the creation of entities and relationships. This resulted in an incomplete and often inaccurate knowledge graph. A direct API manipulation approach was considered but deemed too complex and would bypass LightRAG's robust ingestion features.

## Decision

We will implement a hybrid **Enriched Graph Ingestion Pipeline**. This approach enhances the reliability of the file-upload method by embedding locally-processed NLP data into the uploaded file.

The new workflow is as follows:
1.  **Coreference Resolution**: Use `spacy` to perform advanced coreference resolution on the user's statement.
2.  **Entity & Relationship Extraction**: Employ a custom NLP extractor (`extract_entities`, `extract_relationships`) to identify distinct entities and the relationships connecting them from the resolved text.
3.  **Content Restatement**: The user's fact is restated from first-person to third-person to ensure the user is correctly identified as the primary entity in the graph.
4.  **Enriched File Creation**: A temporary text file is created. This file contains the restated fact, along with the extracted entities and relationships included as structured comments (metadata).
5.  **File Upload**: This enriched text file is uploaded to the LightRAG server's `/documents/upload` endpoint.

This method allows LightRAG to use its powerful, native document processing pipeline while being guided by the pre-processed, high-quality metadata embedded in the file, leading to a more accurate and detailed knowledge graph.

## Consequences

### Positive
- **Improved Accuracy**: Providing pre-extracted entities and relationships as metadata significantly improves the accuracy of the final knowledge graph.
- **Leverages LightRAG Pipeline**: The solution still benefits from LightRAG's robust and optimized document ingestion and graph creation pipeline.
- **Reduced Complexity**: This approach is less complex and brittle than attempting to manage the entire graph construction process via direct, sequential API calls for entities and relations.
- **Enhanced Context**: Coreference resolution and fact restatement dramatically improve the agent's ability to retain and correctly attribute context.

### Negative
- **Indirect Control**: The final graph construction is still at the discretion of the LightRAG server's interpretation of the enriched file, offering less direct control than pure API-based manipulation.
- **NLP Overhead**: The agent now bears the computational cost of performing NLP tasks before uploading the memory.
- **New Dependencies**: Adds a dependency on `spacy` and its associated language models.
