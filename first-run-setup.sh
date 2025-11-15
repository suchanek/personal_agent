#!/bin/bash

################################################################################
# Personal Agent First-Run Setup
#
# This script initializes the Personal Agent system with a user profile.
# Run this after installation to create your first user and start services.
#
# Usage:
#   ./first-run-setup.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSAGENT_DIR="${HOME}/.persagent"
USER_ID_FILE="${PERSAGENT_DIR}/env.userid"

################################################################################
# Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

# Validate user_id format (lowercase alphanumeric, dots, hyphens, underscores)
validate_user_id() {
    local user_id="$1"
    if [[ ! "$user_id" =~ ^[a-z0-9._-]+$ ]]; then
        return 1
    fi
    return 0
}

# Normalize user name to user_id (firstname.lastname format)
normalize_to_user_id() {
    local name="$1"
    # Convert to lowercase, replace spaces with dots, remove invalid chars
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/ /./g' | sed 's/[^a-z0-9._-]//g'
}

################################################################################
# Main Setup
################################################################################

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}🚀 Personal Agent First-Run Setup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if user already configured
if [[ -f "$USER_ID_FILE" ]]; then
    EXISTING_USER=$(cat "$USER_ID_FILE")
    log_warning "User already configured: ${EXISTING_USER}"
    echo ""
    read -p "Do you want to create a different user? (y/N): " create_new
    if [[ ! "$create_new" =~ ^[Yy]$ ]]; then
        log_info "Using existing user: ${EXISTING_USER}"
        echo ""
        log_info "To start the system, run:"
        echo -e "  ${CYAN}source .venv/bin/activate${NC}"
        echo -e "  ${CYAN}poe serve-persag${NC}              # Web interface"
        echo -e "  ${CYAN}poe cli${NC}                       # Command-line interface"
        echo ""
        exit 0
    fi
fi

# Check if .venv exists
if [[ ! -d "${SCRIPT_DIR}/.venv" ]]; then
    log_error "Virtual environment not found at ${SCRIPT_DIR}/.venv"
    log_error "Please run the installer first: sudo ./install-personal-agent.sh"
    exit 1
fi

# Get user information
echo -e "${BLUE}Creating your user profile...${NC}"
echo ""

# Get user's full name
default_name=$(id -F 2>/dev/null || whoami)
read -p "Your full name (e.g., 'John Smith') [${default_name}]: " user_name
user_name=${user_name:-$default_name}

# Generate suggested user_id from name
suggested_id=$(normalize_to_user_id "$user_name")
echo ""
echo -e "${CYAN}Suggested user ID:${NC} ${suggested_id}"
echo -e "${YELLOW}Note:${NC} User ID should be lowercase (e.g., 'john.smith', 'alice.jones')"
read -p "User ID [${suggested_id}]: " user_id
user_id=${user_id:-$suggested_id}

# Validate user_id
while ! validate_user_id "$user_id"; do
    log_error "Invalid user ID format. Use lowercase letters, numbers, dots, hyphens, or underscores."
    read -p "User ID: " user_id
done

# Get birth year (optional)
echo ""
read -p "Birth year (optional, press Enter to skip): " birth_year

# Get gender (optional)
echo ""
echo "Gender (optional):"
echo "  1) Male"
echo "  2) Female"
echo "  3) N/A (default)"
read -p "Choice [3]: " gender_choice
case "$gender_choice" in
    1) gender="Male" ;;
    2) gender="Female" ;;
    *) gender="N/A" ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Creating user profile...${NC}"
echo ""
echo -e "  Name:       ${CYAN}${user_name}${NC}"
echo -e "  User ID:    ${CYAN}${user_id}${NC}"
[[ -n "$birth_year" ]] && echo -e "  Birth Year: ${CYAN}${birth_year}${NC}"
echo -e "  Gender:     ${CYAN}${gender}${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Proceed with user creation? (Y/n): " confirm
if [[ "$confirm" =~ ^[Nn]$ ]]; then
    log_warning "User creation cancelled"
    exit 0
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source "${SCRIPT_DIR}/.venv/bin/activate"

# Build switch-user command
SWITCH_CMD="python ${SCRIPT_DIR}/switch-user.py \"${user_id}\" --user-name \"${user_name}\""
[[ -n "$birth_year" ]] && SWITCH_CMD="${SWITCH_CMD} --birth-year ${birth_year}"
[[ "$gender" != "N/A" ]] && SWITCH_CMD="${SWITCH_CMD} --gender \"${gender}\""
SWITCH_CMD="${SWITCH_CMD} --create-if-missing"

# Create user
log_info "Creating user profile..."
if eval "$SWITCH_CMD"; then
    log_success "User profile created successfully"
else
    log_error "Failed to create user profile"
    exit 1
fi

# Restart LightRAG services
echo ""
log_info "Starting LightRAG services..."
if "${SCRIPT_DIR}/smart-restart-lightrag.sh"; then
    log_success "LightRAG services started successfully"
else
    log_warning "Failed to start LightRAG services automatically"
    log_info "You can start them manually with: ./smart-restart-lightrag.sh"
fi

# Final instructions
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${CYAN}Your Personal Agent is ready to use!${NC}"
echo ""
echo "To start the system:"
echo ""
echo -e "  1. Activate the virtual environment:"
echo -e "     ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo -e "  2. Choose your interface:"
echo -e "     ${YELLOW}poe serve-persag${NC}              # Web interface (recommended)"
echo -e "     ${YELLOW}poe cli${NC}                       # Command-line interface"
echo -e "     ${YELLOW}poe team${NC}                      # Team CLI interface"
echo ""
echo -e "  3. Access the web interface at:"
echo -e "     ${CYAN}http://localhost:8501${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
