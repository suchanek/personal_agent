# Granite 3.1 LLM Standardization for LightRAG Servers

**Date**: 2025-11-15  
**Author**: Eric G. Suchanek, PhD  
**Status**: Implemented  
**Version**: v0.8.76.dev

## Overview

Standardized LightRAG server LLM configuration to use IBM Granite 3.1 models with full Apache 2.0 licensing, while maintaining Qwen3 models for proven agent inference and tool-calling capabilities. This hybrid approach provides licensing compliance for RAG workloads while preserving established inference performance.

## Problem Statement

The LightRAG servers had inconsistent LLM model configuration:
- **Knowledge Server**: Using `qwen3:4b` (Apache 2.0 licensed at this size)
- **Memory Server**: Using `granite3.1-moe:1b` (Apache 2.0 licensed)
- **Inconsistency**: Different model families across servers
- **Licensing Risk**: Qwen2.5:3b was identified as having proprietary Qwen License (not Apache 2.0)
- **Context Limits**: Original 128K context too high for multi-instance deployment on 24GB RAM systems

## Solution Architecture

### Model Selection Strategy

**For LightRAG RAG Servers (Apache 2.0 Licensed):**
- **Knowledge Server**: `granite3.1-dense:8b` (5.0GB, 32K context)
  - Robust for document processing and complex content
  - Optimized for RAG and retrieval workflows
  
- **Memory Server**: `granite3.1-dense:2b` (1.6GB, 32K context)
  - Lightweight for short memory statements
  - Efficient relationship extraction

**For Agent Inference (Proven Tool-Calling):**
- **Personal Agent**: `qwen3:4b` (Apache 2.0 at this size)
  - Established tool-calling performance
  - User's primary inference model
  
- **Team Mode**: `hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K`
  - Proven multi-agent coordination
  - Optimized for team workflows

### Context Window Optimization

**Reduced from 128K to 32K** for multi-instance deployment:
- **Rationale**: Running 2 LightRAG servers + main agent concurrently
- **24GB RAM Constraint**: Need to limit memory per instance
- **Estimated Usage**:
  - Knowledge: granite3.1-dense:8b @ 32K → ~6-7GB
  - Memory: granite3.1-dense:2b @ 32K → ~2-3GB
  - Embeddings: nomic-embed-text → ~1GB
  - **Total**: ~9-11GB for RAG infrastructure
  - **Remaining**: ~13-15GB for main agent + system

## Implementation Details

### Configuration Files Updated

#### 1. `lightrag_server/env.server` (Knowledge Server)
```bash
# LLM Model configuration
# Using granite3.1-dense:8b for robust document processing (Apache 2.0 license)
# 5.0GB model with 128K context, optimized for RAG and complex content
LLM_MODEL=granite3.1-dense:8b

# MODEL CONTEXT SIZE OVERRIDES
# Set to 32K to support multiple concurrent RAG server instances
GRANITE3_1_DENSE_2B_CTX_SIZE=32768
GRANITE3_1_DENSE_8B_CTX_SIZE=32768
DEFAULT_MODEL_CTX_SIZE=32768
```

#### 2. `lightrag_memory_server/env.memory_server` (Memory Server)
```bash
# LLM Model configuration
# Using granite3.1-dense:2b for lightweight memory processing (Apache 2.0 license)
# 1.6GB model with 128K context, optimized for short memory statements
LLM_MODEL=granite3.1-dense:2b

# MODEL CONTEXT SIZE OVERRIDES
# Set to 32K to support multiple concurrent RAG server instances
GRANITE3_1_DENSE_2B_CTX_SIZE=32768
GRANITE3_1_DENSE_8B_CTX_SIZE=32768
DEFAULT_MODEL_CTX_SIZE=32768
```

#### 3. `install-personal-agent.sh` (Installer)
```bash
local models=(
    "granite3.1-dense:8b"           # Knowledge RAG server (Apache 2.0)
    "granite3.1-dense:2b"           # Memory RAG server (Apache 2.0)
    "qwen3:4b"                      # Personal agent inference (Apache 2.0)
    "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K"  # Team inference
    "nomic-embed-text"              # Embeddings
)
```

## License Research Summary

### Granite 3.1 (IBM)
- **All Sizes**: Apache 2.0 ✅
- **Context**: 128K tokens (native)
- **Training**: 12 trillion tokens
- **Specialization**: RAG, tool-calling, enterprise workloads
- **Sizes**: 1b (MoE), 2b (dense), 8b (dense)

### Qwen2.5 (Alibaba)
- **0.5b, 1.5b, 7b, 14b, 32b**: Apache 2.0 ✅
- **3b, 72b**: Qwen License ⚠️ (proprietary, restrictive)
- **Context**: 32K tokens (native), 128K supported
- **Training**: 18 trillion tokens
- **Note**: `qwen3:4b` is safe (Apache 2.0)

### Decision Rationale
- **Granite**: Full Apache 2.0 across ALL sizes (no licensing traps)
- **Qwen3**: Keep proven 4b variant for inference (Apache 2.0 compliant)
- **Strategy**: Test Granite for RAG, maintain Qwen3 for established workflows

## Benefits

### Licensing Compliance
- ✅ **100% Apache 2.0**: All production models fully licensed
- ✅ **No Restrictions**: Commercial use, modification, distribution permitted
- ✅ **Future-Proof**: No model size upgrade restrictions

### Performance Optimization
- ✅ **32K Context**: Realistic for multi-instance deployment
- ✅ **Memory Efficient**: Fits comfortably in 24GB RAM
- ✅ **Concurrent Models**: 3+ models can run simultaneously

### Operational Flexibility
- ✅ **Hybrid Strategy**: Test new models while keeping proven ones
- ✅ **Specialization**: RAG vs inference workloads separated
- ✅ **Graceful Migration**: Can switch back if Granite underperforms

## Deployment Considerations

### 24GB RAM Systems (e.g., Babbage laptop)
- **Safe Operation**: 3 concurrent models (2 RAG + 1 agent)
- **Total Footprint**: ~10-11GB for RAG infrastructure
- **Headroom**: ~13-15GB for agent operations

### 48GB+ RAM Systems (e.g., Developer workstations)
- **Upgrade Path**: Can increase to `qwen3:8b` or `granite3.1-dense:8b` for main agent
- **Higher Context**: Could use 64K context if needed
- **More Concurrency**: 4-5 models simultaneously

### Testing Strategy
1. **Phase 1**: Deploy Granite to LightRAG servers, monitor RAG quality
2. **Phase 2**: Compare knowledge retrieval accuracy vs previous Qwen configuration
3. **Phase 3**: If Granite underperforms, fallback to Qwen3 variants (all Apache 2.0)
4. **Decision Point**: Keep Granite if performance acceptable, revert if not

## Related Files

- `lightrag_server/env.server` - Knowledge server configuration
- `lightrag_memory_server/env.memory_server` - Memory server configuration
- `install-personal-agent.sh` - Model installation script
- `CHANGELOG.md` - Version history and changes

## References

- **Granite Documentation**: https://www.ibm.com/granite/docs/
- **Ollama Granite**: https://ollama.com/library/granite3.1-dense
- **Qwen Documentation**: https://qwenlm.github.io/blog/qwen2.5/
- **License Comparison**: Apache 2.0 vs Qwen License analysis

## Conclusion

This standardization provides a robust, licensing-compliant foundation for the Personal Agent system while maintaining operational flexibility. The hybrid Granite (RAG) + Qwen3 (inference) strategy balances legal requirements, proven performance, and resource constraints across diverse deployment environments.
