# ADR-058: Modular User ID Management and Centralized User Configuration

## Status

**Accepted**

## Context

The primary configuration file, `src/personal_agent/config/settings.py`, had accumulated both system-level settings and user-specific logic, such as functions for retrieving the current user ID and constructing user-specific data paths. This blending of responsibilities led to several issues:

1.  **Circular Imports**: Multiple modules, including Streamlit components and core agent logic, needed to import user-specific functions from `settings.py`, while `settings.py` itself had broad dependencies. This created complex and fragile import chains that were prone to circular dependency errors.
2.  **Poor Separation of Concerns**: Mixing general application settings with dynamic, user-specific logic violated the Single Responsibility Principle, making the code harder to understand, maintain, and test.
3.  **Coupled User Data**: User-specific configurations, particularly the Docker files for the LightRAG servers, were located within the project's directory structure. This tightly coupled the user's runtime data with the codebase, complicating updates and making it difficult for users to manage their data independently.

A refactoring was necessary to decouple these concerns, improve modularity, and create a more robust and maintainable configuration system.

## Decision

We have decided to implement a comprehensive refactoring to isolate user management and centralize user-specific data:

1.  **Create a Dedicated User ID Manager**: All functions related to user ID and user-specific path management have been extracted from `settings.py` and moved into a new, dedicated module: `src/personal_agent/config/user_id_mgr.py`. This module is now the single source of truth for all user-centric configuration logic.

2.  **Centralize User Configuration in `~/.persag`**: All user-specific runtime configurations, most notably the `lightrag_server` and `lightrag_memory_server` directories, will be stored in a `.persag` directory within the user's home directory (`~/.persag`). This decouples user data from the project's source code.

3.  **Automated Environment Setup**: The `load_user_from_file` function in the new `user_id_mgr.py` module will automatically handle the creation of the `~/.persag` directory. On its first run, it copies the default LightRAG server configurations from the project root into the `~/.persag` directory, ensuring a seamless setup experience for the user.

4.  **Resolve Circular Dependencies**: All modules that previously imported user-specific functions from `settings.py` have been updated to import directly from the new `user_id_mgr.py` module. The `config` package's `__init__.py` continues to export these functions to maintain backward compatibility for any existing imports.

## Consequences

### Positive

-   **Improved Modularity**: The separation of user management logic into its own module makes the configuration system cleaner and easier to navigate.
-   **Elimination of Circular Imports**: The refactoring resolves the persistent circular dependency issues, making the codebase more stable and predictable.
-   **Decoupled User Data**: Storing user configurations in `~/.persag` separates user data from the application's source code. This allows users to update the application without affecting their data and simplifies the process of backing up or migrating user profiles.
-   **Enhanced Maintainability**: With a clear separation of concerns, both system-level settings and user-specific logic are easier to find, modify, and test.

### Negative

-   **First-Run Side Effect**: The automatic creation of directories and copying of files into the user's home directory is a side effect that might not be immediately obvious to a developer reading the source code. However, this is a one-time setup cost that significantly improves the long-term user and developer experience.
