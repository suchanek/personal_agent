#!/usr/bin/env bash
# sd_shortcut.sh — run txt2img via sd311 and emit only a data-URI to stdout
# this script is designed to run INSIDE an Apple shortcut!
# Author: Eric G. Suchanek, PhD
# Last revision: 2025-10-15 22:16:37
# Requires: conda env "sd311" with torch3 installed (see newsd.sh)
set -euo pipefail
IFS=$'\n\t'
export BASH_SILENCE_DEPRECATION_WARNING=1

PROMPT="${*:-}"
MODEL="XL"
STEPS=5
CFG=11
PREFIX="shortcut_sd"
PROGRAM_DIR="/usr/local/bin"
SCRIPT="$PROGRAM_DIR/txt2img.py"
LOG="/tmp/sd_shortcut.log"
PY="/Users/egs/miniforge3/envs/sd311/bin/python"   # <- sd311 interpreter

notify() { /usr/bin/osascript -e "display notification \"$1\" with title \"Stable Diffusion\"" >/dev/null 2>&1 || true; }

notify "Generating image…"
cd "$PROGRAM_DIR"

# Run; send stderr to log; keep only the first valid data-URI from stdout
DATA_URI="$(
  "$PY" "$SCRIPT" \
    --prompt "$PROMPT" \
    --model "$MODEL" \
    --steps "$STEPS" \
    --cfg "$CFG" \
    --prefix "$PREFIX" \
    2>>"$LOG" \
  | grep -Eo '^data:image/(png|jpe?g);base64,[A-Za-z0-9+/=]+' \
  | head -n1
)"

if [[ -z "$DATA_URI" ]]; then
  echo "Error: No data-URI found on stdout" >>"$LOG"
  notify "Generation failed"
  exit 1
fi

notify "Image ready!"
printf '%s\n' "$DATA_URI"