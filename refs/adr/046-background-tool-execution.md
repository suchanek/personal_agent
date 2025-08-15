# ADR-046: Non-Blocking Background Tool Execution

## Status

**Accepted**

## Context

The agent frequently needs to execute long-running processes, such as starting servers or running tests, without blocking the main execution thread. The existing `run_shell_command` tool is synchronous, forcing the agent to wait for the command to complete. This limitation hinders the agent's ability to multitask and manage background processes effectively.

To address this, a new tool is required to execute shell commands in a non-blocking, asynchronous manner, allowing the agent to remain responsive while background tasks are running.

## Decision

We will introduce a new `run_in_background` tool within a dedicated `BackgroundTools` class. This tool will be responsible for executing shell commands in a non-blocking background process.

### Key Features:

- **Asynchronous Execution**: The tool will immediately return a process ID (PID) and status, allowing the agent to continue its operations without waiting for the command to finish.
- **Process Management**: The agent will be able to monitor the status of background tasks and manage them as needed.
- **Clear Separation**: Placing this tool in a separate `BackgroundTools` class provides a clear distinction from the synchronous `run_shell_command` and improves code organization.

## Consequences

### Positive:
- **Improved Responsiveness**: The agent can now execute long-running tasks without becoming unresponsive.
- **Enhanced Multitasking**: The agent can manage multiple background processes simultaneously, improving its efficiency.
- **Better Organization**: The dedicated `BackgroundTools` class provides a clear and organized structure for managing background operations.

### Negative:
- **Increased Complexity**: The introduction of asynchronous process management adds a layer of complexity to the agent's architecture. Careful implementation and testing are required to ensure stability.
