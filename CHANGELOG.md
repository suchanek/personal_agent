## [Unreleased]

### Changed
- **Tool Naming**: Renamed `AgnoMemoryTools` to `PersagMemoryTools` and `KnowledgeTools` to `PersagKnowledgeTools` to better reflect their roles within the personal agent (`persag`) ecosystem.

### Fixed
- **Tool Call Extraction and Response Handling**: Overhauled the response handling logic to correctly parse and display tool calls and their results. This resolves a critical bug where the Streamlit UI would show raw tool call syntax instead of the executed content from the writer agent. The new `extract_tool_calls_and_metrics` function now robustly handles various tool call formats from different models and agents.
- **Team Delegation and Reasoning**: Switched the `personal_agent_team` from `route` to `coordinate` mode and integrated `ReasoningTools` to significantly improve the coordinator's ability to delegate tasks to the correct specialized agents.
- **Streamlit `arun` Compatibility**: Fixed a bug that caused the Streamlit app to crash when using `agent.arun()` with asynchronous tools in single-agent mode.


### Added
- **Qwen Model Settings**: Implemented specific, environment-configurable settings for the Qwen model, including parameters for temperature, `min_p`, `top_p`, and `top_k`. These settings are now applied during model initialization and are displayed in the Streamlit UI for transparency. This is documented in [QWEN_MODEL_SETTINGS_IMPLEMENTATION.md](./refs/QWEN_MODEL_SETTINGS_IMPLEMENTATION.md).

### Changed
- **Streamlined Streamlit UI and Default Team Mode**: The Streamlit application now defaults to the more capable team-based mode, with a `--single` flag to run in a single-agent configuration. The runtime mode-switching UI has been removed to simplify the user experience. This change is documented in [ADR-072](./refs/adr/072-streamlit-ui-simplification.md).
- **Enhanced Team and Agent Visibility**: The `show_members_responses` and `show_tool_calls` flags are now enabled by default for the `PersonalAgentTeam` and most specialized agents, respectively. This provides greater transparency into agent operations.
- **Dedicated Knowledge Agent for Team Memory and Knowledge Operations**: All memory and knowledge-related operations within the `PersonalAgentTeam` are now explicitly routed through a dedicated `Knowledge Agent` (an `AgnoPersonalAgent` instance). This ensures consistent fact restatement, LLM processing, and streamlines UI integration for memory storage, retrieval, and knowledge management. This refines the architectural decisions made in [ADDR-071](./refs/adr/071-dedicated-knowledge-agent-for-team-memory.md).

### Fixed
- **File Tools Path Handling**: Corrected a recurring issue where file-related tools (`FileTools`, `ShellTools`, `PythonTools`) were failing due to being initialized with string paths instead of the required `pathlib.Path` objects. All tools now correctly use `Path` objects and consistently point to the user's home directory, resolving multiple `'str' object has no attribute 'iterdir'` and `'str' object has no attribute 'joinpath'` errors. This is documented in [ADR-073](./refs/adr/073-file-tools-path-fix.md).
- **Corrected Model Name Typo**: Fixed a typo in `src/personal_agent/core/agent_model_manager.py` from `qwen3:1.7B` to `qwen3:1.7b` to ensure correct model loading.
- **Streamlit Memory Deletion Functionality**: Resolved a critical bug in `tools/paga_streamlit_agno.py` where memory deletion was non-functional due to Streamlit's conditional rendering context issues. The UI now reliably handles memory deletion with proper confirmation flows and immediate visual feedback.
