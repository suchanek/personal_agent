# Configuration System Refactoring

## Overview

This document describes the major refactoring of the Personal Agent configuration management system, replacing scattered environment variables with a centralized, thread-safe `PersonalAgentConfig` singleton class.

## Problem Statement

The previous system had several critical issues:

### 1. **Environment Variable Race Conditions**
```python
# OLD PROBLEMATIC PATTERN:
# settings.py loads at import time
LLM_MODEL = get_env_var("LLM_MODEL", "qwen3:4b")  # Cached immediately

# Later, in streamlit_config.py:
args = parse_args()
if args.provider:
    os.environ["PROVIDER"] = args.provider  # TOO LATE! Already cached
```

### 2. **Scattered State Management**
- Configuration spread across multiple modules
- No single source of truth
- Difficult to track what changed and when
- Hard to switch providers dynamically

### 3. **Lack of Observability**
- No way to know when configuration changed
- No callbacks or events for reactive updates
- Impossible to coordinate updates across components

### 4. **Threading Issues**
- No thread safety
- Race conditions in multi-threaded environments (Streamlit, Flask)
- Unpredictable state in concurrent scenarios

## Solution: PersonalAgentConfig Singleton

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PersonalAgentConfig                     │
│                    (Singleton)                           │
├─────────────────────────────────────────────────────────┤
│  Core State:                                             │
│  - user_id          (from ~/.persag/env.userid)         │
│  - provider         (ollama, lm-studio, openai)         │
│  - model            (provider-specific)                  │
│  - agent_mode       (single, team)                       │
│  - use_remote       (bool)                               │
│  - debug_mode       (bool)                               │
│  - use_mcp          (bool)                               │
│                                                           │
│  Service URLs:                                            │
│  - ollama_url, remote_ollama_url                         │
│  - lmstudio_url, remote_lmstudio_url                     │
│  - openai_url                                             │
│  - lightrag_url, lightrag_memory_url                     │
│                                                           │
│  Features:                                                │
│  - Thread-safe with RLock                                │
│  - Change notification callbacks                         │
│  - Configuration snapshots                               │
│  - Environment variable sync                             │
└─────────────────────────────────────────────────────────┘
```

### Key Features

#### 1. **Thread-Safe Singleton**
```python
from personal_agent.config.runtime_config import get_config

config = get_config()  # Always returns the same instance
# Thread-safe operations with internal RLock
```

#### 2. **Provider-Aware Model Management**
```python
# Automatically sets correct model for provider
config.set_provider("lm-studio")
# model is now "qwen3-4b-instruct-2507-mlx"

config.set_provider("ollama")
# model is now "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K"
```

#### 3. **Change Notifications**
```python
def on_provider_change(key, old_value, new_value):
    print(f"Provider changed: {old_value} -> {new_value}")
    # Reinitialize agents, update UI, etc.

config.register_callback(on_provider_change)
config.set_provider("lm-studio")  # Callback fires
```

#### 4. **User Management Integration**
```python
# Properly integrates with existing user system
config.set_user_id("john_doe", persist=True)
# 1. Sets USER_ID environment variable
# 2. Writes to ~/.persag/env.userid
# 3. Refreshes user-dependent paths
# 4. Notifies callbacks
```

#### 5. **Configuration Snapshots**
```python
# Immutable snapshot for safe caching
snapshot = config.snapshot()
# Can be safely passed around without worrying about changes
```

## Migration Guide

### Before (Environment Variables)

```python
# OLD: Scattered, race-prone
import os
from personal_agent.config import PROVIDER, LLM_MODEL

provider = os.getenv("PROVIDER", "ollama")
model = os.getenv("LLM_MODEL", "qwen3:4b")

# Change provider (doesn't work reliably)
os.environ["PROVIDER"] = "lm-studio"
# Other modules may have already cached the old value!
```

### After (PersonalAgentConfig)

```python
# NEW: Centralized, thread-safe
from personal_agent.config.runtime_config import get_config

config = get_config()
provider = config.provider
model = config.model

# Change provider (works reliably)
config.set_provider("lm-studio")
# All modules see the change immediately
# Callbacks notify interested parties
```

## Updated Components

### 1. **streamlit_config.py**
- Now uses `get_config()` to set initial configuration from command-line args
- No more environment variable manipulation at module level
- Proper ordering: config first, then imports

**Key Changes:**
```python
# Before:
os.environ["PROVIDER"] = args.provider
os.environ["LLM_MODEL"] = default_model

# After:
config = get_config()
config.set_provider(args.provider, auto_set_model=True)
```

### 2. **reasoning_team.py**
- CLI uses config for provider management
- No more global PROVIDER variable modifications
- Uses `config.provider` and `config.model` throughout

**Key Changes:**
```python
# Before:
global PROVIDER
PROVIDER = args.provider

# After:
config = get_config()
config.set_provider(args.provider, auto_set_model=True)
```

### 3. **AgentModelManager**
- New method: `create_model_from_config()`
- Recommended way to create models for consistency

**Key Changes:**
```python
# Before:
model = AgentModelManager.create_model_for_provider(
    provider=PROVIDER,
    model_name=LLM_MODEL,
    use_remote=use_remote
)

# After:
model = AgentModelManager.create_model_from_config()
# Automatically uses config.provider, config.model, config.use_remote
```

## Usage Examples

### Basic Configuration Access
```python
from personal_agent.config.runtime_config import get_config

config = get_config()

# Read configuration
print(f"Provider: {config.provider}")
print(f"Model: {config.model}")
print(f"User: {config.user_id}")
print(f"Mode: {config.agent_mode}")
```

### Switching Providers
```python
config = get_config()

# Switch to LM Studio (auto-sets model)
config.set_provider("lm-studio")
# Now: provider="lm-studio", model="qwen3-4b-instruct-2507-mlx"

# Switch to specific model
config.set_provider("ollama", auto_set_model=False)
config.set_model("llama3.1:8b")
```

### Remote Endpoints
```python
config = get_config()

# Use remote endpoints
config.set_use_remote(True)

# Get effective URL for current provider
url = config.get_effective_base_url()
# Returns remote URL for current provider
```

### Change Notifications
```python
def reinitialize_agent(key, old_value, new_value):
    if key in ("provider", "model"):
        print(f"Reinitializing agent with {new_value}")
        # ... agent reinitialization logic

config = get_config()
config.register_callback(reinitialize_agent)

# Any provider/model change will trigger reinitialization
config.set_provider("lm-studio")
```

### Custom Configuration Values
```python
config = get_config()

# Store custom values
config.set("api_timeout", 30)
config.set("max_retries", 3)

# Retrieve with defaults
timeout = config.get("api_timeout", 60)
retries = config.get("max_retries", 5)
```

## Command-Line Integration

### Streamlit App
```bash
# Set provider via command line
poe serve-persag --provider lm-studio

# Multiple options
poe serve-persag --provider lm-studio --remote --debug
```

### Team CLI
```bash
# Set provider for team
poe team --provider lm-studio

# With remote endpoints
poe team --provider ollama --remote
```

## Benefits

### 1. **Eliminates Race Conditions**
- Configuration set BEFORE any module imports
- No more cached environment variable issues
- Guaranteed consistency across all modules

### 2. **Single Source of Truth**
- All configuration in one place
- Easy to inspect current state
- Clear API for all configuration operations

### 3. **Observable Changes**
- Know exactly when configuration changes
- React to changes with callbacks
- Coordinate updates across components

### 4. **Thread Safety**
- Safe for use in Streamlit (multi-threaded)
- Safe for use in Flask REST API
- Proper locking prevents race conditions

### 5. **Better Testability**
- Can reset configuration between tests
- Easy to mock and inject
- Clear initialization and cleanup

### 6. **User Management Integration**
- Proper persistence to ~/.persag/env.userid
- Automatic path refreshing on user switch
- Consistent with existing user system

## Testing

Run the example to see it in action:
```bash
python examples/config_example.py
```

This demonstrates:
- Provider switching
- Model management
- Change callbacks
- Configuration snapshots
- Custom values

## Future Enhancements

### Potential Additions:
1. **Configuration Validation**
   - Validate model/provider compatibility
   - Check URL reachability
   - Verify service availability

2. **Configuration Persistence**
   - Save/load configuration to file
   - User-specific configuration profiles
   - Configuration history/undo

3. **Hot Reloading**
   - Watch configuration files for changes
   - Automatic reload on external changes
   - Graceful reconfiguration

4. **Advanced Observability**
   - Configuration change history
   - Audit log of changes
   - Performance metrics

## Migration Checklist

- [x] Create `PersonalAgentConfig` singleton class
- [x] Add thread safety with RLock
- [x] Implement change notification callbacks
- [x] Integrate with user management system
- [x] Update `streamlit_config.py`
- [x] Update `reasoning_team.py`
- [x] Update `AgentModelManager`
- [x] Add `create_model_from_config()` method
- [x] Create example script
- [x] Document refactoring
- [ ] Update remaining modules gradually
- [ ] Add configuration validation
- [ ] Add comprehensive tests

## Backward Compatibility

The refactoring maintains backward compatibility:

1. **Environment Variables Still Work**
   - Config reads from env vars on initialization
   - Config writes to env vars on changes
   - Existing code using env vars will still work

2. **Gradual Migration**
   - Old and new systems can coexist
   - Modules can be migrated incrementally
   - No breaking changes to existing APIs

3. **Legacy Support**
   - `settings.py` still provides legacy constants
   - Imports from `personal_agent.config` still work
   - Gradual deprecation path

## Conclusion

The `PersonalAgentConfig` refactoring solves critical state management issues in the Personal Agent system. By providing a centralized, thread-safe, observable configuration system, it eliminates race conditions, improves reliability, and enables proper dynamic provider switching.

The refactoring is backward compatible and allows for gradual migration, making it a safe and practical improvement to the codebase.
