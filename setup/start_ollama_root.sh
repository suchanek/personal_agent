#!/usr/bin/env bash
set -euo pipefail

# launchd (root) env
export HOME="/var/root"
export USER="root"
export LOGNAME="root"
export TMPDIR="/var/tmp"
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Ollama env (your settings)
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_ORIGINS="*"
export OLLAMA_MAX_LOADED_MODELS="2"
export OLLAMA_NUM_PARALLEL="8"
export OLLAMA_MAX_QUEUE="512"
export OLLAMA_KEEP_ALIVE="30m"
export OLLAMA_DEBUG="1"
export OLLAMA_FLASH_ATTENTION="1"
export OLLAMA_KV_CACHE_TYPE="f16"
export OLLAMA_CONTEXT_LENGTH="12232"
export OLLAMA_MODELS="/Volumes/BigDataRaid/LLM/ollama_models"

LOG_DIR="/var/log/ollama"
OUT_LOG="${LOG_DIR}/ollama.out.log"
ERR_LOG="${LOG_DIR}/ollama.err.log"
mkdir -p "$LOG_DIR" "$HOME/.cache" "$HOME/.config" "$HOME/.local/share"

echo "[$(date '+%F %T')] start_ollama.sh: HOST=$OLLAMA_HOST MODELS=$OLLAMA_MODELS" >>"$OUT_LOG" 2>&1

# Wait up to 120s for the external volume; exit 75 if missing so launchd retries
deadline=$((SECONDS + 120))
while [[ ! -d "$OLLAMA_MODELS" && $SECONDS -lt $deadline ]]; do
  echo "[$(date '+%F %T')] waiting for $OLLAMA_MODELS ..." >>"$OUT_LOG"
  sleep 2
done

if [[ ! -d "$OLLAMA_MODELS" ]]; then
  echo "[$(date '+%F %T')] ERROR: $OLLAMA_MODELS not mounted; exit 75" >>"$ERR_LOG"
  exit 75  # EX_TEMPFAIL
fi

env | grep '^OLLAMA_' | tee "$LOG_DIR/ollama.env"

exec /usr/local/bin/ollama serve >>"$OUT_LOG" 2>>"$ERR_LOG"
