# ADR-077: Developer Environment and Setup Overhaul

## Status

Accepted

## Context

The project's setup process had become increasingly complex and brittle. The `README.md` instructions were lagging behind the project's evolution, leading to a difficult and error-prone onboarding experience for developers. Key issues included:

*   Ambiguous Python version requirements.
*   Slow and complex dependency management with `poetry` alone.
*   Insufficient instructions for critical dependencies like Docker.
*   Outdated commands and workflow descriptions.
*   In-code workarounds for issues in dependencies that were no longer necessary.

This friction was a barrier to contribution and efficient development.

## Decision

To address these issues, we decided to perform a comprehensive overhaul of the developer environment and setup process. The key changes are:

1.  **Standardize on Python 3.12**: We now explicitly recommend and target Python 3.12 to ensure a consistent runtime environment and access to modern language features.
2.  **Introduce `uv` for Environment Management**: We have integrated `uv` as the primary tool for creating virtual environments. `uv` is significantly faster than `poetry` for this task, dramatically speeding up the initial setup. `poetry` is still used for dependency installation and management within the `uv`-created environment.
3.  **Revamp `README.md`**: The `README.md` has been completely rewritten to provide a clear, step-by-step guide for the entire setup process, including:
    *   Detailed Python 3.12 installation instructions.
    *   `uv` usage for environment creation.
    *   Comprehensive Docker installation and image pulling instructions.
    *   Updated Ollama setup, including a robust system service configuration.
    *   Consolidated and clarified `poe` task commands for running the application.
4.  **CLI and UI Enhancements**:
    *   The reasoning team CLI (`rteam-cli`) now supports a `--query` argument for one-off, non-interactive command execution.
    *   The Streamlit dashboard now features a "Power Off" button for a graceful shutdown of the application.
5.  **Code Cleanup**:
    *   Removed the `agno` role-mapping workaround from `reasoning_team.py`, as the underlying framework issue has been resolved. This simplifies the model creation logic.
    *   Deleted the old, unused `paga_streamlit_team_orig.py` file.
    *   Moved the main Streamlit application to `src/personal_agent/tools/` to better reflect its role as a tool for interacting with the agent.

## Consequences

### Pros

*   **Faster, Simpler Onboarding**: The new `README` and the introduction of `uv` make the setup process significantly faster and less error-prone.
*   **Improved Consistency**: Standardizing on Python 3.12 reduces environment-related bugs.
*   **Enhanced Developer Experience**: Clearer instructions and faster tooling create a more efficient development cycle.
*   **Increased Functionality**: The new CLI query mode and UI shutdown feature improve the agent's usability.
*   **Reduced Code Clutter**: Removing obsolete workarounds and files makes the codebase cleaner and easier to maintain.

### Cons

*   **New Dependency**: Developers must now install `uv`. However, it is a single, simple installation command.
*   **More Prescriptive Setup**: The setup is now more prescriptive (e.g., Python 3.12), which may require some developers to update their local environments.

