# Comprehensive Memory Command Summary

This document provides a comprehensive overview of all memory-related commands available in the Personal AI Agent, detailing their purpose, arguments, and return types. These commands allow for robust management of both local semantic memories (SQLite) and graph-based memories (LightRAG).

## Local Memory Tools (SQLite)

These tools interact with the agent's local semantic memory, stored in an SQLite database.

### `store_user_memory`
*   **Description**: Store a simple fact in your local semantic memory. This tool wraps the public `store_user_memory` method.
*   **Arguments**:
    *   `content` (str): The information to store as a memory.
    *   `topics` (Union[List[str], str, None], optional): Optional list of topics for the memory.
*   **Returns**: `str` (Success or error message).

### `query_memory`
*   **Description**: Search user memories using direct SemanticMemoryManager calls. This tool performs a semantic search for memories matching the query.
*   **Arguments**:
    *   `query` (str): The query to search for in memories.
    *   `limit` (Union[int, None], optional): Maximum number of memories to return.
*   **Returns**: `str` (Found memories or message if none found).
*   **Notes**: If the query is a generic phrase like "all memories" or "what do you know about me", it delegates to `get_all_memories`.

### `search_memory`
*   **Description**: Search user memories - alias for `query_memory` for compatibility.
*   **Arguments**:
    *   `query` (str): The query to search for in memories.
    *   `limit` (Union[int, None], optional): Maximum number of memories to return.
*   **Returns**: `str` (Found memories or message if none found).

### `update_memory`
*   **Description**: Update an existing memory using direct SemanticMemoryManager calls.
*   **Arguments**:
    *   `memory_id` (str): ID of the memory to update.
    *   `content` (str): New memory content.
    *   `topics` (Union[List[str], str, None], optional): Optional list of topics/categories for the memory.
*   **Returns**: `str` (Success or error message).

### `delete_memory`
*   **Description**: Delete a memory using direct SemanticMemoryManager calls.
*   **Arguments**:
    *   `memory_id` (str): ID of the memory to delete.
*   **Returns**: `str` (Success or error message).

### `delete_memories_by_topic`
*   **Description**: Delete all memories associated with a specific topic or list of topics.
*   **Arguments**:
    *   `topics` (Union[List[str], str]): A single topic or a list of topics to delete memories for.
*   **Returns**: `str` (Success or error message).

### `clear_memories`
*   **Description**: Clear all memories for the user using direct SemanticMemoryManager calls.
*   **Arguments**: None.
*   **Returns**: `str` (Success or error message).

### `get_recent_memories`
*   **Description**: Get recent memories by searching all memories and sorting by date.
*   **Arguments**:
    *   `limit` (int, default: 10): Maximum number of recent memories to return.
*   **Returns**: `str` (Recent memories or message if none found).

### `get_all_memories`
*   **Description**: Get all user memories using direct SemanticMemoryManager calls.
*   **Arguments**: None.
*   **Returns**: `str` (All memories or message if none found).

### `get_memory_stats`
*   **Description**: Get memory statistics using direct SemanticMemoryManager calls.
*   **Arguments**: None.
*   **Returns**: `str` (Memory statistics).

### `get_memories_by_topic`
*   **Description**: Get memories by topic without similarity search.
*   **Arguments**:
    *   `topics` (Union[List[str], str, None], optional): A list of topics to filter by. If None, returns all memories.
    *   `limit` (Union[int, None], optional): Maximum number of memories to return.
*   **Returns**: `str` (Found memories or a message if none are found).

### `list_memories`
*   **Description**: List all memories in a simple, user-friendly format.
*   **Arguments**: None.
*   **Returns**: `str` (All memories or message if none found).

## Graph Memory Tools (LightRAG)

These tools interact with the LightRAG knowledge graph, focusing on relationships and structured knowledge.

### `store_graph_memory`
*   **Description**: Store a memory in the LightRAG graph database to capture relationships. Uses a file upload approach with enhanced entity and relationship extraction, combining reliable file upload with advanced NLP processing.
*   **Arguments**:
    *   `content` (str): The information to store as a memory.
    *   `topics` (Union[List[str], str, None], optional): Optional list of topics for the memory.
*   **Returns**: `str` (Success or error message).

### `query_graph_memory`
*   **Description**: Query the LightRAG memory graph to explore relationships between memories.
*   **Arguments**:
    *   `query` (str): The query to search for.
    *   `mode` (str, default: "mix"): Query mode. Options: "local", "global", "hybrid", "naive", "mix", "bypass".
    *   `top_k` (int, default: 5): The number of top items to retrieve.
    *   `response_type` (str, default: "Multiple Paragraphs"): The desired format for the response.
*   **Returns**: `dict` (Dictionary with query results).

### `get_memory_graph_labels`
*   **Description**: Get the list of all entity and relation labels from the memory graph by calling the `/graph/label/list` endpoint.
*   **Arguments**: None.
*   **Returns**: `str` (Sorted graph labels).

## Knowledge Base Tools (Unified)

These tools provide unified access to knowledge bases, including semantic and LightRAG sources.

### `query_knowledge_base`
*   **Description**: Unified knowledge base query with intelligent routing. This tool automatically routes queries between local semantic search and LightRAG based on the mode parameter and query characteristics.
*   **Arguments**:
    *   `query` (str): The search query.
    *   `mode` (str, default: "auto"): Routing mode. Options: "local" (force local semantic search), "global", "hybrid", "mix", "naive", "bypass" (use LightRAG), "auto" (intelligent auto-detection).
    *   `limit` (int, default: 5): Maximum results for local search / top_k for LightRAG.
    *   `response_type` (str, default: "Multiple Paragraphs"): Format for LightRAG responses.
*   **Returns**: `str` (Formatted search results from the appropriate knowledge system).

### `query_lightrag_knowledge` (DEPRECATED)
*   **Description**: DEPRECATED. Direct query to LightRAG knowledge base for backward compatibility. Use `query_knowledge_base` instead.
*   **Arguments**:
    *   `query` (str): The query string to search in the knowledge base.
    *   `mode` (str, default: "naive"): Query mode. Options: "local", "global", "hybrid", "naive", "mix", "bypass".
    *   `top_k` (int, default: 5): The number of top items to retrieve.
    *   `response_type` (str, default: "Multiple Paragraphs"): The desired format for the response.
*   **Returns**: `dict` (Dictionary with query results).

### `query_semantic_knowledge` (DEPRECATED)
*   **Description**: DEPRECATED. Search the local semantic knowledge base (SQLite/LanceDB) for specific facts or documents. Use `query_knowledge_base` instead.
*   **Arguments**:
    *   `query` (str): The query to search for in the semantic knowledge base.
    *   `limit` (int, default: 5): The maximum number of results to return.
*   **Returns**: `str` (A formatted string of search results or a message if no results are found).
