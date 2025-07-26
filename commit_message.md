feat(memory): enhance topic classification for relationships

This commit introduces a new `relationships` category to the topic
classification system.

Previously, statements about social connections were often misclassified as
`unknown` because the system lacked relevant keywords and phrases. This
change adds a comprehensive set of terms related to personal and
professional relationships, significantly improving the accuracy of topic
classification.

This enhancement enables the agent to better understand and organize
memories about the user's social life, leading to more contextually
aware and personalized interactions.

See ADR-039 for more details.