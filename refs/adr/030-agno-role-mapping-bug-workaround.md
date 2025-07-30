# ADR-030: Workaround for Agno OpenAI Role Mapping Bug

## Context

While implementing LMStudio integration (ADR-029), a critical bug was discovered in the `agno.models.openai.OpenAIChat` class. The default role map for the model incorrectly maps the `system` role to `developer`. The OpenAI API and its compatible endpoints (like LMStudio) only accept `['user', 'assistant', 'system', 'tool']` as valid roles. This bug causes a `400 Bad Request` error whenever a team operation attempts to send a system message.

## Decision

Since the bug lies within the imported `agno` framework, a direct fix is not immediately possible. Therefore, a workaround has been implemented within the `personal_agent` codebase.

A new `create_model` factory function was introduced in the multi-purpose reasoning team module. This function intercepts the model creation process and applies a corrected role map to the `OpenAIChat` instance. This ensures that all system messages are correctly sent with the `system` role.

This workaround is applied to all OpenAI models created through the `AgentModelManager`, effectively patching the bug at runtime for the agent's purposes.

## Consequences

### Positive
-   **Immediate Fix**: The workaround immediately resolves the critical bug, allowing the agent to use OpenAI-compatible models (including LMStudio) without errors.
-   **Isolated Solution**: The fix is contained within the agent's codebase and does not require a forked or modified version of the `agno` framework.

### Negative
-   **Technical Debt**: This is a temporary solution. The workaround should be removed once the `agno` framework is updated with a permanent fix.
-   **Maintenance Overhead**: The workaround needs to be maintained and potentially updated if the `agno` framework's model creation process changes.
-   **Potential for Redundancy**: If the bug is fixed in `agno` and the workaround is not removed, it could lead to redundant or conflicting configurations.
