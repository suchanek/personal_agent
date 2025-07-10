# ADR 004: Multi-User Path Configuration

*   **Status:** Implemented
*   **Date:** 2025-07-04

## Context and Problem Statement

The initial multi-user implementation was flawed. User-specific data paths were not being generated correctly, leading to all users sharing the same default data directories. This was caused by two main issues:

1.  **Incorrect Environment Configuration:** The `.env` file defined paths for storage and knowledge directories without incorporating the `${USER_ID}` variable.
2.  **Hardcoded Default Parameters:** The `AgnoPersonalAgent` constructor had hardcoded default paths (`./data/agno`, `./data/knowledge`) that did not respect the user ID provided at runtime.

This defeated the purpose of multi-user support and posed a significant data privacy risk.

## Decision Drivers

*   The critical need to ensure proper data isolation between different users.
*   The requirement for a simple, clean, and maintainable solution that avoids over-engineering.
*   The goal of making the system's path management logic clear and directly tied to the user ID.

## Decision Outcome

A simple and direct solution was implemented to fix the multi-user path configuration.

### 1. Environment Variable Fix

The paths in the `.env` file were updated to correctly include the `${USER_ID}` variable, making them user-specific by default.

**Before:**
```
AGNO_STORAGE_DIR=${DATA_DIR}/${STORAGE_BACKEND}
AGNO_KNOWLEDGE_DIR=${DATA_DIR}/knowledge
```

**After:**
```
AGNO_STORAGE_DIR=${DATA_DIR}/${STORAGE_BACKEND}/${USER_ID}
AGNO_KNOWLEDGE_DIR=${DATA_DIR}/knowledge/${USER_ID}
```

### 2. Simplified Dynamic Path Logic

The `AgnoPersonalAgent.__init__` method was updated to:

*   Use the centrally defined settings (`AGNO_STORAGE_DIR`, `AGNO_KNOWLEDGE_DIR`) as the default values instead of hardcoded strings.
*   Contain simple, direct logic to construct user-specific paths if a custom `user_id` is provided at runtime, overriding the default from the environment.

This approach eliminated the need for redundant helper functions and made the path generation logic explicit and easy to understand within the agent's constructor.

## Consequences

### Positive

*   **True Multi-User Support:** The fix ensures that each user has a completely isolated data directory, preventing data cross-contamination.
*   **Simplified and Clean Code:** The solution is direct, easy to maintain, and avoids unnecessary complexity or helper functions.
*   **Improved Data Privacy:** Proper user isolation is now enforced at the filesystem level.
*   **Scalable Foundation:** This clean implementation provides a solid foundation for future multi-tenant features.

### Negative

*   None. The fix was a necessary correction that simplified the codebase while improving its correctness and security.
