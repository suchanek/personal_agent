#!/bin/bash
################################################################################
# Test Installer Detection and Template Generation
#
# This script tests the key functions without modifying your system
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Testing Installer Detection and Templates${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Set up test environment
AGENT_USER="$(whoami)"
AGENT_HOME="${HOME}"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OLLAMA_MODELS_DIR=""
OLLAMA_KV_CACHE_TYPE=""

# Test 1: Check template files exist
echo -e "${BLUE}Test 1: Checking template files...${NC}"
if [[ -f "setup/start_ollama.sh.template" ]]; then
    echo -e "${GREEN}✓${NC} start_ollama.sh.template exists"
else
    echo -e "${RED}✗${NC} start_ollama.sh.template missing"
    exit 1
fi

if [[ -f "setup/ollama-service.sh.template" ]]; then
    echo -e "${GREEN}✓${NC} ollama-service.sh.template exists"
else
    echo -e "${RED}✗${NC} ollama-service.sh.template missing"
    exit 1
fi
echo ""

# Test 2: Verify all env vars in template
echo -e "${BLUE}Test 2: Verifying env vars in template...${NC}"
required_vars=(
    "export HOME="
    "export USER="
    "export LOGNAME="
    "export PATH="
    "export OLLAMA_MODELS="
    "export OLLAMA_HOST="
    "export OLLAMA_ORIGINS="
    "export OLLAMA_MAX_LOADED_MODELS="
    "export OLLAMA_NUM_PARALLEL="
    "export OLLAMA_MAX_QUEUE="
    "export OLLAMA_KEEP_ALIVE="
    "export OLLAMA_DEBUG="
    "export OLLAMA_FLASH_ATTENTION="
    "export OLLAMA_KV_CACHE_TYPE="
    "export OLLAMA_CONTEXT_LENGTH="
)

all_found=true
for var in "${required_vars[@]}"; do
    if grep -q "${var}" setup/start_ollama.sh.template; then
        echo -e "${GREEN}✓${NC} Found: ${var}"
    else
        echo -e "${RED}✗${NC} Missing: ${var}"
        all_found=false
    fi
done

if ! $all_found; then
    echo -e "${RED}ERROR: Missing critical env vars!${NC}"
    exit 1
fi
echo ""

# Test 3: Models directory configuration
echo -e "${BLUE}Test 3: Testing models directory configuration...${NC}"

# Check if existing plist has a models directory
existing_plist="${HOME}/Library/LaunchAgents/local.ollama.plist"
if [[ -f "${existing_plist}" ]]; then
    plist_models=$(grep -A1 "OLLAMA_MODELS" "${existing_plist}" | tail -1 | sed 's/.*<string>\(.*\)<\/string>.*/\1/' 2>/dev/null || true)
    if [[ -n "${plist_models}" ]]; then
        OLLAMA_MODELS_DIR="${plist_models}"
        echo -e "${GREEN}✓${NC} Preserving existing models directory: ${OLLAMA_MODELS_DIR}"
    else
        OLLAMA_MODELS_DIR="/Users/Shared/personal_agent_data/ollama"
        echo -e "${GREEN}✓${NC} Would use default: ${OLLAMA_MODELS_DIR}"
    fi
else
    OLLAMA_MODELS_DIR="/Users/Shared/personal_agent_data/ollama"
    echo -e "${GREEN}✓${NC} Would use default: ${OLLAMA_MODELS_DIR}"
fi

echo "  Note: Use --ollama-models-dir=/custom/path to override"
echo ""

# Test 4: RAM detection and optimization
echo -e "${BLUE}Test 4: Testing RAM detection...${NC}"

total_ram_bytes=$(sysctl -n hw.memsize)
ram_gb=$((total_ram_bytes / 1024 / 1024 / 1024))
echo "  Detected ${ram_gb}GB system RAM"

if [[ ${ram_gb} -le 16 ]]; then
    OLLAMA_KV_CACHE_TYPE="q4_0"
    OLLAMA_MAX_LOADED_MODELS="2"
    echo -e "${GREEN}✓${NC} RAM-optimized for 16GB: q4_0 cache, max 2 models"
elif [[ ${ram_gb} -le 24 ]]; then
    OLLAMA_KV_CACHE_TYPE="q6_0"
    OLLAMA_MAX_LOADED_MODELS="3"
    echo -e "${GREEN}✓${NC} RAM-optimized for 24GB: q6_0 cache, max 3 models"
elif [[ ${ram_gb} -le 32 ]]; then
    OLLAMA_KV_CACHE_TYPE="q8_0"
    OLLAMA_MAX_LOADED_MODELS="4"
    echo -e "${GREEN}✓${NC} RAM-optimized for 32GB: q8_0 cache, max 4 models"
else
    OLLAMA_KV_CACHE_TYPE="f16"
    OLLAMA_MAX_LOADED_MODELS="5"
    echo -e "${GREEN}✓${NC} RAM-optimized for 48GB+: f16 cache, max 5 models"
fi

export SYSTEM_RAM_GB="${ram_gb}"
echo ""

# Test 5: Template substitution
echo -e "${BLUE}Test 5: Testing template substitution...${NC}"

test_output="/tmp/test_start_ollama_$$.sh"

sed -e "s|__OLLAMA_MODELS_DIR__|${OLLAMA_MODELS_DIR}|g" \
    -e "s|__SYSTEM_RAM__|${SYSTEM_RAM_GB}|g" \
    -e "s|__MAX_LOADED_MODELS__|${OLLAMA_MAX_LOADED_MODELS}|g" \
    -e "s|__KV_CACHE_TYPE__|${OLLAMA_KV_CACHE_TYPE}|g" \
    setup/start_ollama.sh.template > "${test_output}"

echo -e "${GREEN}✓${NC} Generated test script: ${test_output}"
echo ""

# Verify substitutions worked
echo -e "${BLUE}Test 6: Verifying substitutions...${NC}"

if grep -q "__OLLAMA_MODELS_DIR__\|__SYSTEM_RAM__\|__MAX_LOADED_MODELS__\|__KV_CACHE_TYPE__" "${test_output}"; then
    echo -e "${RED}✗${NC} ERROR: Placeholders still present in generated script!"
    grep "__" "${test_output}"
    exit 1
else
    echo -e "${GREEN}✓${NC} All placeholders replaced"
fi

if grep -q "export OLLAMA_MODELS=\"${OLLAMA_MODELS_DIR}\"" "${test_output}"; then
    echo -e "${GREEN}✓${NC} OLLAMA_MODELS set correctly"
else
    echo -e "${RED}✗${NC} OLLAMA_MODELS not set correctly"
    exit 1
fi

if grep -q "export OLLAMA_KV_CACHE_TYPE=\"${OLLAMA_KV_CACHE_TYPE}\"" "${test_output}"; then
    echo -e "${GREEN}✓${NC} OLLAMA_KV_CACHE_TYPE set correctly"
else
    echo -e "${RED}✗${NC} OLLAMA_KV_CACHE_TYPE not set correctly"
    exit 1
fi

echo ""

# Test 7: Verify syntax
echo -e "${BLUE}Test 7: Checking generated script syntax...${NC}"
if bash -n "${test_output}"; then
    echo -e "${GREEN}✓${NC} Generated script has valid syntax"
else
    echo -e "${RED}✗${NC} Generated script has syntax errors!"
    exit 1
fi
echo ""

# Test 8: Check installer syntax
echo -e "${BLUE}Test 8: Checking installer script syntax...${NC}"
if bash -n install-personal-agent.sh; then
    echo -e "${GREEN}✓${NC} Installer script has valid syntax"
else
    echo -e "${RED}✗${NC} Installer script has syntax errors!"
    exit 1
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}All Tests Passed!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Configuration that would be used:"
echo "  Models Directory: ${OLLAMA_MODELS_DIR}"
echo "  System RAM: ${SYSTEM_RAM_GB}GB"
echo "  KV Cache Type: ${OLLAMA_KV_CACHE_TYPE}"
echo "  Max Loaded Models: ${OLLAMA_MAX_LOADED_MODELS}"
echo ""
echo "Generated script saved to: ${test_output}"
echo ""
echo "To review the generated script:"
echo "  cat ${test_output}"
echo ""
echo "To run dry-run installer:"
echo "  sudo ./install-personal-agent.sh --dry-run"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
