# Port 9623 Connection Error Fix

## Problem Summary

The PersonalAgent was trying to connect to port 9623 for the LightRAG memory server, but getting connection refused errors:

```
ERROR    PersonalAgent: ERROR 2025-07-16 11:35:42,701 -                                           agent_memory_manager.py:1291
         src.personal_agent.core.agent_memory_manager.store_graph_memory - Error storing memory                               
         in graph: Cannot connect to host localhost:9623 ssl:default [Multiple exceptions: [Errno                             
         61] Connect call failed ('::1', 9623, 0, 0), [Errno 61] Connect call failed                                          
         ('127.0.0.1', 9623)]
```

## Root Cause

**Port Configuration Mismatch**: The environment configuration was set to connect to port 9623, but the actual LightRAG memory server was running on port 9622.

### Docker Container Configuration
From `docker ps` output:
- `lightrag_memory` container: `0.0.0.0:9622->9621/tcp` (host port 9622 → container port 9621)
- `lightrag_pagent` container: `0.0.0.0:9621->9621/tcp` (host port 9621 → container port 9621)

### Previous Environment Configuration (INCORRECT)
```bash
LIGHTRAG_MEMORY_URL=http://localhost:9623
LIGHTRAG_MEMORY_PORT=9623
```

### Server Configuration
The `lightrag_memory_server/config.ini` shows:
```ini
[server]
port = 9622
```

## Solution

Updated the environment configuration files to match the actual running services:

### Fixed `.env` Configuration
```bash
# LightRAG Service URLs (for connecting to separate Docker containers)
LIGHTRAG_URL=http://localhost:9621
LIGHTRAG_SERVER_URL=http://localhost:9621/webui
LIGHTRAG_MEMORY_URL=http://localhost:9622

# Port configurations
PORT=9621
LIGHTRAG_PORT=9621
LIGHTRAG_MEMORY_PORT=9622
```

### Fixed `env.example` Configuration
Updated the template file to match the correct port configuration for future deployments.

## Verification

After the fix, the LightRAG memory server is accessible:
```bash
$ curl -s http://localhost:9622/health
{"status":"healthy","working_directory":"/app/data/rag_storage",...}
```

## Impact

This fix resolves the dual memory storage system where:
1. **Local SQLite storage** continues to work (was unaffected)
2. **LightRAG graph memory storage** now works correctly
3. Memory operations will now succeed with both local and graph storage instead of falling back to local-only

## Files Modified

1. `.env` - Updated port configurations
2. `env.example` - Updated template port configurations
3. `src/personal_agent/core/agent_memory_manager.py` - Fixed UserMemory attribute access

## Additional Fix: UserMemory Attribute Error

After fixing the port configuration, a secondary issue was discovered where the code was trying to access `memory.id` but the `UserMemory` object uses `memory.memory_id`. Fixed all three occurrences in the agent_memory_manager.py file.

## Prevention

To prevent this issue in the future:
1. Ensure Docker container port mappings match environment configuration
2. Verify service health endpoints after configuration changes
3. Check both `.env` and `env.example` files when updating port configurations
4. Use proper attribute names when accessing UserMemory objects (`memory_id` not `id`)
