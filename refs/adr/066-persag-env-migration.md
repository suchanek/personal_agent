# ADR-066: Migrate `.env` to `~/.persag` for Complete Configuration Decoupling

- Status: accepted
- Date: 2025-08-15
- Deciders: Personal Agent Development Team

## Context and Problem Statement

Previous architectural decisions ([ADR-048](./048-decoupled-user-docker-config.md), [ADR-058](./058-modular-user-id-management.md)) successfully decoupled user-specific data and Docker configurations from the project repository by moving them to the `~/.persag` directory. However, the main `.env` file, which can contain sensitive information like API keys and user-specific paths, still resided in the project root. This posed a security risk and prevented a complete separation of user configuration from the codebase.

To achieve full configuration decoupling and enhance security, the `.env` file must also be moved to the `~/.persag` directory.

## Decision Drivers

- **Security:** Prevent sensitive information in the `.env` file from being accidentally committed to the repository.
- **Consistency:** Consolidate all user-specific configuration into a single, well-defined location (`~/.persag`).
- **Portability:** Allow users to easily back up and restore their entire configuration by simply copying the `~/.persag` directory.

## Considered Options

1.  **Manual Migration:** Require users to manually move their `.env` file to `~/.persag`. This would be simple to implement but would be error-prone and a poor user experience.
2.  **Automatic Migration:** Update the `PersagManager` to automatically migrate the `.env` file from the project root to `~/.persag` on the first run. This would be a seamless experience for the user.

## Decision Outcome

Chosen option: **Automatic Migration**.

We have updated the `PersagManager` to automatically migrate the `.env` file from the project root to the `~/.persag` directory. The `migrate_to_persag.py` script has also been updated to reflect this change.

This ensures a smooth transition for existing users and a clean setup for new users, with all user-specific configuration now located in `~/.persag`.

### Positive Consequences

- Complete decoupling of user configuration from the project repository.
- Improved security by moving potentially sensitive information out of the project root.
- A more consistent and portable configuration.

### Negative Consequences

- None.

## Implementation

- **`src/personal_agent/core/persag_manager.py`**:
    - Added `migrate_env_files` method to migrate the `.env` file.
    - Updated `ensure_persag_home_exists` to call the new migration method.
- **`migrate_to_persag.py`**:
    - Updated to include the `.env` file in the migration process.
- **`pyproject.toml` and `src/personal_agent/__init__.py`**:
    - Bumped the project version to `0.2.0` to signify this major architectural change.

## Validation

The migration was validated by running the `migrate_to_persag.py` script and verifying that the `.env` file was correctly moved to the `~/.persag` directory and that the application continued to function correctly.
