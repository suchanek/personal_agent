# Switch-User PERSAG_HOME Directory Fix

## Problem Summary

The `switch-user.py` script was not working correctly after the refactoring that moved LightRAG docker directories from the project root to `~/.persag` (PERSAG_HOME). The script was still trying to use the project root directory structure instead of the new `~/.persag` location for docker services.

## Root Cause Analysis

### Primary Issue
The `LightRAGManager` class in `src/personal_agent/core/lightrag_manager.py` was hardcoding docker directory paths relative to the `project_root` parameter:

```python
# OLD - Incorrect approach
self.lightrag_server_dir = self.project_root / "lightrag_server"
self.lightrag_memory_dir = self.project_root / "lightrag_memory_server"
```

This caused the manager to look for docker directories in the project root instead of `~/.persag`.

### Secondary Issue
The `UserManager` class was using `PERSAG_ROOT` instead of `DATA_DIR` for the user registry, causing inconsistencies in user data management.

## Solution Implementation

### 1. LightRAGManager Fix (`src/personal_agent/core/lightrag_manager.py`)

**Before:**
```python
def __init__(self, project_root: str = None):
    self.project_root = Path(project_root) if project_root else Path.cwd()
    self.lightrag_server_dir = self.project_root / "lightrag_server"
    self.lightrag_memory_dir = self.project_root / "lightrag_memory_server"
```

**After:**
```python
def __init__(self, project_root: str = None):
    # Import settings to get the correct PERSAG_HOME-based paths
    from personal_agent.config.settings import LIGHTRAG_SERVER_DIR, LIGHTRAG_MEMORY_DIR
    
    # Use the centralized configuration paths from PERSAG_HOME
    self.lightrag_server_dir = Path(LIGHTRAG_SERVER_DIR)
    self.lightrag_memory_dir = Path(LIGHTRAG_MEMORY_DIR)
    
    # Keep project_root for backward compatibility, but it's no longer used for docker paths
    self.project_root = Path(project_root) if project_root else Path.cwd()
```

**Key Changes:**
- Now imports and uses `LIGHTRAG_SERVER_DIR` and `LIGHTRAG_MEMORY_DIR` from centralized settings
- These settings are properly configured to point to `~/.persag/lightrag_server` and `~/.persag/lightrag_memory_server`
- Maintains backward compatibility by keeping the `project_root` parameter
- Added documentation clarifying that `project_root` is deprecated for docker paths

### 2. UserManager Fix (`src/personal_agent/core/user_manager.py`)

**Before:**
```python
from personal_agent.config import PERSAG_ROOT, STORAGE_BACKEND
self.data_dir = data_dir or PERSAG_ROOT
self.registry = UserRegistry(data_dir, storage_backend)
```

**After:**
```python
from personal_agent.config import DATA_DIR, STORAGE_BACKEND
self.data_dir = data_dir or DATA_DIR
self.registry = UserRegistry(self.data_dir, self.storage_backend)
```

**Key Changes:**
- Uses `DATA_DIR` instead of `PERSAG_ROOT` for consistent data directory handling
- Properly passes the configured data directory to `UserRegistry`
- Ensures user registry and user data are stored in the correct location

## Configuration Architecture

The fix leverages the existing centralized configuration in `src/personal_agent/config/settings.py`:

```python
# Per-user configuration base directory for docker configs and user state
LIGHTRAG_SERVER_DIR = os.path.join(PERSAG_HOME, "lightrag_server")
LIGHTRAG_MEMORY_DIR = os.path.join(PERSAG_HOME, "lightrag_memory_server")
```

Where `PERSAG_HOME` defaults to `~/.persag` but can be overridden via environment variable.

## Testing Results

### Test Scenarios Verified

1. **User Creation and Switching:**
   ```bash
   python switch-user.py alice --user-name "Alice Smith" --no-restart
   python switch-user.py bob --user-name "Bob Johnson"
   python switch-user.py test_user --no-restart
   ```

2. **Docker Directory Verification:**
   ```bash
   ls -la ~/.persag/
   # Shows: lightrag_server, lightrag_memory_server directories
   ```

3. **Configuration Updates:**
   ```bash
   cat ~/.persag/lightrag_server/.env | grep USER_ID
   cat ~/.persag/lightrag_memory_server/.env | grep USER_ID
   cat ~/.persag/env.userid
   ```

### Test Results

✅ **User Creation**: Successfully creates new users with proper directory structure  
✅ **User Switching**: Correctly switches between users with complete configuration updates  
✅ **LightRAG Integration**: Docker services use `~/.persag` directory structure  
✅ **Configuration Updates**: USER_ID properly updated in docker .env files  
✅ **Persistence**: User changes persisted to `~/.persag/env.userid`  
✅ **Service Restart**: LightRAG services restart with correct user context  

## Directory Structure

After the fix, the system correctly uses:

```
~/.persag/
├── env.userid                    # Current user persistence
├── users_registry.json          # User registry database
├── lightrag_server/              # LightRAG main server docker config
│   ├── .env                     # Contains USER_ID=<current_user>
│   └── docker-compose.yml
├── lightrag_memory_server/       # LightRAG memory server docker config
│   ├── .env                     # Contains USER_ID=<current_user>
│   └── docker-compose.yml
└── backups/                     # User data backups
```

## Impact and Benefits

### Fixed Issues
- ✅ Switch-user script now works with `~/.persag` directory structure
- ✅ Docker services correctly restart with new user context
- ✅ User isolation properly maintained across switches
- ✅ Configuration consistency between user registry and LightRAG services

### Maintained Compatibility
- ✅ Existing user data and configurations preserved
- ✅ All switch-user script features continue to work
- ✅ Backward compatibility maintained for existing installations

### Architecture Improvements
- ✅ Centralized configuration usage (single source of truth)
- ✅ Proper separation of concerns between user data and docker configs
- ✅ Clear deprecation path for legacy parameters

## Files Modified

1. **`src/personal_agent/core/lightrag_manager.py`**
   - Updated `__init__()` method to use centralized PERSAG_HOME paths
   - Added proper imports for configuration settings
   - Deprecated `project_root` parameter for docker paths

2. **`src/personal_agent/core/user_manager.py`**
   - Fixed data directory configuration to use `DATA_DIR`
   - Corrected parameter passing to `UserRegistry`
   - Updated documentation for deprecated parameters

## Future Considerations

1. **Parameter Cleanup**: The `project_root` parameter in `LightRAGManager` can be removed in a future version once all callers are updated.

2. **Configuration Validation**: Consider adding validation to ensure `PERSAG_HOME` directory structure exists and is properly configured.

3. **Migration Support**: For users upgrading from project-root docker configs, consider adding automatic migration support.

## Conclusion

This fix successfully resolves the switch-user functionality with the new `~/.persag` directory structure while maintaining full backward compatibility and improving the overall architecture through better use of centralized configuration.
