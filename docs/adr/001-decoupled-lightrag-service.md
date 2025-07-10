# ADR 005: Decoupled LightRAG Service Architecture

*   **Status:** Implemented
*   **Date:** 2025-07-04

## Context and Problem Statement

The LightRAG service was originally defined within the main application's `docker-compose.yml` file. This created a monolithic architecture with several limitations:

1.  **Inflexible Deployment:** It was difficult to run the LightRAG service on a separate host, as its configuration and lifecycle were tied to the main application.
2.  **Configuration Complexity:** Managing different environments (e.g., a local LightRAG vs. a remote, shared LightRAG instance) required complex and error-prone changes to configuration files.
3.  **Scalability Constraints:** The monolithic setup limited the ability to scale the knowledge base service independently of the agent application.

## Decision Drivers

*   The need for greater deployment flexibility, allowing the LightRAG service to be hosted independently.
*   The requirement to simplify configuration for different environments.
*   The goal of creating a more modular and scalable architecture.

## Decision Outcome

The LightRAG service was architecturally decoupled from the main application.

### 1. Standalone LightRAG Server

A dedicated `lightrag_server/` directory was created, containing its own `docker-compose.yml` and `config.ini`. This allows the LightRAG service to be managed as a completely independent component.

### 2. Centralized Configuration via `LIGHTRAG_URL`

A single environment variable, `LIGHTRAG_URL`, was introduced in the main application's settings (`src/personal_agent/config/settings.py`) to act as the single source of truth for the LightRAG server's address.

*   All application components that need to connect to LightRAG (the agent core, the Streamlit UI for health checks, etc.) were updated to use this variable.

### 3. Enhanced Tooling

Tooling was created and updated to support this new architecture:

*   The `switch-ollama.sh` script was enhanced to also switch the `LIGHTRAG_URL` between local and remote values, providing a seamless developer experience.
*   A generic `scripts/restart-container.sh` script was added to simplify the management of any Docker container by name.

## Consequences

### Positive

*   **Modularity and Flexibility:** The LightRAG service is now a standalone component that can be deployed and managed anywhere, independently of the main application.
*   **Simplified Configuration:** Switching between a local and remote LightRAG instance is now as simple as changing one environment variable, managed by a script.
*   **Improved Scalability:** The knowledge base and the agent application can be scaled independently to meet different demands.
*   **Enhanced Robustness:** The Streamlit UI now provides a live health check of the configured `LIGHTRAG_URL`, giving immediate feedback on the service's status.

### Negative

*   **Increased Number of Services:** The new architecture requires managing two separate services (the main app and the LightRAG server) instead of one. This is a standard practice in microservice architectures and is a worthwhile trade-off for the flexibility and scalability gained.
