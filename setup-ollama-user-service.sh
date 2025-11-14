#!/bin/bash
################################################################################
# Setup Ollama as User LaunchAgent Service
# 
# This script configures Ollama to run as a user-level LaunchAgent service
# that starts automatically when you log in.
################################################################################

set -e

USER_HOME="${HOME}"
MODELS_DIR="/Volumes/BigDataRaid/LLM/ollama_models"  # Your existing models location
STARTUP_SCRIPT="${USER_HOME}/.local/bin/start_ollama.sh"
PLIST_FILE="${USER_HOME}/Library/LaunchAgents/local.ollama.plist"
LOG_DIR="${USER_HOME}/Library/Logs/ollama"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Setting up Ollama as User LaunchAgent"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Stop any running Ollama processes
echo "1. Stopping existing Ollama processes..."
pkill -f "Ollama.app" 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true

# Unload existing LaunchAgent if loaded
if launchctl list | grep -q "local.ollama"; then
    echo "   Unloading existing LaunchAgent..."
    launchctl unload "${PLIST_FILE}" 2>/dev/null || true
fi

sleep 2
echo "   ✓ Stopped existing processes"
echo ""

# 2. Create directories
echo "2. Creating necessary directories..."
mkdir -p "${USER_HOME}/.local/bin"
mkdir -p "${USER_HOME}/Library/LaunchAgents"
mkdir -p "${LOG_DIR}"
mkdir -p "${MODELS_DIR}"
echo "   ✓ Directories created"
echo ""

# 3. Create startup script
echo "3. Creating Ollama startup script..."
cat > "${STARTUP_SCRIPT}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# User LaunchAgent environment
export HOME="${HOME:-$(eval echo ~$(whoami))}"
export USER="${USER:-$(whoami)}"
export LOGNAME="${LOGNAME:-$(whoami)}"
export PATH="/usr/local/bin:/opt/homebrew/bin:${PATH}"

# Ollama model storage location - BigDataRaid
export OLLAMA_MODELS="/Volumes/BigDataRaid/LLM/ollama_models"

# Ollama configuration
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_ORIGINS="*"
export OLLAMA_MAX_LOADED_MODELS="3"
export OLLAMA_NUM_PARALLEL="8"
export OLLAMA_MAX_QUEUE="512"
export OLLAMA_KEEP_ALIVE="30m"
export OLLAMA_DEBUG="1"
export OLLAMA_FLASH_ATTENTION="1"
# KV Cache Type: q6_0 (6-bit quantized) - better quality, reasonable memory
export OLLAMA_KV_CACHE_TYPE="q6_0"
export OLLAMA_CONTEXT_LENGTH="12232"

# Ensure model directory exists
mkdir -p "$OLLAMA_MODELS"

LOG_DIR="${HOME}/Library/Logs/ollama"
OUT_LOG="${LOG_DIR}/ollama.out.log"
ERR_LOG="${LOG_DIR}/ollama.err.log"
mkdir -p "$LOG_DIR"

echo "[$(date '+%F %T')] start_ollama.sh: USER=${USER} HOST=${OLLAMA_HOST} MODELS=${OLLAMA_MODELS}" >> "$OUT_LOG" 2>&1

env | grep '^OLLAMA_' | tee -a "$LOG_DIR/ollama.env"

exec /usr/local/bin/ollama serve >> "$OUT_LOG" 2>> "$ERR_LOG"
EOF

chmod +x "${STARTUP_SCRIPT}"
echo "   ✓ Startup script created at ${STARTUP_SCRIPT}"
echo ""

# 4. Create LaunchAgent plist
echo "4. Creating LaunchAgent plist..."
cat > "${PLIST_FILE}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>local.ollama</string>
    <key>ProgramArguments</key>
    <array>
      <string>${STARTUP_SCRIPT}</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
      <key>OLLAMA_MODELS</key>
      <string>${MODELS_DIR}</string>
      <key>OLLAMA_HOST</key>
      <string>0.0.0.0:11434</string>
      <key>OLLAMA_ORIGINS</key>
      <string>*</string>
      <key>OLLAMA_MAX_LOADED_MODELS</key>
      <string>3</string>
      <key>OLLAMA_NUM_PARALLEL</key>
      <string>8</string>
      <key>OLLAMA_MAX_QUEUE</key>
      <string>512</string>
      <key>OLLAMA_KEEP_ALIVE</key>
      <string>30m</string>
      <key>OLLAMA_KV_CACHE_TYPE</key>
      <string>q6_0</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/ollama.out.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/ollama.err.log</string>
  </dict>
</plist>
EOF

chmod 644 "${PLIST_FILE}"
echo "   ✓ LaunchAgent plist created at ${PLIST_FILE}"
echo ""

# 5. Load the LaunchAgent
echo "5. Loading Ollama LaunchAgent service..."
launchctl load "${PLIST_FILE}"
sleep 3
echo "   ✓ Service loaded"
echo ""

# 6. Verify
echo "6. Verifying service status..."
if launchctl list | grep -q "local.ollama"; then
    echo "   ✓ Service is running"
else
    echo "   ✗ Service may not have started properly"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Ollama User Service Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Configuration:"
echo "  • Models directory: ${MODELS_DIR}"
echo "  • Host: 0.0.0.0:11434"
echo "  • Logs: ${LOG_DIR}/"
echo ""
echo "Management commands:"
echo "  • Check status:  launchctl list | grep local.ollama"
echo "  • View logs:     tail -f ${LOG_DIR}/ollama.out.log"
echo "  • Stop service:  launchctl unload ${PLIST_FILE}"
echo "  • Start service: launchctl load ${PLIST_FILE}"
echo "  • Restart:       launchctl unload ${PLIST_FILE} && launchctl load ${PLIST_FILE}"
echo ""
echo "The service will start automatically when you log in."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
