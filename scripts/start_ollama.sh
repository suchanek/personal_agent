#!/bin/bash
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_ORIGINS="*"                 # or "http://your.ui:3000"
export OLLAMA_MAX_LOADED_MODELS=3
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_QUEUE=512
export OLLAMA_KEEP_ALIVE="10m"
export OLLAMA_DEBUG=1
export OLLAMA_FLASH_ATTENTION=1
# KV Cache Type: q8_0 (8-bit quantized) optimized for 24GB systems
# - Uses ~50% less memory than f16 (~3.5GB vs 7GB per model)
# - Allows safe operation with 3 models on 24GB RAM (10.5GB vs 21GB)
# - Minimal quality degradation compared to f16
# - Alternative: f16 for systems with 32GB+ RAM
export OLLAMA_KV_CACHE_TYPE="q8_0"
#export OLLAMA_NEW_ENGINE=1
#export OLLAMA_NEW_ESTIMATES=1
# Optional / advanced:
# export OLLAMA_LOG_LEVEL=INFO
# export OLLAMA_CONTEXT_LENGTH=8192
# export OLLAMA_MODELS="/Volumes/Fast/ollama-models"

exec /usr/local/bin/ollama serve

