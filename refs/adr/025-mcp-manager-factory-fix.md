# ADR-025: MCP Manager Refactored to Factory Pattern to Fix Asyncio Context Errors

**Date**: 2025-07-18
**Status**: Accepted
**Supersedes**: [ADR-016](./016-mcp-singleton-manager.md)

## Context

The previous migration to a singleton pattern for the `MCPManager` (documented in the now-superseded ADR-016) introduced a critical `asyncio` context management bug. During application cleanup, the following error would occur:

```
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

This error was caused by a fundamental violation of `asyncio` task boundaries. The singleton manager initialized persistent MCP connections within one `asyncio` task context, but the application's cleanup phase attempted to close them from a different task. The underlying `MCPTools` library uses `anyio` task groups, which create task-specific cancel scopes that cannot be exited from a different task.

The stateful singleton, while intended to improve performance, was architecturally incompatible with the `asyncio` lifecycle of the tools it was managing.

## Decision

We will refactor the `MCPManager` from a stateful singleton to a stateless **Factory**.

The key characteristics of this new approach are:

1.  **Stateless Factory**: The `MCPManager` will no longer hold persistent connections or state. Its sole responsibility is to create correctly configured `MCPTools` instances on demand.
2.  **Agent-Managed Lifecycle**: Instead of the manager handling initialization and cleanup, the `AgnoPersonalAgent` will receive fresh `MCPTools` instances from the factory and pass them directly to the `agno.Agent`.
3.  **Delegation to Framework**: The `agno` framework is designed to manage the lifecycle of the tools it is given. By providing it with fresh instances, we delegate the responsibility of entering and exiting the async context to the framework, which correctly handles it within the appropriate `asyncio` task.

This approach resolves the `RuntimeError` by ensuring that the `asyncio` context for each MCP tool is managed correctly within the scope of the task that uses it.

## Consequences

### Positive

-   **Critical Bug Fix**: Eliminates the `RuntimeError` and ensures stable application shutdown and resource cleanup.
-   **Architectural Soundness**: Aligns the implementation with Python's `asyncio` best practices and the intended usage pattern of the `agno` framework's tools.
-   **Code Simplification**: Removes the need for manual `__aenter__` and `__aexit__` calls and complex `AsyncExitStack` management within the manager.
-   **Improved Isolation**: Each agent instance effectively gets its own set of MCP tools, preventing potential cross-agent interference.

### Negative

-   **Loss of Connection Sharing**: The primary benefit of the singleton—sharing a single set of connections across the entire application—is lost. Each agent run will establish its own connections.
-   **Minor Performance Overhead**: There will be a slight performance cost for establishing new MCP server connections for each agent lifecycle, compared to the (non-functional) persistent singleton model. However, this is a necessary trade-off for stability and correctness, and the performance is still vastly superior to the original "agent-within-an-agent" model.
