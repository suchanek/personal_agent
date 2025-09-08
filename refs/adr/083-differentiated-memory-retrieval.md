# ADR-083: Differentiated Memory Retrieval for Controllable Verbosity

- **Status**: Accepted
- **Date**: 2025-09-08

## Context and Problem Statement

The agent exhibited a significant behavioral issue where it would respond with overly detailed and verbose information when asked for a list of memories. Queries like "list all memories" or "what do you know about me?" triggered the `get_all_memories` tool, which returns a complete dump of all memory objects, including metadata.

This behavior had several negative consequences:
- **Poor User Experience**: Users were overwhelmed with data when a simple summary was expected.
- **Excessive Token Consumption**: The verbose output consumed a large portion of the context window, increasing operational costs and risking context overflow.
- **Performance**: Processing and displaying large amounts of memory data was inefficient.

The root cause was a lack of distinction in the agent's tools and instructions between a "summary" request and a "detailed" request. The agent's logic defaulted to providing all available information, failing to understand the user's intent for a more concise overview.

## Decision Drivers

- The need to improve the naturalness and efficiency of the agent's interaction.
- The requirement to control token usage and reduce context window pressure.
- User feedback indicating that the memory listing was too verbose.
- The desire to make the agent's behavior more intelligent and context-aware.

## Considered Options

1.  **Modify `get_all_memories`**: Add a parameter to the existing `get_all_memories` tool to control the level of detail.
2.  **Create a New, Distinct Tool**: Introduce a new, separate tool specifically for concise memory listing and overhaul instructions to create a clear distinction between the two tools.
3.  **Rely on Post-processing**: Have the agent retrieve the full details and then summarize them before presenting to the user.

## Decision Outcome

**Option 2 was chosen.** A new, performance-optimized tool, `list_all_memories`, was introduced, while the existing `get_all_memories` was retained for explicitly detailed requests.

This involved a multi-layered implementation:

1.  **Tool Creation and Refinement**:
    - A new `list_all_memories` method was created in the `AgentMemoryManager`. It is optimized to return only a simple list of memory content strings, omitting all metadata like topics, timestamps, and IDs.
    - The `PersagMemoryTools` toolkit was updated to expose `list_all_memories` with a clear docstring explaining its purpose (concise summaries). The docstring for `get_all_memories` was also updated to clarify it should only be used for explicitly detailed requests.

2.  **Instruction Overhaul**:
    - The agent's core instructions (`AgentInstructionManager` and `reasoning_team`) were fundamentally rewritten.
    - **Clear Function Selection Rules** and **Pattern Matching Guidelines** were added.
    - `list_all_memories` is now the mandatory default for all general memory listing queries (e.g., "show me all memories", "what do you know about me?").
    - `get_all_memories` is now to be used *only* when the user explicitly asks for "details", "full content", or "complete information".

3.  **CLI Enhancement**:
    - The user-facing CLI was updated to include a `brief` command, giving users direct access to the new concise listing functionality.

### Positive Consequences

- **Improved User Experience**: The agent's default behavior is now to be concise and helpful, providing summaries first.
- **Reduced Token Usage**: Significantly lowers the number of tokens used for common memory-related queries.
- **Better Performance**: The optimized `list_all_memories` tool is faster as it processes less data.
- **Enhanced Agent Intelligence**: The agent now demonstrates a better understanding of user intent by differentiating between summary and detailed requests.
- **Clearer Architecture**: The toolset and instructions now have a clear and unambiguous separation of concerns for memory retrieval.

### Negative Consequences

- **Increased Instruction Complexity**: The agent's instructions are now longer and more complex to enforce this behavior, which could have a minor impact on prompt processing time. However, the overall performance gain from reduced output verbosity far outweighs this.
