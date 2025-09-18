# ADR-087: Robust UI Memory Storage and Context Handling

**Date**: 2025-09-18
**Status**: Proposed

## Context

The system exhibited two critical bugs related to memory storage, originating from different parts of the architecture but converging to impact user experience and data integrity:

1.  **Streamlit UI Failure**: When operating in "team mode," the Streamlit UI could not store user memories. The `StreamlitMemoryHelper` attempted to call a `memory_manager` attribute on a `TeamWrapper` object, which did not possess it. This wrapper was an overly complex abstraction designed to make the multi-agent team compatible with UI components built for a single-agent interface.
2.  **`delta_year` Timestamp Failure**: The `delta_year` feature, which allows users to store memories from the perspective of a past age, was non-functional. The root cause was that user context was being passed down the memory pipeline as a plain dictionary instead of a `User` domain object. The `AgentMemoryManager` requires a `User` object to access the `get_memory_timestamp()` method, which performs the `delta_year` calculation.

Both issues highlight a need for more robust and simpler architectural patterns when connecting UI components to the agent's core logic.

## Decision

To resolve these issues and prevent future occurrences, we will adopt two architectural principles:

1.  **Direct Agent Interaction for UI Components**: UI helpers and wrappers must interact with a stable, predictable agent interface. In a multi-agent team, this means directly accessing the designated agent responsible for a specific capability (e.g., the `Knowledge Agent` for memory operations) instead of interfacing with the team coordinator or a complex wrapper. This simplifies the UI logic and decouples it from the team's internal structure.

2.  **Enforced Type Safety at the Memory Pipeline Boundary**: The function serving as the entry point to the core memory storage system (`memory_functions.store_user_memory`) is now responsible for ensuring that incoming data is converted into the required domain objects. It will explicitly check if user context is a dictionary and, if so, convert it into a `User` object before passing it to the `AgentMemoryManager`. This enforces type safety and ensures that all necessary methods and attributes are available for processing.

## Consequences

### Positive
- **Increased Reliability**: The Streamlit UI is now more reliable and less prone to breaking when the team structure changes.
- **Functional Correctness**: The `delta_year` feature now works as intended, allowing for accurate, age-adjusted timestamping of memories.
- **Simplified Architecture**: Eliminates the need for the complex `TeamWrapper` class, reducing code complexity and improving maintainability.
- **Improved Decoupling**: The UI is better decoupled from the agent's internal implementation details.
- **Enhanced Maintainability**: Centralizing the type conversion logic in `memory_functions.py` creates a single point of responsibility for data integrity in the memory pipeline.

### Negative
- None identified. The changes are strictly corrective and improve architectural soundness.
