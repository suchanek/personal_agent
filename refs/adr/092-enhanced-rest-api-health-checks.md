# ADR-092: Enhanced REST API Health Checks for System Stability

## Context

The existing REST API had a basic `/api/v1/health` endpoint that returned a simple "healthy" status. This was insufficient for diagnosing the operational status of the agent's complex, multi-component architecture. When a component like the agent, team, or memory manager failed to initialize, the API would still report as healthy, masking critical issues and making debugging difficult.

A more robust health check was needed to provide a clear and accurate picture of the system's state, ensuring that the API only reports as "healthy" when all its critical dependencies are fully operational.

## Decision

We will enhance the `/api/v1/health` endpoint to perform a comprehensive series of internal checks against the application's global state. The new health check will verify the availability and readiness of the following core components:

1.  **Streamlit Connection**: Ensures the API is properly connected to the Streamlit session.
2.  **Agent Availability**: Checks if the `AgnoPersonalAgent` instance is initialized and available.
3.  **Team Availability**: Checks if the `PersonalAgentTeam` instance is initialized and available.
4.  **Memory Helper**: Verifies that the memory management subsystem is ready.
5.  **Knowledge Helper**: Verifies that the knowledge management subsystem is ready.

The system will be considered "healthy" only if the Streamlit connection, memory, and knowledge helpers are available, and at least one of the agent or team is available.

The response from the health check endpoint will now include a detailed breakdown of these checks, providing immediate insight into the status of each component.

## Consequences

### Positive

-   **Improved Reliability**: The health check now accurately reflects the system's ability to serve requests.
-   **Faster Debugging**: The detailed response from the health endpoint allows developers to quickly identify which component has failed.
-   **Enhanced Monitoring**: The endpoint can be used by external monitoring tools to get a precise status of the agent's operational readiness.
-   **Increased Stability**: By ensuring all components are ready before reporting as healthy, we prevent the system from trying to handle requests in a partially initialized state.

### Negative

-   **Increased Complexity**: The health check logic is now more complex as it is coupled with the global state manager.
-   **Dependency on Global State**: The health check is dependent on the `GlobalState` manager being correctly implemented and maintained.
