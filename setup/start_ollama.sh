#!/bin/bash
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_ORIGINS="*"                 # or "http://your.ui:3000"
export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_QUEUE=512
export OLLAMA_KEEP_ALIVE="60m"
export OLLAMA_DEBUG=1
#export OLLAMA_NEW_ENGINE=1
#export OLLAMA_NEW_ESTIMATES=1
# Optional / advanced:
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE="f16"
# export OLLAMA_LOG_LEVEL=INFO
export OLLAMA_CONTEXT_LENGTH=12232
# export OLLAMA_MODELS="/Volumes/Fast/ollama-models"

exec /usr/local/bin/ollama serve

