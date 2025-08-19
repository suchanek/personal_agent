# ADR-071: Dedicated Knowledge Agent for Team Memory and Knowledge Operations

## Status
Accepted

## Context
The multi-agent `PersonalAgentTeam` was designed to route user requests to specialized agents. While `ADR-069` (Personal Agent Team Refactor) introduced the concept of a `Knowledge Agent`, the explicit routing and consistent handling of all memory and knowledge operations through this dedicated agent, especially within the Streamlit UI, required further refinement. Previously, memory handling might have relied on less centralized mechanisms or fallbacks, potentially leading to inconsistencies in fact restatement, LLM processing, and overall architectural clarity.

## Decision
All memory and knowledge-related operations within the `PersonalAgentTeam` will be explicitly routed through a dedicated `Knowledge Agent`. This `Knowledge Agent` will be an instance of `AgnoPersonalAgent`, configured specifically for memory and knowledge management (disabling its general-purpose tools to avoid conflicts with team coordination).

The `Knowledge Agent` will be the first member of the `PersonalAgentTeam`, ensuring its prominence and accessibility for memory and knowledge tasks. The `PersonalAgentTeamWrapper` and the Streamlit UI (`paga_streamlit_agno.py`) will be updated to consistently leverage this dedicated `Knowledge Agent` for all memory storage, retrieval, and knowledge ingestion/querying.

## Consequences

### Positive
- **Improved Modularity and Separation of Concerns**: Clearly defines the `Knowledge Agent` as the single source of truth for all memory and knowledge operations within the team, enhancing the team's overall architecture.
- **Consistent Memory Processing**: Ensures that all user memory storage operations (e.g., `store_user_memory`) within the team context benefit from the `AgnoPersonalAgent`'s built-in fact restatement and LLM processing, leading to higher quality and more consistent memory storage.
- **Streamlined UI Integration**: Simplifies the Streamlit UI's interaction with the team's memory and knowledge systems by providing a consistent interface through the dedicated `Knowledge Agent`.
- **Enhanced Maintainability**: Centralizing these operations reduces code duplication and makes it easier to manage and debug memory and knowledge-related functionalities.
- **Clearer Delegation**: Reinforces the team coordinator's role as a router, delegating specialized tasks to the most appropriate agent.

### Negative
- **Increased Initial Complexity**: Requires careful configuration of the `Knowledge Agent` and updates to the team's initialization and UI interaction logic.
- **Potential for Misconfiguration**: If the `Knowledge Agent` is not correctly set up or integrated, memory and knowledge features within the team might not function as expected.

## Related ADRs
- [ADR-069: Personal Agent Team Refactor](./069-personal-agent-team-refactor.md)
- [ADR-068: Unified Agent and Team Streamlit UI](./068-unified-agent-team-streamlit-ui.md)
