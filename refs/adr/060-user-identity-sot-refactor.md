# ADR-060: User Identity Single Source of Truth Refactor

## Status

**Accepted**

## Context

The project had duplicated logic for managing user identity and user-specific paths across multiple modules (`settings.py`, `PersagManager`, `UserRegistry`). This led to inconsistencies, bugs, and made the codebase difficult to maintain. A centralized, single source of truth was needed to ensure that the current user's context was handled consistently and predictably throughout the application.

## Decision

1.  **Centralize User Logic**: Consolidate all user identity and path management logic into a new `src/personal_agent/config/user_id_mgr.py` module. This module is now the single source of truth for all user-centric operations.
2.  **Delegate to `user_id_mgr.py`**: Refactor `PersagManager`, `UserRegistry`, and `settings.py` to delegate all user-related operations to the new `user_id_mgr.py` module.
3.  **Isolate Initialization**: The `user_id_mgr.py` module now handles the initialization of the `~/.persag` directory, including the creation of the `env.userid` file and the migration of Docker configurations.
4.  **Non-Destructive Testing**: A new integration test, `tests/test_user_id_mgr_non_destructive.py`, was created to validate the entire user identity flow in an isolated, temporary environment, ensuring that the refactoring is robust and does not affect the user's actual data.

## Consequences

### Positive

-   Eliminates code duplication and the risk of inconsistencies.
-   Improves maintainability by centralizing user identity logic.
-   Enhances the robustness of dynamic user switching.
-   Provides a clear, non-destructive way to test the user identity system.

### Negative

-   None.
