# ADR-097: Decouple Dashboard from Direct Docker Management

**Status:** Accepted

**Context:**

The previous version of the management dashboard included a "Docker Services" tab that attempted to directly manage the agent's Docker containers (e.g., LightRAG). This implementation proved to be unreliable and presented a poor user experience for several reasons:

1.  **Permission Issues:** The user running the Streamlit dashboard often lacks the necessary permissions to access the Docker socket (`/var/run/docker.sock`), leading to connection failures.
2.  **Environmental Fragility:** The dashboard's functionality was dependent on Docker Desktop (or the Docker daemon) being active. If it wasn't running, the dashboard would produce unhelpful errors.
3.  **Poor Error Handling:** Errors during Docker interactions could degrade the entire dashboard experience without providing clear, actionable guidance to the user.
4.  **Tight Coupling:** It tightly coupled the dashboard's functionality to the local machine's Docker setup, making the dashboard less portable and focused.

**Decision:**

To improve stability, security, and user experience, we have decided to decouple the dashboard from direct Docker management.

1.  **Remove Direct Docker Control:** The "Docker Services" tab has been removed from the dashboard's primary user interface. This removes the fragile, direct-control functionality.
2.  **Improve Docker Utility Robustness:** The underlying Docker utility functions (`docker_utils.py`) will be significantly hardened. They will now perform robust pre-checks for Docker availability and handle specific exceptions (e.g., `PermissionError`) gracefully.
3.  **Provide Clear User Guidance:** In components where Docker information might be displayed, the UI will first check for accessibility. If the Docker daemon is not available, it will display a clear, informative message explaining the possible reasons and guiding the user to stable command-line tools (`smart-restart-lightrag.sh`, `docker ps`).
4.  **Shift Responsibility:** The responsibility for direct Docker management is shifted to the user's command line, which is a more reliable, secure, and appropriate environment for managing system-level services. The dashboard will focus on its core purpose: managing the agent's application-level state (Users, Memory, Knowledge).

**Consequences:**

**Positive:**
-   **Increased Stability:** The dashboard is no longer prone to failures or crashes when Docker is unavailable.
-   **Improved User Experience:** Users receive clear, actionable guidance when Docker isn't found, rather than cryptic errors.
-   **Better Security & Separation of Concerns:** The web UI is no longer a direct interface to system-level services, which is a more secure posture.
-   **Focused Application:** The dashboard can better excel at its primary goal of managing the agent's data and configuration.

**Negative:**
-   **Loss of Convenience:** Users lose the convenience of a one-click Docker restart from the UI. However, given the unreliability and poor experience of the previous implementation, this is a net positive trade-off for stability and clarity.
