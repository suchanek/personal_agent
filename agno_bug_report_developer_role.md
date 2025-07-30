# Bug Report: Invalid 'developer' Role in OpenAI Chat Model

## Summary
The Agno framework's OpenAI chat model incorrectly maps the `system` role to `developer`, causing API errors when using Team coordination with OpenAI-compatible endpoints.

## Error Details
**Error Message:**
```
API status error from OpenAI API: Error code: 400 - {'error': "'messages' array must only contain objects with a 'role' field that is in [user, assistant, system, tool]. Got 'developer'."}
```

**Stack Trace Location:**
- File: `agno/models/openai/chat.py`
- Lines: 89-95
- Function: `default_role_map`

## Root Cause
In `agno/models/openai/chat.py`, the `default_role_map` incorrectly maps system messages:

```python
# Current (INCORRECT) mapping
default_role_map = {
    "system": "developer",  # ← This is wrong!
    "user": "user",
    "assistant": "assistant",
    "tool": "tool", 
    "model": "assistant",
}
```

**Problem:** OpenAI's Chat Completions API only accepts these roles: `['user', 'assistant', 'system', 'tool']`. The `developer` role is not valid and causes a 400 Bad Request error.

## When This Occurs
- Using Agno Teams with `mode="coordinate"` or other team coordination modes
- When the team leader sends system messages to OpenAI-compatible endpoints
- Affects both OpenAI API and LMStudio/local OpenAI-compatible servers
- Direct agent calls work fine (they don't trigger the team coordination system)

## Reproduction Steps
1. Create an Agno Team with OpenAI model
2. Set team mode to "coordinate" 
3. Run team with any user input
4. Team coordination sends system message with 'developer' role
5. OpenAI API rejects the request with 400 error

## Expected Behavior
System messages should be sent with `role: "system"` to comply with OpenAI API specifications.

## Proposed Fix
Change the role mapping in `agno/models/openai/chat.py`:

```python
# CORRECTED mapping
default_role_map = {
    "system": "system",  # Fix: should be "system", not "developer"
    "user": "user",
    "assistant": "assistant", 
    "tool": "tool",
    "model": "assistant",
}
```

## Workaround
Users can override the role mapping in their code:

```python
model = create_openai_model()
if hasattr(model, 'role_map') and model.role_map is None:
    model.role_map = {
        "system": "system",  # Override the incorrect default
        "user": "user",
        "assistant": "assistant",
        "tool": "tool", 
        "model": "assistant",
    }
```

## Impact
- **Severity:** High - Breaks team functionality with OpenAI models
- **Scope:** All users using Agno Teams with OpenAI-compatible models
- **Workaround:** Available but requires manual intervention

## Environment
- Agno Framework: Latest version (as of January 2025)
- Python: 3.12
- OpenAI API: Current specification
- LMStudio: Compatible endpoints

## Additional Notes
This appears to be a misunderstanding of OpenAI's API specification. The `developer` role may have been confused with other AI providers or an outdated API version. The OpenAI Chat Completions API has consistently used `system` for system messages.

## References
- [OpenAI Chat Completions API Documentation](https://platform.openai.com/docs/api-reference/chat/create)
- OpenAI API Role Specification: `user`, `assistant`, `system`, `tool`
