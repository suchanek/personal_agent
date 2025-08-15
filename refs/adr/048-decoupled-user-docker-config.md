# ADR-048: Decoupled User and Docker Configuration with ~/.persag

- **Status**: Accepted
- **Date**: 2025-08-05

## Context

The previous architecture stored user-specific and Docker-related configurations directly within the project repository. Key files and directories such as `env.userid`, `lightrag_server/`, and `lightrag_memory_server/` were located at the project root.

This approach led to several issues:
- **Repository Clutter**: The project's version control was cluttered with user-specific, non-code files.
- **Tight Coupling**: User configuration was tightly coupled with the codebase, making it difficult to manage different user environments or deploy the agent cleanly.
- **User Isolation**: On a multi-user system, this could lead to conflicts or require complex workarounds to isolate user data.
- **Deployment Complexity**: Deploying the agent required manual separation of configuration files from the core application code.

## Decision

We have decided to refactor the configuration management system to centralize all user-specific and Docker-related configurations into a dedicated `~/.persag` directory located in the user's home directory.

This refactoring introduces several key components:
1.  **`~/.persag` Directory**: A single, standardized location (`/Users/<user>/.persag`) to store all user-specific data, including `env.userid`, Docker service configurations, and backups.
2.  **`PersagManager`**: A new class (`src/personal_agent/core/persag_manager.py`) that acts as the single point of control for managing the `~/.persag` directory. It handles initialization, validation, migration, and provides a centralized API for accessing configuration paths.
3.  **Dynamic User ID Retrieval**: The static `USER_ID` constant, previously imported from `settings.py`, has been replaced with a dynamic `get_userid()` function. This function retrieves the current user ID directly from `~/.persag/env.userid`, ensuring the system always has the correct user context.
4.  **Automatic Migration**: A seamless, automatic migration process was implemented within the `PersagManager`. On first run, it detects the old project-based configuration and migrates it to the new `~/.persag` structure, ensuring a smooth transition for existing users.

## Consequences

### Positive
- **Repository Decoupling**: The project repository is now completely free of user-specific files and configurations, making it cleaner and easier to manage.
- **True User Isolation**: Each user on a system has their own `~/.persag` directory, ensuring complete data and configuration isolation.
- **Single Source of Truth**: All user and Docker configurations are now managed in one predictable location, simplifying debugging and management.
- **Simplified Deployment**: Deploying the agent is now more straightforward, as the application code is fully separated from user-specific runtime configuration.
- **Enhanced Robustness**: The `PersagManager` provides validation and backup capabilities, improving the overall resilience of the configuration system.

### Negative
- **External Configuration**: Configuration is now stored outside the project directory. Users and developers will need to be aware of the `~/.persag` location for manual inspection or debugging.
- **One-Time Migration**: Existing users must go through a one-time, albeit automatic, migration process.
