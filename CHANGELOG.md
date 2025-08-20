## [Unreleased]

### Fixed
- **Streamlit Memory Deletion Functionality**: Resolved a critical bug in `tools/paga_streamlit_agno.py` where memory deletion was non-functional due to Streamlit's conditional rendering context issues. The UI now reliably handles memory deletion with proper confirmation flows and immediate visual feedback.

### Changed
- **Dedicated Knowledge Agent for Team Memory and Knowledge Operations**: All memory and knowledge-related operations within the `PersonalAgentTeam` are now explicitly routed through a dedicated `Knowledge Agent` (an `AgnoPersonalAgent` instance). This ensures consistent fact restatement, LLM processing, and streamlines UI integration for memory storage, retrieval, and knowledge management. This refines the architectural decisions made in [ADDR-071](./refs/adr/071-dedicated-knowledge-agent-for-team-memory.md).