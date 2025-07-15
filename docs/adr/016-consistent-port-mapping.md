# ADR-016: Consistent Port Mapping for Service-Host Interaction

**Date**: 2025-07-15

**Status**: Accepted

## Context

A critical and widespread connection failure issue was identified, affecting tools like `docmgr.py` and other components that interact with the LightRAG services. The root cause was a fundamental inconsistency between the Docker port mappings and the application's configuration.

-   **Docker Configuration**: The `docker-compose.yml` files correctly mapped the services' internal port (`9621`) to different external *host* ports (e.g., `9622` for the KB server, `9623` for the memory server).
-   **Application Configuration**: However, various application configuration files (`settings.py`, `.env`, etc.) and management scripts were incorrectly configured to connect to the *internal* port (`9621`) from the host machine, which is not accessible from outside the Docker network.

This resulted in `Connection Refused` errors and made the services unreachable from the host application.

## Decision

To resolve this, a systematic correction of all port configurations was implemented to enforce a clear and consistent distinction between internal container ports and external host ports.

1.  **Standardized Port Mapping**: The official port mapping is now defined as:
    *   **LightRAG Server (KB)**: Host Port `9622` -> Container Port `9621`
    *   **LightRAG Memory Server**: Host Port `9623` -> Container Port `9621`

2.  **Configuration-Wide Correction**: All application-level configurations that define service URLs and ports were updated to use the correct external **host ports** (`9622` and `9623`). This includes:
    *   `src/personal_agent/config/settings.py`
    *   `.env` and all `env.*` example files
    *   `smart-restart-lightrag.sh`
    *   `src/personal_agent/core/lightrag_manager.py`

3.  **Clarification in Code**: Comments were added where necessary to explicitly distinguish between host and container ports to prevent future confusion.

## Consequences

### Positive

*   **Restored Functionality**: All tools and services that connect to the LightRAG servers are now fully functional.
*   **Increased Stability**: The system is more stable and reliable as the networking configuration is now correct and consistent.
*   **Improved Clarity**: The distinction between host and container ports is now clearly defined and enforced, making the system easier to understand and maintain.
*   **Eliminated Confusion**: The risk of misconfiguring ports in the future is significantly reduced.
### Negative

*   None. This was a critical bug fix with no downside.
