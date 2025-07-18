# ADR-023: Re-enable User Memory Retrieval

## Context

During recent refactoring and integration efforts, a critical configuration error was introduced in `src/personal_agent/core/agno_agent.py`. Specifically, the `Agent` initialization was set with `enable_user_memories=False`:

```python
self.agent = Agent(
    # ... other parameters ...
    enable_agentic_memory=False,  # Disable agno's native memory to use our custom memory system
    enable_user_memories=False,  # Disable agno's native memory
    # ...
)
```

While `enable_agentic_memory=False` was an intentional decision to leverage our custom `AgentMemoryManager` and its tools (like `query_memory`), setting `enable_user_memories=False` inadvertently disabled the agent's ability to utilize any user-specific memory retrieval mechanisms, including those provided by our custom tools. This resulted in the agent being unable to effectively recall or respond to queries related to user-stored facts, even when the underlying memory system was functional.

## Decision

To re-enable the agent's capability to retrieve user memories and leverage the `query_memory` tool provided by our custom `AgentMemoryManager`, we will change the `enable_user_memories` parameter to `True` in the `Agent` initialization within `src/personal_agent/core/agno_agent.py`.

```python
self.agent = Agent(
    # ... other parameters ...
    enable_agentic_memory=False,  # Still disable agno's native agentic memory
    enable_user_memories=True,   # Re-enable agno's native user memory to allow user retrieval
    # ...
)
```

It is important to note that `memory=None` will remain, as our custom memory system handles the storage and retrieval, and we do not want agno's default memory storage mechanisms to interfere or create conflicts.

## Consequences

### Positive
- **Restored User Memory Retrieval**: The agent will now be able to effectively retrieve and utilize user-specific memories, significantly improving its personalization capabilities.
- **Enhanced Agent Performance**: The agent will be able to provide more accurate and contextually relevant responses to user queries that rely on stored facts.
- **Full Utilization of Custom Memory System**: Ensures that the `query_memory` tool and other custom memory features are properly integrated and accessible to the agent.

### Negative
- None identified. This change corrects an unintended side effect and restores expected functionality without introducing new issues, as the custom memory system is still responsible for the actual memory management.