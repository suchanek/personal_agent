# ADR 003: Knowledge Graph Memory System & Unified Knowledge Architecture

*   **Status:** Implemented
*   **Date:** 2025-07-05

## Context and Problem Statement

The agent's original memory system was based solely on local semantic search (SQLite + LanceDB). While fast for simple fact retrieval, it lacked the ability to understand and reason about the *relationships* between different pieces of information. To achieve a deeper level of understanding, the agent needed a system that could perform graph-based reasoning, entity extraction, and knowledge synthesis.

Furthermore, with two different types of memory systems (semantic and graph), there was no unified way to query them, forcing the agent to make complex decisions about which system to use for any given query.

## Decision Drivers

*   The need to move beyond simple semantic search to a more advanced, relationship-aware memory system.
*   The requirement for a unified interface to query all knowledge sources, simplifying the agent's internal logic.
*   The desire to create a more powerful and scalable memory architecture that could support complex reasoning.

## Decision Outcome

A **Dual Memory Architecture** was designed and implemented, orchestrated by a central **Knowledge Coordinator**.

### 1. Dual Memory Architecture

The agent now employs two distinct but integrated memory layers:

*   **Local Memory Layer (SQLite + LanceDB):** Continues to provide fast semantic search, deduplication, and topic classification for simple, direct fact recall.
*   **Graph Memory Layer (LightRAG Server):** A new, dedicated LightRAG server instance was introduced to handle graph-based memory. It provides advanced relationship mapping, entity extraction, and multi-hop graph traversal.

### 2. The Knowledge Coordinator

The `KnowledgeCoordinator` (`src/personal_agent/core/knowledge_coordinator.py`) was created to act as the brain of the dual memory system.

*   **Unified Interface:** It exposes a single `query_knowledge_base()` tool to the agent, abstracting away the complexity of the underlying memory systems.
*   **Intelligent Query Routing:** The coordinator analyzes the user's query and, based on the specified mode or a set of heuristics, intelligently routes the query to the most appropriate system:
    *   **Local Semantic:** Used for simple facts, definitions, and short queries.
    *   **LightRAG Graph:** Used for queries involving relationships, comparisons, complex analysis, or multiple entities.
*   **Fallback Mechanism:** If the primary system fails or returns no results, the coordinator can automatically fall back to the other system, ensuring a robust user experience.

### 3. Dual Storage

To populate both systems, the `store_user_memory()` function was enhanced to write to both the local and graph memories simultaneously, ensuring data consistency.

## Consequences

### Positive

*   **Revolutionary Memory Capabilities:** The agent can now understand and reason about relationships, a significant leap in its intelligence.
*   **Simplified Agent Logic:** The agent's core logic is simplified as it no longer needs to decide which memory system to query. It just uses the unified `query_knowledge_base()` tool.
*   **Scalable and Modular:** The dedicated LightRAG memory server can be scaled independently, and the modular design allows for the future addition of new knowledge sources.
*   **Robustness:** The intelligent routing and fallback mechanisms make the memory system more resilient to failures.

### Negative

*   **Increased Infrastructure Complexity:** The new architecture requires running a dedicated LightRAG memory server in addition to the main application and Ollama.
*   **Data Duplication:** Storing memories in two different systems leads to data duplication. This is a deliberate trade-off to optimize for both fast semantic recall and deep graph-based reasoning.
