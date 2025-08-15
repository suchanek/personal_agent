# ADR-054: Simplification of Agent Execution and Tool Call Retrieval

## Status

**Accepted**

## Context

The `AgnoPersonalAgent` class contained custom, complex `run` and `run_custom` methods. These methods manually iterated through the asynchronous response stream from the underlying `agno.Agent.arun()` method to piece together the final response and collect tool call information. This implementation was verbose, difficult to maintain, and contained leftover diagnostic code.

Furthermore, initial testing revealed that relying on `agent.history` to retrieve tool calls was unreliable, as the history was not consistently populated after a run.

Finally, the agent's initialization logic included a complex and buggy tool-filtering mechanism that attempted to dynamically limit tools based on the model's perceived capabilities. This system was causing `AttributeError` and `NameError` exceptions, preventing the agent from initializing correctly.

## Decision

We will refactor the `AgnoPersonalAgent` to simplify its execution flow and tool handling by adopting the following changes:

1.  **Adopt Non-Streaming `arun`**: The primary `run` method will now call the superclass `arun` method with `stream=False`. This provides a final `RunResponse` object directly, eliminating the need for manual stream iteration and ensuring the complete response is received.

2.  **Standardize Tool Call Retrieval**: Tool calls will be retrieved from the `self.run_response.tools` attribute, which is reliably populated after a non-streaming `arun` call. The custom `get_last_tool_calls` method will be retained to access this data from a dedicated `_collected_tool_calls` list.

3.  **Remove Complex Tool Filtering**: The entire dynamic tool-limiting logic will be removed from the `_do_initialization` method. The agent will now load all its defined tools in a straightforward manner, removing the source of the initialization errors and simplifying the codebase.

## Consequences

### Pros

*   **Simplified Code**: The agent's execution logic is now significantly cleaner, more readable, and easier to maintain by removing over 200 lines of complex, redundant code.
*   **Increased Reliability**: By using the framework's intended non-streaming response pattern, we rely on battle-tested `agno` functionality instead of a custom implementation. This also resolves the `AttributeError` and `NameError` bugs during initialization.
*   **Correctness**: This approach correctly and reliably captures tool call information, which is critical for debugging and UI display.

### Cons

*   **Loss of Streaming in Core `run`**: The core `agent.run()` method no longer supports streaming internally. However, streaming is primarily a UI/presentation-layer concern and can be handled by calling `agent.arun(stream=True)` directly from the UI layer if needed, while the core non-streaming `run` is used for internal logic and testing.
