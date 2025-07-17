# ADR-014: Dedicated Service Ports

**Date**: 2025-07-14

**Status**: Accepted

## Context

A critical issue was discovered where both the LightRAG Knowledge Base server and the LightRAG Memory server were configured to use the same `PORT` environment variable. This created a race condition. Whichever service started second would fail because the port was already allocated by the first, leading to unpredictable and frequent container restart failures.

While the port numbers were manually corrected in the `docker-compose.yml` files to be distinct (9621 and 9623), the underlying configuration (`env.server`, `env.memory_server`) still referenced a generic `PORT` variable. This is ambiguous and error-prone, as it hides the true port configuration and could easily be misconfigured in the future.

## Decision

To eliminate this ambiguity and prevent future conflicts, we will introduce dedicated, explicit environment variables for each service's port.

1.  **Introduce New Environment Variables**:
    *   `LIGHTRAG_SERVER_PORT` will be used for the main Knowledge Base server.
    *   `LIGHTRAG_MEMORY_PORT` will be used for the Memory server.

2.  **Update Environment Configuration**:
    *   The `env.server` and `env.memory_server` files (and their corresponding examples) will be updated to use these new, specific variables instead of the generic `PORT`.

3.  **Update Docker Compose Files**:
    *   The `docker-compose.yml` files for both services will be modified to read these new, dedicated variables to define their port mappings. For example: `ports: - "${LIGHTRAG_SERVER_PORT:-9621}:${LIGHTRAG_SERVER_PORT:-9621}"`.

4.  **Update System Scripts**:
    *   All relevant management scripts, including `smart-restart-lightrag.sh` and the `LightRAGManager` Python class, will be updated to use the new, specific port variables when checking for port availability and managing services.

## Consequences

### Positive

*   **Clarity and Explicitness**: The configuration is now unambiguous. It is immediately clear which port belongs to which service.
*   **Reduced Risk of Error**: Eliminates the possibility of accidentally assigning the same port to both services.
*   **Improved Maintainability**: Makes the system easier to understand, configure, and debug for future developers.
*   **Enhanced Reliability**: Programmatic restarts and service management become more reliable as they can target specific, predictable ports.

### Negative

*   **Minor Configuration Change**: Users with existing `.env` files will need to update them to use the new variable names. This is a small, one-time change.
