# ADR-034: SmolLM2 Optimization Fix

**Date**: 2025-07-23
**Status**: Accepted

## Context

The agent's instruction manager contained a hardcoded optimization for models perceived as "small" (like SmolLM2). If the generated instruction prompt exceeded 1000 characters, the system would discard the carefully constructed, sophisticated instructions and replace them with a much simpler, hardcoded version. 

This behavior had several negative consequences:

*   It overrode the user-selected instruction sophistication level (`MINIMAL`, `CONCISE`, `STANDARD`, etc.).
*   It removed detailed guidance and nuanced rules, potentially degrading the agent's performance.
*   The check was applied to all models, not just SmolLM2, leading to unintended instruction simplification for larger, more capable models.

## Decision

We decided to remove the aggressive SmolLM2 optimization logic from the `AgentInstructionManager`. The 1000-character length check and the subsequent instruction replacement have been eliminated.

A basic validation check has been retained to log a warning if instructions are exceptionally short (under 100 characters), which could indicate a potential issue, but it does not alter the instructions.

## Consequences

### Positive

*   **Instruction Integrity**: The agent now respects the selected instruction level at all times, ensuring that the full sophistication of the prompts is preserved.
*   **Improved Performance**: By using the intended detailed instructions, the agent's reasoning and performance are expected to be more reliable and aligned with the configured personality and rules.
*   **Model Agnostic**: The instruction pipeline is now consistent across all models, removing the problematic special casing.

### Negative

*   None identified. The original problem was based on a flawed assumption that smaller models require drastically simplified instructions.

## Technical Details

The following change was made in `src/personal_agent/core/agent_instruction_manager.py`:

```diff
- # Special handling for SmolLM2 instruct model - use optimized instructions
- # Check if we're dealing with SmolLM2 and use model-specific instructions
- if len(instructions) > 1000:  # Lower threshold for small models
-     logger.warning(f"Instructions are long ({len(instructions)} chars) - creating SmolLM2-optimized version")
-     # SmolLM2-Instruct optimized instructions - much simpler
-     instructions = f"""You are a helpful AI assistant talking to {self.user_id}..."""
+ # Basic validation - only check for extremely short instructions
+ if len(instructions) < 100:
+     logger.warning(f"Instructions seem too short: '{instructions[:200]}...'")
```

---
