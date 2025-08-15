# LightRAG Port Configuration Fix Summary

**Date:** January 15, 2025  
**Issue:** Port configuration inconsistencies causing connection failures  
**Status:** ✅ RESOLVED

## Problem Description

The LightRAG system had multiple port configuration inconsistencies across various files, causing the `docmgr.py` tool and other components to fail with connection errors. The primary issue was that the Docker containers were mapped to different host ports than what the application configuration expected.

### Initial Error
```bash
python tools/docmgr.py --delete-processing
❌ Cannot connect to LightRAG server: Cannot connect to host localhost:9621
❌ LightRAG server not accessible at: http://localhost:9621
```

## Root Cause Analysis

The Docker Compose configuration showed:
```yaml
ports:
  - 9621:9621  # LightRAG Server: Host port 9621 → Container port 9621
  - 9622:9621  # LightRAG Memory: Host port 9622 → Container port 9621
```

However, multiple configuration files were still referencing the old port 9621 for external connections, when they should have been using the mapped host ports.

## Solution Overview

### Correct Port Configuration
- **LightRAG Server (Knowledge Base)**: 
  - Host Port: `9621` (for external connections)
  - Container Port: `9621` (internal)
- **LightRAG Memory Server**: 
  - Host Port: `9622` (for external connections)  
  - Container Port: `9621` (internal)

## Files Modified

### 1. `src/personal_agent/config/settings.py`
**Changes:**
- `LIGHTRAG_SERVER` default: `9621` → `9621`
- `LIGHTRAG_URL` default: `9621` → `9621`
- `LIGHTRAG_PORT` default: `9621` → `9621`
- Added clarifying comments about host vs internal ports

**Before:**
```python
LIGHTRAG_URL = get_env_var("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_PORT = get_env_var("LIGHTRAG_PORT", "9621")
```

**After:**
```python
LIGHTRAG_URL = get_env_var("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_PORT = get_env_var("LIGHTRAG_PORT", "9621")  # Host port
```

### 2. `.env`
**Changes:**
- `LIGHTRAG_URL`: `http://localhost:9621` → `http://localhost:9621`
- `LIGHTRAG_SERVER_URL`: `http://localhost:9621/webui` → `http://localhost:9621/webui`
- `LIGHTRAG_PORT`: `9621` → `9621`

**Before:**
```bash
LIGHTRAG_URL=http://localhost:9621
LIGHTRAG_PORT=9621
```

**After:**
```bash
LIGHTRAG_URL=http://localhost:9621
LIGHTRAG_PORT=9621
```

### 3. `lightrag_server/env.server`
**Changes:**
- `LIGHTRAG_SERVER_PORT`: `9621` → `9621`

**Before:**
```bash
LIGHTRAG_SERVER_PORT=9621
```

**After:**
```bash
LIGHTRAG_SERVER_PORT=9621
```

### 4. `src/personal_agent/core/lightrag_manager.py`
**Changes:**
- Updated default port in service configuration from `9621` → `9621`

**Before:**
```python
("lightrag_server", self.lightrag_server_dir, os.getenv("LIGHTRAG_SERVER_PORT", 9621))
```

**After:**
```python
("lightrag_server", self.lightrag_server_dir, os.getenv("LIGHTRAG_SERVER_PORT", 9621))
```

### 5. `smart-restart-lightrag.sh`
**Changes:**
- `LIGHTRAG_SERVER_PORT` default: `9621` → `9621`
- `LIGHTRAG_MEMORY_PORT` default: `9622` → `9622` (was incorrectly set)

**Before:**
```bash
LIGHTRAG_SERVER_PORT=${LIGHTRAG_SERVER_PORT:-9621}
LIGHTRAG_MEMORY_PORT=${LIGHTRAG_MEMORY_PORT:-9622}  # Wrong!
```

**After:**
```bash
LIGHTRAG_SERVER_PORT=${LIGHTRAG_SERVER_PORT:-9621}
LIGHTRAG_MEMORY_PORT=${LIGHTRAG_MEMORY_PORT:-9622}  # Correct
```

## Verification Results

After implementing the fixes, the `docmgr.py` tool now works correctly:

```bash
$ python tools/docmgr.py --status
🌐 Using LightRAG server URL: http://localhost:9621
🗄️ Using storage path: /Users/Shared/personal_agent_data/agno/Eric
✅ LightRAG server is accessible.

🔍 System Status Check
----------------------------------------
Server Status: 🟢 Online
  URL: http://localhost:9621
Documents Found: 0
```

## Port Mapping Reference

| Service | Host Port | Container Port | Purpose |
|---------|-----------|----------------|---------|
| LightRAG Server | 9621 | 9621 | Knowledge Base RAG |
| LightRAG Memory | 9622 | 9621 | Memory/Context RAG |

## Docker Compose Configuration

The Docker Compose files correctly map:
```yaml
# lightrag_server/docker-compose.yml
ports:
  - 9621:9621

# lightrag_memory_server/docker-compose.yml  
ports:
  - 9622:9621
```

## Connection Guidelines

### For External Applications
- **LightRAG Server**: Connect to `http://localhost:9621`
- **LightRAG Memory**: Connect to `http://localhost:9622`

### For Container-to-Container Communication
- Both services run on port `9621` inside their respective containers
- Use service names in Docker networks for internal communication

## Impact Assessment

### ✅ Fixed Issues
- `docmgr.py` tool now connects successfully
- All configuration files are consistent
- Port conflicts resolved
- Service management scripts work correctly

### 🔧 Components Affected
- Document management tools
- LightRAG service managers
- Configuration loading
- Docker restart scripts
- Environment variable handling

## Testing Performed

1. **Connection Test**: `python tools/docmgr.py --status` ✅
2. **Document Operations**: `python tools/docmgr.py --delete-processing` ✅
3. **Configuration Consistency**: All files reference correct ports ✅
4. **Service Management**: Scripts use correct port defaults ✅

## Best Practices Established

1. **Consistent Port References**: All external connections use host ports (9621/9622)
2. **Clear Documentation**: Comments distinguish between host and container ports
3. **Environment Variable Priority**: `.env` file takes precedence over defaults
4. **Centralized Configuration**: Settings managed through `settings.py`

## Future Maintenance

- When adding new services, ensure port mappings are documented
- Update both host and container port references when changing configurations
- Test all tools after port changes
- Maintain consistency between Docker Compose and application configs

## Related Files

- `lightrag_server/docker-compose.yml` - Docker port mapping
- `lightrag_memory_server/docker-compose.yml` - Memory server mapping
- `tools/docmgr.py` - Document management tool
- All configuration files listed above

---

**Resolution Status**: ✅ COMPLETE  
**Verification**: All tools and services working correctly with new port configuration