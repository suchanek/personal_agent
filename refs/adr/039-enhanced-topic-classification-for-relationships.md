# ADR 039: Enhanced Topic Classification for Relationships

## Status

**Accepted**

## Context

The existing topic classification system, which relies on a keyword and phrase-based matching system defined in `topics.yaml`, was failing to correctly categorize user statements about social connections and relationships. Key terms like "friend" and "enemy" were not present in any topic category, causing such statements to be misclassified as `unknown`. This limited the agent's ability to organize and retrieve memories related to the user's social life, impacting the quality of its contextual understanding and interaction.

## Decision

To address this deficiency, we will enhance the topic classification system by introducing a new, dedicated `relationships` category in the `src/personal_agent/core/topics.yaml` file.

This new category will include a comprehensive set of keywords and phrases related to various types of social connections, such as:
- **Keywords**: `friend`, `enemy`, `colleague`, `partner`, `neighbor`, `mentor`, `ally`, etc.
- **Phrases**: `"my friend"`, `"know someone"`, `"social circle"`, `"work colleague"`, etc.

This change expands the classifier's vocabulary, allowing it to accurately identify and tag memories concerning personal and professional relationships.

## Consequences

### Positive
- **Improved Accuracy**: Significantly reduces `unknown` classifications for relationship-related memories.
- **Better Memory Organization**: Enables more precise topic-based filtering and retrieval of social information.
- **Enhanced Contextual Understanding**: The agent can now better grasp the user's social context, leading to more relevant and personalized interactions.
- **Multi-Topic Classification**: The system can now correctly assign multiple topics to a single memory (e.g., a statement about a "work colleague" can be tagged as both `work` and `relationships`).

### Negative
- A minor increase in the size of the `topics.yaml` file, which has a negligible impact on performance.