# ADR-096: Centralized Configuration Management with Singleton

- **Status**: Accepted
- **Date**: 2025-10-13
- **Context**: The application's configuration was managed through scattered environment variables and module-level constants. This led to several critical issues, including race conditions during dynamic updates (e.g., switching model providers), a lack of a single source of truth, and poor observability. The system was not thread-safe, making it unreliable in concurrent environments like Streamlit and the REST API.
- **Decision**: We will implement a thread-safe singleton class, `PersonalAgentConfig`, to serve as the central, authoritative source for all runtime configurations. This class will manage the application's core state (e.g., `user_id`, `provider`, `model`, `agent_mode`), provide change notification callbacks, and synchronize its state with environment variables for backward compatibility. All configuration access and modifications will be channeled through this singleton.
- **Consequences**:
    - **Positive**:
        - **Eliminates Race Conditions**: By centralizing state and using thread-safe mechanisms, we prevent race conditions and ensure configuration consistency across the application.
        - **Single Source of Truth**: Simplifies state management and improves maintainability.
        - **Enables Dynamic Switching**: Reliably supports dynamic switching of model providers and other settings at runtime.
        - **Improved Observability**: The callback system allows components to react to configuration changes in real-time.
        - **Enhanced Testability**: The configuration can be easily controlled and reset in testing environments.
    - **Negative**:
        - **Increased Coupling**: All modules requiring configuration will now depend on the `PersonalAgentConfig` singleton.
        - **Migration Effort**: Existing code must be migrated to use the new configuration system instead of directly accessing environment variables.
