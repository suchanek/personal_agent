# ADR-068: Unified Agent and Team Interface in Streamlit

- **Status**: Accepted
- **Date**: 2025-08-17

## Context and Problem Statement

The project supported two primary modes of interaction: a single `AgnoPersonalAgent` and a multi-agent `PersonalAgentTeam`. Previously, these modes were likely accessed through separate applications or scripts, leading to a fragmented user experience. Users could not easily switch between or compare the two modes, and it required maintaining separate UI codebases, increasing complexity and duplicated effort.

## Decision Drivers

- The need for a single, intuitive user interface for all agent interactions.
- The desire to reduce code duplication and maintenance overhead.
- The goal of providing a seamless way for users to leverage both single-agent and multi-agent capabilities.

## Considered Options

1.  **Keep separate applications**: Maintain distinct UIs for the single agent and the team. This is the status quo, which leads to the problems described above.
2.  **Create a unified UI**: Refactor the main Streamlit application to incorporate both modes, with a mechanism to switch between them at runtime.
3.  **Embed one mode within the other**: For example, make the team interface a tab within the single-agent UI, or vice-versa. This was considered less flexible than a full runtime switch.

## Decision Outcome

Chosen option: **Create a unified UI**.

The `paga_streamlit_agno.py` application has been refactored to serve as a single entry point for both the single agent and the agent team.

### Implementation Details

- A new session state key, `SESSION_KEY_AGENT_MODE`, tracks the current mode ("single" or "team").
- The sidebar now features a dropdown menu allowing the user to dynamically switch between "Single Agent" and "Team of Agents" modes.
- On switching, the application re-initializes the appropriate agent or team, clears the chat history, and updates the helper classes (`StreamlitMemoryHelper`, `StreamlitKnowledgeHelper`) to point to the active system.
- The core chat logic in `render_chat_tab` now conditionally calls either `agent.run()` or `team.arun()` based on the selected mode.
- UI elements, such as titles and informational sections, dynamically adapt to display context-relevant information for the active mode.

## Consequences

### Positive

- **Improved User Experience**: Users have a single, coherent interface for all interactions, allowing them to easily switch between and compare the single agent and the team.
- **Reduced Code Duplication**: UI components, chat logic, and helper functionalities are now shared, significantly reducing the amount of duplicated code.
- **Simplified Maintenance**: Having a single application to manage simplifies development, debugging, and deployment.
- **Centralized Entry Point**: `paga_streamlit_agno.py` becomes the canonical way to interact with the agent system graphically.

### Negative or Neutral

- **Increased Complexity in a Single File**: The `paga_streamlit_agno.py` file has grown in complexity to manage the state and logic for both modes. This is mitigated by clear function separation and session state management.
- **State Management Overhead**: The session state is now more complex, as it must handle the initialization and configuration of both the agent and the team, though only one is active at a time.
