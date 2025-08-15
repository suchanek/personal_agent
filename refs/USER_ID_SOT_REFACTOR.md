# User Identity Single Source of Truth Refactor

Status: completed  
Date: 2025-08-12

## Overview

This refactor consolidates all user identity and per-user path logic into a single source of truth, eliminating duplicated behavior and drift across modules. The centralized implementation lives in [src/personal_agent/config/user_id_mgr.py](src/personal_agent/config/user_id_mgr.py), and all other components (settings, persistence/validation, registry) delegate to it.

Primary motivations:
- Prevent subtle bugs from multiple sources of "truth" for the current user.
- Ensure dynamic user switching is respected consistently everywhere, by always reading from the filesystem when requested.
- Respect PERSAG_HOME and PERSAG_ROOT overrides in a predictable way.
- Remove function-level imports and normalize import locations to module level where specified.

## Objectives

- Centralize user ID read/write and user-dependent path generation into user_id_mgr.
- Update PersagManager and UserRegistry to delegate to user_id_mgr functions.
- Refactor settings to remove duplicate init and identity logic—only delegate to user_id_mgr.
- Add a non-destructive integration test that exercises the full flow in an isolated temp environment.

## Scope

Modules directly refactored:
- [src/personal_agent/core/persag_manager.py](src/personal_agent/core/persag_manager.py)
- [src/personal_agent/core/user_registry.py](src/personal_agent/core/user_registry.py)
- [src/personal_agent/config/settings.py](src/personal_agent/config/settings.py)

Centralized single source of truth:
- [src/personal_agent/config/user_id_mgr.py](src/personal_agent/config/user_id_mgr.py)

Integration test (non-destructive):
- [tests/test_user_id_mgr_non_destructive.py](tests/test_user_id_mgr_non_destructive.py)

## Centralized Functions (user_id_mgr)

All modules should use these in preference to local logic:

- [`python.load_user_from_file()`](src/personal_agent/config/user_id_mgr.py:24)
  - Initializes PERSAG_HOME directory structure (or environment override)
  - Copies default LightRAG docker directories from project root on first run
  - Ensures env.userid exists
  - Sets os.environ["USER_ID"]
  - Returns the current user id

- [`python.get_userid()`](src/personal_agent/config/user_id_mgr.py:100)
  - Reads the current USER_ID dynamically from env.userid
  - Supports dynamic user switching without globals

- [`python.get_current_user_id()`](src/personal_agent/config/user_id_mgr.py:112)
  - Thin alias to get_userid

- [`python.get_user_storage_paths()`](src/personal_agent/config/user_id_mgr.py:124)
  - Returns a dict of user-dependent storage paths using PERSAG_ROOT and STORAGE_BACKEND

- [`python.refresh_user_dependent_settings()`](src/personal_agent/config/user_id_mgr.py:170)
  - Recomputes user-dependent paths for a given or current user id (pure calculation, no side effects on global module constants)

## PersagManager Refactor

File: [src/personal_agent/core/persag_manager.py](src/personal_agent/core/persag_manager.py)

Key changes:
- PersagManager now respects PERSAG_HOME from settings:
  - [`python.PersagManager()`](src/personal_agent/core/persag_manager.py:20) initializes `self.persag_dir = Path(PERSAG_HOME)`.
- Initialization delegates to user_id_mgr:
  - [`python.PersagManager.initialize_persag_directory()`](src/personal_agent/core/persag_manager.py:28) calls [`python.load_user_from_file()`](src/personal_agent/config/user_id_mgr.py:24) to create structure, copy default docker directories, and initialize env.userid.
- User ID retrieval is no longer duplicated:
  - [`python.PersagManager.get_userid()`](src/personal_agent/core/persag_manager.py:59) delegates to [`python.get_userid()`](src/personal_agent/config/user_id_mgr.py:100).
- User ID writes are preserved for CLI/UX:
  - [`python.PersagManager.set_userid()`](src/personal_agent/core/persag_manager.py:65) updates env.userid under PERSAG_HOME and syncs `os.environ["USER_ID"]`.
- Docker migration/validation retained:
  - [`python.PersagManager.migrate_docker_directories()`](src/personal_agent/core/persag_manager.py:91) can migrate from a specified project root to PERSAG_HOME with backups.
  - [`python.PersagManager.validate_persag_structure()`](src/personal_agent/core/persag_manager.py:156) checks env.userid and LightRAG docker dirs under PERSAG_HOME.

Validation note:
- The validator flags the default user id ("default_user") as invalid to encourage explicit user setup. Tests and flows should set a new user id before asserting validation success.

## UserRegistry Refactor

File: [src/personal_agent/core/user_registry.py](src/personal_agent/core/user_registry.py)

Key changes:
- Imports moved to module level (reduces function-level imports):
  - `from personal_agent.config.user_id_mgr import get_current_user_id, get_userid`
- Delegated current user retrieval:
  - [`python.UserRegistry.get_current_user()`](src/personal_agent/core/user_registry.py:196) returns `self.get_user(get_current_user_id())`
- Delegated ensure/registration to centralized getter:
  - [`python.UserRegistry.ensure_current_user_registered()`](src/personal_agent/core/user_registry.py:205) uses `current_user_id = get_userid()` and auto-registers if necessary.
- Registry path remains based on the active DATA_DIR and STORAGE_BACKEND, with file writes isolated to the configured location.

## Settings Refactor

File: [src/personal_agent/config/settings.py](src/personal_agent/config/settings.py)

Key changes:
- Delegates initialization to [`python.load_user_from_file()`](src/personal_agent/config/user_id_mgr.py:24) at module import:
  - See import at line 28 and call at line 31.
- Delegates user storage paths to user_id_mgr:
  - Imports [`python.get_user_storage_paths()`](src/personal_agent/config/user_id_mgr.py:124) and [`python.get_userid()`](src/personal_agent/config/user_id_mgr.py:100) (lines 129-131) and populates dynamic paths (AGNO_STORAGE_DIR, etc.) from the returned mapping.
- Exposes user-facing helpers for downstream modules:
  - Imports [`python.get_current_user_id()`](src/personal_agent/config/user_id_mgr.py:112) and [`python.refresh_user_dependent_settings()`](src/personal_agent/config/user_id_mgr.py:170) (lines 175-176).
- Removed legacy/dynamic import fallbacks and duplicate logic for user retrieval.

## Non-Destructive Test

File: [tests/test_user_id_mgr_non_destructive.py](tests/test_user_id_mgr_non_destructive.py)

Purpose:
- Validates the refactored flow end-to-end without modifying any real ~/.persag state by running under isolated temp directories.

What it does:
- Sets `PERSAG_HOME` and `PERSAG_ROOT` to temp dirs before importing settings to isolate all effects.
- Exercises:
  - [`python.load_user_from_file()`](src/personal_agent/config/user_id_mgr.py:24),
  - [`python.get_userid()`](src/personal_agent/config/user_id_mgr.py:100),
  - [`python.get_user_storage_paths()`](src/personal_agent/config/user_id_mgr.py:124),
  - [`python.refresh_user_dependent_settings()`](src/personal_agent/config/user_id_mgr.py:170)
- Uses [`python.PersagManager.initialize_persag_directory()`](src/personal_agent/core/persag_manager.py:28) to initialize and (optionally) migrate docker dirs from a fake project root.
- Sets a non-default user id via [`python.PersagManager.set_userid()`](src/personal_agent/core/persag_manager.py:65) and validates the structure with [`python.PersagManager.validate_persag_structure()`](src/personal_agent/core/persag_manager.py:156).
- Confirms [`python.UserRegistry.ensure_current_user_registered()`](src/personal_agent/core/user_registry.py:205) and [`python.UserRegistry.get_current_user()`](src/personal_agent/core/user_registry.py:196) work under the isolated paths only.

How to run:
- With pytest:
  - `pytest -q tests/test_user_id_mgr_non_destructive.py`
- Directly:
  - `python tests/test_user_id_mgr_non_destructive.py`

Safety:
- All filesystem writes are scoped to TemporaryDirectory and environment overrides set in the test. The real user's ~/.persag is untouched.

## Backward Compatibility

- Existing deployments continue to read USER_ID from PERSAG_HOME/env.userid (default: ~/.persag).
- settings.py still exposes derived path constants; however, they’re computed via the centralized user_id_mgr ensuring consistency and correctness.
- PersagManager retains migration of docker directories with backups to avoid data loss.

## Design Considerations

- Dynamic user switching: All retrievals of the current user id ultimately read from env.userid to reflect changes without requiring module reload.
- Avoid circular imports: user_id_mgr imports only minimal constants (PERSAG_ROOT, STORAGE_BACKEND) from settings; settings imports user_id_mgr functions in a directed manner.
- Validation semantics: Enforcing a non-default USER_ID for “valid structure” encourages explicit identity setup. Flows/tests should set a specific id before asserting valid structure.

## Follow-ups / Recommendations

- Add CLI command to switch users safely that calls [`python.PersagManager.set_userid()`](src/personal_agent/core/persag_manager.py:65) and prints derived paths from [`python.refresh_user_dependent_settings()`](src/personal_agent/config/user_id_mgr.py:170).
- Optionally provide a “doctor” command to run [`python.PersagManager.validate_persag_structure()`](src/personal_agent/core/persag_manager.py:156) and suggest auto-fixes.
- Consider persisting user metadata (name/type) at env.userid creation time to improve UX for first-run flows.

## Summary of Modified Entry Points

- [`python.PersagManager()`](src/personal_agent/core/persag_manager.py:20)
- [`python.PersagManager.initialize_persag_directory()`](src/personal_agent/core/persag_manager.py:28)
- [`python.PersagManager.get_userid()`](src/personal_agent/core/persag_manager.py:59)
- [`python.PersagManager.set_userid()`](src/personal_agent/core/persag_manager.py:65)
- [`python.PersagManager.validate_persag_structure()`](src/personal_agent/core/persag_manager.py:156)

- [`python.UserRegistry.get_current_user()`](src/personal_agent/core/user_registry.py:196)
- [`python.UserRegistry.ensure_current_user_registered()`](src/personal_agent/core/user_registry.py:205)

- [`python.load_user_from_file()`](src/personal_agent/config/user_id_mgr.py:24)
- [`python.get_userid()`](src/personal_agent/config/user_id_mgr.py:100)
- [`python.get_current_user_id()`](src/personal_agent/config/user_id_mgr.py:112)
- [`python.get_user_storage_paths()`](src/personal_agent/config/user_id_mgr.py:124)
- [`python.refresh_user_dependent_settings()`](src/personal_agent/config/user_id_mgr.py:170)

- [tests/test_user_id_mgr_non_destructive.py](tests/test_user_id_mgr_non_destructive.py)