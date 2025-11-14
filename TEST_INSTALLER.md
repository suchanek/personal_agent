# Testing the Updated Installer Cleanly

## 🧪 Testing Strategy

Since you already have a working Ollama setup, we need to test without breaking it.

## Option 1: Dry-Run Test (Safest)

```bash
# Test what the installer would do without making changes
sudo ./install-personal-agent.sh --dry-run

# Test with your custom models directory
sudo ./install-personal-agent.sh --dry-run --ollama-models-dir=/Volumes/BigDataRaid/LLM/ollama_models
```

**What it shows:**
- ✅ All detection logic
- ✅ What files would be created
- ✅ What commands would run
- ❌ No actual changes

## Option 2: Test Individual Functions (Recommended)

Create a test script that runs just the detection functions:

```bash
#!/bin/bash
# test-detection.sh

# Source the installer functions
AGENT_USER="suchanek"
AGENT_HOME="/Users/suchanek"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OLLAMA_MODELS_DIR=""
OLLAMA_KV_CACHE_TYPE=""

# Copy detection functions from installer
detect_ollama_models_directory() {
    # ... function code ...
}

detect_system_ram() {
    # ... function code ...
}

# Run tests
echo "Testing detection functions..."
detect_ollama_models_directory
echo "Detected models dir: ${OLLAMA_MODELS_DIR}"

detect_system_ram
echo "RAM: ${SYSTEM_RAM_GB}GB"
echo "KV Cache: ${OLLAMA_KV_CACHE_TYPE}"
echo "Max Models: ${OLLAMA_MAX_LOADED_MODELS}"
```

## Option 3: Test Template Generation Only

Test just the template substitution without running the installer:

```bash
# Set test variables
export OLLAMA_MODELS_DIR="/Volumes/BigDataRaid/LLM/ollama_models"
export SYSTEM_RAM_GB="24"
export OLLAMA_MAX_LOADED_MODELS="3"
export OLLAMA_KV_CACHE_TYPE="q6_0"

# Generate test output
sed -e "s|__OLLAMA_MODELS_DIR__|${OLLAMA_MODELS_DIR}|g" \
    -e "s|__SYSTEM_RAM__|${SYSTEM_RAM_GB}|g" \
    -e "s|__MAX_LOADED_MODELS__|${OLLAMA_MAX_LOADED_MODELS}|g" \
    -e "s|__KV_CACHE_TYPE__|${OLLAMA_KV_CACHE_TYPE}|g" \
    setup/start_ollama.sh.template > /tmp/test_start_ollama.sh

# Review the generated file
cat /tmp/test_start_ollama.sh

# Check it has all env vars
grep "export OLLAMA_" /tmp/test_start_ollama.sh
grep "export HOME\|export USER\|export PATH" /tmp/test_start_ollama.sh
```

## Option 4: Test on a Clean VM/Container (Most Thorough)

If you have Docker or a VM:
```bash
# Create a test macOS environment
# Run full installer there
```

## Option 5: Backup and Test Specific Components

```bash
# 1. Backup your current working setup
cp ~/.local/bin/start_ollama.sh ~/.local/bin/start_ollama.sh.backup
cp ~/Library/LaunchAgents/local.ollama.plist ~/Library/LaunchAgents/local.ollama.plist.backup

# 2. Test just the Ollama service setup function
# (Manually extract and run setup_ollama_service in isolation)

# 3. Restore if needed
cp ~/.local/bin/start_ollama.sh.backup ~/.local/bin/start_ollama.sh
cp ~/Library/LaunchAgents/local.ollama.plist.backup ~/Library/LaunchAgents/local.ollama.plist
```

## ✅ Recommended Testing Sequence

### Step 1: Quick Validation
```bash
# Verify templates exist
ls -la setup/*.template

# Check installer syntax
bash -n install-personal-agent.sh
```

### Step 2: Dry-Run Test
```bash
sudo ./install-personal-agent.sh --dry-run 2>&1 | tee /tmp/installer-dryrun.log

# Review the log
less /tmp/installer-dryrun.log
```

### Step 3: Template Generation Test
```bash
# Test template substitution (see Option 3 above)
# Verify generated file has all env vars
```

### Step 4: Verify Detection Logic
```bash
# Create simple test script
cat > test-detection.sh <<'EOF'
#!/bin/bash
AGENT_USER="suchanek"
AGENT_HOME="/Users/suchanek"
INSTALL_DIR="$(pwd)"

# Test models directory detection
echo "Testing models directory detection..."
for pattern in "/Volumes/*/LLM/ollama_models" "/Volumes/*/ollama_models"; do
    for path in $pattern; do
        if [[ -d "${path}" ]]; then
            model_count=$(find "${path}" -name "*.gguf" 2>/dev/null | wc -l | tr -d ' ')
            echo "  Found ${model_count} models in ${path}"
        fi
    done
done

# Test RAM detection
total_ram_bytes=$(sysctl -n hw.memsize)
ram_gb=$((total_ram_bytes / 1024 / 1024 / 1024))
echo "Detected ${ram_gb}GB RAM"

if [[ ${ram_gb} -le 24 ]]; then
    echo "Would use: q6_0 cache, max 3 models"
fi
EOF

chmod +x test-detection.sh
./test-detection.sh
```

## 🔍 What to Check in Dry-Run Output

Look for:
1. ✅ "Auto-detected models directory with X models: /Volumes/BigDataRaid/LLM/ollama_models"
2. ✅ "Detected 24GB system RAM"
3. ✅ "RAM-optimized for 24GB: q6_0 cache, max 3 models"
4. ✅ "Creating Ollama startup script from template..."
5. ✅ "Would create ollama-service.sh from template"
6. ✅ Symlink path shows Resources/ollama (not MacOS/ollama)

## 🚨 Safety Checks Before Real Install

```bash
# 1. Verify Ollama is currently working
poe ollama-status

# 2. Check current models are accessible
ollama list

# 3. Backup current config
mkdir -p ~/installer-backup
cp ~/.local/bin/start_ollama.sh ~/installer-backup/ 2>/dev/null || true
cp ~/Library/LaunchAgents/local.ollama.plist ~/installer-backup/ 2>/dev/null || true
cp ./ollama-service.sh ~/installer-backup/ 2>/dev/null || true

# 4. Run dry-run and review
sudo ./install-personal-agent.sh --dry-run | tee ~/installer-backup/dryrun.log
```

## 📝 Minimal Test Script

I can create a minimal test script that just runs the detection and template generation:
