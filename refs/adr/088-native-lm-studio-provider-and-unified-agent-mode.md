# ADR-088: Native LM Studio Provider and Unified Agent Mode Configuration

**Date**: 2025-09-21

**Status**: Accepted

## Context

The agent's architecture needed to evolve to address two primary challenges:
1.  **Expanding Model Support**: While the agent supported Ollama and OpenAI providers, there was a growing need to natively and reliably support models served through LM Studio, which is popular for running a wide variety of GGUF models locally.
2.  **Ambiguous Agent Configuration**: The mechanism for controlling the agent's toolset was implicit and confusing. The agent could run in a "team mode" (with a minimal set of memory/knowledge tools) or a "standalone mode" (with a full suite of tools like web search, file operations, etc.). This mode was previously auto-detected based on the `--remote` flag, which was not intuitive and led to unpredictable behavior.

## Decision

To address these issues, we have decided to implement the following architectural changes:

1.  **Integrate a Dedicated LM Studio Provider**: We will add `lm-studio` as a first-class model provider within the `AgentModelManager`. This involves creating dedicated logic to handle LM Studio's API endpoint, including correct URL management for both local and remote instances. This makes using models from LM Studio as simple as changing a configuration setting.

2.  **Introduce a Unified `--single` Flag for Mode Configuration**: We will introduce a new, explicit command-line flag: `--single`.
    - When the `--single` flag is present, the `AgnoPersonalAgent` will be initialized in "standalone mode," loading its full suite of built-in tools (`alltools=True`).
    - When the flag is absent, the agent will default to "team mode," loading only the essential memory and knowledge tools, making it a specialized and lightweight member of a larger team.

3.  **Deprecate Implicit Mode Detection**: The previous logic that tied the agent's mode to the `--remote` flag will be removed entirely. The `--remote` flag will now only control the endpoint URL (local vs. remote), while the `--single` flag will exclusively control the agent's capabilities.

## Consequences

### Positive
- **Clear and Explicit Configuration**: The agent's behavior is now unambiguous. Developers and users can clearly understand and control whether the agent is running with its full capabilities or as a specialized team member.
- **Enhanced Model Flexibility**: Native support for LM Studio significantly broadens the range of models that can be used with the agent, especially for users who prefer GGUF-formatted models.
- **Improved Maintainability**: The code is simplified by removing the complex and error-prone auto-detection logic. The separation of concerns is clearer: one flag for connectivity (`--remote`), one for capability (`--single`).
- **Consistent User Experience**: The `--single` flag works identically across both the command-line interface (`paga_team_cli`) and the Streamlit UI, providing a consistent experience.

### Negative
- **Minor Breaking Change**: Users who previously relied on the implicit behavior of the `--remote` flag to enable standalone mode will need to update their scripts to use the `--single` flag instead. This is considered a minor issue, as the new system is more explicit and easier to use correctly.
