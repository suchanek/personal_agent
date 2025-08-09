# ADR-055: Clarified Agent Memory Instructions

- **Status**: Accepted
- **Date**: 2025-08-09

## Context

The agent was exhibiting confusion regarding its role in handling user memories. The instructions were ambiguous about the conversion of user statements between first-person (input), third-person (storage), and second-person (presentation). This led to inconsistent memory handling and unnecessary cognitive load on the agent, as it tried to manage conversions that were meant to be handled by the underlying system.

For example:
- **User Input (1st Person):** "I attended Maplewood School."
- **System Storage (3rd Person):** "Eric attended Maplewood School."
- **Agent Presentation (2nd Person):** "You attended Maplewood School."

The agent's instructions did not clearly delineate its responsibility from the system's automatic processes, causing it to hesitate or incorrectly attempt to manage these grammatical transformations.

## Decision

We have updated the agent's core instructions within `src/personal_agent/core/agent_instruction_manager.py` to provide a crystal-clear, three-stage process for memory handling.

1.  **Stage 1: Input Processing:** The agent is instructed to expect user information in the first person (e.g., "I have a dog named Snoopy"). It should take this input directly.

2.  **Stage 2: Storage Format (System Responsibility):** The instructions now explicitly state that the system **automatically** handles the conversion from the user's first-person input to a third-person format for storage in the knowledge graph. The agent is told not to worry about this step.

3.  **Stage 3: Presentation Format (Agent Responsibility):** The agent's primary responsibility is defined as converting the retrieved third-person memories into the second person when presenting them back to the user.

This clarification was applied to all instruction sophistication levels (STANDARD, EXPLICIT, LLAMA3, QWEN) to ensure consistent behavior across all models.

## Consequences

### Positive
- **Eliminates Ambiguity**: The agent now has a clear and unambiguous mental model for memory operations.
- **Reduced Agent Confusion**: The agent no longer needs to "overthink" the conversion process, leading to more reliable and direct use of the `store_user_memory` tool.
- **Improved Consistency**: Memory handling is now consistent across all instruction levels and models.
- **Simplified Agent Logic**: The agent's responsibility is simplified to focus on natural language presentation rather than grammatical transformations for storage.

### Negative
- None identified. This change clarifies an existing process without altering the underlying memory management logic (`AgentMemoryManager.restate_user_fact()` continues to function as before).
