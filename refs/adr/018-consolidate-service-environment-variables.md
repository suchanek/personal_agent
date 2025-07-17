# ADR-018: Consolidate Service Environment Variables into .env Files

**Date**: 2025-07-15

**Status**: Accepted

## Context

The configuration for our Dockerized services, specifically the LightRAG Memory Server, was scattered across two different locations:

1.  The service-specific `.env` file (e.g., `lightrag_memory_server/env.memory_server`)
2.  The `environment` section within the `docker-compose.yml` file.

This led to several problems:
*   **Configuration Duplication**: Variables were often defined in both places.
*   **Precedence Confusion**: It was not immediately clear which value would take precedence, leading to unpredictable behavior (Docker Compose's `environment` section overrides `env_file`).
*   **Maintenance Overhead**: To change a configuration, a developer might need to check and modify multiple files, increasing the risk of error.
*   **Inconsistent Values**: A variable (`PDF_CHUNK_SIZE`) had different values in the `.env` file and the `docker-compose.yml` file, with the Docker value silently overriding the intended configuration.

## Decision

To resolve these issues and establish a clear, single source of truth for service configuration, we have decided to consolidate all environment variables into the service-specific `.env` file.

1.  **Single Source of Truth**: The `.env` file within each service directory (e.g., `lightrag_memory_server/.env`) is now the **only** location for defining environment variables for that service.

2.  **Remove `environment` from Docker Compose**: The `environment` section has been completely removed from the `docker-compose.yml` files. The `env_file` directive is now the sole mechanism for loading the container's environment.

3.  **Consolidate All Variables**: All variables previously defined in the `docker-compose.yml`'s `environment` section have been moved into the corresponding `.env` file, ensuring all configuration is in one place.

## Consequences

### Positive

*   **Simplified Maintenance**: Configuration is now managed in a single, predictable location for each service, making updates faster and safer.
*   **Eliminates Confusion**: There is no longer any ambiguity about where a configuration value is set or which value takes precedence.
*   **Cleaner Docker Files**: The `docker-compose.yml` files are now cleaner and more focused on defining the service's structure, rather than its configuration.
*   **Increased Reliability**: The risk of inconsistent or overridden configuration values is eliminated, leading to a more stable and predictable system.

### Negative

*   None. This is a best-practice change that improves the project's architecture without any functional downside.
