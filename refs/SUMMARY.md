
# Staged Changes Summary

Date: 2025-11-16
Branch: v0.8.77ldev

This document summarizes the currently staged changes (as of the above date). The changes touch memory management, REST API, tooling, and a few UX/streamlit improvements. Use this file as a concise reference in `refs/` for reviewers.

## High-level summary

- Added two utility scripts to improve memory clearing and verification:
  - `inject_charlie_brown_friends_facts.py` — a small helper to inject a set of Charlie Brown / Peanuts facts into the REST API-backed memory store (for testing/demo).
  - `poll_lightrag_memory_clear.py` — simple polling script that queries the memory stats endpoint and waits for LightRAG to report zero documents.

- REST API: added a blocking endpoint `DELETE /api/v1/memory/clear` that triggers a full memory clear via the memory helper and returns once the helper reports success/failure. This endpoint is intended for scripted workflows that need the clear to be initiated from the API layer.

- Core memory behavior and tooling:
  - `src/personal_agent/core/agent_memory_manager.py` — improved memory-clear handling: after initiating LightRAG deletions, the manager now waits for the LightRAG pipeline to become idle (new `_wait_for_pipeline_idle` helper) before reporting success. This reduces race conditions between deletion and verification.
  - `src/personal_agent/tools/memory_cleaner.py` (restored) — async CLI-driven memory cleaner module (clears SQLite + LightRAG, vacuums DB, deletes graph files, supports dry-run/verify/no-confirm). A CLI wrapper module `src/personal_agent/tools/clear_all_memories.py` was also (re)added to provide `python -m` invocation.

- Streamlit / UI improvements:
  - `src/personal_agent/tools/streamlit_tabs.py` — improved default date-range logic for memory tab (use earliest memory date as start, extend end to today, fallback to 1 year range instead of 5 days). Added documentation snippets for the new `DELETE /api/v1/memory/clear` endpoint in sidebar examples.

- Project task and tooling updates:
  - `pyproject.toml` — fixed `poe` task naming and invocation for memory clearing: replaced an invalid `script` entry with `tool.poe.tasks.memory-clear` and set a `cmd` to run the module. Also removed the `demo-memory` task from quick-start sequences to avoid running the demo by default.

- Minor config and env updates:
  - `lightrag_memory_server/env.memory_server` — updated `WEBUI_DESCRIPTION` string.

- File moves into `refs/`:
  - Several instruction-related markdown files were moved into `refs/` (`INSTRUCTION_*.md`). These are preserved and renamed under `refs/` for organization and long-term reference.

## Rationale / Notes

- Waiting for LightRAG pipeline idle: multiple parts of the system (API + CLI + tests) had intermittent failures due to the asynchronous LightRAG ingestion/deletion pipeline. Adding a short polling/wait mechanism reduces false negatives when verifying deletion.

- The new API endpoint `DELETE /api/v1/memory/clear` intentionally returns once the memory helper reports a result. Because LightRAG deletions may be long-running internally, the memory manager now optionally waits for the pipeline to idle before returning success — this is surfaced to API callers.

- The `inject_charlie_brown_friends_facts.py` script is intended for test/demo purposes only. It clears memories via the new API endpoint and then injects a curated list of facts; it should not be used in production environments as-is.

## Items of follow-up (suggested)

- Consider adding an authenticated admin-only route for `DELETE /api/v1/memory/clear` (currently the endpoint appears unprotected).
- Add e2e tests that exercise the API-clearing flow plus polling to ensure that the pipeline-wait behavior is stable across loads.
- Consider configurable timeout for pipeline wait in the memory manager and expose the timeout via the REST API/CLI options.

---

Done: summary created to document the staged changes prior to commit.
