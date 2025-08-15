# ADR-028: Mandating the Ephemeral Agent Pattern for MCP Tool Stability

**Date**: 2025-07-18
**Status**: Reaffirmed

## Context

This ADR serves as a formal documentation of a **necessary architectural requirement** that was validated through failed experimentation. The only stable and reliable method for interacting with MCP (Model Context Protocol) tools is the **ephemeral agent pattern**.

In the `dev/v0.10.1` and `dev/v0.10.2` branches, alternative approaches were explored, including a stateless factory (ADR-025) intended to provide reusable MCP client instances. These experiments consistently resulted in critical failures, including `asyncio` context errors and resource leaks, rendering the agent unstable.

These failed experiments proved that maintaining any long-lived client or connection to MCP servers within the agent's primary lifecycle is architecturally unsound and introduces unavoidable state management conflicts.

## Decision

The use of the **ephemeral agent pattern is mandatory** for all MCP tool interactions. This is not a new decision, but a reaffirmation of the original, working architecture.

The required implementation pattern is as follows:
1.  For any MCP tool call, a new, single-purpose MCP client must be dynamically created.
2.  The client connects to the required MCP server.
3.  A single tool operation is executed.
4.  The client is immediately and completely torn down, ensuring all associated resources are released.

This pattern ensures that every MCP tool call is perfectly isolated, stateless, and safe.

## Consequences

### Positive
- **Guaranteed Stability**: This is the only pattern that has proven to be stable and free from `asyncio` and resource-leakage bugs.
- **Architectural Clarity**: Formally documents why alternative, seemingly more performant, approaches are not viable for this project.
- **Justification for Abandoned Branches**: Provides the official reasoning for abandoning the `v0.10.1` and `v0.10.2` branches.

### Negative
- **Performance Overhead**: Acknowledges the minor performance cost of creating and destroying a client for each call. This cost is accepted as a non-negotiable trade-off for fundamental system stability.
