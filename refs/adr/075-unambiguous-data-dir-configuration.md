# ADR-075: Unambiguous Data Directory Configuration

**Date**: 2025-08-25
**Status**: Accepted

## Context

The codebase exhibited inconsistent and problematic usage of the `DATA_DIR` environment variable. Direct usage of `DATA_DIR` was found in several modules, bypassing the established user-specific directory structure and creating several issues:

-   **Multi-user Isolation Bypass**: Direct `DATA_DIR` usage could lead to data leakage between users.
-   **Path Construction Errors**: Manual path building was error-prone.
-   **Security Issues**: MCP servers were granted broader filesystem access than necessary.
-   **Maintenance Problems**: Directory structure changes required updates in multiple locations.

## Decision

To address these issues, we will refactor all modules to eliminate direct `DATA_DIR` usage in application code. Instead of using the generic `DATA_DIR`, the code will use more specific, pre-constructed environment variables that point to user-specific directories.

The following changes will be made:

-   `src/personal_agent/tools/knowledge_tools.py`: Will use `AGNO_KNOWLEDGE_DIR` instead of `Path(settings.DATA_DIR) / "knowledge"`.
-   `src/personal_agent/config/mcp_servers.py`: Will use `USER_DATA_DIR` for the MCP filesystem server arguments.
-   `src/personal_agent/tools/filesystem.py`: Path validation will use `USER_DATA_DIR`.
-   `src/personal_agent/core/agno_storage.py`: Will use `AGNO_STORAGE_DIR` for the default storage directory.

This change enforces the use of the existing abstraction layer for user-specific data, ensuring proper data isolation and improving security and maintainability.

## Consequences

### Positive

-   **Enhanced Security**: Enforces user data isolation, particularly for MCP servers.
-   **Improved Maintainability**: Centralizes path construction in the configuration, simplifying future changes.
-   **Better User Isolation**: Guarantees that each user's data is stored in a separate, dedicated directory structure.
-   **Reduced Risk**: Eliminates a class of manual path construction errors.

### Negative

-   None identified.
