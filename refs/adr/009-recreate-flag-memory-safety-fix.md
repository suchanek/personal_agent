# 9. Recreate Flag Memory Safety Fix

*   **Status:** Accepted
*   **Context:** The `--recreate` flag, intended for a clean reset of the dual memory system, had critical safety issues. In the Streamlit application, it defaulted to `True`, causing accidental data loss on every launch. In the CLI, `clear_all_memories()` was called prematurely during initialization, leading to SQLite memories not being cleared when explicitly requested via `--recreate`.
*   **Decision:** To resolve these issues and ensure memory safety:
    1.  **Streamlit Default Parameter Fix**: Changed the default `recreate` parameter in `tools/paga_streamlit_agno.py` to `False` to prevent accidental memory destruction on launch.
    2.  **CLI Timing Fix**: Relocated the `clear_all_memories()` call in `src/personal_agent/core/agno_agent.py` to occur *after* the memory system (`self.agno_memory`) is fully initialized. This ensures that when `--recreate` is used, both SQLite and LightRAG memories are properly cleared.
    3.  **Streamlit CLI Parameter Support**: Added explicit command-line argument parsing for `--recreate` in `tools/paga_streamlit_agno.py` to allow users to intentionally clear memories from the Streamlit interface.
*   **Consequences:**
    *   **Positive:**
        *   **Enhanced Memory Safety**: User memories are now preserved by default across all application entry points (CLI and Streamlit).
        *   **Reliable Recreation**: The `--recreate` flag now functions correctly, providing a dependable way to reset both local SQLite and LightRAG graph memories when explicitly requested.
        *   **Improved User Experience**: Prevents unexpected data loss and provides clear control over memory management.
        *   **Consistent Behavior**: Ensures that memory clearing operations are consistently applied to both memory systems.
    *   **Negative:**
        *   Requires users to be aware of the `--recreate` flag for intentional memory clearing, but this is a necessary trade-off for data safety.
