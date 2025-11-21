# Filesystem Tools Fix: "current directory" Literal Interpretation Bug

## Issue Summary

When asked to create and save a file to "current directory", the agent literally interpreted "current directory" as a directory name instead of understanding it as a reference to the working directory (`.` or `./`).

### Example of the Bug

User request: "Create and save a file to current directory"
Result: Created directory named `current directory/` and saved file there
Expected: Save file to the actual current working directory

## Root Cause

The [`create_and_save_file`](src/personal_agent/tools/personal_agent_tools.py:274) method in both:
- `src/personal_agent/tools/personal_agent_tools.py` (PersonalAgentFilesystemTools)
- `src/personal_agent/tools/filesystem.py` (MCP-based tools)

These methods accept a `directory` parameter but did not normalize natural language references before processing them. When the LLM passed `directory="current directory"` as a literal string, the code:

1. Treated it as a directory name
2. Created `os.path.join("current directory", filename)` → `"current directory/filename.txt"`
3. Called `os.makedirs("current directory", exist_ok=True)` which created the literal directory

## Solution Implemented

Added natural language normalization to both filesystem tool implementations:

### In `personal_agent_tools.py` (lines 294-300)

```python
# Normalize natural language directory references
directory_lower = directory.lower().strip()
if directory_lower in ["current directory", "current dir", "here", "this directory", "."]:
    directory = "."
elif directory_lower in ["home", "home directory", "home dir"]:
    directory = "~"
```

### In `filesystem.py` (lines 352-365)

```python
# Normalize natural language path references
# Extract directory and filename if path contains common phrases
if "/" in file_path or "\\" in file_path:
    dir_part = os.path.dirname(file_path)
    file_part = os.path.basename(file_path)
    
    # Normalize directory part
    dir_lower = dir_part.lower().strip()
    if dir_lower in ["current directory", "current dir", "here", "this directory"]:
        dir_part = "."
    elif dir_lower in ["home", "home directory", "home dir"]:
        dir_part = "~"
    
    # Reconstruct path
    file_path = os.path.join(dir_part, file_part) if dir_part else file_part
```

## Normalized Phrases

The fix now recognizes and normalizes these natural language references:

**Current Directory:**
- "current directory"
- "current dir"
- "here"
- "this directory"
- "." (already worked)

**Home Directory:**
- "home"
- "home directory"
- "home dir"
- "~" (already worked)

## Testing

To verify the fix works:

```python
# Before fix:
create_and_save_file(filename="test.txt", directory="current directory")
# Result: Creates "current directory/test.txt" ❌

# After fix:
create_and_save_file(filename="test.txt", directory="current directory")
# Result: Creates "./test.txt" in actual current directory ✅
```

## Additional Fix

Also fixed a type hint issue in `personal_agent_tools.py`:
- Changed `variable_to_return: str = None` to `variable_to_return: str | None = None`

## Files Modified

1. `src/personal_agent/tools/personal_agent_tools.py` - Lines 294-300, 280
2. `src/personal_agent/tools/filesystem.py` - Lines 352-365

## Impact

This fix ensures that when users or the LLM use natural language to refer to common directory locations, the filesystem tools correctly interpret them as path references rather than literal directory names.