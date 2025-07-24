refactor(core): Unify memory and knowledge tools into a single Toolkit

This commit introduces a significant architectural refactoring by consolidating all memory and knowledge-related tools into a single, cohesive `MemoryAndKnowledgeTools` class.

Previously, tool functions were dynamically generated from multiple managers, leading to a complex and scattered initialization process within the main agent class. This new approach simplifies the agent's setup, improves modularity, and aligns more closely with the `agno` framework's idiomatic use of `Toolkit` classes.

Key changes:
- Introduced `MemoryAndKnowledgeTools` as the central toolkit for all memory and knowledge operations.
- Removed the now-redundant `get_memory_tools` method from `AgentMemoryManager`.
- Simplified the `AgnoPersonalAgent` initialization logic to use the new unified toolkit.
- Updated agent instructions to reflect the new tool structure.

This change makes the codebase more maintainable, readable, and easier to extend.

See ADR-035: Unified Memory and Knowledge Tools for more details.
