# ADR-016: MCP Singleton Manager Migration

**Date**: 2025-07-18
**Status**: Accepted

## Context

The previous integration of MCP (Model Context Protocol) servers in the `AgnoPersonalAgent` was based on a complex, on-demand "agent-within-an-agent" architecture. This design had several significant drawbacks:

1.  **Performance Overhead**: Each call to an MCP tool triggered the creation of a new server process, introducing significant latency (2-3 seconds per call).
2.  **Code Complexity**: The implementation required over 120 lines of complex asynchronous logic, including closures and temporary agent instantiation, making it difficult to maintain and debug.
3.  **Resource Inefficiency**: The ephemeral nature of the servers meant resources were wasted on repeated process startups. If multiple agent instances were running, they could not share server connections.
4.  **Lifecycle Management Issues**: The complex async context management led to resource cleanup warnings and potential instability.

The official `agno` framework documentation recommends a simpler, more performant approach where `MCPTools` instances are initialized once and maintain persistent connections. A migration was necessary to align with best practices and address the performance and complexity issues.

## Decision

We have decided to refactor the MCP integration to use a **Singleton Manager pattern**. This new `MCPManager` is responsible for the entire lifecycle of all configured MCP servers.

The key characteristics of this new architecture are:

1.  **Singleton Instance**: A single `MCPManager` instance is shared across the entire application, ensuring that MCP server connections are centralized and managed consistently.
2.  **Persistent Connections**: The `MCPManager` initializes all MCP servers once upon application startup. These servers remain running and their connections persist, eliminating the per-call startup overhead.
3.  **Centralized Lifecycle Management**: The manager handles the initialization (`initialize`), resource sharing (`get_tools`), and graceful shutdown (`cleanup`) of all MCP tools and their underlying server processes.
4.  **Simplified Agent Integration**: The `AgnoPersonalAgent` no longer contains complex MCP logic. It simply requests the list of initialized tools from the `MCPManager` during its own initialization.

This approach moves the responsibility of MCP management out of the agent and into a dedicated, reusable, and efficient service layer.

## Consequences

### Positive

-   **Massive Performance Improvement**: Latency for MCP tool calls has been reduced by over 95%, from seconds to milliseconds.
-   **Drastic Code Simplification**: The MCP-related code within `AgnoPersonalAgent` has been reduced by over 90%, removing the complex and error-prone "agent-within-an-agent" logic.
-   **Improved Resource Management**: MCP servers are started only once, and connections are shared across all parts of the application, significantly reducing memory and process overhead.
-   **Enhanced Stability and Reliability**: Centralized lifecycle management ensures that server processes are started and stopped cleanly, resolving previous cleanup issues.
-   **Better Maintainability**: The code is now easier to understand, debug, and extend due to the clear separation of concerns.

### Negative

-   **Loss of Per-Call Specialized Instructions**: The old method allowed for creating temporary sub-agents with highly specialized instructions for each tool call. This capability is lost. The main agent now relies on its general instructions and the tool's docstring to use MCP tools. This is a reasonable trade-off for the significant gains in performance and simplicity.
-   **Tightly Coupled Server Lifecycle**: All MCP servers are now tied to the application's lifecycle. A server cannot be restarted independently without restarting the main application (though this could be addressed in future enhancements to the manager).
