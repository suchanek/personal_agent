# ADR-036: Decisive Tool Usage via Prompt Engineering

## Status

**Proposed**

## Context

The agent, despite having a sophisticated suite of tools for memory and knowledge, has exhibited hesitation and incorrect tool selection. For example, when asked broad questions like "What do you know about me?", it would sometimes fail to call any tool, or use a less appropriate one like `query_memory` instead of the more comprehensive `get_all_memories`. This leads to suboptimal, incomplete, or unhelpful responses.

The root cause is not a flaw in the tools themselves, but in the ambiguity of the instructions provided to the LLM. The previous prompts did not draw a sharp enough distinction between the different types of information the agent manages (user-specific vs. general factual) or provide clear, unambiguous triggers for specific tools.

## Decision

We will implement a significant prompt engineering overhaul to make the agent more decisive and accurate in its tool usage. This involves the following key changes to the `AgentInstructionManager`:

1.  **Conceptual Separation**: We will explicitly define two distinct information domains in the prompts:
    *   **Memory**: Information *about the user*. Managed by tools like `store_user_memory`, `query_memory`, and `get_all_memories`.
    *   **Knowledge**: General factual information from documents, texts, and URLs. Managed by tools like `ingest_knowledge_file` and `query_knowledge_base`.

2.  **Clearer Instructions**: The `concise` and `detailed` instruction sets will be rewritten to reflect this Memory vs. Knowledge paradigm.

3.  **Explicit Decision Flow**: We will provide the agent with a simple "flowchart" within the prompt to guide its decision-making process (e.g., "User asks about themselves -> Use MEMORY tools").

4.  **Direct Tool Triggers**: We will map common user queries directly to specific tool calls in the instructions. For example, the prompt will explicitly state: `"what do you know about me" -> get_all_memories() RIGHT NOW`. This reduces ambiguity and encourages immediate, correct tool use.

5.  **Toolkit Initialization Fix**: Correct a bug in the `MemoryAndKnowledgeTools` `Toolkit` where `async` tools were not being registered correctly during initialization. The fix involves passing all sync and async tools to the parent constructor at once, ensuring all tools are available to the agent.

## Consequences

### Positive
- **Improved Reliability**: The agent will be significantly more reliable in selecting the correct tool for a given query.
- **Reduced Hesitation**: The explicit instructions will reduce instances where the agent fails to use a tool when it should.
- **Better Responses**: By using the correct tools more often, the agent will provide more accurate and comprehensive answers.
- **Improved Maintainability**: The clear separation in the prompts makes the agent's logic easier to understand and modify.
- **Correct Tool Registration**: The toolkit initialization fix ensures all memory and knowledge tools are properly registered and available to the agent.

### Negative
- **Increased Prompt Size**: The new instructions are more verbose, which slightly increases the token count for each call. However, this is a necessary trade-off for improved performance and reliability.
