# ADR 012: Docker Smart Restart and Module Refactoring

## Status

Accepted

## Context

The project faced several challenges related to Docker container management and code architecture:

1.  **Inability to Force Restart**: The `docker_user_sync.py` script ignored the `--force-restart` flag if the `USER_ID` in the containers was already consistent with the environment. This prevented manual intervention for maintenance or to resolve stale container issues.
2.  **Circular Import Warnings**: The `docker_integration.py` module, located in the `core` library, was importing `DockerUserSync` from the `scripts` directory, leading to circular dependency warnings and a fragile architecture.
3.  **Port Conflicts**: Stale or zombie Docker containers were not being properly cleaned up, leading to port conflicts that prevented new LightRAG servers from starting.
4.  **Unreliable Agent Initialization**: The agent's startup process did not enforce Docker consistency, making it unreliable in multi-user environments or when containers were in an inconsistent state.

## Decision

We decided to implement a comprehensive solution that addresses both the immediate operational issues and the underlying architectural problems.

### 1. Implement "Smart Restart" Logic

The `sync_user_ids()` method in `docker_user_sync.py` was modified to respect the `--force-restart` flag under all conditions. If `force_restart` is `True`, the script will now process and restart all relevant Docker containers, even if their `USER_ID`s are already consistent. Clearer status messages were added to differentiate between a standard synchronization and a forced restart.

### 2. Refactor Docker Module Architecture

To resolve the circular import issue and improve code organization, we moved the `DockerUserSync` class from the `scripts` directory into a new, dedicated library module:

```
src/personal_agent/core/docker/
├── __init__.py
└── user_sync.py
```

This change establishes a clear separation between executable scripts and library code, making the system more maintainable and scalable.

### 3. Enhance Docker Integration Layer

The `docker_integration.py` module was updated to support the `force_restart` parameter in its `ensure_docker_user_consistency` function. It now imports `DockerUserSync` from the new `src.personal_agent.core.docker` module, resolving the circular dependency.

### 4. Integrate into Agent Initialization

The `AgnoPersonalAgent`'s initialization process was updated to call `ensure_docker_user_consistency` with `force_restart=True`. This ensures that every time the agent starts, it begins with a fresh and consistent set of Docker containers, preventing issues related to stale states or port conflicts.

## Consequences

### Positive

- **Reliable Container Management**: Administrators can now reliably force-restart Docker containers for maintenance or troubleshooting.
- **Improved Architecture**: The refactored module structure eliminates circular dependencies, making the codebase cleaner and more maintainable.
- **Robust Agent Startup**: The agent's initialization is now more resilient and predictable, as it guarantees Docker consistency.
- **Reduced Port Conflicts**: Proactively restarting containers at startup prevents issues with stale containers occupying necessary ports.
- **Clearer User Feedback**: The command-line tool now provides more descriptive output about the actions it's taking.

### Negative

- **Slightly Longer Startup Time**: The agent's startup time is marginally increased because it now includes a mandatory Docker container restart. This is a minor trade-off for the significant increase in reliability.
- **Refactoring Effort**: Moving modules and updating import paths required careful changes across several files.
