# ADR-045: Enhanced Ollama Reasoning Team with AgnoPersonalAgent Integration and Advanced CLI

**Date**: 2025-08-01

**Status**: Accepted

## Context

The initial implementation of the standalone Ollama Reasoning Team (`paga_team_cli`) served as a lightweight proof-of-concept. While functional, it had several limitations:
- It used a generic `agno.Agent` for its memory component, which lacked the advanced features, specific instructions, and robust tool handling of the main `AgnoPersonalAgent`.
- Its command-line interface was basic, offering simple chat functionality without the powerful memory management commands (`!`, `?`, `@`, etc.) available in the main `paga_cli`.
- The user experience was minimal, lacking the rich formatting and clear guidance of the primary agent.
- There was a growing need to unify the user experience and capabilities across the different interfaces of the personal agent project.

## Decision

To address these limitations, we decided to significantly refactor the Ollama Reasoning Team with two primary goals:

1.  **Integrate `AgnoPersonalAgent`**: Replace the generic memory agent with a full instance of the `AgnoPersonalAgent`. This immediately provides the team with the same powerful, fine-tuned memory and knowledge capabilities as the main agent, including its sophisticated instruction set and tool management.
2.  **Implement an Advanced CLI**: Rebuild the team's command-line interface to mirror the functionality of `paga_cli`. This involves integrating the `CommandParser` to handle direct memory commands and using the `rich` library for a more intuitive and visually appealing user experience.

The integration of `AgnoPersonalAgent` is achieved by:
- Instantiating `AgnoPersonalAgent` within the team creation process.
- Using its `_ensure_initialized()` method to wait for its lazy-initialization to complete.
- Injecting the team's shared memory object into the agent instance.
- Appending the necessary `AgnoMemoryTools` and `KnowledgeTools` to the agent's existing toolset.

This approach allows the `AgnoPersonalAgent` to function as a specialized, stateful member of the team, leveraging its full capabilities while participating in the team's shared memory context.

## Consequences

### Positive
- **Feature Parity**: The reasoning team now has the same advanced memory and knowledge management capabilities as the main agent.
- **Consistent User Experience**: Users now have a consistent set of commands and a similar interface whether they are using the main CLI or the team CLI.
- **Increased Power**: The team can now handle much more complex tasks by leveraging the full potential of the `AgnoPersonalAgent`.
- **Improved Maintainability**: Reusing `AgnoPersonalAgent` and `CommandParser` reduces code duplication and centralizes agent logic.
- **Better Usability**: The new `rich`-based CLI is more user-friendly and provides clearer feedback.

### Negative
- **Increased Complexity**: The initialization logic for the team is now slightly more complex due to the need to correctly instantiate and configure the `AgnoPersonalAgent` within the team's asynchronous context.
- **Tighter Coupling**: The team is now more tightly coupled to the `AgnoPersonalAgent` implementation, though this is a deliberate design choice to ensure consistency.
