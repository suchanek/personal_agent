# ADR-090: REST API for Memory and Knowledge Management

## Status

Accepted

## Context

As the agent's capabilities grow, there is an increasing need for programmatic access to its core memory and knowledge functions from external systems. Automating memory ingestion, integrating with other applications, or building custom interfaces requires a standardized, language-agnostic way to interact with the agent's data stores without relying solely on the Streamlit UI or CLI.

## Decision

We will implement a RESTful API integrated directly into the Streamlit application. This API will provide a comprehensive set of endpoints for managing the agent's memory and knowledge base.

The key architectural decision is to use a thread-safe **Global State Manager**. This component will hold the shared `AgnoPersonalAgent` or `PersonalAgentTeam` instance, making it accessible to both the main Streamlit application thread and the separate thread running the REST API server (powered by FastAPI). This approach solves the critical issue of Streamlit's thread-local session state, enabling the API to access the live, initialized agent instance.

The API will expose endpoints for:
- **Memory:** Storing text/URLs, searching, listing, and getting statistics.
- **Knowledge:** Storing text/URLs, searching, and checking status.
- **System:** Health checks and overall system status.

## Consequences

### Positive
- **Interoperability:** Enables any external application, script, or service to interact with the agent's memory and knowledge base via standard HTTP requests.
- **Automation:** Facilitates automated workflows for data ingestion and retrieval.
- **Decoupling:** Allows the development of alternative frontends or integrations without modifying the agent's core logic.
- **Centralization:** The API runs alongside the main application, ensuring it always interacts with the currently active and configured agent instance.

### Negative
- **Increased Complexity:** Introduces a new layer to the application, including the Global State Manager and API routing logic.
- **Dependency:** The REST API's availability is tied to the running state of the Streamlit application.
- **Security:** The initial implementation will not include authentication, making it suitable only for local, trusted environments. Production use would require adding a security layer (e.g., API keys, OAuth).
