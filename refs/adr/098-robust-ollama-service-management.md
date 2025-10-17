# ADR-098: Robust Ollama Service Management

**Status:** Accepted

**Context:**

The previous installation script (`install-personal-agent.sh`) installed the Ollama application but managed it in a fragile way. It would attempt to launch the GUI application (`Ollama.app`) directly. This approach had several significant drawbacks:

1.  **GUI Dependency:** It required a GUI session and relied on a user-facing application for a background service, which is not a robust practice.
2.  **Potential for Conflicts:** If the user manually started the Ollama app, it could conflict with the instance launched by the script, leading to two Ollama processes and unpredictable behavior.
3.  **Lack of Persistence:** The Ollama process would not automatically restart on login or system reboot, requiring manual intervention.
4.  **Poor Service Management:** It was difficult to check the status, view logs, or manage the Ollama process in a standardized way.

**Decision:**

To create a more stable, reliable, and maintainable system, the installation script has been overhauled to manage Ollama as a proper background service using macOS's native `launchd` system.

1.  **Implement LaunchAgent Service:** The script now creates a `launchd` property list (`.plist`) file in the user's `~/Library/LaunchAgents` directory. This defines a service that runs `ollama serve` as a background process.
2.  **Automatic Startup:** The LaunchAgent is configured to start automatically whenever the user logs in, ensuring Ollama is always available without manual steps.
3.  **Prevent Conflicts:** The script now explicitly checks for and terminates any running `Ollama.app` GUI instances before loading the new service. This prevents the common issue of running two conflicting Ollama servers.
4.  **Standardized Management:** Users can now manage the Ollama service using standard `launchctl` commands (e.g., `launchctl list`, `launchctl load/unload`), and logs are directed to a standard location (`~/Library/Logs/ollama.log`), providing a conventional and reliable management experience.
5.  **Update User Guidance:** The final instructions provided by the installer have been updated to clearly explain that Ollama is running as a background service and how to monitor it.

**Consequences:**

**Positive:**
-   **Increased Reliability:** Ollama runs as a true background service, independent of the GUI application, and starts automatically on login.
-   **Improved Stability:** The risk of conflicting Ollama processes is eliminated, leading to a more stable and predictable environment.
-   **Better Maintainability:** The service can be managed and monitored using standard, well-documented macOS tools.
-   **Enhanced User Experience:** The installation is now a "set it and forget it" process. Users no longer need to manually start Ollama before using the agent.

**Negative:**
-   **Increased Complexity:** The installation script is slightly more complex due to the addition of the LaunchAgent setup logic. However, this is a worthwhile trade-off for the significant gains in reliability.
