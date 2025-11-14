# Ollama User-Level Service Setup - Complete

## ✅ What's Been Configured

### 1. Startup Script
**Location:** `~/.local/bin/start_ollama.sh`

This script starts Ollama with optimized configuration:
- **Models Directory:** `/Volumes/BigDataRaid/LLM/ollama_models`
- **Host:** `0.0.0.0:11434` (accessible from network)
- **KV Cache:** `q6_0` (6-bit quantized for quality+memory balance)
- **Max Loaded Models:** 3 (optimized for 24GB RAM)
- **Flash Attention:** Enabled
- **Parallel Requests:** 8
- **Context Length:** 12232 tokens
- **Keep Alive:** 30 minutes

### 2. Service Manager
**Location:** `./ollama-service.sh`

Easy management commands:
```bash
./ollama-service.sh status    # Check if running
./ollama-service.sh start     # Start Ollama
./ollama-service.sh stop      # Stop Ollama
./ollama-service.sh restart   # Restart Ollama
./ollama-service.sh logs      # View output logs
./ollama-service.sh logs err  # View error logs
./ollama-service.sh models    # List available models
```

### 3. Login App (Auto-Start)
**Location:** `~/Applications/StartOllama.app`

To make Ollama start automatically when you log in:

**Option A - Manual:**
1. Open **System Settings** > **General** > **Login Items**
2. Click the **+** button
3. Navigate to `~/Applications` and select **StartOllama.app**
4. Click **Add**

**Option B - Command Line:**
```bash
osascript -e 'tell application "System Events" to make login item at end with properties {path:"'$HOME'/Applications/StartOllama.app", hidden:false}'
```

## 📊 Current Status

You have **36 models** available including:
- Qwen3 family (1.7B, 4B, 8B, 14B, 30B variants)
- Llama3.1/3.2/3.3 models
- Granite 3.1 (MoE and Dense)
- DeepSeek-R1
- Phi4
- CodeLlama
- Nomic embeddings

## 🔧 Configuration Files

### Startup Script Environment Variables
All optimizations are in `~/.local/bin/start_ollama.sh`:
```bash
OLLAMA_MODELS="/Volumes/BigDataRaid/LLM/ollama_models"
OLLAMA_HOST="0.0.0.0:11434"
OLLAMA_MAX_LOADED_MODELS="3"
OLLAMA_NUM_PARALLEL="8"
OLLAMA_MAX_QUEUE="512"
OLLAMA_KEEP_ALIVE="30m"
OLLAMA_KV_CACHE_TYPE="q6_0"
OLLAMA_CONTEXT_LENGTH="12232"
OLLAMA_FLASH_ATTENTION="1"
```

### Log Files
- **Output:** `~/Library/Logs/ollama/ollama.out.log`
- **Errors:** `~/Library/Logs/ollama/ollama.err.log`
- **Startup:** `~/Library/Logs/ollama/startup.log`
- **Environment:** `~/Library/Logs/ollama/ollama.env`

## 🚀 Quick Start

### Start Ollama Now
```bash
./ollama-service.sh start
```

### Check Status
```bash
./ollama-service.sh status
```

### Test API
```bash
curl http://localhost:11434/api/version
```

### List Models
```bash
ollama list
# or
./ollama-service.sh models
```

### Run a Model
```bash
ollama run qwen3:8b
```

## 🔍 Troubleshooting

### Ollama Won't Start
```bash
# Check error logs
./ollama-service.sh logs err

# Check if port is in use
lsof -i :11434

# Kill any existing processes
pkill -f "ollama serve"
./ollama-service.sh start
```

### Models Not Found
```bash
# Verify models directory
ls -la /Volumes/BigDataRaid/LLM/ollama_models

# Check environment
tail ~/Library/Logs/ollama/ollama.env
```

### High Memory Usage
```bash
# Reduce loaded models (edit ~/.local/bin/start_ollama.sh)
OLLAMA_MAX_LOADED_MODELS="2"  # Change from 3 to 2

# Or use more aggressive quantization
OLLAMA_KV_CACHE_TYPE="q4_0"  # Even lower memory

# Then restart
./ollama-service.sh restart
```

## ⚙️ Customization

To change settings, edit `~/.local/bin/start_ollama.sh` and restart:
```bash
nano ~/.local/bin/start_ollama.sh
./ollama-service.sh restart
```

## 📝 Note About LaunchAgent

The LaunchAgent plist exists at `~/Library/LaunchAgents/local.ollama.plist` but macOS is giving I/O errors when trying to load it (common macOS quirk). Instead, we use the **StartOllama.app** method which is more reliable and user-friendly.

If you want to try the LaunchAgent approach later:
```bash
launchctl load ~/Library/LaunchAgents/local.ollama.plist
```

## ✨ Integration with Personal Agent

The Personal Agent system will automatically detect Ollama running on `localhost:11434`. Make sure:

1. Ollama is running: `./ollama-service.sh status`
2. Your `.env` file has: `OLLAMA_URL=http://localhost:11434`
3. Models are pulled: `./ollama-service.sh models`

---

**Created:** November 14, 2025  
**Models Directory:** `/Volumes/BigDataRaid/LLM/ollama_models`  
**Service Running:** Yes ✓  
**Auto-Start:** Ready (add StartOllama.app to Login Items)
