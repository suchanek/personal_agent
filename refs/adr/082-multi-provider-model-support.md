# ADR-082: Multi-Provider Model Support

- **Date**: 2025-09-05
- **Status**: Accepted

## Context

The agent's architecture was previously tightly coupled to Ollama as the sole provider for language models. This limited the agent's flexibility, preventing the use of other powerful models available through different APIs, such as those from OpenAI. Past attempts to create custom wrappers for tool-calling, like `OllamaTools`, proved to be unstable and led to reliability issues. To enhance the agent's capabilities and future-proof its design, a more extensible solution was required.

## Decision

We will refactor the `AgentModelManager` to support multiple, pluggable model providers. This will be achieved by:

1.  **Introducing a `model_provider` parameter** during agent initialization, which can be configured via the `MODEL_PROVIDER` environment variable.
2.  **Creating dedicated model classes** for each provider (e.g., `Ollama`, `OpenAI`) within the `AgentModelManager`.
3.  **Using the standard, official `agno` library classes** (`agno.models.ollama.Ollama`, `agno.models.openai.OpenAI`) as the foundation for these provider-specific classes. This eliminates the need for custom, brittle wrappers.
4.  **Managing provider-specific configurations**, such as API keys (`OPENAI_API_KEY`), through environment variables.
5.  **Removing the unstable `OllamaTools` wrapper** in favor of the more reliable standard `agno` class.

## Consequences

### Positive

-   **Flexibility**: The agent can now seamlessly switch between different model providers (initially Ollama and OpenAI), allowing users to leverage the best model for their needs (e.g., local models for privacy, powerful cloud models like GPT-4o for performance).
-   **Extensibility**: The new architecture makes it straightforward to add support for other model providers in the future by simply adding a new provider class in `AgentModelManager`.
-   **Stability**: By removing the custom `OllamaTools` wrapper and relying on the core `agno` library, the agent's tool-calling capabilities with Ollama models are more reliable and less prone to errors.
-   **Transparency**: The Streamlit UI and agent configuration now clearly display which model provider and model name are in use.

### Negative

-   **Increased Configuration**: Users now have to manage an additional `MODEL_PROVIDER` environment variable and ensure that the corresponding API keys (e.g., `OPENAI_API_KEY`) are set correctly when using non-local providers.

### Neutral

-   The agent's core logic and UI have been updated to be provider-aware, which is a necessary complexity increase for the added flexibility.
