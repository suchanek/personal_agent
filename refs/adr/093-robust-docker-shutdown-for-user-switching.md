# ADR-093: Robust Docker Shutdown for User Switching

- **Status**: Accepted
- **Date**: 2025-09-30

## Context

The `switch-user.py` script is responsible for changing the active user. When switching, Docker services (LightRAG) need to be restarted with the new user's context to ensure data isolation. The previous implementation only focused on *restarting* the services after the user switch, but it didn't explicitly shut them down *before* the switch. This could lead to race conditions, incomplete shutdowns, or containers not cleanly stopping before the new ones were started, potentially causing port conflicts or state inconsistencies.

## Decision

We will modify the user switching process to ensure a clean shutdown of all LightRAG Docker services *before* the user context is changed.

1.  A `stop_all_services` method will be added to the `DockerUserSync` class in `src/personal_agent/core/docker/user_sync.py`. This method will iterate through all configured Docker services and execute a `docker-compose down` command for any that are currently running.
2.  This functionality will be exposed through a new convenience function, `stop_lightrag_services`, in `src/personal_agent/core/docker_integration.py`.
3.  The `switch_user_context` function in `switch-user.py` will be updated to call `stop_lightrag_services` at the beginning of the process, right before it switches the user ID in the system.

## Consequences

### Positive

- User switching becomes more robust and reliable.
- Reduces the risk of port conflicts and stale container states.
- Creates a cleaner separation of concerns: stop services, switch user, start services.

### Negative

- The user switching process might take a few seconds longer due to the explicit shutdown step. This is an acceptable trade-off for increased stability.
