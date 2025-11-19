# ADR-100: Streamlit Provider State Management

- **Status**: Implemented
- **Date**: 2025-11-18
- **Context**: The Streamlit UI allowed users to switch between different LLM providers (Ollama, LM Studio, OpenAI). However, the application's state management was inconsistent. Some parts of the code read the provider from the `PROVIDER` environment variable, while the UI selection was a transient state. This led to a desynchronized state where the UI might show one provider selected, but the agent backend would attempt to use the model associated with the original environment variable. This caused errors, incorrect model loading, and a confusing user experience.
- **Decision**: We will manage the active LLM provider using a dedicated Streamlit session state variable (`SESSION_KEY_CURRENT_PROVIDER`).
    1. On application startup, the session state will be initialized from the `PROVIDER` environment variable.
    2. All UI components (provider dropdown, model list) will read the provider directly from `st.session_state`.
    3. When a user selects a new provider, the `SESSION_KEY_CURRENT_PROVIDER` in `st.session_state` will be updated atomically within the existing `ConfigStateTransaction` system.
    4. All backend logic that depends on the provider (e.g., `get_available_models`) will now accept the provider as a parameter, which will be passed from the session state.
    5. When the provider is changed, the UI automatically scans and updates the available models list for the new provider, ensuring immediate availability of provider-specific models without requiring manual intervention.
- **Consequences**:
    - **Positive**:
        - Fixes the state desynchronization bug, making provider switching reliable.
        - Creates a single source of truth for the active provider within a user session.
        - Improves user experience by ensuring the UI accurately reflects the agent's configuration.
        - Simplifies logic, as components no longer need to guess the active provider and can rely on the session state.
        - Enhances responsiveness by automatically scanning and updating model lists when providers change, eliminating manual refresh requirements.
    - **Negative**:
        - None. This change corrects a bug and improves architectural soundness.
