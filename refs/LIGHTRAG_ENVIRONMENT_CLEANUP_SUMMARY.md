# LightRAG Environment Variable Cleanup Summary

**Date**: September 24, 2025  
**Issue**: Duplicate and conflicting environment variables in LightRAG Docker service configurations  
**Status**: ✅ RESOLVED  
**Impact**: Fixed model configuration inconsistencies preventing proper model updates

## Problem Description

The LightRAG Docker services were experiencing model configuration issues where users could not successfully change LLM and embedding models. Despite updating configurations, the services continued using old models due to duplicate and conflicting environment variable definitions within the Docker service `.env` files.

### Root Cause Analysis

The issue was caused by **duplicate environment variable definitions** within the same `.env` files, where later definitions would override earlier ones:

#### LightRAG Server Issues
- **Line 21**: `LLM_MODEL=qwen3:4b` and `EMBEDDING_MODEL=qwen3-embedding:4b`
- **Line 65**: `EMBEDDING_MODEL=nomic-embed-text` (overrode the previous setting!)

#### LightRAG Memory Server Issues  
- **Line 18**: `LLM_MODEL=qwen3:4b` and `EMBEDDING_MODEL=qwen3-embedding:4b`
- **Line 37**: `EMBEDDING_MODEL=nomic-embed-text` (overrode the previous setting!)

### Configuration Conflicts Identified

Multiple environment files contained inconsistent model definitions:
- `env.orig` files had `LLM_MODEL=qwen3:1.7b` and `EMBEDDING_MODEL=nomic-embed-text`
- `env.server` files had `LLM_MODEL=qwen3:4b` and `EMBEDDING_MODEL=qwen3-embedding:4b`
- `env.memory_server` files had mixed configurations
- Duplicate timeout settings causing configuration bloat

## Solution Implemented

### 1. Fixed ~/.persag Docker Service Configurations

**LightRAG Server (`~/.persag/lightrag_server/.env`)**:
- ✅ Updated `LLM_MODEL=qwen3:4b`
- ✅ Updated `EMBEDDING_MODEL=qwen3-embedding:4b`
- ✅ Removed duplicate `EMBEDDING_MODEL=nomic-embed-text` definition
- ✅ Removed duplicate timeout settings

**LightRAG Memory Server (`~/.persag/lightrag_memory_server/.env`)**:
- ✅ Updated `LLM_MODEL=qwen3:4b`
- ✅ Updated `EMBEDDING_MODEL=qwen3-embedding:4b`
- ✅ Removed duplicate `EMBEDDING_MODEL=nomic-embed-text` definition

### 2. Fixed Current Directory Environment Files

**LightRAG Server Files**:
- ✅ **`lightrag_server/env.orig`**: Updated models and removed duplicate EMBEDDING_MODEL
- ✅ **`lightrag_server/env.server`**: Removed duplicate EMBEDDING_MODEL and timeout settings

**LightRAG Memory Server Files**:
- ✅ **`lightrag_memory_server/env.memory_server`**: Removed duplicate EMBEDDING_MODEL
- ✅ **`lightrag_memory_server/env.save`**: Updated models and removed duplicate EMBEDDING_MODEL

### 3. Verification Results

**Docker Container Verification**:
```bash
# LightRAG Server Container
docker exec lightrag_pagent env | grep -E "(LLM_MODEL|EMBEDDING_MODEL)"
EMBEDDING_MODEL=qwen3-embedding:4b
LLM_MODEL=qwen3:4b

# LightRAG Memory Container  
docker exec lightrag_memory env | grep -E "(LLM_MODEL|EMBEDDING_MODEL)"
LLM_MODEL=qwen3:4b
EMBEDDING_MODEL=qwen3-embedding:4b
```

**Smart Restart Script Verification**:
- ✅ Both containers restarted successfully
- ✅ No port conflicts encountered
- ✅ Services running with correct model configurations

## Configuration Analysis

### smart-restart-lightrag.sh Script Behavior

The `smart-restart-lightrag.sh` script **correctly pulls configurations from `~/.persag`** as designed:

```bash
# Script Configuration (Correct)
PERSAG_HOME="${PERSAG_HOME:-$HOME/.persag}"
LIGHTRAG_SERVER_DIR="${LIGHTRAG_SERVER_DIR:-$PERSAG_HOME/lightrag_server}"
LIGHTRAG_MEMORY_DIR="${LIGHTRAG_MEMORY_DIR:-$PERSAG_HOME/lightrag_memory_server}"
```

The script was working as intended - the issue was with the configuration files themselves, not the script's path resolution.

### Environment Variable Hierarchy

The Docker services use this configuration hierarchy:
1. **docker-compose.yml** `env_file` directive points to `.env`
2. **`.env` files** are copied from their respective template files (`env.server`, `env.memory_server`)
3. **config.ini** files use environment variable substitution: `model = ${LLM_MODEL}`

## Files Modified

### ~/.persag Directory (Active Docker Services)
- `~/.persag/lightrag_server/.env` - Cleaned up duplicates, updated models
- `~/.persag/lightrag_memory_server/.env` - Cleaned up duplicates, updated models

### Current Working Directory (Template Files)
- `lightrag_server/env.orig` - Updated models, removed duplicates
- `lightrag_server/env.server` - Removed duplicates, cleaned timeout settings
- `lightrag_memory_server/env.memory_server` - Removed duplicates
- `lightrag_memory_server/env.save` - Updated models, removed duplicates

## Key Improvements

### 1. **Eliminated Configuration Conflicts**
- No more duplicate environment variable definitions
- Single source of truth for each configuration value
- Consistent model definitions across all files

### 2. **Streamlined Configuration**
- Removed redundant timeout setting blocks
- Cleaner, more maintainable configuration files
- Reduced configuration file complexity

### 3. **Verified Model Updates**
- Both Docker containers now use `qwen3:4b` for LLM
- Both Docker containers now use `qwen3-embedding:4b` for embedding
- Configuration changes properly propagated through restart process

## Best Practices Established

### 1. **Single Variable Definition**
- Each environment variable should be defined only once per file
- Later definitions override earlier ones (source of the original problem)
- Use comments to document variable purposes instead of multiple definitions

### 2. **Consistent Model Configuration**
- All environment files should use the same model definitions
- Template files should match active configurations
- Regular verification of Docker container environment variables

### 3. **Configuration Maintenance**
- Use `smart-restart-lightrag.sh` script for proper service restarts
- Verify model configurations after updates using `docker exec` commands
- Keep template files synchronized with active configurations

## Troubleshooting Guide

### Verify Current Model Configuration
```bash
# Check LightRAG Server models
docker exec lightrag_pagent env | grep -E "(LLM_MODEL|EMBEDDING_MODEL)"

# Check LightRAG Memory Server models
docker exec lightrag_memory env | grep -E "(LLM_MODEL|EMBEDDING_MODEL)"
```

### Update Model Configuration
1. **Edit the appropriate `.env` files** in `~/.persag/lightrag_server/` and `~/.persag/lightrag_memory_server/`
2. **Ensure no duplicate variable definitions** exist in the files
3. **Restart services** using `./smart-restart-lightrag.sh --all`
4. **Verify changes** using the docker exec commands above

### Common Issues
- **Models not updating**: Check for duplicate environment variable definitions
- **Service restart failures**: Ensure no port conflicts exist
- **Configuration inconsistencies**: Verify all template files match active configurations

## Impact and Benefits

### Immediate Benefits
- ✅ **Model updates now work correctly**: Users can successfully change LLM and embedding models
- ✅ **Configuration consistency**: All environment files have consistent, clean configurations
- ✅ **Eliminated conflicts**: No more duplicate variable definitions causing confusion
- ✅ **Verified functionality**: Docker containers confirmed running with correct models

### Long-term Benefits
- ✅ **Easier maintenance**: Cleaner configuration files are easier to understand and modify
- ✅ **Reduced errors**: Elimination of duplicates prevents future configuration conflicts
- ✅ **Better documentation**: Clear configuration structure for future reference
- ✅ **Improved reliability**: Consistent configuration reduces service restart issues

## Conclusion

The LightRAG environment variable cleanup successfully resolved the model configuration issues by:

1. **Identifying the root cause**: Duplicate environment variable definitions within `.env` files
2. **Implementing comprehensive fixes**: Updated all environment files across both `~/.persag` and current directory
3. **Verifying the solution**: Confirmed Docker containers are using correct models through direct verification
4. **Establishing best practices**: Created guidelines for future configuration maintenance

The `smart-restart-lightrag.sh` script was working correctly - the issue was with the configuration files it was reading. Users can now successfully update LLM and embedding models, and the changes will be properly applied to the running Docker services.

### Final Status
- **LLM Model**: `qwen3:4b` ✅
- **Embedding Model**: `qwen3-embedding:4b` ✅
- **Configuration Consistency**: All files synchronized ✅
- **Service Functionality**: Both containers running correctly ✅

The environment variable cleanup ensures that future model configuration changes will be applied correctly without conflicts or duplicate definitions interfering with the intended settings.
</content>
<task_progress>
- [x] Clean up duplicate environment variables in ~/.persag Docker service .env files
- [x] Update models in ~/.persag services
- [x] Test configuration changes with restart script
- [x] Verify new models are properly loaded
- [x] Clean up duplicate environment variables in current directory lightrag_server files
- [x] Clean up duplicate environment variables in current directory lightrag_memory_server files
- [x] Update models in current directory env files
- [x] Create comprehensive summary documentation in refs directory
</task_progress>
