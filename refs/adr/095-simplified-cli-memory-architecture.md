# ADR-095: Simplified CLI Memory Architecture

## Status

Accepted

## Context

The command-line interface (CLI) for memory operations, located in `src/personal_agent/cli/memory_commands.py`, had grown complex. It contained logic to dynamically find memory-related tools within the agent's toolkits and included fallback mechanisms to call the agent's internal memory managers directly if a tool was not found.

This approach had several drawbacks:
- **Code Duplication:** The CLI was replicating logic that should be centralized within the agent.
- **Complexity:** The tool-finding and fallback logic made the CLI commands difficult to read and maintain.
- **Poor Separation of Concerns:** The CLI, intended as a presentation layer, was too deeply involved in the application's business logic.
- **Inconsistency:** It created a potential for divergence between how the agent operated internally and how the CLI interacted with its memory.

This complexity was a direct contradiction to the principle established in [ADR-081](./081-unified-agent-memory-interface.md), which mandated that the `AgnoPersonalAgent` should expose a complete and robust set of public methods for all memory operations.

## Decision

We have refactored the entire `memory_commands.py` module to be a thin, simple presentation layer.

The key changes are:
1.  **Direct Delegation:** All CLI functions now directly call the corresponding public methods on the `AgnoPersonalAgent` instance (e.g., `agent.list_all_memories()`, `agent.delete_memory()`).
2.  **Removal of Tool-Finding Logic:** The `find_tool_by_name` helper function and all associated logic for searching through agent toolkits have been removed.
3.  **Elimination of Fallback Mechanisms:** The CLI no longer contains fallback code to call memory managers directly. It trusts that the agent's public interface is the single source of truth for all memory operations.
4.  **Simplified Code:** The refactoring has significantly reduced the line count and complexity of each function in the module, making the code more readable and maintainable.

## Consequences

### Positive
- **Improved Separation of Concerns:** The CLI is now purely a presentation layer, and the agent is the sole authority on memory operations.
- **Reduced Complexity:** The CLI code is dramatically simpler and easier to understand.
- **Enhanced Maintainability:** Changes to memory logic only need to be made in the `AgnoPersonalAgent` class, not in the CLI.
- **Consistency:** The CLI now uses the exact same public methods that other parts of the system (like the UI or API) use, ensuring consistent behavior.

### Negative
- None identified. This change simplifies the architecture and aligns it with previously established design principles.
