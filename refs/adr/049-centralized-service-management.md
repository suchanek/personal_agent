# ADR-049: Centralized Service Management for User Switching

## Status

Accepted

## Context

The previous architecture for managing user-specific services (like LightRAG knowledge and memory servers) was intertwined with the `UserManager`. When a user switch was initiated, the `UserManager` was directly responsible for finding and restarting the relevant Docker containers. This approach had several drawbacks:

- **Tight Coupling**: The `UserManager` was tightly coupled to the implementation details of the Docker services, violating the Single Responsibility Principle.
- **Complexity**: The logic for stopping, starting, and managing services was complex and duplicated across different parts of the system.
- **Scalability**: Adding new user-specific services would require modifying the `UserManager`, making the system harder to extend.
- **User Experience**: The user switching process was managed through disparate scripts, leading to an inconsistent user experience.

## Decision

To address these issues, we will implement a centralized service management system.

1.  **Introduce `ServiceManager`**: A new `ServiceManager` class will be created in `src/personal_agent/core/services.py`. This class will encapsulate all logic related to managing Docker services. It will be responsible for discovering running services, stopping them, and starting them in the correct user context.

2.  **Delegate Responsibility**: The `UserManager` will be refactored to delegate all service management tasks to an instance of the `ServiceManager`. This decouples user management from service management.

3.  **Create `switch-user.py` CLI**: A new, user-friendly CLI script, `scripts/switch_user.py`, will be created as the primary interface for creating and switching users. This script will utilize the `UserManager` to perform the switch, providing a single, consistent entry point for users.

## Consequences

### Positive

- **Improved Separation of Concerns**: The `UserManager` now focuses solely on user state, while the `ServiceManager` handles all service-related operations.
- **Enhanced Maintainability**: The codebase is cleaner, more modular, and easier to understand.
- **Increased Scalability**: Adding new services is simplified, as changes are localized to the `ServiceManager`.
- **Better User Experience**: The `switch-user.py` script provides a clear and simple command-line interface for managing user contexts.
- **Improved Reliability**: Centralizing service logic reduces the risk of errors and ensures a more robust user switching process.

### Negative

- **Increased Abstraction**: Adds one more layer of abstraction to the system, which slightly increases the initial learning curve for new developers.
