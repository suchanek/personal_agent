#!/bin/bash

################################################################################
# Personal Agent Installer for macOS
#
# This script installs and configures the Personal AI Agent system on macOS.
# It must be run as root or with sudo, and will install for the current user.
#
# Usage:
#   sudo ./install-personal-agent.sh           # Full installation
#   sudo ./install-personal-agent.sh --dry-run # Test without making changes
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
AGENT_USER="${SUDO_USER:-$(logname 2>/dev/null || whoami)}"
AGENT_HOME="/Users/${AGENT_USER}"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # Use script's directory as install dir
DATA_DIR="${AGENT_HOME}/.persagent"
LOG_FILE="${AGENT_HOME}/install.log"  # Log in home directory

# Detect shell profile file
# Check user's default shell
AGENT_SHELL=$(dscl . -read "/Users/${AGENT_USER}" UserShell | awk '{print $2}')
if [[ "${AGENT_SHELL}" == *"zsh"* ]]; then
    PROFILE_FILE="${AGENT_HOME}/.zprofile"
else
    PROFILE_FILE="${AGENT_HOME}/.bash_profile"
fi

# Dry-run mode flag
DRY_RUN=false

# Ollama configuration (will be auto-detected or can be overridden)
OLLAMA_MODELS_DIR=""
OLLAMA_KV_CACHE_TYPE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --ollama-models-dir=*)
            OLLAMA_MODELS_DIR="${1#*=}"
            shift
            ;;
        --ollama-kv-cache=*)
            OLLAMA_KV_CACHE_TYPE="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: sudo $0 [--dry-run] [--ollama-models-dir=PATH] [--ollama-kv-cache=TYPE]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

################################################################################
# Logging and Output Functions
################################################################################

log() {
    local msg="$1"
    if $DRY_RUN; then
        echo -e "${MAGENTA}[DRY-RUN]${NC} ${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $msg" | tee -a "${LOG_FILE}"
    else
        echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $msg" | tee -a "${LOG_FILE}"
    fi
}

log_success() {
    local msg="$1"
    if $DRY_RUN; then
        echo -e "${MAGENTA}[DRY-RUN]${NC} ${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $msg" | tee -a "${LOG_FILE}"
    else
        echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $msg" | tee -a "${LOG_FILE}"
    fi
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a "${LOG_FILE}"
}

# Execute command or simulate in dry-run mode
run_cmd() {
    if $DRY_RUN; then
        log "[WOULD RUN] $*"
        return 0
    else
        "$@"
    fi
}

################################################################################
# Detection Functions
################################################################################

detect_ollama_models_directory() {
    log "Configuring Ollama models directory..."
    
    # Priority 1: Command-line argument (override)
    if [[ -n "${OLLAMA_MODELS_DIR}" ]]; then
        log "Using models directory from command line: ${OLLAMA_MODELS_DIR}"
        return 0
    fi
    
    # Priority 2: Check existing ollama plist if it exists (preserve existing setup)
    local existing_plist="${AGENT_HOME}/Library/LaunchAgents/local.ollama.plist"
    if [[ -f "${existing_plist}" ]]; then
        local plist_models=$(grep -A1 "OLLAMA_MODELS" "${existing_plist}" | tail -1 | sed 's/.*<string>\(.*\)<\/string>.*/\1/')
        if [[ -n "${plist_models}" ]]; then
            OLLAMA_MODELS_DIR="${plist_models}"
            log "Preserving existing models directory from plist: ${OLLAMA_MODELS_DIR}"
            return 0
        fi
    fi
    
    # Priority 3: Default location for new installations
    OLLAMA_MODELS_DIR="/Users/Shared/personal_agent_data/ollama"
    log "Using default models directory: ${OLLAMA_MODELS_DIR}"
}

detect_system_ram() {
    log "Detecting system RAM and optimizing Ollama configuration..."
    
    # Get total RAM in GB
    local total_ram_bytes=$(sysctl -n hw.memsize)
    local ram_gb=$((total_ram_bytes / 1024 / 1024 / 1024))
    
    log "Detected ${ram_gb}GB system RAM"
    
    # Set defaults if not overridden by command line
    if [[ -z "${OLLAMA_KV_CACHE_TYPE}" ]]; then
        if [[ ${ram_gb} -le 16 ]]; then
            OLLAMA_KV_CACHE_TYPE="q4_0"
            OLLAMA_MAX_LOADED_MODELS="2"
            log "RAM-optimized for 16GB: q4_0 cache, max 2 models"
        elif [[ ${ram_gb} -le 24 ]]; then
            OLLAMA_KV_CACHE_TYPE="q6_0"
            OLLAMA_MAX_LOADED_MODELS="3"
            log "RAM-optimized for 24GB: q6_0 cache, max 3 models"
        elif [[ ${ram_gb} -le 32 ]]; then
            OLLAMA_KV_CACHE_TYPE="q8_0"
            OLLAMA_MAX_LOADED_MODELS="4"
            log "RAM-optimized for 32GB: q8_0 cache, max 4 models"
        else
            OLLAMA_KV_CACHE_TYPE="f16"
            OLLAMA_MAX_LOADED_MODELS="5"
            log "RAM-optimized for 48GB+: f16 cache, max 5 models"
        fi
    else
        # Use command-line override
        OLLAMA_MAX_LOADED_MODELS="3"  # Conservative default
        log "Using command-line KV cache type: ${OLLAMA_KV_CACHE_TYPE}"
    fi
    
    export SYSTEM_RAM_GB="${ram_gb}"
}

################################################################################
# Pre-flight Checks
################################################################################

preflight_checks() {
    log "Running pre-flight checks..."

    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi

    # Check if macOS
    if [[ "$(uname)" != "Darwin" ]]; then
        log_error "This script is for macOS only"
        exit 1
    fi

    # Check if target user exists (should be current user)
    if ! id "${AGENT_USER}" &>/dev/null; then
        log_error "User '${AGENT_USER}' does not exist."
        exit 1
    fi

    # Check if home directory exists
    if [[ ! -d "${AGENT_HOME}" ]]; then
        log_error "Home directory ${AGENT_HOME} does not exist"
        exit 1
    fi

    log_success "Pre-flight checks passed"
}

################################################################################
# Install Homebrew
################################################################################

install_homebrew() {
    log "Checking Homebrew installation..."

    # Check if Homebrew exists
    if [[ -d "/opt/homebrew" ]]; then
        log_success "Homebrew found at /opt/homebrew"

        # Ensure agent user is in admin group for Homebrew access
        if ! dscl . -read "/Groups/admin" GroupMembership | grep -q "${AGENT_USER}"; then
            log "Adding ${AGENT_USER} to admin group for Homebrew access..."
            if ! $DRY_RUN; then
                dseditgroup -o edit -a "${AGENT_USER}" -t user admin
                log_success "${AGENT_USER} added to admin group"
            else
                log "[WOULD ADD] ${AGENT_USER} to admin group"
            fi
        else
            log_success "${AGENT_USER} already in admin group"
        fi

        # Ensure proper group permissions on Homebrew
        if ! $DRY_RUN; then
            chmod -R g+w /opt/homebrew 2>/dev/null || true
            chgrp -R admin /opt/homebrew 2>/dev/null || true
        else
            log "[WOULD SET] group permissions on /opt/homebrew"
        fi

        # Add to PATH if not already there
        if ! grep -q "brew shellenv" "${PROFILE_FILE}" 2>/dev/null; then
            if ! $DRY_RUN; then
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "${PROFILE_FILE}"
                log_success "Added Homebrew to PATH"
            else
                log "[WOULD ADD] Homebrew to ${AGENT_HOME}/.bash_profile"
            fi
        fi

        return 0
    fi

    # Homebrew doesn't exist, install it system-wide
    log "Installing Homebrew system-wide..."

    if ! $DRY_RUN; then
        # Install Homebrew with non-interactive mode
        NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Set proper group ownership
        chgrp -R admin /opt/homebrew
        chmod -R g+w /opt/homebrew

        # Add agent user to admin group
        dseditgroup -o edit -a "${AGENT_USER}" -t user admin

        # Add Homebrew to PATH for the agent user
        if ! grep -q "brew shellenv" "${PROFILE_FILE}"; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "${PROFILE_FILE}"
        fi

        # Source for current script
        eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

        log_success "Homebrew installed successfully"
    else
        log "[WOULD INSTALL] Homebrew system-wide"
        log "[WOULD ADD] ${AGENT_USER} to admin group"
        log "[WOULD ADD] Homebrew to ${AGENT_HOME}/.bash_profile"
    fi
}

################################################################################
# Install Python 3.12
################################################################################

install_python() {
    log "Checking Python 3.12 installation..."

    # Set Homebrew cache to agent user's directory
    local brew_env="HOMEBREW_CACHE=${AGENT_HOME}/Library/Caches/Homebrew"

    if ! $DRY_RUN; then
        if sudo -u "${AGENT_USER}" bash -c "${brew_env} /opt/homebrew/bin/brew list python@3.12" &>/dev/null; then
            log_success "Python 3.12 already installed"
        else
            log "Installing Python 3.12..."
            sudo -u "${AGENT_USER}" bash -c "${brew_env} /opt/homebrew/bin/brew install python@3.12"
            log_success "Python 3.12 installed"
        fi
    else
        log "[WOULD CHECK] if Python 3.12 is installed"
        log "[WOULD INSTALL] Python 3.12 if needed"
    fi

    # Add Python to PATH
    if ! grep -q "python@3.12" "${PROFILE_FILE}" 2>/dev/null; then
        if ! $DRY_RUN; then
            echo 'export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"' >> "${PROFILE_FILE}"
        else
            log "[WOULD ADD] Python 3.12 to PATH in ${AGENT_HOME}/.bash_profile"
        fi
    fi
}

################################################################################
# Install uv (Python package manager)
################################################################################

install_uv() {
    log "Checking uv installation..."

    if ! $DRY_RUN; then
        if sudo -u "${AGENT_USER}" bash -c 'command -v uv' &>/dev/null; then
            log_success "uv already installed"
            return 0
        fi

        log "Installing uv..."
        sudo -u "${AGENT_USER}" bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
        log_success "uv installed successfully"
    else
        log "[WOULD CHECK] if uv is installed"
        log "[WOULD INSTALL] uv if needed"
    fi

    # Add uv to PATH
    if ! grep -q ".cargo/bin" "${PROFILE_FILE}" 2>/dev/null; then
        if ! $DRY_RUN; then
            echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "${PROFILE_FILE}"
        else
            log "[WOULD ADD] uv to PATH in ${AGENT_HOME}/.bash_profile"
        fi
    fi
}

################################################################################
# Install Poetry
################################################################################

install_poetry() {
    log "Checking Poetry installation..."

    if ! $DRY_RUN; then
        if sudo -u "${AGENT_USER}" bash -c 'command -v poetry' &>/dev/null; then
            log_success "Poetry already installed"
            return 0
        fi

        log "Installing Poetry with Homebrew Python 3.12..."
        # Use Homebrew Python 3.12 explicitly to avoid Command Line Tools Python
        # that doesn't support symlinks in venvs
        sudo -u "${AGENT_USER}" bash -c 'export POETRY_HOME="$HOME/.local/share/pypoetry" && curl -sSL https://install.python-poetry.org | /opt/homebrew/opt/python@3.12/bin/python3.12 -'
        log_success "Poetry installed successfully"
    else
        log "[WOULD CHECK] if Poetry is installed"
        log "[WOULD INSTALL] Poetry if needed"
    fi

    # Add Poetry to PATH
    if ! grep -q ".local/bin" "${PROFILE_FILE}" 2>/dev/null; then
        if ! $DRY_RUN; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${PROFILE_FILE}"
        else
            log "[WOULD ADD] Poetry to PATH in ${AGENT_HOME}/.bash_profile"
        fi
    fi
}

################################################################################
# Install Docker Desktop
################################################################################

install_docker() {
    log "Checking Docker Desktop installation..."

    if [[ -d "/Applications/Docker.app" ]]; then
        log_success "Docker Desktop already installed"
    else
        if ! $DRY_RUN; then
            log "Installing Docker Desktop..."
            local brew_env="HOMEBREW_CACHE=${AGENT_HOME}/Library/Caches/Homebrew"
            sudo -u "${AGENT_USER}" bash -c "${brew_env} /opt/homebrew/bin/brew install --cask docker"
            log_success "Docker Desktop installed"
        else
            log "[WOULD INSTALL] Docker Desktop via Homebrew"
        fi
    fi

    # Start Docker Desktop if not running
    if ! pgrep -f "Docker.app" > /dev/null; then
        if ! $DRY_RUN; then
            log "Starting Docker Desktop..."
            sudo -u "${AGENT_USER}" open -a Docker
            log "Waiting for Docker to start (this may take a minute)..."
            sleep 30

            # Wait for Docker to be ready
            timeout=60
            while ! docker info &>/dev/null && [[ $timeout -gt 0 ]]; do
                sleep 2
                ((timeout-=2))
            done

            if docker info &>/dev/null; then
                log_success "Docker Desktop is running"
            else
                log_warning "Docker Desktop may need manual start"
            fi
        else
            log "[WOULD START] Docker Desktop"
        fi
    else
        log_success "Docker Desktop is running"
    fi
}

################################################################################
# Install Ollama
################################################################################

install_ollama() {
    log "Checking Ollama installation..."

    if [[ -d "/Applications/Ollama.app" ]]; then
        log_success "Ollama already installed"
    else
        log "Installing Ollama from official source (required for Metal GPU acceleration)..."

        if ! $DRY_RUN; then
            local temp_dir="/tmp/ollama_install_$$"
            mkdir -p "${temp_dir}"

            log "Downloading Ollama..."
            if curl -L -o "${temp_dir}/Ollama.zip" "https://ollama.com/download/Ollama-darwin.zip"; then
                log_success "Download complete"
            else
                log_error "Failed to download Ollama"
                rm -rf "${temp_dir}"
                return 1
            fi

            log "Extracting Ollama..."
            if unzip -q "${temp_dir}/Ollama.zip" -d "${temp_dir}"; then
                log_success "Extraction complete"
            else
                log_error "Failed to extract Ollama"
                rm -rf "${temp_dir}"
                return 1
            fi

            log "Installing Ollama to /Applications..."
            if [[ -d "${temp_dir}/Ollama.app" ]]; then
                cp -R "${temp_dir}/Ollama.app" /Applications/
                log_success "Ollama installed"
            else
                log_error "Ollama.app not found in extracted files"
                rm -rf "${temp_dir}"
                return 1
            fi

            # Clean up
            rm -rf "${temp_dir}"
        else
            log "[WOULD DOWNLOAD] Ollama from https://ollama.com/download/Ollama-darwin.zip"
            log "[WOULD EXTRACT] to /Applications/Ollama.app"
        fi
    fi

    # Create symlink for CLI access
    log "Creating symlink for ollama CLI..."
    local ollama_cli="/Applications/Ollama.app/Contents/Resources/ollama"
    local symlink_path="/usr/local/bin/ollama"

    if [[ -f "${ollama_cli}" ]]; then
        if ! $DRY_RUN; then
            # Create /usr/local/bin if it doesn't exist
            mkdir -p /usr/local/bin

            # Remove existing symlink if present
            rm -f "${symlink_path}"

            # Create new symlink
            ln -s "${ollama_cli}" "${symlink_path}"
            log_success "Symlink created: ${symlink_path} -> ${ollama_cli}"
        else
            if [[ -L "${symlink_path}" ]]; then
                log "[EXISTS] symlink: ${symlink_path}"
            else
                log "[WOULD CREATE] symlink: ${symlink_path} -> ${ollama_cli}"
            fi
        fi
    else
        log_warning "Ollama CLI not found at ${ollama_cli}"
    fi

    # Note: /Applications/Ollama.app permissions are managed by the system

    # NOTE: We do NOT start Ollama.app here
    # Instead, we'll set up a LaunchAgent service in setup_ollama_service()
    # This prevents running two Ollama instances

    log_success "Ollama installed with Metal GPU acceleration from official source"
    log "Ollama will be configured as a user LaunchAgent service"
}

################################################################################
# Install LM Studio
################################################################################

install_lm_studio() {
    log "Checking LM Studio installation..."

    if [[ -d "/Applications/LM Studio.app" ]]; then
        log_success "LM Studio already installed"
        return 0
    fi

    # Check if available via brew
    if sudo -u "${AGENT_USER}" /opt/homebrew/bin/brew search --cask lm-studio | grep -q "lm-studio"; then
        log "Installing LM Studio..."
        sudo -u "${AGENT_USER}" /opt/homebrew/bin/brew install --cask lm-studio
        log_success "LM Studio installed"
    else
        log_warning "LM Studio not available via Homebrew. Please install manually from https://lmstudio.ai/"
    fi
}

################################################################################
# Pull Ollama Models
################################################################################

pull_ollama_models() {
    log "Checking and pulling Ollama models..."
    echo ""

    local models=("qwen3:8b" "qwen3:1.7b" "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K" "nomic-embed-text" "granite3.1-dense:2b" "granite3.1-moe:1b")
    local pulled_count=0
    local skipped_count=0
    local total_models=${#models[@]}
    local current=0

    # Function to check if model exists in models directory
    check_model_in_directory() {
        local model_name="$1"
        # Extract base model name (before colon)
        local base_name="${model_name%%:*}"
        # Replace / with _ for huggingface models
        base_name="${base_name//\//_}"
        
        # Check if model directory exists in OLLAMA_MODELS_DIR
        if [[ -d "${OLLAMA_MODELS_DIR}/manifests/registry.ollama.ai/library/${base_name}" ]] || \
           [[ -d "${OLLAMA_MODELS_DIR}/manifests/registry.ollama.ai/${base_name}" ]] || \
           [[ -d "${OLLAMA_MODELS_DIR}/manifests/${base_name}" ]]; then
            return 0
        fi
        return 1
    }

    for model in "${models[@]}"; do
        ((current++))
        echo -e "${BLUE}[Model ${current}/${total_models}]${NC} Checking: ${CYAN}${model}${NC}"
        
        # Try to check via ollama list first (if running), then fall back to directory check
        local model_exists=false
        if timeout 5 sudo -u "${AGENT_USER}" /usr/local/bin/ollama list 2>/dev/null | grep -q "^${model%%:*}"; then
            model_exists=true
        elif check_model_in_directory "${model}"; then
            model_exists=true
        fi
        
        if $model_exists; then
            log_success "Model already exists: ${model}"
            ((skipped_count++))
        else
            if ! $DRY_RUN; then
                echo -e "${YELLOW}⏳ Downloading model: ${model}${NC}"
                echo -e "${YELLOW}   This may take several minutes depending on model size...${NC}"
                
                # Run ollama pull with output visible
                if sudo -u "${AGENT_USER}" /usr/local/bin/ollama pull "${model}"; then
                    log_success "Successfully pulled: ${model}"
                    ((pulled_count++))
                else
                    log_warning "Failed to pull ${model}, you may need to pull it manually"
                fi
            else
                log "[WOULD PULL] model: ${model}"
                ((pulled_count++))
            fi
        fi
        echo ""
    done

    if $DRY_RUN; then
        log_success "Would pull ${pulled_count} model(s), skip ${skipped_count} existing model(s)"
    else
        log_success "Pulled ${pulled_count} new model(s), skipped ${skipped_count} existing model(s)"
    fi
}

################################################################################
# Setup Ollama as User LaunchAgent Service
################################################################################

setup_ollama_service() {
    log "Setting up Ollama as user LaunchAgent (runs when ${AGENT_USER} is logged in)..."

    # Run detection if not already done
    detect_ollama_models_directory
    detect_system_ram

    # First, stop any running Ollama services to prevent conflicts
    if pgrep -f "Ollama.app" > /dev/null; then
        log "Stopping Ollama.app to prevent conflicts with LaunchAgent service..."
        if ! $DRY_RUN; then
            sudo -u "${AGENT_USER}" pkill -f "Ollama.app" 2>/dev/null || true
            sleep 2
        else
            log "[WOULD STOP] Ollama.app"
        fi
    fi

    # Stop any existing system-wide LaunchDaemon (from previous installations)
    if launchctl list | grep -q "com.personalagent.ollama"; then
        log "Removing old system-wide Ollama LaunchDaemon..."
        if ! $DRY_RUN; then
            launchctl unload /Library/LaunchDaemons/local.ollama.system.plist 2>/dev/null || true
            rm -f /Library/LaunchDaemons/local.ollama.system.plist
        else
            log "[WOULD REMOVE] old system-wide LaunchDaemon"
        fi
    fi

    local startup_script="${AGENT_HOME}/.local/bin/start_ollama.sh"
    local plist_file="${AGENT_HOME}/Library/LaunchAgents/local.ollama.plist"
    local template_dir="${INSTALL_DIR}/setup"

    # Create directory for startup script
    if ! $DRY_RUN; then
        mkdir -p "${AGENT_HOME}/.local/bin"
        mkdir -p "${AGENT_HOME}/Library/LaunchAgents"
        mkdir -p "${AGENT_HOME}/Library/Logs/ollama"
    else
        if [[ -d "${AGENT_HOME}/.local/bin" ]]; then
            log "[EXISTS] ${AGENT_HOME}/.local/bin"
        else
            log "[WOULD CREATE] ${AGENT_HOME}/.local/bin"
        fi
        if [[ -d "${AGENT_HOME}/Library/LaunchAgents" ]]; then
            log "[EXISTS] ${AGENT_HOME}/Library/LaunchAgents"
        else
            log "[WOULD CREATE] ${AGENT_HOME}/Library/LaunchAgents"
        fi
    fi

    # Create the startup script from template
    if ! $DRY_RUN; then
        log "Creating Ollama startup script from template..."
        sed -e "s|__OLLAMA_MODELS_DIR__|${OLLAMA_MODELS_DIR}|g" \
            -e "s|__SYSTEM_RAM__|${SYSTEM_RAM_GB}|g" \
            -e "s|__MAX_LOADED_MODELS__|${OLLAMA_MAX_LOADED_MODELS}|g" \
            -e "s|__KV_CACHE_TYPE__|${OLLAMA_KV_CACHE_TYPE}|g" \
            "${template_dir}/start_ollama.sh.template" > "${startup_script}"
        
        chmod +x "${startup_script}"
        chown "${AGENT_USER}:staff" "${startup_script}"
        log_success "Startup script created at ${startup_script}"
        log "  Models: ${OLLAMA_MODELS_DIR}"
        log "  RAM optimization: ${OLLAMA_KV_CACHE_TYPE} cache, max ${OLLAMA_MAX_LOADED_MODELS} models"
    else
        if [[ -f "${startup_script}" ]]; then
            log "[EXISTS] ${startup_script}"
        else
            log "[WOULD CREATE] ${startup_script} from template"
        fi
    fi

    # Create the plist file
    if ! $DRY_RUN; then
        log "Creating Ollama LaunchAgent plist..."
        cat > "${plist_file}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>local.ollama</string>
    <key>ProgramArguments</key>
    <array>
      <string>${startup_script}</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
      <key>OLLAMA_MODELS</key>
      <string>${OLLAMA_MODELS_DIR}</string>
      <key>OLLAMA_HOST</key>
      <string>0.0.0.0:11434</string>
      <key>OLLAMA_ORIGINS</key>
      <string>*</string>
      <key>OLLAMA_MAX_LOADED_MODELS</key>
      <string>${OLLAMA_MAX_LOADED_MODELS}</string>
      <key>OLLAMA_NUM_PARALLEL</key>
      <string>8</string>
      <key>OLLAMA_MAX_QUEUE</key>
      <string>512</string>
      <key>OLLAMA_KEEP_ALIVE</key>
      <string>30m</string>
      <key>OLLAMA_KV_CACHE_TYPE</key>
      <string>${OLLAMA_KV_CACHE_TYPE}</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${AGENT_HOME}/Library/Logs/ollama/ollama.out.log</string>
    <key>StandardErrorPath</key>
    <string>${AGENT_HOME}/Library/Logs/ollama/ollama.err.log</string>
  </dict>
</plist>
EOF
        chmod 644 "${plist_file}"
        chown "${AGENT_USER}:staff" "${plist_file}"
        # Remove extended attributes that can cause I/O errors
        xattr -c "${plist_file}" 2>/dev/null || true
        log_success "LaunchAgent plist created"
    else
        if [[ -f "${plist_file}" ]]; then
            log "[EXISTS] ${plist_file}"
        else
            log "[WOULD CREATE] ${plist_file}"
        fi
    fi

    # Create models directory if it doesn't exist
    if ! $DRY_RUN; then
        mkdir -p "${OLLAMA_MODELS_DIR}"
        chmod 755 "${OLLAMA_MODELS_DIR}"
        log_success "Created/verified models directory: ${OLLAMA_MODELS_DIR}"
        log "  To use a different location, run installer with: --ollama-models-dir=/your/path"
    else
        if [[ -d "${OLLAMA_MODELS_DIR}" ]]; then
            log "[EXISTS] ${OLLAMA_MODELS_DIR}"
        else
            log "[WOULD CREATE] ${OLLAMA_MODELS_DIR} directory"
        fi
    fi

    # Try to load the user LaunchAgent service
    if ! $DRY_RUN; then
        log "Loading Ollama LaunchAgent service for user ${AGENT_USER}..."
        
        # Try bootstrap first (modern method)
        if sudo -u "${AGENT_USER}" launchctl bootstrap "gui/$(id -u ${AGENT_USER})" "${plist_file}" 2>/dev/null; then
            log_success "Ollama LaunchAgent loaded via bootstrap"
            OLLAMA_SERVICE_METHOD="LaunchAgent"
        # Fallback to load (older method)
        elif sudo -u "${AGENT_USER}" launchctl load "${plist_file}" 2>/dev/null; then
            log_success "Ollama LaunchAgent loaded via load"
            OLLAMA_SERVICE_METHOD="LaunchAgent"
        else
            log_warning "LaunchAgent load failed - will create Login Item app as fallback"
            OLLAMA_SERVICE_METHOD="LoginItem"
        fi
        
        # Give it a moment to start if successful
        if [[ "${OLLAMA_SERVICE_METHOD}" == "LaunchAgent" ]]; then
            sleep 5
            if sudo -u "${AGENT_USER}" launchctl list | grep -q "local.ollama"; then
                log_success "Ollama LaunchAgent service is running"
            else
                log_warning "LaunchAgent loaded but not running - will use Login Item"
                OLLAMA_SERVICE_METHOD="LoginItem"
            fi
        fi
    else
        log "[WOULD LOAD] LaunchAgent service for user ${AGENT_USER}"
        OLLAMA_SERVICE_METHOD="LaunchAgent"
    fi
}

################################################################################
# Setup Ollama Management Tools
################################################################################

setup_ollama_management() {
    log "Setting up Ollama management tools..."
    
    local template_dir="${INSTALL_DIR}/setup"
    local ollama_service_script="${INSTALL_DIR}/ollama-service.sh"
    local create_app_script="${INSTALL_DIR}/create-ollama-login-app.sh"
    
    # Create ollama-service.sh from template
    if ! $DRY_RUN; then
        log "Creating ollama-service.sh management script..."
        sed -e "s|__OLLAMA_MODELS_DIR__|${OLLAMA_MODELS_DIR}|g" \
            -e "s|__KV_CACHE_TYPE__|${OLLAMA_KV_CACHE_TYPE}|g" \
            -e "s|__MAX_LOADED_MODELS__|${OLLAMA_MAX_LOADED_MODELS}|g" \
            "${template_dir}/ollama-service.sh.template" > "${ollama_service_script}"
        
        chmod +x "${ollama_service_script}"
        chown "${AGENT_USER}:staff" "${ollama_service_script}"
        log_success "Created ${ollama_service_script}"
    else
        if [[ -f "${ollama_service_script}" ]]; then
            log "[EXISTS] ${ollama_service_script}"
        else
            log "[WOULD CREATE] ${ollama_service_script} from template"
        fi
    fi
    
    # Create create-ollama-login-app.sh from template
    if ! $DRY_RUN; then
        log "Creating login app generator script..."
        cp "${template_dir}/create-ollama-login-app.sh.template" "${create_app_script}"
        chmod +x "${create_app_script}"
        chown "${AGENT_USER}:staff" "${create_app_script}"
        log_success "Created ${create_app_script}"
    else
        if [[ -f "${create_app_script}" ]]; then
            log "[EXISTS] ${create_app_script}"
        else
            log "[WOULD CREATE] ${create_app_script}"
        fi
    fi
    
    # If LaunchAgent method failed, create the StartOllama.app now
    if [[ "${OLLAMA_SERVICE_METHOD:-}" == "LoginItem" ]] && ! $DRY_RUN; then
        log "Creating StartOllama.app as fallback auto-start method..."
        sudo -u "${AGENT_USER}" bash "${create_app_script}"
        log_success "StartOllama.app created - add to Login Items for auto-start"
    fi
    
    # Add poe tasks to pyproject.toml if not already present
    if ! $DRY_RUN; then
        local pyproject="${INSTALL_DIR}/pyproject.toml"
        if [[ -f "${pyproject}" ]] && ! grep -q "ollama-status" "${pyproject}"; then
            log "Adding ollama management tasks to pyproject.toml..."
            
            # Find the line with "# === Quick Start Tasks ===" and insert before it
            local insert_line=$(grep -n "# === Quick Start Tasks ===" "${pyproject}" | cut -d: -f1)
            if [[ -n "${insert_line}" ]]; then
                # Create temp file with new tasks
                head -n $((insert_line - 1)) "${pyproject}" > "${pyproject}.tmp"
                cat >> "${pyproject}.tmp" <<'EOFTASKS'
# === Ollama Service Management ===
[tool.poe.tasks.ollama-status]
help = "Check Ollama service status"
cmd = "./ollama-service.sh status"

[tool.poe.tasks.ollama-start]
help = "Start Ollama service"
cmd = "./ollama-service.sh start"

[tool.poe.tasks.ollama-stop]
help = "Stop Ollama service"
cmd = "./ollama-service.sh stop"

[tool.poe.tasks.ollama-restart]
help = "Restart Ollama service"
cmd = "./ollama-service.sh restart"

[tool.poe.tasks.ollama-models]
help = "List available Ollama models"
cmd = "./ollama-service.sh models"

[tool.poe.tasks.ollama-logs]
help = "View Ollama output logs"
cmd = "./ollama-service.sh logs"

EOFTASKS
                tail -n +${insert_line} "${pyproject}" >> "${pyproject}.tmp"
                mv "${pyproject}.tmp" "${pyproject}"
                chown "${AGENT_USER}:staff" "${pyproject}"
                log_success "Added poe tasks for Ollama management"
            fi
        fi
    else
        local pyproject="${INSTALL_DIR}/pyproject.toml"
        if [[ -f "${pyproject}" ]] && ! grep -q "ollama-status" "${pyproject}"; then
            log "[WOULD ADD] poe tasks to pyproject.toml"
        else
            log "[SKIP] poe tasks already in pyproject.toml"
        fi
    fi
}

################################################################################
# Pull LightRAG Docker Images
################################################################################

pull_lightrag_images() {
    log "Checking LightRAG Docker images..."

    local image="egsuchanek/lightrag_pagent:latest"

    # Check if image already exists locally
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${image}$"; then
        log_success "Docker image already exists locally: ${image}"
        return 0
    fi

    # Try to pull the image, but don't fail if authentication is required
    if ! $DRY_RUN; then
        log "Attempting to pull Docker image: ${image}..."
        if docker pull "${image}" 2>/dev/null; then
            log_success "LightRAG image pulled successfully"
        else
            log_warning "Could not pull Docker image (may require docker login)"
            log "Image will be pulled automatically when starting containers with docker-compose"
            log "If you have Docker Hub credentials, you can login with: docker login"
        fi
    else
        log "[WOULD ATTEMPT] Docker pull: ${image}"
        log "[NOTE] Image will be pulled by docker-compose if not present"
    fi
}

################################################################################
# Setup LightRAG Directories
################################################################################

setup_lightrag_directories() {
    log "Setting up LightRAG server directories..."

    local lightrag_server_dir="${DATA_DIR}/lightrag_server"
    local lightrag_memory_dir="${DATA_DIR}/lightrag_memory_server"

    if ! $DRY_RUN; then
        # Create the directories if they don't exist
        mkdir -p "${lightrag_server_dir}"
        mkdir -p "${lightrag_memory_dir}"

        # Copy template configurations from repo if they exist and directories are empty
        if [[ -d "${INSTALL_DIR}/lightrag_server" && ! "$(ls -A "${lightrag_server_dir}" 2>/dev/null)" ]]; then
            cp -r "${INSTALL_DIR}/lightrag_server/"* "${lightrag_server_dir}/"
            log_success "Copied LightRAG server configuration template"
        fi

        if [[ -d "${INSTALL_DIR}/lightrag_memory_server" && ! "$(ls -A "${lightrag_memory_dir}" 2>/dev/null)" ]]; then
            cp -r "${INSTALL_DIR}/lightrag_memory_server/"* "${lightrag_memory_dir}/"
            log_success "Copied LightRAG memory server configuration template"
        fi

        log_success "LightRAG directories configured at:"
        log "  - ${lightrag_server_dir}"
        log "  - ${lightrag_memory_dir}"
    else
        # Check if directories exist in dry-run mode
        if [[ -d "${lightrag_server_dir}" ]]; then
            log "[EXISTS] ${lightrag_server_dir}"
        else
            log "[WOULD CREATE] ${lightrag_server_dir}"
        fi
        
        if [[ -d "${lightrag_memory_dir}" ]]; then
            log "[EXISTS] ${lightrag_memory_dir}"
        else
            log "[WOULD CREATE] ${lightrag_memory_dir}"
        fi
        
        # Check if copy would happen
        if [[ -d "${INSTALL_DIR}/lightrag_server" && ! "$(ls -A "${lightrag_server_dir}" 2>/dev/null)" ]]; then
            log "[WOULD COPY] LightRAG server configuration templates"
        elif [[ -d "${lightrag_server_dir}" && "$(ls -A "${lightrag_server_dir}" 2>/dev/null)" ]]; then
            log "[SKIP] LightRAG server templates (directory not empty)"
        fi
        
        if [[ -d "${INSTALL_DIR}/lightrag_memory_server" && ! "$(ls -A "${lightrag_memory_dir}" 2>/dev/null)" ]]; then
            log "[WOULD COPY] LightRAG memory server configuration templates"
        elif [[ -d "${lightrag_memory_dir}" && "$(ls -A "${lightrag_memory_dir}" 2>/dev/null)" ]]; then
            log "[SKIP] LightRAG memory server templates (directory not empty)"
        fi
    fi
}

################################################################################
# Clone and Setup Repository
################################################################################

setup_repository() {
    log "Setting up Personal Agent repository..."

    # Verify we're running from the repository
    if [[ ! -f "${INSTALL_DIR}/pyproject.toml" ]]; then
        log_error "pyproject.toml not found in ${INSTALL_DIR}"
        log_error "This script must be run from the personal_agent repository directory"
        exit 1
    fi

    log_success "Using repository directory: ${INSTALL_DIR}"

    if ! $DRY_RUN; then
        # Check if .venv already exists
        if [[ -d "${INSTALL_DIR}/.venv" ]]; then
            log "Virtual environment already exists at ${INSTALL_DIR}/.venv"
            log_success "Skipping venv creation"
        else
            log "Creating virtual environment 'persagent' with uv (Python 3.12)..."
            sudo -u "${AGENT_USER}" bash -c "source '${PROFILE_FILE}' 2>/dev/null || true; cd '${INSTALL_DIR}' && uv venv .venv --python /opt/homebrew/opt/python@3.12/bin/python3.12 --seed --prompt persagent"
            log_success "Virtual environment created"
        fi

        log "Installing dependencies with Poetry..."
        sudo -u "${AGENT_USER}" bash -c "source '${PROFILE_FILE}' 2>/dev/null || true; cd '${INSTALL_DIR}' && poetry install"

        log_success "Dependencies installed"
    else
        if [[ -d "${INSTALL_DIR}/.venv" ]]; then
            log "[EXISTS] virtual environment in ${INSTALL_DIR}/.venv"
        else
            log "[WOULD CREATE] virtual environment 'persagent' with uv (Python 3.12) in ${INSTALL_DIR}"
        fi
        if [[ -f "${INSTALL_DIR}/poetry.lock" ]]; then
            log "[SKIP] Poetry dependencies (already installed)"
        else
            log "[WOULD INSTALL] dependencies with Poetry in ${INSTALL_DIR}"
        fi
    fi
}

################################################################################
# Configure Environment
################################################################################

configure_environment() {
    log "Configuring environment..."

    local env_file="${AGENT_HOME}/.env"

    if [[ -f "${env_file}" ]]; then
        log_success ".env file already exists at ${env_file}, skipping creation"
        return 0
    fi

    # Create .env file in home directory
    cat > "${env_file}" <<EOF
# Personal AI Agent Environment Variables
# Minimal version - only essential overrides
# Generated on $(date)

# =============================================================================
# BASIC CONFIGURATION
# =============================================================================
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40

LOG_LEVEL=INFO

# =============================================================================
# DIRECTORY CONFIGURATION
# =============================================================================

ROOT_DIR=/
HOME_DIR=${AGENT_HOME}
REPO_DIR=\${HOME_DIR}/repos

# =============================================================================
# AI MODEL CONFIGURATION
# =============================================================================

PROVIDER="ollama"

# =============================================================================
# API Access tokens - secret
# =============================================================================

# GitHub Personal Access Token
GITHUB_PERSONAL_ACCESS_TOKEN=yourtoken
# GitHub Token (for Agno GithubTools)
GITHUB_TOKEN=yourtoken
# GitHub Access Token (alternative name)
GITHUB_ACCESS_TOKEN=yourtoken

# Brave Search API Key  
BRAVE_API_KEY=yourtoken

# MULTIMODAL AGENTS: API Keys for Media Generation
MODELS_LAB_API_KEY=yourtoken
ELEVEN_LABS_API_KEY=yourtoken
GIPHY_API_KEY=yourtoken
OPENAI_API_KEY=sk-proj-yourtoken
EOF

    # Set proper permissions
    chmod 600 "${env_file}"

    # Create data directory
    mkdir -p "${DATA_DIR}"

    log_success "Environment configured"
}

################################################################################
# Set Permissions
################################################################################

set_permissions() {
    log "Setting proper permissions..."

    # Make scripts executable
    chmod +x "${INSTALL_DIR}/scripts/"*.sh 2>/dev/null || true
    chmod +x "${INSTALL_DIR}/"*.sh 2>/dev/null || true

    log_success "Permissions set"
}

################################################################################
# Post-Install Health Checks
################################################################################

health_checks() {
    log "Running post-install health checks..."

    local all_ok=true

    # Check Homebrew
    if sudo -u "${AGENT_USER}" /opt/homebrew/bin/brew --version &>/dev/null; then
        log_success "Homebrew: OK"
    else
        log_error "Homebrew: FAILED"
        all_ok=false
    fi

    # Check Python
    if sudo -u "${AGENT_USER}" /opt/homebrew/opt/python@3.12/bin/python3.12 --version &>/dev/null; then
        log_success "Python 3.12: OK"
    else
        log_error "Python 3.12: FAILED"
        all_ok=false
    fi

    # Check Poetry
    if sudo -u "${AGENT_USER}" bash -c "source ${PROFILE_FILE} && poetry --version" &>/dev/null; then
        log_success "Poetry: OK"
    else
        log_error "Poetry: FAILED"
        all_ok=false
    fi

    # Check Docker
    if docker info &>/dev/null; then
        log_success "Docker: OK"
    else
        log_warning "Docker: Not running (may need manual start)"
    fi

    # Check Ollama symlink
    if [[ -L "/usr/local/bin/ollama" ]]; then
        local symlink_target=$(readlink "/usr/local/bin/ollama")
        if [[ "${symlink_target}" == *"Resources/ollama" ]]; then
            log_success "Ollama symlink: OK (${symlink_target})"
        else
            log_warning "Ollama symlink: Incorrect path (${symlink_target})"
        fi
    else
        log_warning "Ollama symlink: Missing"
    fi

    # Check Ollama service
    if sudo -u "${AGENT_USER}" launchctl list | grep -q "local.ollama"; then
        log_success "Ollama LaunchAgent: Running"
    elif [[ -f "${AGENT_HOME}/Applications/StartOllama.app/Contents/MacOS/StartOllama" ]]; then
        log_success "Ollama Login Item app: Created (add to Login Items)"
    else
        log_warning "Ollama service: Not configured"
    fi

    # Check Ollama models directory
    if [[ -d "${OLLAMA_MODELS_DIR}" ]]; then
        log_success "Ollama models directory: OK (${OLLAMA_MODELS_DIR})"
    else
        log_warning "Ollama models directory: Not found (${OLLAMA_MODELS_DIR})"
    fi

    # Check Ollama API (if running)
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        local version=$(curl -s http://localhost:11434/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        log_success "Ollama API: Responding (version ${version})"
    else
        log_warning "Ollama API: Not responding (service may not be started yet)"
    fi

    # Check install directory
    if [[ -d "${INSTALL_DIR}" ]]; then
        log_success "Install directory: OK"
    else
        log_error "Install directory: FAILED"
        all_ok=false
    fi

    if $all_ok; then
        log_success "All critical health checks passed!"
    else
        log_warning "Some health checks failed, please review above"
    fi
}

################################################################################
# Print Post-Install Instructions
################################################################################

print_instructions() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if $DRY_RUN; then
        echo -e "${MAGENTA}Dry-Run Complete!${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "This was a dry-run. No changes were made to your system."
        echo ""
        echo "To perform the actual installation, run:"
        echo "   sudo ./install-personal-agent.sh"
        echo ""
    else
        echo -e "${GREEN}Personal Agent Installation Complete!${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Next Steps:"
        echo ""
        echo "1. Log out and log back in as ${AGENT_USER}, or reload your shell:"
        echo "   source ${PROFILE_FILE}"
        echo ""
        echo "2. Navigate to the repository:"
        echo "   cd ${INSTALL_DIR}"
        echo ""
        echo "3. Start LightRAG services:"
        echo "   ./smart-restart-lightrag.sh"
        echo ""
        echo "4. Start the Personal Agent:"
        echo "   poe serve-persag              # Web interface"
        echo "   poe cli                       # Command-line interface"
        echo ""
        echo "5. Optional: Configure API keys in:"
        echo "   ${INSTALL_DIR}/.env"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo -e "${YELLOW}Ollama Configuration (${SYSTEM_RAM_GB}GB RAM):${NC}"
        echo ""
        echo "• Models Directory: ${OLLAMA_MODELS_DIR}"
        echo "• KV Cache Type: ${OLLAMA_KV_CACHE_TYPE} (optimized for ${SYSTEM_RAM_GB}GB RAM)"
        echo "• Max Loaded Models: ${OLLAMA_MAX_LOADED_MODELS}"
        echo "• Host: 0.0.0.0:11434"
        echo ""
        if [[ "${OLLAMA_SERVICE_METHOD:-}" == "LaunchAgent" ]]; then
            echo "• Auto-start: LaunchAgent (starts when you log in)"
            echo "  Check status: poe ollama-status"
            echo "  View logs: poe ollama-logs"
            echo "  Manage: launchctl [load|unload] ${AGENT_HOME}/Library/LaunchAgents/local.ollama.plist"
        else
            echo "• Auto-start: Login Item app created"
            echo "  Add ~/Applications/StartOllama.app to Login Items:"
            echo "  System Settings > General > Login Items > Click '+' > Select StartOllama.app"
            echo "  Or run: osascript -e 'tell application \"System Events\" to make login item at end with properties {path:\"${AGENT_HOME}/Applications/StartOllama.app\", hidden:false}'"
        fi
        echo ""
        echo "• Management commands:"
        echo "  poe ollama-status    # Check if running"
        echo "  poe ollama-start     # Start service"
        echo "  poe ollama-stop      # Stop service"
        echo "  poe ollama-restart   # Restart service"
        echo "  poe ollama-models    # List models"
        echo "  poe ollama-logs      # View logs"
        echo ""
    fi
    echo "Installation log saved to: ${LOG_FILE}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

################################################################################
# Main Installation Flow
################################################################################

main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}Personal Agent Installer for macOS${NC}"
    if $DRY_RUN; then
        echo -e "${MAGENTA}DRY-RUN MODE - No changes will be made${NC}"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Create initial log directory
    if ! $DRY_RUN; then
        mkdir -p "${AGENT_HOME}" 2>/dev/null || true
        touch "${AGENT_HOME}/install.log" 2>/dev/null && LOG_FILE="${AGENT_HOME}/install.log" || LOG_FILE="/tmp/personal_agent_install.log"
    else
        LOG_FILE="/tmp/personal_agent_install_dryrun.log"
        echo "Dry-run log will be saved to: ${LOG_FILE}"
    fi

    preflight_checks
    install_homebrew
    install_python
    install_uv
    install_poetry
    install_docker
    install_ollama
    install_lm_studio
    setup_repository
    configure_environment
    setup_ollama_service
    setup_ollama_management
    pull_ollama_models
    pull_lightrag_images
    setup_lightrag_directories
    set_permissions
    health_checks
    print_instructions
}

# Run main installation
main "$@"
