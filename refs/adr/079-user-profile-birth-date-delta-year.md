# ADR-079: User Profile Enhancement with Birth Date and Delta Year

- **Status**: Accepted
- **Date**: 2025-09-01
- **Author**: Gemini

## Context

The user management system required a feature to allow users to write memories from the perspective of a specific age or life stage. This is crucial for autobiographical memory creation, maintaining temporal consistency in memories, and supporting therapeutic applications like memory preservation. The system lacked the necessary data model and logic to support this "age-perspective memory writing."

## Decision

We decided to enhance the `User` data model by adding two new optional fields:

1.  **`birth_date`**: An `Optional[str]` in ISO format (`YYYY-MM-DD`) to store the user's birth date.
2.  **`delta_year`**: An `Optional[int]` representing the user's age in years from their birth date from which they wish to write memories.

This enhancement includes:
-   **Comprehensive Validation**: Strict validation rules were implemented for both fields. `birth_date` must be a valid, non-future date within a reasonable range (e.g., not more than 150 years ago). `delta_year` must be a non-negative integer.
-   **Cross-Field Validation**: When both fields are present, the system calculates a "memory year" (`birth_year + delta_year`) and ensures it does not fall in the future.
-   **Delta-Year Aware Timestamps**: The `update_last_seen` method in the `User` model was modified. If `delta_year` is set, it adjusts the year of the timestamp to the calculated "memory year" while retaining the current month, day, and time. This ensures all recorded interactions reflect the user's chosen age perspective.
-   **System-Wide Integration**: The new fields were integrated into the entire user management stack, including the `UserManager`, `UserRegistry`, and Streamlit UI utility functions, ensuring a consistent implementation.
-   **Testing**: A new test suite (`test_birth_date_integration.py`) was created to validate the new functionality, including field validation, timestamp adjustments, and edge cases.

## Consequences

### Positive
-   **Enables Age-Perspective Memory Writing**: Users can now create memories with the authentic temporal context of a specific life stage.
-   **Ensures Temporal Consistency**: System-generated timestamps automatically reflect the user's chosen age perspective, providing a consistent experience.
-   **Enriches User Profiles**: The user model is now more comprehensive, paving the way for future features like memory timelines and age-based analytics.
-   **Supports New Use Cases**: Opens up applications in therapeutic memory preservation, detailed autobiographical writing, and historical documentation.

### Negative
-   **Increased Complexity**: The `User` model and timestamp generation logic are now more complex.
-   **Potential for Confusion**: Users need to understand how `birth_date` and `delta_year` interact to use the feature correctly. Clear UI and documentation are essential.

### Neutral
-   The changes required updates across multiple components of the user management system.
-   Existing user data and functionality remain unaffected due to the optional nature of the new fields and backward-compatible integration.
