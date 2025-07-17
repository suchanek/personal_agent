# Memory System Improvement Plan

This document outlines the analysis and plan to improve the consistency and correctness of the memory tools and rules within the Agno Personal Agent.

## 1. System Analysis

A thorough review of the following files was conducted:
- `src/personal_agent/core/semantic_memory_manager.py`
- `src/personal_agent/core/agno_agent.py`

### Key Findings:

*   **`semantic_memory_manager.py`**: Defines a robust, LLM-free memory system. The `SemanticMemoryManager` class provides core functionalities for adding, updating, deleting, and searching memories. The most important methods are `add_memory()` for storage and `search_memories()`, which uses a powerful combination of semantic similarity, topic matching, and keyword searching for retrieval.

*   **`agno_agent.py`**: This file integrates the `SemanticMemoryManager` into the `AgnoPersonalAgent`.
    *   The `_get_memory_tools()` method wraps the `SemanticMemoryManager`'s functions into tools available to the agent (e.g., `query_memory`, `store_user_memory`).
    *   The `_get_detailed_memory_rules()` function provides the critical instructions to the LLM on how and when to use these memory tools.

## 2. Identified Inconsistencies

The primary issue lies in the agent's instructions, which could lead to confusion and suboptimal behavior.

1.  **Contradictory Guidance on General Memory Queries**: The instructions in `_get_detailed_memory_rules()` are conflicting about which tool to use for a general question like "What do you remember about me?".
    *   One rule suggests calling `get_all_memories()`.
    *   Another rule correctly identifies `query_memory()` as the primary tool.
    *   Using `get_all_memories()` is inefficient and verbose, while `query_memory()` is designed for intelligent, semantic retrieval.

2.  **Tool Alias Confusion**: The agent has two tools, `query_memory` and `search_memory`, that are aliases for the same function. This is redundant and can confuse the model.

3.  **Lack of Clarity Between Knowledge and Memory**: The instructions do not draw a sharp enough distinction between querying the knowledge base (for documents and general info) and querying the user's semantic memory (for personal facts).

## 3. Proposed Refined Memory Strategy

To address these issues, the following strategy will be implemented:

*   **`query_memory` as the Primary Tool**: `query_memory` will be the default, primary tool for *any* question about the user's personal information.
*   **`get_all_memories` for Explicit Requests**: `get_all_memories` will *only* be used when the user explicitly asks for a full list of all their memories.
*   **Eliminate Redundancy**: The `search_memory` alias will be removed to simplify the toolset.
*   **Clear Instructions**: The agent's instructions will be rewritten to reflect this clear hierarchy and purpose for each tool.

## 4. Detailed Plan & Proposed Changes

### Agent Decision Flow

```mermaid
graph TD
    A[User asks a question about themself] --> B{Is it an explicit request for ALL memories?};
    B -- Yes --> C[Use get_all_memories()];
    B -- No --> D[Use query_memory("relevant keywords")];
    A -- User states a new fact --> E[Use store_user_memory("the fact")];
```

### Implementation Steps

The following changes will be made to `src/personal_agent/core/agno_agent.py`:

1.  **Remove `search_memory` alias**: The `search_memory` tool will be removed from the list in the `_get_memory_tools()` function.

2.  **Rewrite `_get_detailed_memory_rules()`**: The instructions will be updated to be clear and consistent as follows:

    ```python
    def _get_detailed_memory_rules(self) -> str:
        """Returns detailed, prescriptive memory usage rules."""
        return """
            ## SEMANTIC MEMORY SYSTEM - CRITICAL & IMMEDIATE ACTION REQUIRED - YOUR MAIN ROLE!

            Your primary function is to remember information about the user. You must use your memory tools immediately and correctly.

            **MEMORY STORAGE - NO HESITATION RULE**:
            - When the user provides a new piece of information about themselves or tells you to remember something, IMMEDIATELY call `store_user_memory(content="the fact to remember")`.

            **MEMORY RETRIEVAL - DECISION TREE**:
            When the user asks a question about themselves, follow this logic:

            1.  **Did the user ask for ALL memories?**
                - If the query is "Show me all my memories", "What are all my memories?", or "List everything you know", IMMEDIATELY call `get_all_memories()`.

            2.  **For ALL other questions about the user, use `query_memory`**.
                - This is your PRIMARY and MOST IMPORTANT memory tool for retrieval.
                - "What do you remember about me?" -> `query_memory("user's personal information, preferences, and facts")`
                - "What do I like?" -> `query_memory("user preferences, likes, and interests")`
                - "What did I tell you about my job?" -> `query_memory("user's job and career")`
                - "What have we talked about recently?" -> `get_recent_memories()` is best for this specific case.

            **HOW TO RESPOND - CRITICAL IDENTITY RULES**:
            - You are an AI assistant, NOT the user.
            - When you retrieve a memory, present it in the second person.
            - CORRECT: "I remember you told me you enjoy hiking."
            - INCORRECT: "I enjoy hiking."
        """