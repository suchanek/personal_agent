# User Registry Architecture Fix and Multi-User System Improvements

**Date:** November 14, 2025  
**Version:** v0.8.76.dev  
**Author:** Eric G. Suchanek, PhD

## Executive Summary

This document describes a comprehensive refactoring of the Personal Agent's multi-user system architecture that resolved critical bugs in user registry management, Docker service coordination, and user switching workflows. The changes establish clear separation between shared data storage and user-specific configurations, implement proper user ID normalization, and eliminate stale configuration file issues.

## Problem Statement

The multi-user system suffered from several architectural issues:

1. **Incorrect Registry Location**: `UserRegistry` was creating registry files in user-specific directories (`~/.persagent/<user_id>/`) instead of the shared data location (`/Users/Shared/personal_agent_data/`), causing:
   - Multiple conflicting registry files
   - User switching failures
   - Dashboard and CLI seeing different user lists
   - Stale data synchronization issues

2. **Docker Service Hanging**: Docker containers would hang indefinitely during startup due to the `--wait` flag blocking until services reported healthy status, which never occurred reliably

3. **Redundant Consistency Checks**: Docker consistency validation was running 3 times per user switch operation, causing unnecessary delays

4. **Case-Sensitive User Matching**: User IDs were case-sensitive, allowing duplicate users like "Paula" and "paula" to be created

5. **Missing Directory Creation**: Dashboard user creation didn't create the required directory structure, unlike the CLI tool

6. **Stale Registry Files**: Multiple registry files existed in wrong locations from previous incorrect implementations

## Architecture Overview

### Storage Hierarchy

The system uses two distinct storage locations with clear separation of concerns:

```
PERSAG_ROOT (Default: /Users/Shared/personal_agent_data/)
├── users_registry.json          # Single source of truth for all users
├── agno/                         # User data storage
│   ├── <user_id>/               # Per-user directories
│   │   ├── knowledge/           # Source files for semantic KB
│   │   ├── rag_storage/         # LightRAG knowledge graph
│   │   ├── inputs/              # Knowledge inputs
│   │   ├── memory_rag_storage/  # LightRAG memory graph
│   │   ├── memory_inputs/       # Memory inputs
│   │   └── lancedb/             # Vector embeddings

PERSAG_HOME (Default: ~/.persagent/)
├── current_user.json            # Active user tracking
├── lightrag_server/             # Knowledge Docker configs
│   ├── docker-compose.yml
│   └── env.server
└── lightrag_memory_server/      # Memory Docker configs
    ├── docker-compose.yml
    └── env.memory_server
```

### Key Principles

1. **Single Registry**: One `users_registry.json` file at `PERSAG_ROOT/users_registry.json`
2. **Shared Data**: All user data directories under `PERSAG_ROOT/agno/`
3. **User Configs**: User-agnostic Docker configs in `PERSAG_HOME/`
4. **Normalized IDs**: User IDs are lowercase, dot-separated (e.g., "john.doe")
5. **Display Names**: Separate `user_name` field for proper capitalization

## Implementation Details

### 1. UserRegistry Refactoring

**File:** `src/personal_agent/core/user_registry.py`

**Changes:**
- Changed default `data_dir` from `config.persag_home` to `config.persag_root`
- Registry file now always at: `{PERSAG_ROOT}/users_registry.json`
- Added case-insensitive user lookup in `get_user()` and `remove_user()`
- Implemented user ID normalization: lowercase + space-to-dot conversion
- Added regex validation for user IDs (alphanumeric, dots, hyphens, underscores)
- Changed default `cognitive_state` from 50 to 100
- **CRITICAL**: `add_user()` now returns the normalized user_id instead of boolean

**Before:**
```python
def __init__(self, data_dir: str = None, storage_backend: str = None):
    config = get_config()
    # Used persag_home - WRONG for shared registry
    self.data_dir = Path(data_dir or config.persag_home)
    self.registry_file = self.data_dir / "users_registry.json"

def add_user(self, user_id: str, ...) -> bool:
    # ... normalization code ...
    return True  # Just returned success/failure
```

**After:**
```python
def __init__(self, data_dir: str = None, storage_backend: str = None):
    config = get_config()
    # Use persag_root for shared registry location
    self.data_dir = Path(data_dir or config.persag_root)
    self.registry_file = self.data_dir / "users_registry.json"

def add_user(self, user_id: str, ...) -> Optional[str]:
    # ... normalization code ...
    return user_id  # Returns normalized user_id for directory creation
```

**User ID Normalization:**
```python
def add_user(self, user_id: str, user_name: str = None, ...):
    # Normalize user_id: lowercase, space-to-dot
    user_id = user_id.lower().strip()
    user_id = user_id.replace(" ", ".")
    
    # Validate format
    if not re.match(r'^[a-z0-9._-]+$', user_id):
        raise ValueError(f"Invalid user_id format: {user_id}")
    
    # Store with normalized ID but preserve display name
    user_dict = {
        "user_id": user_id,  # e.g., "eric.suchanek"
        "user_name": user_name or user_id,  # e.g., "Eric Suchanek"
        ...
    }
    return user_id  # Return for directory creation
```

**Example:**
- Input: user_id="Eric Suchanek", user_name="Eric Suchanek"
- Normalized: user_id="eric.suchanek", user_name="Eric Suchanek" 
- Directory: `/Users/Shared/personal_agent_data/agno/eric.suchanek/`

### 2. UserManager Simplification

**File:** `src/personal_agent/core/user_manager.py`

**Changes:**
- Removed complex `data_dir` and `storage_backend` parameter passing to `UserRegistry()`
- `UserRegistry` now uses its own defaults from global config
- Changed default `cognitive_state` to 100
- **CRITICAL**: `create_user()` now returns the normalized user_id from `add_user()`

**Before:**
```python
def __init__(self, data_dir: str = None, storage_backend: str = None, ...):
    self.data_dir = data_dir or DATA_DIR
    self.storage_backend = storage_backend or STORAGE_BACKEND
    # Passing user-specific paths to shared registry - WRONG
    self.registry = UserRegistry(data_dir=self.data_dir, 
                                  storage_backend=self.storage_backend)

def create_user(self, user_id: str, user_name: str, ...):
    if self.registry.add_user(...):
        return {
            "success": True,
            "user_id": user_id,  # Original, not normalized!
        }
```

**After:**
```python
def __init__(self, data_dir: str = None, storage_backend: str = None, ...):
    self.data_dir = data_dir or DATA_DIR
    self.storage_backend = storage_backend or STORAGE_BACKEND
    # UserRegistry uses its own defaults (PERSAG_ROOT)
    self.registry = UserRegistry()

def create_user(self, user_id: str, user_name: str, ...):
    normalized_user_id = self.registry.add_user(...)
    if normalized_user_id:
        return {
            "success": True,
            "user_id": normalized_user_id,  # Normalized for directory creation!
            "user_name": user_name,
        }
```

### 3. Docker Service Coordination Fix

**File:** `src/personal_agent/core/docker/user_sync.py`

**Changes:**
- Removed `--wait` flag from `docker-compose up` command
- Reduced timeout from 120s to 60s
- Added 2-second sleep for container initialization

**Before:**
```python
def start_docker_service(...):
    cmd = f"docker-compose -f {compose_file} up -d --wait"
    # Would hang indefinitely waiting for health checks
```

**After:**
```python
def start_docker_service(...):
    cmd = f"docker-compose -f {compose_file} up -d"
    result = subprocess.run(...)
    # Give containers time to initialize
    time.sleep(2)
```

### 4. Eliminating Redundant Checks

**File:** `src/personal_agent/core/docker_integration.py`

**Changes:**
- Removed redundant `check_docker_consistency()` call in `ensure_docker_consistency()`
- Function now performs single check instead of triple checking

**Before:**
```python
async def ensure_docker_consistency(...):
    # First check
    issues = await check_docker_consistency(user_id)
    
    if issues:
        # Fix issues...
        
        # Second check - REDUNDANT
        issues = await check_docker_consistency(user_id)
```

**After:**
```python
async def ensure_docker_consistency(...):
    # Single check and fix cycle
    issues = await check_docker_consistency(user_id)
    
    if issues:
        # Fix issues...
        # No redundant re-check
```

### 5. Dashboard Directory Creation

**File:** `src/personal_agent/streamlit/utils/user_utils.py`

**Changes:**
- Added directory creation logic to `create_new_user()`
- Creates all 6 required user directories
- Matches behavior of `switch-user.py` CLI tool
- **CRITICAL**: Uses normalized user_id from create_user result

**Added Code:**
```python
def create_new_user(...):
    # Create user in registry
    result = user_manager.create_user(...)
    
    if result.get("success"):
        # IMPORTANT: Use the normalized user_id returned from create_user
        normalized_user_id = result.get("user_id", user_id)
        
        # Get settings for the normalized user_id
        settings = refresh_user_dependent_settings(user_id=normalized_user_id)
        
        # Create directory structure
        user_dirs = [
            settings["AGNO_STORAGE_DIR"],
            settings["AGNO_KNOWLEDGE_DIR"],
            settings["LIGHTRAG_STORAGE_DIR"],
            settings["LIGHTRAG_INPUTS_DIR"],
            settings["LIGHTRAG_MEMORY_STORAGE_DIR"],
            settings["LIGHTRAG_MEMORY_INPUTS_DIR"],
        ]
        
        for dir_path in user_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
```

**Example:**
- User creates "Eric Suchanek" in dashboard
- `create_user()` returns `{"user_id": "eric.suchanek", "user_name": "Eric Suchanek"}`
- Directories created at: `/Users/Shared/personal_agent_data/agno/eric.suchanek/`

### 6. Switch User Script Simplification

**File:** `switch-user.py`

**Changes:**
- Removed complex `data_dir` construction for `UserManager`
- Now uses default configuration from global config
- **CRITICAL**: `create_user_if_needed()` now returns normalized user_id
- Main function uses normalized user_id for all operations

**Before:**
```python
def create_user_if_needed(user_id: str, ...) -> bool:
    result = user_manager.create_user(user_id, user_name, user_type)
    if result["success"]:
        return True
    return False

def main():
    create_user_if_needed(args.user_id, ...)
    create_user_directories(args.user_id)  # Wrong - not normalized!
    switch_user_context(args.user_id)
```

**After:**
```python
def create_user_if_needed(user_id: str, ...) -> tuple:
    """Returns: (success: bool, normalized_user_id: str)"""
    result = user_manager.create_user(user_id, user_name, user_type)
    if result["success"]:
        normalized_user_id = result.get("user_id", user_id)
        return True, normalized_user_id
    return False, user_id

def main():
    success, normalized_user_id = create_user_if_needed(args.user_id, ...)
    print_info(f"Using normalized user ID: {normalized_user_id}")
    create_user_directories(normalized_user_id)  # Correct - normalized!
    switch_user_context(normalized_user_id)
```

**Example:**
```bash
$ ./switch-user.py "Eric Suchanek"
Using normalized user ID: eric.suchanek
Creating directories for user 'eric.suchanek'
  • /Users/Shared/personal_agent_data/agno/eric.suchanek/
  • /Users/Shared/personal_agent_data/agno/eric.suchanek/knowledge/
  ...
```

### 7. Migration Tooling

**File:** `migrate_user_ids.py` (created)

A standalone migration script to normalize existing user IDs and rename directories:

```python
def normalize_user_id(user_id: str) -> str:
    """Normalize user_id to lowercase with dots."""
    return user_id.lower().replace(" ", ".")

def migrate_user_registry(registry_path: Path):
    """Update registry with normalized user_ids."""
    # Load registry
    # Normalize all user_ids
    # Preserve user_names for display
    # Save updated registry

def migrate_directories(persag_root: Path):
    """Rename user directories to match normalized IDs."""
    # Find agno/<old_user_id> directories
    # Rename to agno/<normalized_user_id>
```

## Data Model

### User Registry Schema

```json
{
  "users": [
    {
      "user_id": "eric.suchanek",      // Normalized: lowercase, dots
      "user_name": "Eric Suchanek",     // Display name: proper capitalization
      "user_type": "Admin",
      "created_at": "2025-11-14T12:01:10.567117",
      "last_seen": "2025-11-14T12:01:10.567120",
      "email": "suchanek@mac.com",
      "phone": "5135934522",
      "address": "4264 Meadow Creek CT\nLiberty Township, OH 45011",
      "birth_date": "1960-04-11",
      "delta_year": 0,
      "cognitive_state": 90,
      "gender": "Male",
      "npc": false
    }
  ]
}
```

### Current User Tracking

**File:** `~/.persagent/current_user.json`

```json
{
  "user_id": "eric.suchanek",
  "timestamp": "2025-11-14T12:01:10.567120"
}
```

## Testing and Validation

### Test Coverage

1. **User Registry Tests**:
   - Case-insensitive lookup
   - User ID normalization
   - Validation of invalid formats
   - Registry persistence

2. **User Manager Tests**:
   - Directory creation
   - User switching
   - Profile updates

3. **Docker Integration Tests**:
   - Service startup without hanging
   - User context synchronization
   - Environment variable updates

### Manual Validation Steps

1. **Verify Single Registry**:
   ```bash
   find /Users/Shared/personal_agent_data -name "users_registry.json"
   # Should return only: /Users/Shared/personal_agent_data/users_registry.json
   ```

2. **Test User Creation**:
   ```bash
   # Dashboard: Create user "Paula Smith"
   # Verify: user_id="paula.smith", user_name="Paula Smith"
   # Check directories created in agno/paula.smith/
   ```

3. **Test User Switching**:
   ```bash
   ./switch-user.py eric.suchanek
   # Verify: Services restart quickly
   # Verify: No hanging on docker-compose up
   ```

## Migration Guide

### For Existing Installations

1. **Backup Current Registry**:
   ```bash
   cp /Users/Shared/personal_agent_data/users_registry.json \
      /Users/Shared/personal_agent_data/users_registry.json.backup
   ```

2. **Update User Names** (if needed):
   - Edit registry to add proper `user_name` fields
   - Example: `"Eric" → user_id="eric", user_name="Eric Suchanek"`

3. **Run Migration Script**:
   ```bash
   python migrate_user_ids.py
   ```
   
   This will:
   - Normalize all user_ids to lowercase
   - Rename directories to match
   - Update current_user.json

4. **Delete Stale Registries**:
   ```bash
   # Remove any old registry files
   rm /Users/Shared/personal_agent_data/agno/users_registry.json
   rm ~/.persagent/.persag/users_registry.json
   ```

5. **Verify**:
   ```bash
   # Should show only one file
   find /Users/Shared/personal_agent_data -name "users_registry.json"
   find ~/.persagent -name "users_registry.json"
   ```

## Benefits

### 1. Single Source of Truth
- One registry file eliminates synchronization issues
- Dashboard and CLI always see the same users
- No more stale or conflicting data

### 2. Improved User Experience
- Case-insensitive user IDs prevent duplicates
- Proper display names (user_name) for UI
- Faster user switching (no redundant checks)

### 3. Robust Docker Management
- Services start reliably without hanging
- Consistent environment synchronization
- Proper timeout handling

### 4. Better Data Organization
- Clear separation: PERSAG_ROOT (data) vs PERSAG_HOME (configs)
- Predictable directory structure
- User-agnostic configuration management

### 5. Maintainability
- Simplified code with fewer parameters
- Global config as single source of truth
- Easier debugging with centralized registry

## Future Enhancements

### Potential Improvements

1. **User Groups**: Add support for user groups/organizations
2. **Access Control**: Implement role-based permissions
3. **Audit Trail**: Track user changes and access patterns
4. **Backup/Restore**: Automated registry backup and recovery
5. **Cloud Sync**: Optional cloud synchronization of user data
6. **Multi-Tenancy**: Support for isolated tenant environments

### Known Limitations

1. **Single Machine**: Current design assumes single-machine deployment
2. **File Locking**: No distributed locking for concurrent access
3. **Registry Size**: JSON registry scales to ~1000 users before performance degrades
4. **Migration**: Manual migration required for existing installations

## Related Documentation

- [CONFIGURATION_REFACTOR.md](./CONFIGURATION_REFACTOR.md) - Global config management
- [DOCKER_SMART_RESTART_IMPLEMENTATION_SUMMARY.md](./DOCKER_SMART_RESTART_IMPLEMENTATION_SUMMARY.md) - Docker service management
- [USER_SWITCHING.md](./USER_SWITCHING.md) - User switching workflows
- [ADR-096: Centralized Configuration Management](./adr/096-centralized-configuration-management.md)

## Conclusion

This refactoring establishes a solid foundation for multi-user support in the Personal Agent system. By centralizing the user registry at `PERSAG_ROOT`, implementing proper user ID normalization, fixing Docker service coordination issues, and eliminating redundant operations, the system now provides reliable, fast, and consistent user management across all interfaces.

The changes maintain backward compatibility where possible while providing a clear migration path for existing installations. The separation of concerns between shared data storage and user-specific configurations creates a more maintainable and scalable architecture.

---

**Implementation Date:** November 14, 2025  
**Version:** v0.8.76.dev  
**Status:** ✅ Complete
