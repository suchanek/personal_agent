# 010: AntiDuplicateMemory Class Refactoring for Polymorphic Compatibility

*   **Status:** Accepted
*   **Date:** 2025-07-11

## Context and Problem Statement

The `AntiDuplicateMemory` class, which inherits from `agno.memory.v2.memory.Memory`, had method signatures that diverged from its parent class. This divergence caused issues with polymorphism, making it difficult to use `AntiDuplicateMemory` instances where a `Memory` object was expected. Specifically, the `add_user_memory`, `create_user_memories`, and `delete_user_memory` methods had different parameter lists and return types, breaking the Liskov Substitution Principle. This inconsistency could lead to runtime errors and made the codebase harder to maintain and reason about.

## Decision

We decided to refactor the method signatures in `AntiDuplicateMemory` to be compatible with the `Memory` base class. The primary goal was to ensure that an `AntiDuplicateMemory` object could be used wherever a `Memory` object is type-hinted, without causing unexpected behavior.

The following changes were made:

1.  **Signature Alignment**: The parameters for `add_user_memory`, `create_user_memories`, and `delete_user_memory` were updated to match the parent `Memory` class.
2.  **Optional Parameters**: `user_id` was changed to be an optional parameter (`Optional[str] = None`) in the method signatures. If not provided, it defaults to the value from the application's configuration. This provides flexibility while maintaining compatibility.
3.  **New `refresh_from_db` Parameter**: A `refresh_from_db: bool = True` parameter was added to the method signatures. This allows controlling the internal state-refreshing behavior of the `AntiDuplicateMemory` class without breaking the parent class's contract.
4.  **Return Type Correction**: The return type of `delete_user_memory` was changed from `bool` to `None`, and the method was updated to raise exceptions on failure, mirroring the behavior of the parent class.
5.  **Intentional Deviation**: The return type of `add_user_memory` remains `Optional[str]` (compared to `str` in the parent). This is a deliberate and accepted deviation, as returning `None` is the mechanism by which this subclass signals that a duplicate memory was detected and rejected, a core feature of its design.

A new test suite, `test_method_signature_fixes.py`, was created to verify these changes, ensure polymorphic compatibility, and prevent future regressions.

## Consequences

### Positive

*   **Improved Polymorphism**: `AntiDuplicateMemory` can now be reliably used wherever a `Memory` instance is expected, improving code robustness and flexibility.
*   **Enhanced Maintainability**: The consistent API across the memory hierarchy makes the code easier to understand, maintain, and extend.
*   **Increased Robustness**: Aligning exception handling and return types with the base class leads to more predictable behavior.
*   **Dedicated Verification**: The new test suite ensures that the class adheres to the intended contract and protects against future breaking changes.

### Negative

*   None. The changes are internal to the class and its interaction with the base class, improving the overall design without introducing breaking changes to the external API.
