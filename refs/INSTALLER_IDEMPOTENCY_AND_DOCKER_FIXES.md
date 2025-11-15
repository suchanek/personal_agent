# Installer Idempotency and Docker Service Fixes

**Author**: Eric G. Suchanek, PhD  
**Date**: November 14, 2025  
**Version**: 0.8.76.dev  
**Status**: Completed

## Executive Summary

This document details a comprehensive overhaul of the Personal Agent installation system (`install-personal-agent.sh`) and LightRAG Docker service management. The work focused on achieving true idempotency, eliminating interactive prompts, improving error handling, and fixing critical Docker service startup issues.

## Problem Statement

The installation system suffered from several critical issues:

1. **Docker Service Failures**: LightRAG containers failing to start with "too many colons" errors
2. **Non-Idempotent Behavior**: Installer couldn't safely run multiple times without manual intervention
3. **Interactive Prompts**: `uv venv` and other tools prompting for user input during automated installations
4. **Misleading Dry-Run Mode**: Showing "WOULD CREATE" for resources that already existed
5. **Service Dependency Issues**: Ollama model checking requiring the service to be running
6. **Docker Authentication**: Image pull failures blocking installation progress

## Solutions Implemented

### 1. Docker Compose Configuration Fixes

#### Problem: "Too Many Colons" Error
The Docker Compose files contained `build:` sections that triggered package installations during container startup, producing output that corrupted volume mount parsing.

**Root Cause Analysis**:
```yaml
# PROBLEMATIC CONFIGURATION
build:
  context: .
  dockerfile: Dockerfile
volumes:
  - ${AGNO_STORAGE_DIR}:/app/rag_storage  # Colon separator confused by build output
```

When containers started, the build process ran `pip install spacy` and downloaded models, producing console output containing colons. Docker's volume mount parser encountered this unexpected output and failed with "too many colons in volume specification".

**Solution**:
- Removed all `build:` sections from production docker-compose files
- Use pre-built images from Docker Hub: `egsuchanek/lightrag_pagent:latest`
- Build sections belong only in development environments

**Files Modified**:
- `~/.persagent/lightrag_server/docker-compose.yml`
- `~/.persagent/lightrag_memory_server/docker-compose.yml`
- `lightrag_server/docker-compose.yml` (template)
- `lightrag_memory_server/docker-compose.yml` (template)

**Changes**:
```yaml
# BEFORE
services:
  lightrag_server:
    build:
      context: .
      dockerfile: Dockerfile
    image: lightrag_pagent
    # ... rest of config

# AFTER
services:
  lightrag_server:
    image: egsuchanek/lightrag_pagent:latest
    # ... rest of config - build section completely removed
```

#### Problem: Incorrect Healthcheck Ports
The memory server's healthcheck was using port 9621 (internal) instead of 9622 (exposed), preventing proper container health detection.

**Solution**:
Updated healthcheck to use the exposed port for external verification:
```yaml
# Memory Server Configuration
ports:
  - "9622:9621"  # External:Internal mapping
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9622/health"]  # Use exposed port
```

### 2. Installer Idempotency Enhancements

#### Philosophy: True Idempotency
The installer was redesigned following the principle that running it multiple times should:
- Detect existing resources accurately
- Skip already-completed steps safely
- Report clearly what would be done vs. what exists
- Never fail due to pre-existing conditions

#### Implementation Pattern

**Before** (misleading):
```bash
if [[ "$DRY_RUN" == "true" ]]; then
    log_info "Would create directory: $dir"
fi
```

**After** (accurate):
```bash
if [[ "$DRY_RUN" == "true" ]]; then
    if [[ -d "$dir" ]]; then
        log_info "[EXISTS] Directory: $dir"
    else
        log_info "[WOULD CREATE] Directory: $dir"
    fi
fi
```

#### Functions Enhanced with Existence Checking

1. **`setup_lightrag_directories()`**
   - Checks for existing LightRAG config directories
   - Reports `[EXISTS]`, `[SKIP]`, or `[WOULD CREATE]`
   - Validates docker-compose.yml and env files

2. **`setup_ollama_service()`**
   - Checks for existing Ollama directories
   - Validates startup scripts
   - Verifies LaunchAgent plist files
   - Reports existing vs would-create for each resource

3. **`setup_ollama_management()`**
   - Checks for management scripts in `~/bin/`
   - Reports existence status for each utility script

4. **`setup_repository()`**
   - **Critical Fix**: Checks for existing `.venv` before creation
   - Prevents interactive `uv venv` prompts about overwriting
   - Ensures non-interactive installation

### 3. Offline Ollama Model Detection

#### Problem: Service Dependency
Model checking used `ollama list` which requires the Ollama service to be running, causing failures during fresh installations or when the service is stopped.

#### Solution: Directory-Based Detection
Implemented `check_model_in_directory()` function that inspects the Ollama manifest structure directly:

```bash
check_model_in_directory() {
    local model_name=$1
    local base_name="${model_name%%:*}"
    local tag="${model_name#*:}"
    [[ "$tag" == "$model_name" ]] && tag="latest"
    
    # Check manifest directory structure
    local manifest_dir="${OLLAMA_MODELS_DIR}/manifests/registry.ollama.ai/library/${base_name}"
    if [[ -d "$manifest_dir" ]] && [[ -f "${manifest_dir}/${tag}" ]]; then
        return 0  # Model exists
    fi
    return 1  # Model not found
}
```

**Manifest Structure**:
```
$OLLAMA_MODELS_DIR/
├── manifests/
│   └── registry.ollama.ai/
│       └── library/
│           ├── qwen3/
│           │   ├── latest
│           │   ├── 8b
│           │   └── 1.7b
│           └── llama3.2/
│               └── latest
└── blobs/
    └── sha256-*
```

**Benefits**:
- Works without Ollama service running
- Fast directory-based checking
- No API call overhead
- Reliable for automation

### 4. Docker Image Pull Handling

#### Problem: Authentication Failures
Docker image pulls from Docker Hub were failing with authentication errors, even though the images are public, because there was no CLI authentication configured.

#### Solution: Non-Fatal Pulls with Graceful Degradation

```bash
pull_lightrag_images() {
    if docker pull egsuchanek/lightrag_pagent:latest; then
        log_success "Successfully pulled LightRAG image"
    else
        log_warn "Unable to pull LightRAG image from Docker Hub"
        log_warn "This may be due to Docker Hub authentication"
        log_warn "The image will be automatically pulled when starting containers"
        # Continue installation - not fatal
    fi
}
```

**Rationale**:
- Public images don't require authentication for pulling via `docker-compose up`
- Pre-pulling is an optimization, not a requirement
- Failing to pre-pull shouldn't block installation
- Users get clear guidance about what's happening

### 5. Non-Interactive Installation

#### Problem: Interactive Prompts
Several tools used during installation would prompt for user input, blocking automated deployments:
- `uv venv` asking about overwriting existing virtual environments
- Package managers requesting confirmation
- Service installers awaiting user approval

#### Solution: Existence Checking and Skip Logic

**Virtual Environment Creation**:
```bash
setup_repository() {
    # ... other setup ...
    
    # Check for existing .venv before creating
    if [[ -d "${INSTALL_DIR}/.venv" ]]; then
        log_info "Virtual environment already exists at ${INSTALL_DIR}/.venv"
        log_info "Skipping venv creation"
    else
        log_info "Creating virtual environment..."
        uv venv "${INSTALL_DIR}/.venv"
    fi
    
    # ... rest of setup ...
}
```

**Benefits**:
- No interactive prompts during installation
- Safe for CI/CD pipelines
- Can be run via automation tools
- Idempotent behavior

## Technical Details

### Docker Compose Volume Mount Syntax

**Critical Understanding**: Docker Compose volume mounts use colon (`:`) as a separator:
```yaml
volumes:
  - host_path:container_path[:options]
```

Any output containing colons during container startup can corrupt this parsing, leading to errors like:
```
Error response from daemon: invalid mount config for type "bind": 
invalid mount path: 'too many colons in volume specification'
```

**Prevention**:
- Never use `build:` sections in production compose files
- Keep image pulling separate from container startup
- Use pre-built images from registries

### Ollama LaunchAgent Configuration

**Service File**: `~/Library/LaunchAgents/local.ollama.plist`

**Key Configuration**:
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>OLLAMA_HOST</key>
    <string>0.0.0.0:11434</string>
    <key>OLLAMA_MODELS</key>
    <string>/Users/Shared/personal_agent_data/ollama</string>
    <key>OLLAMA_KEEP_ALIVE</key>
    <string>24h</string>
    <key>OLLAMA_MAX_LOADED_MODELS</key>
    <string>3</string>
    <key>OLLAMA_KV_CACHE_TYPE</key>
    <string>q8_0</string>
</dict>
```

**Memory Optimization**:
- `q8_0` KV cache: ~3.5GB per model (vs ~7GB with `f16`)
- Allows 3 concurrent models on 24GB RAM systems
- Reduces memory footprint by 50%

### LightRAG Docker Architecture

**Two Separate Services**:

1. **Knowledge Server** (port 9621)
   - Graph-based knowledge base
   - Document ingestion and retrieval
   - Configuration: `~/.persagent/lightrag_server/`

2. **Memory Server** (port 9622)
   - Memory relationship graphs
   - User memory persistence
   - Configuration: `~/.persagent/lightrag_memory_server/`

**Port Mappings**:
```yaml
# Knowledge Server
ports:
  - "9621:9621"  # External:Internal

# Memory Server  
ports:
  - "9622:9621"  # External port differs for instance identification
```

## Testing and Validation

### Dry-Run Mode Testing
```bash
# Test dry-run accuracy
sudo -E bash install-personal-agent.sh --dry-run

# Verify output shows:
# [EXISTS] for existing resources
# [WOULD CREATE] for missing resources
# [SKIP] for steps that would be skipped
```

### Fresh Installation Testing
```bash
# Complete clean installation
sudo -E bash install-personal-agent.sh

# Should complete without:
# - Interactive prompts
# - Docker pull failures blocking progress
# - Errors about existing resources
```

### Idempotency Testing
```bash
# Run installer multiple times
sudo -E bash install-personal-agent.sh
sudo -E bash install-personal-agent.sh
sudo -E bash install-personal-agent.sh

# Each run should:
# - Complete successfully
# - Report existing resources accurately
# - Not recreate or overwrite existing configs
```

### Docker Service Verification
```bash
# Verify services start correctly
./restart-lightrag.sh

# Check container health
docker ps
docker logs lightrag_server
docker logs lightrag_memory_server

# Verify healthchecks
curl http://localhost:9621/health
curl http://localhost:9622/health
```

## Files Modified

### Docker Compose Templates
1. `lightrag_server/docker-compose.yml`
2. `lightrag_memory_server/docker-compose.yml`

### User Configuration Files
1. `~/.persagent/lightrag_server/docker-compose.yml`
2. `~/.persagent/lightrag_memory_server/docker-compose.yml`

### Installation Scripts
1. `install-personal-agent.sh` (comprehensive updates)
   - `setup_lightrag_directories()`
   - `setup_ollama_service()`
   - `setup_ollama_management()`
   - `setup_repository()`
   - `pull_ollama_models()`
   - `pull_lightrag_images()`

### Service Management
1. `restart-lightrag.sh` (intelligent Docker service management)

## Impact Assessment

### Positive Outcomes
✅ **Reliability**: Docker services start consistently without errors  
✅ **Automation**: Installation can run completely non-interactively  
✅ **Accuracy**: Dry-run mode provides accurate system state reporting  
✅ **Robustness**: Handles edge cases (service stopped, no Docker auth, existing resources)  
✅ **Maintainability**: Clear patterns for future enhancements  
✅ **User Experience**: No confusing prompts or misleading messages  

### Performance Improvements
- Faster installations (skips unnecessary recreation)
- Reduced network usage (skips re-downloading existing images)
- Lower cognitive load (clear, accurate status reporting)

### Risk Mitigation
- No data loss from overwriting existing configurations
- Safe to run multiple times during troubleshooting
- Graceful handling of partial installations
- Clear error messages guide problem resolution

## Future Enhancements

### Potential Improvements
1. **Rollback Mechanism**: Ability to undo partial installations
2. **Upgrade Path**: Detect version changes and upgrade configs
3. **Health Checking**: Post-install validation of all services
4. **Dependency Verification**: Check system requirements before starting
5. **Configuration Validation**: Verify docker-compose.yml syntax before use

### Configuration Management
1. **Template Versioning**: Track docker-compose template versions
2. **Migration Scripts**: Handle config format changes between versions
3. **Backup Strategy**: Automatic backup before modifying configs

## Lessons Learned

### Docker Compose Best Practices
1. **Separation of Concerns**: Keep build and run configurations separate
2. **Image Registries**: Use pre-built images for production deployments
3. **Healthcheck Ports**: Use exposed ports for external verification
4. **Volume Syntax**: Be vigilant about colon separators in volume mounts

### Installation Script Design
1. **Idempotency First**: Design every operation to be safely repeatable
2. **Existence Checking**: Always verify before creating or modifying
3. **Non-Interactive**: Assume automation, avoid prompts
4. **Clear Reporting**: Distinguish between would-do and actually-did
5. **Graceful Degradation**: Make failures informative, not fatal

### Service Management
1. **Offline Detection**: Don't depend on services being running
2. **Directory Inspection**: File system is more reliable than APIs
3. **Smart Defaults**: Provide reasonable fallbacks for missing configs

## References

### Related Documentation
- Docker Compose Specification: https://docs.docker.com/compose/compose-file/
- Ollama Configuration: https://github.com/ollama/ollama/blob/main/docs/faq.md
- macOS LaunchAgent: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/

### Project Files
- `OLLAMA_SETUP.md` - Ollama service configuration guide
- `CHANGELOG.md` - Project version history
- `install-personal-agent.sh` - Main installer script
- `restart-lightrag.sh` - Docker service management

## Conclusion

This comprehensive overhaul transformed the installation system from a fragile, one-time setup script into a robust, idempotent deployment tool. The changes enable:

- **Automated Deployments**: CI/CD pipelines can run installations without human intervention
- **Troubleshooting**: Users can safely re-run the installer to fix issues
- **Testing**: Development and testing workflows benefit from repeatable installations
- **Documentation**: Dry-run mode serves as living documentation of system state

The work demonstrates the importance of idempotency in system administration tools and provides a solid foundation for future enhancements to the Personal Agent deployment system.
