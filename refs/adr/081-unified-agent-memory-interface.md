# ADR-081: Unified Agent-Level Memory Interface and UI Refactor

**Date**: 2025-09-03
**Status**: Accepted

## Context

The previous architecture for accessing agent memory was fragmented and brittle. UI components, particularly the `StreamlitMemoryHelper`, had to reach deep into the `AgnoPersonalAgent`'s internal state, accessing its `memory_manager` and `db` components directly. This created a tight coupling, making the UI code complex and prone to breaking with any change in the agent's internal structure.

Furthermore, several issues were identified:
1.  **Incomplete Interface**: The `AgnoPersonalAgent` class lacked a comprehensive public API for all available memory operations.
2.  **UI Bugs**: The `StreamlitMemoryHelper` was buggy, especially when handling `asyncio` event loops required by the agent's methods, leading to `RuntimeError: cannot run current thread` errors.
3.  **Inaccurate Stats**: The UI could not accurately report the memory synchronization status because there was no way to get the entity count from the LightRAG graph memory.
4.  **Flawed Team Logic**: The `PersonalAgentTeam` coordinator had a logical flaw where it would retrieve memories but fail to pass them to the writer agent, making memory-based content generation non-functional.

## Decision

We decided to perform a major refactoring to address these issues by establishing a clean, unified, and robust interface for all memory operations at the agent level.

1.  **Expand `AgnoPersonalAgent` Interface**: The `AgnoPersonalAgent` class will be the single source of truth for all memory operations. We will add a comprehensive set of public, async methods that delegate directly to the `AgentMemoryManager`. This includes methods for listing, querying, updating, and deleting memories, as well as retrieving stats and graph labels.

2.  **Refactor `StreamlitMemoryHelper`**: The `StreamlitMemoryHelper` will be completely refactored to be a thin client that *only* calls the new public methods on the `AgnoPersonalAgent` instance. All internal access to the agent's components will be removed. A dedicated `_run_async` helper will be implemented to safely execute these async methods within Streamlit's synchronous environment.

3.  **Implement Graph Entity Count**: A `get_graph_entity_count()` method will be added to the `AgentMemoryManager` and exposed through the `AgnoPersonalAgent` to allow the UI to fetch the live entity count from the LightRAG server for accurate sync status reporting.

4.  **Correct Team Coordinator Logic**: The instructions for the `PersonalAgentTeam` coordinator will be updated to enforce the correct workflow for memory-based writing: (1) delegate to the knowledge agent to retrieve memories, then (2) delegate to the writer agent with the retrieved memories explicitly included in the prompt.

5.  **Introduce `Workflow` Examples**: To provide a more robust architectural pattern for sequential, stateful agent coordination, we will add examples of `agno.Workflow` objects. These will demonstrate a better way to handle tasks like memory-based writing, where a strict order of operations and explicit data flow are critical.

## Consequences

### Positive
- **Decoupling**: The UI is now fully decoupled from the agent's internal implementation. The agent can be refactored internally without breaking the UI.
- **Robustness**: `asyncio`-related bugs in the Streamlit UI are resolved. Memory operations are more reliable.
- **Simplicity**: The `StreamlitMemoryHelper` is significantly simpler, cleaner, and easier to maintain.
- **Functionality**: The UI can now accurately display memory sync status. Memory-based writing in the team mode is now functional.
- **Better Architecture**: The introduction of `Workflow` examples provides a better-defined pattern for developers to use for complex, sequential agent tasks.

### Negative
- **Minor Overhead**: The delegation from the agent to the memory manager adds a very small layer of indirection, but the impact on performance is negligible.
