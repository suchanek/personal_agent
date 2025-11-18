# Memory Tool Parameter Confusion - Root Cause & Fix

**Date:** 2025-11-18
**Issue:** LLM was calling `list_all_memories(query=charlie.brown)` causing validation errors
**Root Cause:** Tool signature confusion between `list_all_memories()` (no params) and `query_memory(query, limit)` (with params)
**Solution:** Enhanced documentation, explicit instructions, and parameter validation

---

## The Problem

### Observed Error
```
ValidationError: list_all_memories(query=charlie.brown)
Unexpected keyword argument [query]
```

The LLM was trying to call `list_all_memories()` with a `query` parameter, which this function doesn't accept.

### Root Cause
Two memory tools with similar names but different signatures:

```python
# This takes NO parameters
async def list_all_memories(self) -> str:
    """Returns simplified list of all memories"""

# This DOES take parameters
async def query_memory(self, query: str, limit: Union[int, None] = None) -> str:
    """Searches memories by query"""
```

The LLM was confusing these tools because:
1. Both have "memory" in the name
2. Tool instructions weren't explicit enough about parameters
3. Docstrings didn't clearly warn against passing parameters

---

## The Fix (3-Part Solution)

### Part 1: Enhanced Tool Docstrings

**File:** `src/personal_agent/core/agno_agent.py` (Lines 720-794)

Added explicit warnings in docstrings:

```python
async def list_all_memories(self, **kwargs) -> str:
    """List all memories in a simple, user-friendly format.

    ⚠️ IMPORTANT: This tool takes NO parameters. Use list_all_memories() with no arguments.
    Do NOT pass query, limit, or any other parameters to this function.

    **Usage:** list_all_memories()

    **Do NOT use:** list_all_memories(query=...), list_all_memories(limit=...)

    Use query_memory(query, limit) instead if you need to search for specific memories.
    """
```

Key improvements:
- ⚠️ Warning icon and strong language
- Shows correct vs incorrect usage
- Redirects to correct tool for searches
- Clear consequences

### Part 2: Enhanced Agent Instructions

**File:** `src/personal_agent/core/agent_instruction_manager.py` (Lines 287-323)

Added critical parameter rules at the top of memory instructions:

```python
**⚠️ CRITICAL PARAMETER RULES - DO NOT IGNORE:**
- list_all_memories() takes NO PARAMETERS. Call with empty parentheses: list_all_memories()
- get_all_memories() takes NO PARAMETERS. Call with empty parentheses: get_all_memories()
- ❌ NEVER: list_all_memories(query=...), list_all_memories(limit=...), list_all_memories(anything)
- ❌ NEVER: get_all_memories(query=...), get_all_memories(limit=...), get_all_memories(anything)
- ✅ ONLY use query_memory(query, limit) when searching for specific memories
- If you accidentally pass parameters to list_all_memories/get_all_memories, the call will FAIL
```

Also added clear pattern matching:
```
- Keywords for list_all_memories(): 'list', 'show', 'what memories', 'how many', 'summary'
- Keywords for get_all_memories(): 'detailed', 'full', 'complete', 'everything about'
- Keywords for query_memory(): 'about', 'remember', 'search', 'find', 'specific'
```

### Part 3: Runtime Parameter Validation

**File:** `src/personal_agent/core/agno_agent.py` (Lines 741-752, 779-790)

Added **kwargs validation to catch parameter errors at runtime:

```python
# Validate that no parameters were passed
if kwargs:
    invalid_params = ", ".join(kwargs.keys())
    raise ValueError(
        f"❌ ERROR: list_all_memories() does NOT accept parameters.\n"
        f"Invalid parameters passed: {invalid_params}\n"
        f"✅ Correct usage: list_all_memories() with NO parameters\n"
        f"❌ Wrong usage: list_all_memories(query=...), list_all_memories(limit=...)\n"
        f"\n"
        f"If you need to SEARCH for specific memories, use query_memory(query, limit) instead.\n"
        f"If you need detailed information, use get_all_memories() instead."
    )
```

Benefits:
- Catches errors early
- Provides helpful error message
- Suggests correct alternative
- Clear, actionable feedback to LLM

---

## Memory Tool Reference

### `list_all_memories()`
- **Parameters:** NONE
- **Returns:** Simplified list of all memories
- **When to use:** General memory queries, summaries, quick lists
- **Example trigger phrases:** "What memories do you have?", "List all memories", "Memory summary"

### `get_all_memories()`
- **Parameters:** NONE
- **Returns:** Detailed list with timestamps, topics, IDs
- **When to use:** User explicitly asks for full details
- **Example trigger phrases:** "Show detailed memories", "Complete memory information"

### `query_memory(query: str, limit: int = None)`
- **Parameters:** YES - query (required), limit (optional)
- **Returns:** Filtered/searched memories matching query
- **When to use:** Search for specific memories, filter by topic
- **Example trigger phrases:** "Do you remember...", "Tell me about my...", "Search memories for..."

---

## Testing & Verification

### How to Verify the Fix

1. **Check tool docstrings:**
   ```bash
   grep -A 20 "def list_all_memories" src/personal_agent/core/agno_agent.py
   ```
   Should show ⚠️ warnings and parameter usage

2. **Check instructions:**
   ```bash
   grep -A 10 "CRITICAL PARAMETER RULES" src/personal_agent/core/agent_instruction_manager.py
   ```
   Should show strong warnings about parameters

3. **Test parameter validation:**
   ```python
   # This should raise ValueError with helpful message
   await agent.list_all_memories(query="test")
   ```

### Expected Behavior After Fix

**Before:** LLM tries `list_all_memories(query=charlie.brown)` → Confusing validation error

**After:**
- LLM sees clear instructions: "list_all_memories() takes NO PARAMETERS"
- If LLM still tries with parameters → Clear error message explaining the mistake
- Error message suggests: "Use query_memory(query, limit) instead"

---

## Files Modified

### 1. `src/personal_agent/core/agno_agent.py`
- Lines 720-756: Enhanced `list_all_memories()` docstring + validation
- Lines 758-794: Enhanced `get_all_memories()` docstring + validation

### 2. `src/personal_agent/core/agent_instruction_manager.py`
- Lines 287-323: Added critical parameter rules and clearer pattern matching

### 3. Related Files (Not Modified)
- `src/personal_agent/tools/memory_functions.py` - Actual tool implementations
- `src/personal_agent/core/agent_memory_manager.py` - Memory manager

---

## Why This Approach is Better

### Alternative Approaches Considered

1. **Rename tools** (e.g., `list_all()`, `get_all()`)
   - ❌ Too disruptive, breaks existing code
   - ✅ Rejected

2. **Add separate tool for each** (e.g., `list_summaries()`, `list_detailed()`)
   - ❌ Increases tool count, more confusion
   - ✅ Rejected

3. **Just add docstrings** (what we did)
   - ✅ Non-breaking, clear to LLM
   - ✅ Helpful error messages
   - ✅ Guides LLM to correct tool
   - ✅ **Selected**

4. **Add runtime validation** (what we added)
   - ✅ Catches errors immediately
   - ✅ Provides actionable feedback
   - ✅ **Selected**

---

## Impact & Performance

### Query Performance
- **No negative impact** - validation only runs if parameters passed
- **Faster error messages** - better feedback than cryptic Pydantic errors
- **LLM learns faster** - clear instructions reduce mistakes

### Memory Usage
- **No overhead** - simple string check in kwargs
- **Minimal docstring increase** - ~100 bytes per tool

### User Experience
- **Better error messages** - instead of "Unexpected keyword argument"
- **Self-correcting** - LLM learns from error messages
- **Improved confidence** - clear instructions reduce LLM confusion

---

## Future Enhancements

### Potential Improvements

1. **Tool description generation**
   - Auto-generate clearer tool descriptions for Agno
   - Explicitly list "accepts no parameters" in tool metadata

2. **Tool grouping hints**
   - Add metadata to group related tools
   - Help LLM understand tool families

3. **Example-based learning**
   - Add more examples to instructions
   - Show correct/incorrect patterns

4. **Monitoring**
   - Track how often parameter validation fails
   - Adjust instructions based on failure patterns

---

## Rollback Plan

If issues arise, this fix is safe to roll back:

```bash
# Revert changes
git diff src/personal_agent/core/agno_agent.py
git diff src/personal_agent/core/agent_instruction_manager.py

# The fixes are purely additive (docstrings + validation)
# No structural changes, backward compatible
```

---

## Summary

### Problem
LLM confused `list_all_memories()` (no params) with `query_memory()` (with params)

### Solution
Three-part approach:
1. ✅ Enhanced docstrings with ⚠️ warnings
2. ✅ Explicit agent instructions about parameters
3. ✅ Runtime validation with helpful error messages

### Result
- LLM gets clear guidance
- Errors are caught early with actionable feedback
- Self-correcting system that learns from mistakes
- No breaking changes, fully backward compatible

---

## References

**Files Modified:**
- `src/personal_agent/core/agno_agent.py`
- `src/personal_agent/core/agent_instruction_manager.py`

**Related Documentation:**
- `refs/MEMORY_RETRIEVAL_PERFORMANCE_OPTIMIZATION.md` - Fast path optimization

**Commit:** [Link when created]

**Author:** Claude Code
**Date:** 2025-11-18
