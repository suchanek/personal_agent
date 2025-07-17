# ADR-020: Environment Variable Consolidation and Cleanup

**Date**: 2025-07-17

**Status**: Accepted

## Context

The project's environment configuration, primarily managed through `.env` files, had several issues that hindered development and posed potential security risks:

1.  **Security Risk**: Sensitive API keys and tokens were stored in the main `.env` file, which is often tracked by version control.
2.  **Configuration Bloat**: The `.env` file contained a large number of variables, many of which were duplicates, unused, or simply overriding sensible defaults with the same values.
3.  **Poor Organization**: Variables were not logically grouped, making the file difficult to read and maintain.
4.  **Inconsistent Overrides**: The same variables were defined in multiple places (e.g., root `.env`, service-specific `.env` files, and `docker-compose.yml` files), leading to confusion about which value would take precedence.

## Decision

To address these issues, we have implemented a comprehensive cleanup and consolidation of all environment variables.

1.  **Separation of Secrets**:
    *   A new file, `.env.secrets.template`, has been created to hold all sensitive API keys and tokens.
    *   Developers are now instructed to copy this template to `.env.secrets`, populate it with their credentials, and add `.env.secrets` to their `.gitignore` file. This ensures secrets are never committed to version control.

2.  **Consolidation and Cleanup**:
    *   The main `.env` file has been cleaned and reorganized into a new, well-documented `.env.clean` file.
    *   All unused, deprecated, and duplicated variables have been removed. The total number of variables in the primary `.env` file has been reduced by nearly 50%.
    *   Variables are now grouped into logical sections (e.g., `BASIC CONFIGURATION`, `SERVER URLS AND PORTS`, `AI MODEL CONFIGURATION`).

3.  **Reliance on Sensible Defaults**:
    *   The `src/personal_agent/config/settings.py` file now provides sensible default values for most configuration variables, especially timeouts.
    *   The `.env` file is now used only to *override* these defaults when necessary, rather than redefining them. A minimal `.env.minimal` example has been provided to illustrate this principle.

4.  **Suppression of Deprecation Warnings**:
    *   To address noisy `DeprecationWarning` messages from third-party libraries (like `spacy` and `click`), a multi-layered suppression strategy has been implemented:
        *   The `PYTHONWARNINGS` environment variable is now set in the virtual environment's activation script (`.venv/bin/activate`) to ignore these specific warnings globally.
        *   A new wrapper script, `tools/docmgr_wrapper.sh`, has been created to run scripts with the necessary warning flags.
        *   Direct `warnings.filterwarnings()` calls have been added to key scripts as a fallback.

## Consequences

### Positive

*   **Improved Security**: Secrets are now properly isolated from the main configuration, significantly reducing the risk of accidental exposure.
*   **Simplified Configuration**: The `.env` files are now much cleaner, smaller, and easier to understand and maintain.
*   **Reduced Noise**: The suppression of irrelevant deprecation warnings provides a cleaner and more focused developer experience.
*   **Increased Clarity**: It is now much clearer which variables are essential for the application to run and which are optional overrides.
*   **Enhanced Reliability**: By removing unused and duplicated variables, the risk of configuration-related bugs is reduced.

### Negative

*   **One-Time Setup**: Developers will need to perform a one-time action to create their `.env.secrets` file from the new template. This is a small price to pay for the significant security and maintainability improvements.
