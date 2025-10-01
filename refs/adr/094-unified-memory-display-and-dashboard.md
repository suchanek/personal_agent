# ADR-094: Unified Memory Display and Standalone Management Dashboard

## Status

Accepted

## Context

The project has two distinct Streamlit interfaces:
1.  The primary agent interaction UI (`paga_streamlit_agno.py`).
2.  A system management dashboard for administrative tasks (`dashboard.py`).

There was a need to provide a more intuitive and consistent view of user memories across both interfaces. Previously, memories were displayed with static timestamps, which didn't reflect the user's age or the context of when the memory was recorded. Additionally, user switching functionality was not robust.

## Decision

We have implemented the following changes:

1.  **Dynamic Memory Timestamps**: Both the main agent UI and the management dashboard will now display memories with dynamic, human-readable timestamps (e.g., "3 days ago," "at age 25"). This provides a more intuitive understanding of the memory's context and chronology.
2.  **Standalone Management Dashboard**: The role of `dashboard.py` is clarified as a standalone tool for system administration (user management, service status, etc.), distinct from the main agent's conversational UI.
3.  **Robust User Switching**: The user switching logic has been fixed to ensure stability and reliability when changing user contexts.

This approach provides a clear separation of concerns between agent interaction and system management, while creating a unified and user-friendly experience for viewing memories.

## Consequences

-   **Improved User Experience**: Dynamic memory dates make the agent's memory recall more natural and easier to understand.
-   **Clearer Architecture**: The distinction between the main UI and the management dashboard is now formally documented.
-   **Increased Stability**: The fix to user switching improves the reliability of the multi-user system.
-   Code for dynamic date calculation is now shared or duplicated across two different UI components, which should be monitored for future refactoring opportunities.
