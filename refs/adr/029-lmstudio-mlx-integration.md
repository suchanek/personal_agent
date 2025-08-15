# ADR-029: Integration of LMStudio for MLX Model Support

## Context

The agent's capabilities are closely tied to the models it can leverage. To expand local model support beyond Ollama, especially for users on Apple Silicon, there was a need to integrate models running on Apple's MLX framework. LMStudio provides an OpenAI-compatible server that can serve these MLX models, offering a practical way to broaden our model ecosystem.

## Decision

We decided to integrate LMStudio as a first-class supported backend for running local models. This is implemented by treating LMStudio as a standard OpenAI-compatible endpoint.

The key changes include:
1.  **Configuration**: Added `LMSTUDIO_URL` and `REMOTE_LMSTUDIO_URL` to the environment settings to define the endpoints for the LMStudio server.
2.  **Model Manager Update**: The `AgentModelManager` was enhanced to detect when an LMStudio endpoint is being used (based on the URL containing `:1234`). When detected, it configures the `agno.models.openai.OpenAIChat` client with the correct `base_url` and a dummy API key (`lm-studio`), as LMStudio does not require authentication.
3.  **Default Model**: The default `LLM_MODEL` was changed to `qwen3-4b-mlx` to reflect the new primary local model.
4.  **Team Integration**: The multi-purpose reasoning team was updated to allow switching the provider to `openai` to use the LMStudio integration seamlessly.

## Consequences

### Positive
-   **Broader Model Support**: The agent can now run MLX-optimized models, expanding the range of available local LLMs.
-   **Enhanced Performance on Apple Silicon**: Users with Apple hardware can benefit from models specifically optimized for the MLX framework.
-   **Increased Flexibility**: The agent is less dependent on a single local model provider (Ollama).

### Negative
-   **Upstream Dependency**: The integration relies on LMStudio maintaining its OpenAI API compatibility. Any breaking changes in LMStudio could affect the agent's functionality.
-   **Discovered Upstream Bug**: The integration process revealed a critical bug in the `agno` framework's `OpenAIChat` model, where the `system` role is incorrectly mapped to `developer`. A temporary workaround was required. See ADR-030 for details.
