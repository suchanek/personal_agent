# ADR-080: Journaling and Safety Topics

- **Status**: Proposed
- **Date**: 2025-09-01
- **Author**: Eric G. Suchanek, PhD

## Context

The agent's ability to understand and categorize user input is crucial for providing relevant and helpful responses. As the agent's capabilities expand, it's important to enhance its topic classification system to cover a wider range of user expressions, including personal reflections and sensitive topics.

## Decision

We will introduce two new topics to the `TopicClassifier`:

1.  **`journal`**: This topic will cover a wide range of personal writing, reflections, and self-expression. This will allow the agent to better understand and categorize user's personal thoughts and feelings.
2.  **`self_harm_risk`**: This is a critical safety feature that will enable the agent to identify and respond appropriately to users who may be in distress. The agent will be able to recognize expressions of self-harm and provide resources for help.

To support these new topics, we will also:

*   Enhance the `TopicClassifier` to improve its accuracy, especially for phrases that include common stopwords.
*   Create a new `analyze_topic.py` script to allow for easy testing and analysis of the topic classifier.
*   Update the Streamlit UI to include the new `journal` topic in the memory management section.

## Consequences

### Positive

*   **Improved User Understanding**: The agent will be able to better understand and categorize a wider range of user inputs.
*   **Enhanced Safety**: The `self_harm_risk` topic will allow the agent to identify and respond to users in distress, potentially preventing harm.
*   **Better Memory Organization**: The `journal` topic will help organize user's personal reflections and memories more effectively.

### Negative

*   **Increased Complexity**: The topic classification system will become more complex with the addition of new topics.
*   **Potential for False Positives**: The `self_harm_risk` topic may have false positives, which could lead to unnecessary interventions. Careful tuning and testing will be required to minimize this risk.
