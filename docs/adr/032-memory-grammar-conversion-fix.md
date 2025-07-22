# ADR-032: Memory Grammar Conversion Fix

## Status

Accepted

## Context

The Personal AI Agent was experiencing a critical issue where memories stored in a third-person format (e.g., "charlie was born on 4/11/1965") were not being properly converted to a second-person format (e.g., "you were born on 4/11/1965") when presented to the user. This led to an unnatural conversational flow and a poor user experience, as the agent would refer to the user by name or in the third person instead of using appropriate second-person pronouns.

This problem was particularly evident in interactions where the agent was recalling personal facts about the user, leading to responses like "I remember charlie was born on 4/11/1965" instead of the more natural "I remember you were born on 4/11/1965". This violated the agent's core identity rule of being a friendly AI assistant that knows information *about* the user, rather than pretending to *be* the user or referring to the user as a third party.

## Decision

To address this, the `get_detailed_memory_rules()` method within the `AgentInstructionManager` class (specifically for the `STANDARD` instruction level and inherited by `EXPLICIT` and `EXPERIMENTAL`) has been enhanced. This enhancement includes:

1.  **Explicit Grammar Conversion Requirement**: Clear instructions have been added to mandate that memories, regardless of their stored format (which may be third-person for internal consistency), *must* be converted to second-person when presented to the user.
2.  **Concrete Examples**: Specific examples of correct and incorrect responses are provided to guide the model's behavior.
3.  **Key Conversion Patterns**: Defined grammar transformation rules for common patterns, such as:
    *   `"charlie was/is" → "you were/are"`
    *   `"charlie has/had" → "you have/had"`
    *   `"charlie's [noun]" → "your [noun]"`
    This ensures consistent use of second-person pronouns (you, your, yours) when presenting user information.

These rules are now applied to all instruction levels, with varying degrees of detail in their respective instruction sets.

## Consequences

*   **Positive**:
    *   **Improved User Experience**: Conversations with the agent will feel more natural, personal, and less confusing due to correct pronoun usage.
    *   **Consistent Identity Maintenance**: The agent will more effectively maintain its identity as an AI assistant speaking *to* the user, rather than *about* the user in the third person or adopting the user's persona.
    *   **Enhanced Conversational Flow**: Responses will integrate seamlessly into a natural dialogue, improving overall interaction quality.
    *   **Reduced Confusion**: Eliminates awkward third-person references, making the agent's communication clearer.

*   **Negative**:
    *   The effectiveness of this fix relies on the LLM's ability to consistently apply these grammar conversion rules based on the provided instructions. While explicit, there's always a potential for misinterpretation by the model.
    *   Requires careful monitoring of agent responses to ensure consistent application of the new rules.
    *   Potential for minor performance overhead if the grammar conversion logic becomes complex, though the current approach is instruction-based.

This decision reinforces the agent's core identity and significantly enhances the quality of user interactions by ensuring grammatically correct and contextually appropriate memory recall.
