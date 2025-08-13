# ADR-061: Centralized and Consolidated Configuration Management

## Status

Accepted

## Context

The project's configuration settings, including paths, service URLs, timeouts, and feature flags, were previously defined in `src/personal_agent/config/settings.py` but were not consistently or centrally exposed. Different modules would import specific variables, leading to scattered dependencies and making it difficult to get a holistic view of the system's configuration. As the application grew, this decentralized approach increased the risk of inconsistencies and made configuration management cumbersome. A more organized and accessible system was needed to improve maintainability and clarity.

## Decision

We will consolidate all key configuration variables and expose them through the top-level `src/personal_agent/config/__init__.py` file. This turns the `config` module into a centralized hub for all configuration settings.

This refactoring involves:
1.  **Explicitly Exporting Variables**: All important configuration variables from `settings.py` will be explicitly listed in the `__all__` array of `config/__init__.py`.
2.  **Categorization**: The exported variables will be grouped by category (e.g., Core paths, LightRAG settings, LLM and service URLs, Timeouts) in the `__init__.py` file to improve readability and discoverability.
3.  **Updating Imports**: All modules throughout the application will be updated to import configuration variables directly from the `personal_agent.config` package instead of from the deeper `personal_agent.config.settings` module.

## Consequences

### Positive
- **Single Source of Truth**: Provides a clear, centralized, and easily discoverable location for all configuration settings.
- **Improved Maintainability**: Simplifies refactoring and updating configuration, as all exposed variables are managed in one place.
- **Enhanced Readability**: Grouping variables by category in the `__init__.py` file makes it easier for developers to understand the available settings.
- **Reduced Coupling**: Modules are decoupled from the specific implementation of the `settings.py` file, depending only on the `config` package.

### Negative
- **Minor Initial Refactoring Effort**: Requires a one-time effort to update all import statements across the codebase.
