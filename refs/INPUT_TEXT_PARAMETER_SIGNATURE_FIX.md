# Input Text Parameter Signature Fix

**Date:** 2025-01-15
**Type:** Bug Fix
**Component:** Memory Storage System
**Status:** Completed

## Problem

After refactoring `streamlit_helpers.py`, memory storage via the dashboard failed with:
```
❌ Failed to store fact: Error updating memory: AgentMemoryManager.store_user_memory()
got an unexpected keyword argument 'input_text'
```

## Root Cause

The `input_text` parameter was added to track the source/context of memory storage operations (e.g., "Direct fact storage", "REST API", "Imported memory"). However, the parameter signature was inconsistent across the memory storage call chain:

**Parameter Flow:**
```
StreamlitMemoryHelper.add_memory(input_text="...")
  ↓
memory_functions.store_user_memory(agent, ..., input_text="...")
  ↓
agent.memory_manager.store_user_memory(..., input_text="...")  ❌ MISSING!
```

**Signature Mismatch:**
- ✅ `StreamlitMemoryHelper.add_memory()` - Had `input_text` parameter
- ✅ `memory_functions.store_user_memory()` - Had `input_text` parameter
- ❌ `AgentMemoryManager.store_user_memory()` - **Missing** `input_text` parameter

The parameter was being passed through the call chain but rejected at the final destination.

## Call Sites Using input_text

1. **Dashboard Memory Import** (`dashboard_memory_management.py:734`, `777`):
   ```python
   memory_helper.add_memory(
       memory_text=content_text,
       topics=topics,
       input_text=f"Imported memory (confidence: {confidence}, proxy: {is_proxy})",
   )
   ```

2. **Direct Fact Storage** (`streamlit_tabs.py:536`):
   ```python
   memory_helper.add_memory(
       memory_text=fact_input.strip(),
       topics=topic_list,
       input_text="Direct fact storage",
   )
   ```

3. **REST API Storage** (`rest_api.py:304`, `406`):
   ```python
   memory_helper.add_memory(
       memory_text=content,
       topics=topics,
       input_text="REST API",
   )
   ```

## Solution

Added the `input_text` parameter to `AgentMemoryManager.store_user_memory()` signature:

**File:** `src/personal_agent/core/agent_memory_manager.py:105`

```python
async def store_user_memory(
    self,
    content: str = "",
    topics: Union[List[str], str, None] = None,
    user=None,
    confidence: float = 1.0,
    is_proxy: bool = False,
    proxy_agent: Optional[str] = None,
    input_text: Optional[str] = None,  # ← Added
) -> MemoryStorageResult:
    """Store information as a user memory in BOTH local SQLite and LightRAG graph systems.

    Args:
        content: The information to store as a memory
        topics: Optional list of topics/categories for the memory (None = auto-classify)
        user: Optional User instance for delta_year timestamp adjustment
        confidence: Confidence score for the memory (0.0-1.0)
        is_proxy: Whether this memory was created by a proxy agent
        proxy_agent: Name of the proxy agent that created this memory
        input_text: Optional input text describing the source/context (currently unused, for future use)

    Returns:
        MemoryStorageResult: Structured result with detailed status information
    """
```

## Implementation Notes

- **Parameter is currently unused**: The `input_text` field is accepted but not stored in the memory object
- **Future-proofing**: Added for forward compatibility if we decide to track memory sources
- **No behavioral change**: Memory storage logic remains unchanged
- **Minimal fix**: Only modified the signature to prevent the error

## Alternative Considered

We considered removing `input_text` from all callers since it's not currently stored. However, this would require changes across multiple files and potentially discard future-useful tracking information. The minimal fix was preferred.

## Impact

- ✅ Memory storage via dashboard now works correctly
- ✅ Memory import from JSON/CSV works
- ✅ Direct fact storage works
- ✅ REST API memory storage works
- ✅ No changes to existing memory storage behavior

## Testing

Verified memory storage works through:
1. Dashboard memory management interface
2. Direct fact storage forms
3. Memory import functionality

## Files Modified

1. `src/personal_agent/core/agent_memory_manager.py` - Added `input_text` parameter to `store_user_memory()`

## Related Components

- Memory storage system (`AgentMemoryManager`)
- Streamlit memory helpers (`StreamlitMemoryHelper`)
- Memory functions (`memory_functions.py`)
- Dashboard memory management UI
- REST API memory endpoints

## Future Enhancements

If we want to actually track the source/context of memories:
1. Add `input_text` field to the `Memory` model/dataclass
2. Store it in the SQLite database schema
3. Display it in the UI alongside confidence and proxy information
4. Include it in memory export/import operations
