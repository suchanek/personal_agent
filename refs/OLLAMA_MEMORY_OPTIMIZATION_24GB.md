# Ollama Memory Optimization for 24GB Deployment Systems

**Date:** 2025-11-10  
**Author:** Eric G. Suchanek, PhD  
**Status:** Implemented  

## Overview

Optimized Ollama configuration for production deployment on 24GB RAM systems by switching from f16 to q8_0 KV cache type and increasing concurrent model capacity from 2 to 3 models.

## Problem Statement

The initial Ollama configuration used:
- **f16 KV cache type**: ~7GB memory per model
- **2 max loaded models**: Limited concurrency
- **Unused template files**: Confusion between templates and active configuration

With 3 models on f16, memory usage would be ~21GB, leaving minimal headroom on 24GB systems for OS and other processes. Additionally, outdated template files in `setup/` and `scripts/` directories created maintenance confusion.

## Solution

### 1. KV Cache Type Optimization

Switched from **f16** to **q8_0** (8-bit quantized) across all configuration files:

**Memory Impact:**
- f16: ~7GB per model → 3 models = 21GB
- q8_0: ~3.5GB per model → 3 models = 10.5GB
- **Savings: ~50% memory reduction per model**

**Quality Trade-off:**
- q8_0 provides minimal quality degradation compared to f16
- Suitable for production deployment on memory-constrained systems
- f16 remains recommended for development systems with 32GB+ RAM

### 2. Increased Model Capacity

Updated `OLLAMA_MAX_LOADED_MODELS` from **2 → 3**:
- Enables concurrent loading of multiple model sizes
- Better multi-user support
- Improved request throughput

### 3. Configuration Cleanup

**Removed unused template files:**
- `setup/start_ollama.sh` - Outdated, not referenced by install script
- Considered removing `scripts/start_ollama.sh` (also unused)

**Single source of truth:**
- Install script (`install-personal-agent.sh`) generates startup script via heredoc
- Runtime script: `~/.local/bin/start_ollama.sh`
- LaunchAgent plist: `~/Library/LaunchAgents/local.ollama.agent.plist`

## Files Modified

### Core Configuration Files

1. **`install-personal-agent.sh`**
   - Startup script template (heredoc, lines ~568-586)
   - LaunchAgent plist EnvironmentVariables (lines ~625-638)
   - Added detailed comments explaining q8_0 choice for 24GB systems

2. **`scripts/start_ollama.sh`**
   - Repository template (currently unused but kept for reference)
   - Updated with q8_0 and detailed comments

3. **`src/personal_agent/config/settings.py`**
   - Added `OLLAMA_KV_CACHE_TYPE = "q8_0"` constant (lines ~305-317)
   - Comprehensive comment block explaining optimization rationale

4. **`~/.local/bin/start_ollama.sh`** (runtime)
   - Active service startup script
   - Updated with full q8_0 configuration and 5-line comment block

### Documentation Comments Added

All configuration files now include detailed comments:

```bash
# KV Cache Type: q8_0 (8-bit quantized) optimized for 24GB systems
# - Uses ~50% less memory than f16 (~3.5GB vs 7GB per model)
# - Allows safe operation with 3 models on 24GB RAM (10.5GB vs 21GB)
# - Minimal quality degradation compared to f16
# - Alternative: f16 for systems with 32GB+ RAM
export OLLAMA_KV_CACHE_TYPE="q8_0"
```

## Configuration Values

### Final Ollama Settings

```bash
OLLAMA_MAX_LOADED_MODELS=3       # Increased from 2
OLLAMA_NUM_PARALLEL=8            # Concurrent request handling
OLLAMA_MAX_QUEUE=512             # Request queue size
OLLAMA_KEEP_ALIVE=30m            # Model retention time
OLLAMA_DEBUG=1                   # Enhanced logging
OLLAMA_FLASH_ATTENTION=1         # Performance optimization
OLLAMA_KV_CACHE_TYPE=q8_0        # Changed from f16
OLLAMA_CONTEXT_LENGTH=12232      # Context window size
```

## Memory Budget (24GB System)

### With q8_0 Configuration

| Component | Memory Usage |
|-----------|--------------|
| macOS System | ~4-6GB |
| Ollama (3 models) | ~10.5GB |
| Docker Containers | ~2-4GB |
| Application | ~2-3GB |
| **Available Buffer** | ~3-6GB |

### Previous f16 Configuration (for comparison)

| Component | Memory Usage |
|-----------|--------------|
| macOS System | ~4-6GB |
| Ollama (3 models) | ~21GB |
| Docker Containers | ~2-4GB |
| Application | ~2-3GB |
| **Available Buffer** | **-5 to -2GB** ⚠️ |

## Testing & Verification

**Service Restart:**
```bash
ollama-reload  # Shell alias to reload service
```

**Configuration Verification:**
```bash
ollama-env  # Shell alias to display current Ollama environment
# Confirmed: OLLAMA_KV_CACHE_TYPE=q8_0
```

**Active Configuration:**
- Service successfully reloaded with new settings
- All environment variables applied correctly
- Memory usage reduced as expected

## Deployment Considerations

### Development Environment (36GB RAM)
- Can optionally use f16 for maximum quality
- q8_0 still recommended for consistency with production

### Production Environment (24GB RAM)
- **Must use q8_0** to ensure stable operation
- Monitor actual memory usage under load
- Adjust `OLLAMA_MAX_LOADED_MODELS` if needed based on specific model sizes

### Model Size Variations
Different models have different memory footprints:
- Small models (1-2B): ~1-2GB with q8_0
- Medium models (4-8B): ~3-5GB with q8_0
- Large models (13B+): ~6-8GB with q8_0

Adjust concurrent model count based on actual deployment mix.

## Shell Aliases Created

For convenient service management:

```bash
# Reload Ollama service
alias ollama-reload='launchctl unload ~/Library/LaunchAgents/local.ollama.agent.plist && sleep 2 && launchctl load ~/Library/LaunchAgents/local.ollama.agent.plist && echo "Ollama service reloaded"'

# Show current Ollama environment
alias ollama-env='launchctl getenv OLLAMA_KV_CACHE_TYPE 2>/dev/null || cat ~/.local/log/ollama/ollama.env 2>/dev/null || echo "Ollama environment not available"'
```

## Benefits

1. **Memory Efficiency**: 50% reduction in per-model memory footprint
2. **Increased Capacity**: Support for 3 concurrent models on 24GB systems
3. **Production Ready**: Safe operation with adequate memory headroom
4. **Maintainability**: Clear documentation and single source of truth
5. **Flexibility**: Easy adjustment for different deployment targets

## Future Considerations

- Monitor actual memory usage patterns in production
- Consider dynamic adjustment of `OLLAMA_MAX_LOADED_MODELS` based on available RAM
- Evaluate q4_0 for even more memory-constrained scenarios (at cost of quality)
- Test with specific model combinations used in production

## References

- Ollama Environment Variables: https://github.com/ollama/ollama/blob/main/docs/env.md
- KV Cache Types: f32 (highest quality) → f16 → q8_0 → q4_0 (lowest memory)
- LaunchAgent Configuration: `~/Library/LaunchAgents/local.ollama.agent.plist`
- Runtime Script: `~/.local/bin/start_ollama.sh`
