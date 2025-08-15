# ADR-062: Unambiguous Data Directory Configuration

## Context

The configuration variable `DATA_DIR` was used inconsistently throughout the codebase. In some modules, it pointed to the global application data root (`PERSAG_ROOT`), while in others, it referred to the current user's specific data directory. This ambiguity created confusion, made path management difficult to reason about, and increased the risk of configuration-related bugs.

## Decision

To resolve this ambiguity and improve clarity, we have refactored the data directory configuration with the following changes:

1.  **Introduce `USER_DATA_DIR`**: A new, explicit configuration variable, `USER_DATA_DIR`, has been created. This variable now consistently and unambiguously points to the data directory for the currently active user (e.g., `~/.persag/agno/{user_id}/data`).
2.  **Standardize `DATA_DIR`**: The existing `DATA_DIR` variable has been standardized to always point to the global application data root, `PERSAG_ROOT`.
3.  **Update Modules**: All modules that handle data paths, including `settings.py`, `user_id_mgr.py`, `agno_agent.py`, and the `show_config.py` tool, have been updated to use this new, clearer distinction.

## Consequences

- **Improved Clarity**: The purpose of each data directory variable is now explicit and self-documenting, reducing cognitive overhead for developers.
- **Reduced Risk of Errors**: By removing the ambiguity, we minimize the risk of misconfigurations and path-related bugs.
- **Enhanced Maintainability**: Code that depends on data paths is now easier to understand, maintain, and debug.
