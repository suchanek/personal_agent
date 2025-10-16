#!/bin/bash

################################################################################
# Personal Agent Installer for macOS
#
# This script installs and configures the Personal AI Agent system on macOS.
# It must be run as root or with sudo, and assumes the 'personalagent' user
# already exists on the system.
#
# Usage:
#   sudo ./install-personal-agent.sh           # Full installation
#   sudo ./install-personal-agent.sh --dry-run # Test without making changes
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
AGENT_USER="persagent"
AGENT_HOME="/Users/${AGENT_USER}"
INSTALL_DIR="${AGENT_HOME}"
DATA_DIR="${AGENT_HOME}/.persag"
LOG_FILE="${INSTALL_DIR}/install.log"
REPO_URL="https://github.com/suchanek/personal_agent.git"  # Update with actual repo URL

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

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: sudo $0 [--dry-run]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

    # Check if personalagent user exists
    if ! id "${AGENT_USER}" &>/dev/null; then
        log_error "User '${AGENT_USER}' does not exist. Please create it first."
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
    local ollama_cli="/Applications/Ollama.app/Contents/MacOS/ollama"
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
            log "[WOULD CREATE] symlink: ${symlink_path} -> ${ollama_cli}"
        fi
    else
        log_warning "Ollama CLI not found at ${ollama_cli}"
    fi

    # Ensure proper permissions
    if ! $DRY_RUN; then
        chown -R "${AGENT_USER}:staff" "/Applications/Ollama.app" 2>/dev/null || true
    else
        log "[WOULD SET] permissions on /Applications/Ollama.app"
    fi

    # Start Ollama if not running
    if ! pgrep -f "Ollama.app" > /dev/null; then
        log "Starting Ollama..."
        if ! $DRY_RUN; then
            sudo -u "${AGENT_USER}" open -a Ollama
            sleep 10
        else
            log "[WOULD START] Ollama.app as ${AGENT_USER}"
        fi
    fi

    log_success "Ollama is ready with Metal GPU acceleration"
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

    local models=("qwen3:8b" "qwen3:1.7b" "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K" "nomic-embed-text")
    local pulled_count=0
    local skipped_count=0

    for model in "${models[@]}"; do
        # Check if model already exists
        if sudo -u "${AGENT_USER}" /usr/local/bin/ollama list 2>/dev/null | grep -q "^${model%%:*}" || \
           sudo -u "${AGENT_USER}" ollama list 2>/dev/null | grep -q "^${model%%:*}"; then
            log_success "Model already exists: ${model}"
            ((skipped_count++))
        else
            if ! $DRY_RUN; then
                log "Pulling model: ${model}..."
                if sudo -u "${AGENT_USER}" /usr/local/bin/ollama pull "${model}" 2>/dev/null || \
                   sudo -u "${AGENT_USER}" ollama pull "${model}" 2>/dev/null; then
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
    done

    if $DRY_RUN; then
        log_success "Would pull ${pulled_count} model(s), skip ${skipped_count} existing model(s)"
    else
        log_success "Pulled ${pulled_count} new model(s), skipped ${skipped_count} existing model(s)"
    fi
}

################################################################################
# Setup Ollama as LaunchAgent Service
################################################################################

setup_ollama_service() {
    log "Setting up Ollama LaunchAgent service..."

    local startup_script="/usr/local/bin/start_ollama.sh"
    local launch_agents_dir="${AGENT_HOME}/Library/LaunchAgents"
    local plist_file="${launch_agents_dir}/com.personal-agent.ollama.plist"

    # Create the startup script in /usr/local/bin
    if ! $DRY_RUN; then
        log "Creating Ollama startup script at ${startup_script}..."
        cat > "${startup_script}" <<'EOF'
#!/bin/bash
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_ORIGINS="*"
export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_QUEUE=512
export OLLAMA_KEEP_ALIVE="10m"
export OLLAMA_DEBUG=1
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE="f16"
# export OLLAMA_LOG_LEVEL=INFO
export OLLAMA_CONTEXT_LENGTH=12232


exec /usr/local/bin/ollama serve
EOF
        chmod +x "${startup_script}"
        log_success "Startup script created"
    else
        log "[WOULD CREATE] ${startup_script}"
    fi

    # Create LaunchAgents directory if it doesn't exist
    if ! $DRY_RUN; then
        mkdir -p "${launch_agents_dir}"
    else
        log "[WOULD CREATE] ${launch_agents_dir}"
    fi

    # Create the plist file
    if ! $DRY_RUN; then
        cat > "${plist_file}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.personal-agent.ollama</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${startup_script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${AGENT_HOME}/Library/Logs/ollama.log</string>
    <key>StandardErrorPath</key>
    <string>${AGENT_HOME}/Library/Logs/ollama-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OLLAMA_HOST</key>
        <string>0.0.0.0:11434</string>
        <key>OLLAMA_NUM_PARALLEL</key>
        <string>2</string>
        <key>OLLAMA_MAX_LOADED_MODELS</key>
        <string>2</string>
    </dict>
</dict>
</plist>
EOF

        # Set proper ownership
        chown "${AGENT_USER}:staff" "${plist_file}"
        chmod 644 "${plist_file}"

        # Create logs directory
        mkdir -p "${AGENT_HOME}/Library/Logs"
        chown "${AGENT_USER}:staff" "${AGENT_HOME}/Library/Logs"

        # Load the service as the agent user
        sudo -u "${AGENT_USER}" launchctl load "${plist_file}" 2>/dev/null || true

        log_success "Ollama service configured"
    else
        log "[WOULD CREATE] ${plist_file}"
        log "[WOULD LOAD] LaunchAgent service"
    fi
}

################################################################################
# Pull LightRAG Docker Images
################################################################################

pull_lightrag_images() {
    log "Checking and pulling LightRAG Docker images..."

    local image="ghcr.io/suchanek/lightrag_pagent:latest"

    # Check if image already exists
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${image}$"; then
        log_success "Docker image already exists: ${image}"
    else
        if ! $DRY_RUN; then
            log "Pulling Docker image: ${image}..."
            if docker pull "${image}"; then
                log_success "LightRAG image pulled successfully"
            else
                log_error "Failed to pull LightRAG image"
                return 1
            fi
        else
            log "[WOULD PULL] Docker image: ${image}"
        fi
    fi
}

################################################################################
# Clone and Setup Repository
################################################################################

setup_repository() {
    log "Setting up Personal Agent repository..."

    # Create install directory if it doesn't exist
    if [[ ! -d "${INSTALL_DIR}" ]]; then
        if ! $DRY_RUN; then
            log "Cloning repository..."
            sudo -u "${AGENT_USER}" git clone "${REPO_URL}" "${INSTALL_DIR}"
            log_success "Repository cloned"
        else
            log "[WOULD CLONE] ${REPO_URL} to ${INSTALL_DIR}"
        fi
    else
        log_warning "Install directory already exists, skipping clone"
    fi

    if ! $DRY_RUN; then
        # Change to install directory
        cd "${INSTALL_DIR}"

        log "Creating virtual environment with uv..."
        sudo -u "${AGENT_USER}" bash -c "cd ${INSTALL_DIR} && source ${PROFILE_FILE} 2>/dev/null && uv venv"

        log "Installing dependencies with Poetry..."
        sudo -u "${AGENT_USER}" bash -c "cd ${INSTALL_DIR} && source ${PROFILE_FILE} 2>/dev/null && poetry install"

        log_success "Dependencies installed"
    else
        log "[WOULD CREATE] virtual environment with uv"
        log "[WOULD INSTALL] dependencies with Poetry"
    fi
}

################################################################################
# Configure Environment
################################################################################

configure_environment() {
    log "Configuring environment..."

    local env_file="${INSTALL_DIR}/.env"

    if [[ -f "${env_file}" ]]; then
        log_warning ".env file already exists, backing up..."
        cp "${env_file}" "${env_file}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Create .env file
    cat > "${env_file}" <<EOF
# Personal Agent Configuration
# Generated on $(date)

# User Configuration
USER_ID=${AGENT_USER}
PERSAG_ROOT=${DATA_DIR}

# Ollama Configuration
OLLAMA_URL=http://localhost:11434

# LightRAG Configuration
LIGHTRAG_URL=http://localhost:9621
LIGHTRAG_MEMORY_URL=http://localhost:9622

# Optional: Add your API keys below
# GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
# BRAVE_API_KEY=your_api_key_here
EOF

    # Set proper ownership
    chown "${AGENT_USER}:staff" "${env_file}"
    chmod 600 "${env_file}"

    # Create data directory
    mkdir -p "${DATA_DIR}"
    chown -R "${AGENT_USER}:staff" "${DATA_DIR}"

    log_success "Environment configured"
}

################################################################################
# Set Permissions
################################################################################

set_permissions() {
    log "Setting proper permissions..."

    # Set ownership of install directory
    chown -R "${AGENT_USER}:staff" "${INSTALL_DIR}"

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

    # Check Ollama
    if pgrep -f "Ollama.app" > /dev/null; then
        log_success "Ollama: OK"
    else
        log_warning "Ollama: Not running"
    fi

    # Check install directory
    if [[ -d "${INSTALL_DIR}" ]]; then
        log_success "Install directory: OK"
    else
        log_error "Install directory: FAILED"
        all_ok=false
    fi

    if $all_ok; then
        log_success "All health checks passed!"
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
        echo "1. Switch to the personalagent user:"
        echo "   sudo su - personalagent"
        echo ""
        echo "2. Start LightRAG services:"
        echo "   cd ${INSTALL_DIR}"
        echo "   ./smart-restart-lightrag.sh"
        echo ""
        echo "3. Start the Personal Agent:"
        echo "   poe serve-persag              # Web interface"
        echo "   poe cli                       # Command-line interface"
        echo ""
        echo "4. Optional: Configure API keys in:"
        echo "   ${INSTALL_DIR}/.env"
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
        mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || mkdir -p "/tmp"
        touch "${LOG_FILE}" 2>/dev/null || LOG_FILE="/tmp/personal_agent_install.log"
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
    pull_ollama_models
    setup_repository
    configure_environment
    setup_ollama_service
    pull_lightrag_images
    set_permissions
    health_checks
    print_instructions
}

# Run main installation
main "$@"
