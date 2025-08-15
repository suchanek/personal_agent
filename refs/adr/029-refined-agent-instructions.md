# ADR-029: Refined Agent Instructions to Prevent Over-Memorization

**Status:** Accepted

**Context:**

The agent, particularly in the `dev/v0.11.0` release, was incorrectly storing its own actions (e.g., creative writing) as user memories. This was due to overly aggressive and ambiguous instructions that created a strong bias towards memory storage. The "NO HESITATION RULE" and the agent's "MEMORY EXPERT" identity were causing it to misinterpret its own actions as user facts.

**Decision:**

1.  The agent's instructions in `src/personal_agent/core/agent_instruction_manager.py` will be significantly refined to be more precise and less aggressive.
2.  The instructions will now include a clear distinction between agent actions and user facts, with explicit examples of what *not* to store.
3.  The "NO HESITATION RULE" for memory storage will be replaced with a more nuanced "Guiding Principle" to encourage more thoughtful memory creation.
4.  The `paga_cli` entry point will be updated to explicitly use the `CONCISE` instruction level to ensure consistent behavior across all interfaces.

**Consequences:**

*   The agent will be more discerning about what it stores in its memory, leading to a higher quality and more relevant set of user memories.
*   The risk of the agent polluting its memory with its own actions will be significantly reduced.
*   The agent's behavior will be more consistent and predictable across different interfaces.
