# ADR 002: Memory Restatement System

*   **Status:** Implemented
*   **Date:** 2025-07-09

## Context and Problem Statement

For the agent to build an accurate knowledge graph of its interactions with a user, it needs to understand the entities and relationships in the user's statements. When a user provides a fact in the first person (e.g., "I have a PhD"), storing it literally in a knowledge graph is problematic. The graph node would be "I", which is ambiguous and not tied to a specific entity. For the graph to be effective, the statement needs to be converted to the third person (e.g., "{user_id} has a PhD").

At the same time, for the agent to have natural-sounding conversations and recall facts as the user stated them, the original first-person statement needs to be preserved.

## Decision Drivers

*   The need for accurate entity and relationship mapping in the LightRAG knowledge graph.
*   The need to maintain a natural user experience by preserving the user's original phrasing in semantic memory.
*   The requirement to avoid corrupting the knowledge graph with ambiguous, first-person pronouns.

## Decision Outcome

A **Dual Memory Storage Strategy** was implemented, where facts are processed and stored differently for each memory system:

1.  **Local Semantic Memory (SQLite/LanceDB):**
    *   **Action:** Stores the user's fact *exactly* as it was entered (e.g., "I have a PhD").
    *   **Benefit:** This preserves the original phrasing, allowing the agent to recall and use the fact in a natural, conversational context.

2.  **Graph Memory System (LightRAG):**
    *   **Action:** Automatically restates the fact to the third person before storing it in the graph (e.g., "{user_id} has a PhD"). This is handled by the `_restate_user_fact()` method in the `AgnoPersonalAgent`.
    *   **Benefit:** This ensures that the knowledge graph correctly maps the fact to the specific user entity, allowing for accurate relationship extraction and complex reasoning.

### Technical Implementation Details

*   **Core Logic:** The `_restate_user_fact()` method was added to `src/personal_agent/core/agno_agent.py`.
*   **Pattern Matching:** The method uses case-insensitive regex with word boundaries (`\b`) to ensure accurate and safe replacement of pronouns and possessives (e.g., `I`, `my`, `I'm`). This prevents partial word replacements (e.g., changing "train" to "tra{user_id}'s").
*   **Integration:** The `store_graph_memory()` method was updated to always use the restated content.
*   **Testing:** A comprehensive test suite (`tests/test_fact_restatement.py`) was created to validate the conversion logic and the dual storage strategy.

## Consequences

### Positive

*   **Accurate Knowledge Graph:** The graph now contains clear, unambiguous relationships tied to specific user entities.
*   **Natural Conversation:** The agent can still recall and use facts exactly as the user stated them.
*   **Robust and Reliable:** The use of regex with word boundaries makes the replacement process safe and accurate.
*   **Clear Separation of Concerns:** The dual storage strategy provides a clean separation between memory for conversational recall and memory for analytical reasoning.

### Negative

*   **Slight Overhead:** There is a minor computational overhead in processing and storing each memory twice. This is negligible in practice but is a trade-off for the benefits.
