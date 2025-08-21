## [Unreleased]

### Changed
- **Streamlined Streamlit UI and Default Team Mode**: The Streamlit application now defaults to the more capable team-based mode, with a `--single` flag to run in a single-agent configuration. The runtime mode-switching UI has been removed to simplify the user experience. This change is documented in [ADR-072](./refs/adr/072-streamlit-ui-simplification.md).
- **Enhanced Team and Agent Visibility**: The `show_members_responses` and `show_tool_calls` flags are now enabled by default for the `PersonalAgentTeam` and most specialized agents, respectively. This provides greater transparency into agent operations.
- **Dedicated Knowledge Agent for Team Memory and Knowledge Operations**: All memory and knowledge-related operations within the `PersonalAgentTeam` are now explicitly routed through a dedicated `Knowledge Agent` (an `AgnoPersonalAgent` instance). This ensures consistent fact restatement, LLM processing, and streamlines UI integration for memory storage, retrieval, and knowledge management. This refines the architectural decisions made in [ADDR-071](./refs/adr/071-dedicated-knowledge-agent-for-team-memory.md).

### Fixed
- **Corrected Model Name Typo**: Fixed a typo in `src/personal_agent/core/agent_model_manager.py` from `qwen3:1.7B` to `qwen3:1.7b` to ensure correct model loading.
- **Streamlit Memory Deletion Functionality**: Resolved a critical bug in `tools/paga_streamlit_agno.py` where memory deletion was non-functional due to Streamlit's conditional rendering context issues. The UI now reliably handles memory deletion with proper confirmation flows and immediate visual feedback.
