# ADR-085: Standalone Dockerized Dashboard

- **Status**: Proposed
- **Date**: 2025-09-16
- **Author**: Gemini

## Context and Problem Statement

The existing Streamlit dashboard was tightly coupled with the main application. Running the dashboard required a full development setup, including all Python dependencies for the agent. This made it difficult to:

- **Deploy the dashboard independently**: The dashboard could not be run as a standalone service.
- **Isolate dependencies**: The dashboard's dependencies were mixed with the agent's dependencies, which could lead to conflicts.
- **Simplify user access**: Users who only needed access to the management dashboard still needed to set up the entire project.

A decoupled, containerized dashboard was needed to address these issues and provide a more flexible and scalable solution.

## Decision Drivers

- Decouple the dashboard from the main application.
- Simplify deployment and management of the dashboard.
- Isolate dependencies and avoid conflicts.
- Improve accessibility for users who only need the dashboard.

## Considered Options

1.  **Keep the integrated dashboard**: Continue with the existing tightly coupled architecture. This was rejected as it did not address the identified problems.
2.  **Create a separate project for the dashboard**: This would provide a clean separation but would also increase the complexity of managing two separate repositories.
3.  **Create a standalone, containerized dashboard within the existing project**: This option provides the benefits of decoupling and dependency isolation without the overhead of a separate repository.

## Decision Outcome

Chosen option: **Create a standalone, containerized dashboard within the existing project**.

A new directory, `dashboard-docker`, has been added to the project. This directory contains all the necessary files to build and run a standalone Docker container for the Streamlit dashboard, including:

- `Dockerfile`: A multi-stage Dockerfile for building a lean, production-ready image.
- `docker-compose.yml`: For easy local deployment and management.
- `requirements.txt`: A minimal set of dependencies required for the dashboard.
- `dashboard.py`: The main Streamlit application, adapted to run in a containerized environment.
- `build.sh` and `run.sh`: Helper scripts for building and running the Docker container.

### Architectural Changes

- **Decoupling**: The dashboard is now a separate application that communicates with the personal agent's backend services (LightRAG, Ollama) over the network.
- **Containerization**: The dashboard is packaged as a Docker container, which encapsulates all its dependencies and provides a consistent runtime environment.
- **Configuration**: The containerized dashboard is configured using environment variables, making it easy to adapt to different environments.

### Benefits

- **Independent Deployment**: The dashboard can be deployed and scaled independently of the main application.
- **Dependency Isolation**: The dashboard's dependencies are isolated within the Docker container, preventing conflicts with the agent's dependencies.
- **Simplified Access**: Users can now run the dashboard with a single `docker-compose up` command, without needing to set up a full Python development environment.
- **Improved Scalability**: The containerized dashboard can be easily deployed to cloud platforms and scaled as needed.

## Consequences

### Positive

- The project architecture is more modular and flexible.
- The developer and user experience is improved.
- The dashboard is more robust and easier to manage.

### Negative

- There is a slight increase in complexity due to the addition of Docker-related files and a new build process for the dashboard.
- Users will need to have Docker installed to run the dashboard.
