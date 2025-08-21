# ADR-072: Streamline Streamlit UI and Default to Team-Based Interaction

**Date**: 2025-08-21

**Status**: Accepted

## Context

The Streamlit UI for the Personal Agent has grown in complexity, offering runtime options to switch between a single-agent mode and a team-based mode. While flexible, this adds cognitive load for the user and increases the maintenance overhead of the UI code. The command-line interface and agent initialization logic also required clarification to better reflect the intended primary mode of operation. The default mode was single-agent, but the more powerful and feature-rich mode is the team-based mode.

## Decision

1.  **Default to Team Mode:** The application will now default to the more capable team-based mode. A `--single` command-line flag is introduced to allow users to run the application in a single-agent configuration if needed. The previous `--team` flag is removed.
2.  **Remove Runtime Mode Switching:** The UI control for switching between agent modes at runtime will be removed. The mode will be determined at application startup, simplifying the user interface and the application's state management.
3.  **Simplify Theme Management:** The custom light theme will be removed in favor of Streamlit's default light theme. This reduces the number of custom CSS files and simplifies the theming logic.
4.  **Enhance Team Visibility:** The `show_members_responses` flag in the `PersonalAgentTeam` will be enabled by default to provide users with greater insight into the team's internal operations and decision-making processes.
5.  **Standardize Tool Visibility:** The `show_tool_calls` flag will be enabled by default for most specialized agents to improve debuggability and transparency.

## Consequences

*   **Improved User Experience:** The Streamlit UI is now more focused and less cluttered. The application's primary mode of operation is clearer to users.
*   **Reduced Code Complexity:** Removing the runtime mode switching logic simplifies the Streamlit application's codebase, making it easier to maintain and extend.
*   **Better Debugging:** Increased visibility into team member responses and tool calls will aid in debugging and understanding agent behavior.
*   **Breaking Change:** The command-line interface for launching the Streamlit application has changed. Users who previously used the `--team` flag will now need to run the application without any flags to get the team mode, and users who want the single agent mode will need to use the `--single` flag.
