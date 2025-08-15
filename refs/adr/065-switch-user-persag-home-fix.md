# ADR-065: Fix `switch-user.py` to Use `~/.persag` for Docker Services

- Status: accepted
- Date: 2025-08-15
- Deciders: Personal Agent Development Team

## Context and Problem Statement

The `switch-user.py` script is a critical component for managing user contexts in the multi-user system. After a recent refactoring ([ADR-048](./048-decoupled-user-docker-config.md)), the Docker configurations for LightRAG services were moved from the project root to the `~/.persag` directory (also known as `PERSAG_HOME`). However, the `switch-user.py` script and its underlying `LightRAGManager` were not updated to reflect this change. They were still attempting to locate and manage the Docker services in the old project root location, causing the user switching functionality to fail.

## Decision Drivers

- **Functionality:** The `switch-user.py` script must work correctly with the new `~/.persag` directory structure.
- **Consistency:** The system must consistently use the centralized configuration for all paths, including Docker service paths.
- **Maintainability:** The code should be easy to understand and maintain, avoiding hardcoded paths.

## Considered Options

1.  **Pass `PERSAG_HOME` to `LightRAGManager`:** This would involve passing the `PERSAG_HOME` path down from `switch-user.py` to `UserManager` and then to `LightRAGManager`. This would work but would add more parameters to the constructors.
2.  **Use Centralized Settings in `LightRAGManager`:** This would involve importing the `LIGHTRAG_SERVER_DIR` and `LIGHTRAG_MEMORY_DIR` directly from the centralized settings in `LightRAGManager`. This would be a cleaner solution as it would not require any changes to the method signatures.

## Decision Outcome

Chosen option: **Use Centralized Settings in `LightRAGManager`**.

We have updated the `LightRAGManager` to import the `LIGHTRAG_SERVER_DIR` and `LIGHTRAG_MEMORY_DIR` paths directly from the centralized configuration (`src/personal_agent/config/settings.py`). This ensures that the manager always uses the correct paths, which are derived from `PERSAG_HOME`.

We also updated the `UserManager` to use `DATA_DIR` instead of `PERSAG_ROOT` for consistency in user data management.

Finally, we updated the `switch-user.py` script to correctly instantiate the `UserManager`.

### Positive Consequences

- The `switch-user.py` script now works correctly with the `~/.persag` directory structure.
- The system is more consistent in its use of centralized configuration.
- The code is more maintainable as it avoids hardcoded paths.

### Negative Consequences

- None.

## Implementation

- **`src/personal_agent/core/lightrag_manager.py`**:
    - Updated the `__init__` method to import and use `LIGHTRAG_SERVER_DIR` and `LIGHTRAG_MEMORY_DIR` from the centralized settings.
    - Deprecated the `project_root` parameter for Docker paths.
- **`src/personal_agent/core/user_manager.py`**:
    - Updated to use `DATA_DIR` instead of `PERSAG_ROOT` for consistency.
- **`switch-user.py`**:
    - Updated to correctly instantiate the `UserManager`.

## Validation

The fix was validated by running the `switch-user.py` script with different users and verifying that the Docker services were correctly restarted with the new user context and that the correct paths in `~/.persag` were used.
