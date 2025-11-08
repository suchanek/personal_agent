# ADR-099: Enhanced Memory Schema with Proxy Tracking and Confidence Scoring

**Date**: 2025-11-06  
**Status**: Accepted

## Context

The existing `UserMemory` class from the Agno framework provides a solid foundation for storing user memories. However, with the introduction of more complex agent interactions, especially in team-based scenarios where multiple agents might contribute to the user's memory, there is a need to track the origin of memories and their reliability. Additionally, for users experiencing cognitive decline, having a measure of memory quality becomes crucial for care management and understanding the progression of their condition. Specifically, we need to:

1.  **Attribute Memories**: Distinguish between memories created directly by the user and those created by proxy agents (e.g., a scheduler bot, a research agent).
2.  **Score Confidence**: Assign a confidence score to memories, reflecting the system's certainty about the information. This is particularly useful when:
    - Memories are inferred rather than explicitly stated
    - Users are experiencing cognitive decline and memory quality varies
    - Care providers need to assess the reliability of stored information
    - Tracking memory quality over time to identify patterns of decline

A direct modification of the upstream `UserMemory` class is undesirable as it would create a fork and complicate future updates. Therefore, a solution is needed that extends the existing schema without creating breaking changes.

## Decision

We will implement a **wrapper pattern** to extend the `UserMemory` class with additional fields for proxy tracking and confidence scoring. This will be achieved by creating a new `EnhancedUserMemory` class that composes the original `UserMemory` and adds the required metadata.

The new `EnhancedUserMemory` class will include:
- `base_memory`: An instance of the original `UserMemory` class.
- `confidence` (float): A score from 0.0 to 1.0 indicating the confidence in the memory's accuracy. The confidence value is determined by:
  - **Proxy memories**: Always 1.0 (full confidence, as they come from reliable agent sources)
  - **User memories with explicit confidence**: Preserved as specified
  - **User memories without explicit confidence**: Automatically mapped from the user's `cognitive_state` field (0-100 scale) to confidence (0.0-1.0 scale)
  - **Fallback**: 1.0 if no user or cognitive_state is available
- `is_proxy` (bool): A flag to indicate if the memory was created by a proxy agent (default: False).
- `proxy_agent` (Optional[str]): The name of the proxy agent that created the memory (default: None).

### Implementation Details

- **Wrapper Class**: The `EnhancedUserMemory` class is implemented in `src/personal_agent/core/enhanced_memory.py`. It delegates all standard `UserMemory` attribute access to the `base_memory` object, ensuring transparency for existing code.
- **Serialization**: The `to_dict()` and `from_dict()` methods are overridden to handle the serialization and deserialization of the enhanced fields.
- **Backward Compatibility**: The `from_dict()` method handles old memory formats that lack the new fields by providing sensible default values. This ensures that existing stored memories remain valid.
- **Memory Managers**: The `SemanticMemoryManager` and `AgentMemoryManager` handle `EnhancedUserMemory` objects. They store the full enhanced data and intelligently detect enhanced vs. standard memory formats during retrieval.
- **Helper Functions**: Utility functions like `ensure_enhanced_memory()` and `extract_user_memory()` facilitate conversion between the base and enhanced types.
- **Cognitive State Mapping**: The `AgentMemoryManager.store_user_memory()` method implements intelligent confidence scoring:
  ```python
  if is_proxy:
      effective_confidence = 1.0  # Proxy memories always reliable
  elif confidence != 1.0:
      effective_confidence = confidence  # Explicit value preserved
  else:
      # Map cognitive state (0-100) to confidence (0.0-1.0)
      if user and hasattr(user, "cognitive_state"):
          effective_confidence = user.cognitive_state / 100.0
      else:
          effective_confidence = 1.0  # Safe default
  ```
- **Testing**: Comprehensive tests in `tests/test_cognitive_state_confidence.py` validate:
  - Proxy memories receive confidence=1.0
  - Cognitive state values (0, 25, 50, 75, 100) correctly map to confidence (0.0, 0.25, 0.5, 0.75, 1.0)
  - Explicit confidence values are preserved
  - Missing user data defaults to confidence=1.0

## Consequences

### Positive

- **No Breaking Changes**: The wrapper pattern ensures that all existing code that consumes `UserMemory` objects continues to function without modification.
- **Extensibility**: The memory system can be extended with additional metadata without altering the core, upstream data structures.
- **Improved Data Richness**: The ability to track memory origin and confidence enables more sophisticated memory management and reasoning capabilities.
- **Clear Separation of Concerns**: The wrapper clearly separates the core memory structure from the application-specific enhancements.
- **Full Backward Compatibility**: The system can read and handle memories stored in the old format, allowing for a seamless, gradual migration.
- **Cognitive Decline Support**: Automatic mapping of cognitive state to confidence scores provides:
  - **Quality Indicators**: Each memory has a measure of reliability based on the user's mental state when created
  - **Temporal Tracking**: Confidence scores over time can reveal patterns of cognitive decline
  - **Care Management**: Care providers can identify periods of confusion or clarity
  - **Adaptive Responses**: The system can weight memories differently based on confidence when retrieving information
  - **Diagnostic Value**: Longitudinal confidence data may help detect early signs of cognitive changes
- **Intelligent Defaults**: The confidence scoring system adapts to available information:
  - Proxy memories maintain full confidence (reliable agent-generated content)
  - Explicit confidence values are respected (manual override when needed)
  - Cognitive state mapping provides automatic, meaningful defaults
  - Safe fallback ensures system stability

### Negative

- **Increased Complexity**: The introduction of a second memory class and the need for conversion logic adds a layer of complexity to the memory subsystem.
- **Storage Overhead**: Storing the additional fields slightly increases the size of each memory object in the database.
- **User Model Dependency**: The cognitive state mapping creates a dependency on the `User` model having a `cognitive_state` field (0-100 scale). However, the fallback mechanism ensures graceful degradation.
- **Interpretation Responsibility**: Confidence scores must be interpreted carefully - a low score indicates the user's cognitive state at creation time, not necessarily that the memory content is incorrect.

## Future Considerations

### Cognitive Decline Analytics
The confidence scoring system provides a foundation for advanced analytics:
- **Trend Analysis**: Plotting confidence scores over time to visualize cognitive trajectory
- **Pattern Recognition**: Identifying time-of-day or situational factors affecting cognitive state
- **Alert Systems**: Triggering notifications when confidence scores drop below thresholds
- **Comparative Analysis**: Comparing memory confidence across topics or memory types

### Clinical Integration
For users experiencing cognitive decline, the system could:
- **Export Reports**: Generate confidence score reports for healthcare providers
- **Medication Tracking**: Correlate confidence scores with medication schedules
- **Activity Correlation**: Link memory quality to daily activities, sleep, or nutrition
- **Baseline Establishment**: Track individual baselines for personalized decline detection

### Adaptive Memory Retrieval
The system could weight memory retrieval by confidence:
- High-confidence memories prioritized in responses
- Low-confidence memories flagged for verification
- Confidence thresholds configurable per user or use case
- Temporal weighting (recent low-confidence vs. older high-confidence memories)

---

```
