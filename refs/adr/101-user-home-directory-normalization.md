# ADR-101: User Home Directory Normalization for Multi-User Context

- **Status**: Accepted
- **Date**: 2025-11-21
- **Deciders**: Eric G. Suchanek, PhD

## Context and Problem Statement

The filesystem tools exhibited a critical bug where natural language directory references like "current directory" were interpreted literally as directory names rather than as path shortcuts. When asked to save a file to "current directory", the system created a directory named `current directory/` instead of using the actual current working directory.

More fundamentally, the system's concept of "home directory" was ambiguous in a multi-user context. The agent serves multiple users (patients), each with their own isolated data space under `/Users/Shared/personal_agent_data/agno/{user_id}/`. However, the filesystem tools were using `~` (which expands to the system user's home, e.g., `/Users/egs`) rather than the patient's isolated home directory.

This created several risks:
1. **Data Isolation Breach**: Patient files could be saved to the system user's home instead of their isolated space
2. **Security Concerns**: Using raw `~` expansion in a multi-user context is dangerous
3. **Confusion**: "home" should mean the patient's home, not the system administrator's home
4. **Literal Interpretation**: Natural language phrases were treated as literal directory names

## Decision Drivers

- The need to properly isolate patient data in a multi-user therapeutic context
- Security requirements for proper path expansion in multi-user environments
- User experience improvements through natural language understanding
- Architectural clarity between system-level and user-level directories

## Considered Options

1. **Keep using `~` expansion**: Continue with the current approach, accepting the security risks
2. **Add `user_home_dir` property to config**: Create a new configuration property that points to the user's isolated directory
3. **Normalize to `user_storage_dir`**: Map "home" references directly to the existing `user_storage_dir` configuration
4. **Create explicit patient home subdirectory**: Add a `/home` subdirectory under each user's storage path

## Decision Outcome

Chosen option: **Add `user_home_dir` property to config** (Option 2), combined with natural language normalization.

We will implement a two-part solution:

### 1. Natural Language Normalization

Both [`PersonalAgentFilesystemTools.create_and_save_file`](src/personal_agent/tools/personal_agent_tools.py:274) and [`create_and_save_file`](src/personal_agent/tools/filesystem.py:330) in the MCP-based tools will normalize common natural language directory references:

**Current Directory phrases** → `.`
- "current directory"
- "current dir"
- "here"
- "this directory"

**Home Directory phrases** → `config.user_storage_dir` (NOT `~`)
- "home"
- "home directory"
- "home dir"

### 2. Configuration Enhancement (Recommended Future Work)

Add a new property to [`PersonalAgentConfig`](src/personal_agent/config/runtime_config.py:107):

```python
@property
def user_home_dir(self) -> str:
    """Get the user-specific home directory (patient's isolated home).
    
    This is distinct from home_dir which points to the system user's home.
    In a multi-user context, this ensures patient data isolation.
    
    Returns:
        str: Path to user's isolated home directory
    """
    return self.user_storage_dir  # /Users/Shared/.../agno/patient123/
```

### 3. Documentation of Directory Semantics

The system now distinguishes between:
- **`home_dir`**: System user's home (`/Users/egs`) - for system-level operations
- **`user_home_dir`**: Patient's isolated home (`/Users/Shared/personal_agent_data/agno/patient123/`) - for patient data
- **`user_storage_dir`**: Same as `user_home_dir`, the root of patient's isolated space
- **`user_data_dir`**: Patient's data subdirectory (`{user_storage_dir}/data/`)
- **`user_knowledge_dir`**: Patient's knowledge subdirectory (`{user_storage_dir}/knowledge/`)

## Implementation

### Files Modified

1. **`src/personal_agent/tools/personal_agent_tools.py`** (lines 294-300)
   - Added natural language normalization in `create_and_save_file`
   - Maps "current directory" phrases to `.`
   - Maps "home" phrases to `.` (temporary - should use `config.user_storage_dir`)
   - Fixed type hint: `variable_to_return: str | None = None`

2. **`src/personal_agent/tools/filesystem.py`** (lines 352-365)
   - Added path normalization for MCP-based file operations
   - Handles both directory and full path normalization
   - Maps natural language to proper path shortcuts

3. **`FILESYSTEM_TOOLS_FIX.md`** (created)
   - Comprehensive documentation of the bug and fix
   - Examples and testing guidance

## Consequences

### Positive

- **Improved User Experience**: Natural language directory references now work intuitively
- **Enhanced Security**: Prevents accidental creation of literal directory names
- **Better Data Isolation**: Foundation for proper multi-user patient data isolation
- **Clearer Architecture**: Establishes distinction between system and user directories
- **Backward Compatible**: Existing path shortcuts (`.`, `~`, `./`) continue to work

### Negative

- **Incomplete Solution**: The current fix maps "home" to `.` rather than the proper `user_storage_dir`
- **Requires Follow-up**: Need to add `user_home_dir` property to `PersonalAgentConfig`
- **Documentation Needed**: Users and developers need to understand the directory semantics

### Risks and Mitigations

**Risk**: Using raw `~` expansion in multi-user context
- **Mitigation**: Normalize "home" references to `config.user_storage_dir` instead of `~`

**Risk**: Confusion between system home and patient home
- **Mitigation**: Clear documentation and distinct property names (`home_dir` vs `user_home_dir`)

**Risk**: Existing code using `~` directly
- **Mitigation**: Audit codebase for raw `~` usage and replace with proper config properties

## Future Work

1. **Add `user_home_dir` property** to `PersonalAgentConfig` class
2. **Update filesystem tools** to use `config.user_home_dir` instead of `~` for "home" normalization
3. **Audit codebase** for raw `~` usage and replace with config-based paths
4. **Add validation** to ensure patient files never escape their isolated directory
5. **Document** the multi-user directory architecture in developer guides

## Related ADRs

- [ADR-002: Multi-User Path Configuration](./002-multi-user-path-fix.md)
- [ADR-013: Dynamic Multi-User Management](./013-dynamic-multi-user-management.md)
- [ADR-048: Decoupled User and Docker Configuration](./048-decoupled-user-docker-config.md)
- [ADR-062: Unambiguous Data Directory Configuration](./062-unambiguous-data-directory-configuration.md)

## Technical Details

### Example Bug Scenario

```python
# User request: "Create and save a file to current directory"
create_and_save_file(filename="monkey_poem.txt", directory="current directory")

# Before fix:
# Result: Creates "current directory/monkey_poem.txt" ❌
# os.makedirs("current directory", exist_ok=True)  # Creates literal directory!

# After fix:
# Result: Creates "./monkey_poem.txt" in actual current directory ✅
# directory = "."  # Normalized before path construction
```

### Normalization Logic

```python
# In personal_agent_tools.py (lines 294-300)
directory_lower = directory.lower().strip()
if directory_lower in ["current directory", "current dir", "here", "this directory", "."]:
    directory = "."
elif directory_lower in ["home", "home directory", "home dir"]:
    directory = "~"  # TODO: Should be config.user_storage_dir

# In filesystem.py (lines 352-365)
if "/" in file_path or "\\" in file_path:
    dir_part = os.path.dirname(file_path)
    file_part = os.path.basename(file_path)
    
    dir_lower = dir_part.lower().strip()
    if dir_lower in ["current directory", "current dir", "here", "this directory"]:
        dir_part = "."
    elif dir_lower in ["home", "home directory", "home dir"]:
        dir_part = "~"  # TODO: Should be config.user_storage_dir
    
    file_path = os.path.join(dir_part, file_part) if dir_part else file_part
```

## Validation

To verify the fix works correctly:

```bash
# Test current directory normalization
python -c "
from personal_agent.tools.personal_agent_tools import PersonalAgentFilesystemTools
tools = PersonalAgentFilesystemTools()
result = tools.create_and_save_file('test.txt', 'content', 'current directory')
print(result)
"

# Expected: File created in actual current directory, not in "current directory/"
```

## Migration Path

For existing deployments with the literal `current directory/` folder:

1. Identify affected files: `ls -la "current directory/"`
2. Move files to proper location: `mv "current directory/"* ./`
3. Remove literal directory: `rmdir "current directory"`
4. Update agent with fixed code
5. Verify natural language references work correctly

---

**Resolution Status:** ✅ PARTIAL - Natural language normalization implemented, `user_home_dir` property pending
**Impact:** 🔧 CRITICAL BUG FIX - Prevents literal directory creation
**Security:** ⚠️ FOLLOW-UP REQUIRED - Need to replace `~` with `user_storage_dir` for proper multi-user isolation