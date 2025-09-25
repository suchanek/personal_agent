# ADR-091: Ollama Docker Connectivity and Configuration Standardization

**Date**: 2025-09-24
**Status**: Accepted

## Context

The LightRAG Docker containers were unable to connect to the Ollama server running on the host machine. The connection error indicated that the Ollama service was not accessible from within the containers. The root cause was the use of `http://localhost:11434` as the `OLLAMA_URL`. Inside a Docker container, `localhost` refers to the container itself, not the host machine.

Additionally, the Docker Compose configurations were using hidden, undocumented `.env` files for environment variables. This created confusion as there were also visible, documented configuration files (`env.server`, `env.memory_server`) present in the same directories, which were not being used. This made configuration management opaque and difficult to maintain.

## Decision

1.  **Fix Ollama Connectivity**: Standardize on using `http://host.docker.internal:11434` for the `OLLAMA_URL` in all Docker-related configurations. `host.docker.internal` is a special DNS name that resolves to the internal IP address of the host, making the host's services accessible from within containers.

2.  **Standardize Configuration Files**: Modify the `docker-compose.yml` files for both the `lightrag_server` and `lightrag_memory_server` to use the visible, documented `env.server` and `env.memory_server` files, respectively. This involves changing the `env_file` directive and the volume mount for the configuration file.

3.  **Cleanup Redundant Files**: Remove the now-unused, hidden `.env` files from the `~/.persag` directory to eliminate them as a source of confusion and establish a single source of truth for configuration.

## Consequences

### Positive
- **Reliable Connectivity**: The Docker containers can now reliably connect to the Ollama server on the host machine.
- **Improved Maintainability**: Configuration is now transparent and centralized in visible, well-documented files, making it easier to understand, debug, and modify.
- **Reduced Confusion**: Eliminating the hidden `.env` files removes ambiguity and ensures developers are editing the correct configuration source.
- **Consistency**: The configuration approach is now consistent across both LightRAG services.

### Negative
- None anticipated. This change corrects a bug and improves configuration hygiene without introducing known drawbacks.
