# ADR-022: Docker Restart Optimization

## Context

During the development and testing of new features, it was observed that the Docker containers for LightRAG services were being restarted every single time the agent was initialized. This occurred even when the containers were already running correctly with the proper `USER_ID` configuration.

The root cause was traced to a hardcoded `force_restart=True` parameter within the `ensure_docker_user_consistency` function call in the agent's initialization sequence (`agno_agent.py` and `agno_agent_new.py`). This forced a stop-and-start cycle on the Docker containers regardless of their current state, leading to unnecessary delays of 10-20 seconds on startup and generating confusing log output.

## Decision

We have decided to change the default behavior to prioritize intelligent, state-aware restarts over forced restarts.

The implementation involves changing the hardcoded parameter from `force_restart=True` to `force_restart=False` in the agent's initialization logic.

```python
# The fix
ready_to_proceed, consistency_message = ensure_docker_user_consistency(
    user_id=self.user_id, auto_fix=True, force_restart=False # Changed to False
)
```

This change leverages the existing intelligence of the `ensure_docker_user_consistency` function, which is designed to:
1.  Check the current running state and `USER_ID` of the Docker containers.
2.  Perform a restart **only if** a configuration mismatch is detected (e.g., wrong `USER_ID` or container not running).

Forced restarts (`force_restart=True`) are now reserved for explicit user actions, such as clicking a "Restart" button in a UI, where the intent is to override the current state.

## Consequences

### Positive
- **Improved Performance**: Agent startup time is significantly reduced, as the 10-20 second delay from unnecessary Docker restarts is eliminated.
- **Enhanced User Experience**: A faster, smoother startup experience.
- **Reduced System Load**: The Docker daemon is no longer subjected to unnecessary stop/start cycles.
- **Cleaner Logs**: Logs are no longer cluttered with redundant restart messages, making them easier to debug.
- **Increased Stability**: Prevents potential service interruptions that could arise from frequent, unnecessary restarts.

### Negative
- None identified. The fix makes the system behave as it was originally intended, without removing any functionality. The ability to force a restart is retained for specific, user-initiated actions.
