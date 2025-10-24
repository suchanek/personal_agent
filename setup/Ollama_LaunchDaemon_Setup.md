# System-Wide Ollama LaunchDaemon Setup Guide

**Date:** 2025-09-18  
**Author:** Eric G. Suchanek

This document describes how to set up a system-wide Ollama service on macOS that starts automatically at boot, runs under a specific user account, and uses a custom model directory.

---

## Overview

We will:
1. Install the startup script in `/usr/local/bin`.
2. Configure a `launchd` plist in `/Library/LaunchDaemons`.
3. Set up proper environment variables.
4. Configure logging and permissions.
5. Start and verify the service.

This setup will ensure Ollama runs at boot and is accessible to other machines on your network.

---

## 1. Install the Startup Script

Create the file `/usr/local/bin/start_ollama.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_MODELS="/Volumes/BigDataRaid/LLM/ollama_models/"
export OLLAMA_KEEP_ALIVE=2h

# Wait for external volume to mount
for i in {1..60}; do
  [[ -d "$OLLAMA_MODELS" ]] && break
  sleep 2
done

# Optional: log the environment for debugging
env | grep '^OLLAMA_' | tee /var/log/ollama.env 2>/dev/null || true

# Adjust path to your actual Ollama binary
exec /opt/homebrew/bin/ollama serve
```

Make the script executable:
```bash
sudo chmod +x /usr/local/bin/start_ollama.sh
```

---

## 2. Create the LaunchDaemon plist

Create the file `/Library/LaunchDaemons/com.suchanek.ollama.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.suchanek.ollama</string>

    <key>ProgramArguments</key>
    <array>
      <string>/usr/local/bin/start_ollama.sh</string>
    </array>

    <key>UserName</key>
    <string>suchanek</string> <!-- Replace with your actual username -->

    <key>EnvironmentVariables</key>
    <dict>
      <key>OLLAMA_MAX_LOADED_MODELS</key><string>2</string>
      <key>OLLAMA_NUM_PARALLEL</key><string>1</string>
      <key>OLLAMA_HOST</key><string>0.0.0.0:11434</string>
      <key>OLLAMA_MODELS</key><string>/Volumes/BigDataRaid/LLM/ollama_models/</string>
      <key>OLLAMA_KEEP_ALIVE</key><string>2h</string>
    </dict>

    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>

    <key>StandardOutPath</key><string>/var/log/ollama.out</string>
    <key>StandardErrorPath</key><string>/var/log/ollama.err</string>
  </dict>
</plist>
```

---

## 3. Fix Permissions

```bash
sudo chown root:wheel /Library/LaunchDaemons/com.suchanek.ollama.plist
sudo chmod 644 /Library/LaunchDaemons/com.suchanek.ollama.plist
```

Ensure the startup script is owned correctly:
```bash
ls -l /usr/local/bin/start_ollama.sh
```

---

## 4. Create Log Files

```bash
sudo touch /var/log/ollama.out /var/log/ollama.err
sudo chown suchanek:staff /var/log/ollama.out /var/log/ollama.err
```

---

## 5. Load and Start the Daemon

Unload any previous user job:
```bash
launchctl bootout gui/$(id -u)/com.suchanek.ollama 2>/dev/null || true
```

Load the new system daemon:
```bash
sudo launchctl bootstrap system /Library/LaunchDaemons/com.suchanek.ollama.plist
sudo launchctl enable system/com.suchanek.ollama
sudo launchctl kickstart -k system/com.suchanek.ollama
```

---

## 6. Verify the Setup

- **Check the running process:**
  ```bash
  ps aux | grep '[o]llama serve'
  ```

- **Inspect logs:**
  ```bash
  tail -f /var/log/ollama.out
  tail -f /var/log/ollama.err
  ```

- **Confirm environment variables:**
  ```bash
  sudo launchctl print system/com.suchanek.ollama | sed -n '/environment = {/,/}/p'
  ```

- **Verify API endpoint:**
  ```bash
  curl -s http://localhost:11434/api/ps | jq .
  ```

You should see each model with `expires_in` close to `2h`.

---

## 7. Optional Commands

- Stop the daemon:
  ```bash
  sudo launchctl bootout system/com.suchanek.ollama
  ```

- Restart the daemon:
  ```bash
  sudo launchctl kickstart -k system/com.suchanek.ollama
  ```

---

## Summary

This setup:
- Runs Ollama at boot, independent of user login.
- Uses a custom models directory on external storage.
- Logs to `/var/log/ollama.*`.
- Keeps models loaded for **2 hours** by default.
- Allows remote connections by listening on `0.0.0.0:11434`.

Make sure to secure access if exposing Ollama on the network.
