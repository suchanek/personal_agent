# ADR-059: Centralized Configuration Display

## Status

**Accepted**

## Context

The project had redundant and inconsistent logic for displaying configuration. The `print_config` and `print_configuration` functions in `src/personal_agent/config/settings.py` duplicated functionality present in `src/personal_agent/tools/show_config.py`. This violated the Single Responsibility Principle and made the code harder to maintain.

## Decision

1.  Consolidate all configuration display logic into `src/personal_agent/tools/show_config.py`, making it the single source of truth.
2.  Remove the redundant `print_config` and `print_configuration` functions from `src/personal_agent/config/settings.py`.
3.  Update `src/personal_agent/tools/show_config.py` to be consistent with the latest configuration settings, including the new `PERSAG_HOME` and user-specific directory paths.
4.  Update the `if __name__ == "__main__"` block in `settings.py` to call the `show_config` function, preserving the ability to display the configuration by running the settings file directly.

## Consequences

### Positive

-   Eliminates code duplication and reduces the risk of inconsistencies.
-   Improves maintainability by centralizing the configuration display logic.
-   Adheres to the Single Responsibility Principle, making the codebase cleaner and easier to understand.

### Negative

-   None.
