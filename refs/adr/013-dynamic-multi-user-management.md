# ADR-013: Dynamic Multi-User Management System

**Date**: 2025-07-13

**Status**: Accepted

## Context

The personal agent was initially designed with a single-user focus. The `USER_ID` was a static configuration value loaded at application startup. This architecture presented significant limitations:

1.  **Static `USER_ID` Imports**: The core issue was that `USER_ID` was imported as a static value (e.g., `from personal_agent.config import USER_ID`). This value was cached at module load time and did not update when the underlying environment variable changed, leading to stale user contexts.
2.  **No User Switching**: To switch user contexts, a full application restart with modified environment variables was required.
3.  **Data Isolation Risk**: All user-specific data paths and service configurations were tied to this static `USER_ID`, making it difficult to manage multiple users' data safely.
4.  **Inflexible Service Management**: The Docker services (`LightRAG`, `LightRAG Memory`) were not designed to dynamically switch user contexts, leading to inconsistent states and frequent "port already allocated" errors upon restart.

A robust, dynamic, and integrated multi-user system was needed to address these issues, enabling seamless user switching and strong data isolation across the entire application stack.

## Decision

We decided to implement a comprehensive, full-stack **Dynamic Multi-User Management System**. This system is built on the principle of a dynamic `USER_ID` that can be changed at runtime, with all parts of the system reacting accordingly without requiring a full application restart.

The key components of this new architecture are:

### 1. Dynamic `USER_ID` Resolution

To solve the static import problem, we replaced direct imports of the `USER_ID` constant with a dynamic function call that always reads the current state from the environment.

**Old (Static) Pattern:**
```python
from personal_agent.config import USER_ID # This gets cached!

def some_function(user_id: str = USER_ID): # Default value is cached at import time
    pass
```

**New (Dynamic) Pattern:**
```python
from personal_agent.config import get_current_user_id

def some_function(user_id: str = None):
    if user_id is None:
        user_id = get_current_user_id() # Always gets the current value
    pass
```

This was implemented via two new functions in `src/personal_agent/config/settings.py`:
-   `get_current_user_id()`: Always returns the latest `USER_ID` from `os.getenv("USER_ID")`.
-   `refresh_user_dependent_settings()`: Recalculates all user-specific configuration paths (e.g., storage directories) immediately after a user switch.

### 2. Centralized User and Service Management

We introduced three new core modules to manage users and services:

-   **`UserRegistry` (`src/personal_agent/core/user_registry.py`)**: A simple, file-based JSON registry (`users_registry.json`) to persistently store and manage user profiles.
-   **`LightRAGManager` (`src/personal_agent/core/lightrag_manager.py`)**: A Python API to manage the lifecycle of LightRAG Docker services. It dynamically updates `.env` and `docker-compose.yml` files to inject the current `USER_ID` before starting containers.
-   **`UserManager` (`src/personal_agent/core/user_manager.py`)**: The central orchestrator for all user-related operations. Its `switch_user` method performs the full sequence of updating the environment, refreshing configurations, and restarting services in the correct user context.

### 3. Robust Service Restart Logic

A new `smart-restart-lightrag.sh` script and a corresponding Python implementation (`SmartDockerRestart`) were introduced. This logic intelligently stops services, waits for ports to be released, and handles retries, preventing common "port already allocated" errors and ensuring service stability.

### 4. Full-Stack Refactoring and Testing

-   **`SemanticMemoryManager`**: All methods were refactored to use the new dynamic `get_current_user_id()` pattern, making all memory operations fully user-aware.
-   **Streamlit UI**: The UI was completely overhauled to use the new managers, transforming it from a static display with placeholder data into a fully functional and interactive user management dashboard.
-   **Dedicated Testing**: A new test suite, `test_user_id_propagation.py`, was created to rigorously validate that the `USER_ID` is correctly propagated and handled across all layers of the new system.

## Consequences

### Positive

-   **Full Multi-User Capability**: The agent now supports multiple users with seamless switching capabilities directly from the UI.
-   **Strong Data Isolation**: User data is now properly isolated at the filesystem and service level.
-   **Improved Reliability**: The "smart restart" logic for Docker services significantly improves system stability.
-   **Enhanced Maintainability**: Centralizing user logic into dedicated managers makes the code cleaner and more modular.
-   **Improved User Experience**: The Streamlit UI is now a fully functional user management dashboard.

### Negative

-   **Increased Complexity**: The architecture is now more complex due to the addition of multiple new managers and the dynamic nature of the configuration.
-   **Dependency on Environment Variables**: The system is critically dependent on the `USER_ID` environment variable being correctly managed.
-   **Slight Performance Overhead**: Switching users incurs a small delay due to the need to restart Docker containers. This is a one-time cost per switch, necessary for proper context isolation.

## Migration Guide for Developers

To ensure compatibility with the new multi-user system, developers should follow these patterns:

1.  **Replace Static Imports**: Change `from personal_agent.config import USER_ID` to `from personal_agent.config import get_current_user_id`.
2.  **Update Function Signatures**: Modify functions that relied on the static `USER_ID`.

    *   **Old:** `def my_function(user_id: str = USER_ID):`
    *   **New:** `def my_function(user_id: str = None):`
3.  **Implement Dynamic Resolution**: Add logic to fetch the current user ID within the function.

    ```python
    if user_id is None:
        user_id = get_current_user_id()
    ```
