# ADR-015: Persistent User Context via Single Source of Truth

**Date**: 2025-07-14

**Status**: Accepted

## Context

The previous user management system, while dynamic, had a potential point of failure. The application's user context was primarily driven by the `USER_ID` environment variable. While the `UserManager` and `switch-user.py` script correctly updated this variable, a user could be specified *only at initialization time* (e.g., via a command-line flag like `paga_cli --user-id "new_user"`).

This created a **transient user session**. The agent would operate as "new_user" for that single run, but the change was never persisted. The next time the application started, it would revert to the previous user, leading to an inconsistent and confusing user experience.

## Decision

To solve this and create a truly robust and predictable user context, we have designated a single file, `env.userid`, as the **single source of truth** for the current user.

1.  **`env.userid` as the Source of Truth**:
    *   A new file, `env.userid`, located at the project root, will store the current user's ID (e.g., `USER_ID="Eric"`).
    *   This file is now the definitive record of the active user.

2.  **Application Startup Logic**:
    *   At application startup, a new function `load_user_from_file()` in `src/personal_agent/config/settings.py` is called *before any other configuration is loaded*.
    *   This function reads `env.userid` and immediately sets the `USER_ID` in the current environment (`os.environ`). This ensures the entire application initializes with the correct, persistent user context.

3.  **Persistent User Switching**: 
    *   The `UserManager.switch_user()` method has been enhanced. In addition to updating the environment variable, it now immediately writes the new user ID to the `env.userid` file, persisting the change.

4.  **Robust Agent Initialization**:
    *   The `AgnoPersonalAgent.initialize()` method has been made more intelligent.
    *   It now compares the user ID it was initialized with against the persistent user ID loaded from `env.userid`.
    *   If they differ, the agent recognizes this as a formal user switch and automatically calls `UserManager.switch_user()`. This triggers the full, persistent switching logic, including updating the `env.userid` file and restarting services.

## Consequences

### Positive

*   **Predictable User Context**: The agent's user context is no longer transient. The user specified in `env.userid` is always the user who will be loaded, eliminating surprises.
*   **Single Source of Truth**: Centralizing the current user state into a single, persistent file makes the system easier to understand, debug, and manage.
*   **Robust Initialization**: The agent now correctly handles being initialized with a new user, automatically persisting this change as a formal user switch.
*   **Improved User Experience**: The user context is consistent across application restarts, providing a seamless experience.

### Negative

*   **Filesystem Dependency**: The application now has a direct dependency on the `env.userid` file for its initial configuration. If this file is corrupted or unreadable, it could affect startup (though it will fall back to a default user).
