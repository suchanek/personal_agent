# ADR-086: Age-Perspective Memory Creation with `delta_year`

**Status:** Accepted

**Date:** 2025-09-17

## Context

The agent's memory system needs a mechanism to store memories from a user's past, not just the present moment. This capability is essential for building a comprehensive personal timeline, allowing users to journal about childhood events, recall past experiences, and construct a richer, more complete digital memory. The existing system only timestamps memories with the current date and time, making it impossible to log historical events accurately.

## Decision

We will introduce a `delta_year` attribute to the `User` model. This optional integer field will represent the user's age at the time the memory occurred.

When a memory is created and `delta_year` is set:
1.  The system will calculate the memory's year by adding the `delta_year` to the user's birth year (`memory_year = user.birth_year + delta_year`).
2.  The month, day, and time of the memory's timestamp will be set to the current month, day, and time of creation.

This approach creates a timestamp that is chronologically consistent with the user's life, placing the memory in the correct year while anchoring it to the present moment of recording. If `delta_year` is `None` or `0`, the memory is timestamped with the current date and time as usual.

This logic will be encapsulated in a `get_memory_timestamp()` method in the `User` model and integrated into the `AgentMemoryManager` and `SemanticMemoryManager` to handle the custom timestamp.

## Consequences

### Positive
- **Enables Rich Historical Memory:** Users can now create a comprehensive timeline of their life, adding memories from any age.
- **Simple and Intuitive:** The `delta_year` concept is easy for users to understand and for the agent to use (e.g., "Remember when I was 10...").
- **Maintains Chronological Consistency:** By setting the correct year, memories are stored in a logical, sequential order, making them easier to retrieve and reason about.
- **Low Technical Overhead:** The implementation is straightforward, primarily affecting the `User` model and the memory creation timestamp logic, without requiring major architectural changes.

### Negative
- **Dependency on Birth Date:** The feature is only functional if the user has set their `birth_date` in their profile. The system will need to handle cases where it's missing.
- **Minor Complexity Increase:** Adds a small amount of complexity to the memory creation process and the `User` model.