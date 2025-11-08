#!/usr/bin/env bash
set -euo pipefail

export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_HOST=0.0.0.0
export OLLAMA_MODELS="/Users/Shared/personal_agent_data/ollama_models/"
export OLLAMA_KEEP_ALIVE=2h
export OLLAMA_DEBUG=1
export OLLAMA_NEW_ESTIMATES=1

env | grep '^OLLAMA_' | tee /tmp/ollama.env

exec /usr/local/bin/ollama serve
