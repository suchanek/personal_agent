# ADR-042: Standalone Ollama Reasoning Team

## Status

Accepted

## Context

The project currently has a sophisticated `AgnoPersonalAgent` that handles memory, knowledge, and various tools. However, there is a need for a more lightweight, standalone team of agents that can perform reasoning tasks using local Ollama models without the full overhead of the `AgnoPersonalAgent`.

The goal is to create a multi-agent team that:
- Uses the `agno.Agent` and `agno.Team` classes.
- Leverages local Ollama models for all agents.
- Can call tools correctly.
- Has access to memory and knowledge, but in a more decoupled way than the main agent.

## Decision

We will create a new `ollama_reasoning_multi_purpose_team.py` module. This module will define a team of agents for various tasks (web search, finance, writing, calculator, and memory/knowledge).

Key characteristics of this implementation:

1.  **Standalone Team:** The team is defined in its own module and can be run independently via a new `paga_team_cli` entry point.
2.  **`agno.Agent` based:** All agents in the team are instances of the `agno.Agent` class, not the more complex `AgnoPersonalAgent`.
3.  **Ollama-powered:** All agents will use Ollama models, created via a helper function that leverages the existing `AgentModelManager`.
4.  **Decoupled Memory/Knowledge:** The memory and knowledge capabilities are provided to a dedicated `Memory Agent` within the team. This agent's initialization mimics the setup of the `AgnoPersonalAgent` to ensure correct access to storage, but it remains a simple `agno.Agent` instance.
5.  **Direct Tool Usage:** The agents are equipped with and directly use tools like `DuckDuckGoTools`, `YFinanceTools`, `CalculatorTools`, and the custom `KnowledgeTools` and `AgnoMemoryTools`.
6.  **New `query_lightrag_knowledge_direct` tool:** A new tool is added to `KnowledgeTools` to allow for direct, unfiltered queries to the LightRAG knowledge base. This is useful for the reasoning team to bypass some of the filtering and processing that `query_knowledge_base` performs.

## Consequences

### Positive

- **Flexibility:** Provides a more lightweight and flexible way to use multi-agent teams for specific tasks.
- **Modularity:** The team is self-contained and can be extended or modified without impacting the main `AgnoPersonalAgent`.
- **Demonstration:** Serves as a clear example of how to build multi-agent teams with `agno`, Ollama, and the project's custom tools.
- **Testing:** The new `paga_team_cli` allows for easy testing of the team's capabilities.

### Negative

- **Code Duplication:** The initialization of the `Memory Agent` duplicates some of the logic from the `AgnoPersonalAgent`'s setup. This is a conscious trade-off for decoupling.
- **Complexity:** Adds another entry point and a new way of running agents to the project, which could slightly increase the learning curve for new developers.
