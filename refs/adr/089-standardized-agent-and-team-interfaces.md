# ADR-089: Standardized Agent and Team Interfaces

- Status: Proposed
- Date: 2025-09-24
- Deciders: Gemini

## Context and Problem Statement

The existing architecture lacked a standardized interface for agents and teams. While both `AgnoPersonalAgent` and `PersonalAgentTeam` had `run` and `arun` methods, their signatures and implementations were not enforced by a common contract. This led to code duplication and made it difficult to treat agents and teams polymorphically, for example, when creating systems where an agent or a team could be used interchangeably. This lack of a unified interface also increased the complexity of the system and made it harder to maintain and extend.

## Decision Drivers

- The need to reduce code duplication.
- The desire to improve modularity and code reuse.
- The goal of creating a more flexible and extensible architecture.
- The need to adhere to the "program to an interface, not an implementation" principle.

## Considered Options

1.  **Do nothing:** Continue with the existing architecture, with separate interfaces for agents and teams. This was rejected as it would perpetuate the existing problems of code duplication and lack of polymorphism.
2.  **Introduce `BaseAgent` and `BaseTeam` abstract base classes:** This option involves creating abstract base classes that define a common interface for all agents and teams. This would enforce a consistent structure and allow for polymorphic use of agents and teams.

## Decision Outcome

Chosen option: "Introduce `BaseAgent` and `BaseTeam` abstract base classes".

We will create two new abstract base classes:

- `BaseAgent`: This class will define the common interface for all agents, including `run` and `arun` methods. `AgnoPersonalAgent` will be refactored to inherit from this class.
- `BaseTeam`: This class will define the common interface for all teams, including `run` and `arun` methods. `PersonalAgentTeam` will be refactored to inherit from this class.

This change will standardize the interfaces for agents and teams, promoting polymorphism and simplifying the overall architecture.

### Positive Consequences

- Improved code modularity and reusability.
- Reduced code duplication.
- A more flexible and extensible architecture.
- Clearer and more maintainable code.

### Negative Consequences

- Requires refactoring of existing agent and team classes.
- Introduces a small amount of additional complexity in the form of new base classes.

## Implementation Plan

1.  Create `src/personal_agent/core/base_agent.py` with the `BaseAgent` class.
2.  Create `src/personal_agent/team/base.py` with the `BaseTeam` class.
3.  Refactor `AgnoPersonalAgent` to inherit from `BaseAgent`.
4.  Refactor `PersonalAgentTeam` to inherit from `BaseTeam`.
5.  Update any other relevant parts of the codebase to reflect these changes.
