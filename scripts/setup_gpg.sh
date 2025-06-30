#!/bin/bash

# GPG Setup Script for .env Backup Encryption
# This script helps you create a GPG key for encrypting sensitive backups

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check if GPG is installed
if ! command -v gpg &> /dev/null; then
    print_error "GPG is not installed!"
    print_info "Install with: brew install gnupg"
    exit 1
fi

print_header "GPG Setup for .env Backup Encryption"

# Check if user already has GPG keys
existing_keys=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep -c "sec " || echo "0")

if [ "$existing_keys" -gt 0 ]; then
    print_info "You already have $existing_keys GPG key(s):"
    gpg --list-secret-keys --keyid-format LONG
    echo
    read -p "Do you want to create a new key specifically for backup encryption? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Using existing GPG keys. You're all set!"
        print_info "Test encryption with: ./scripts/backup_env.sh"
        exit 0
    fi
fi

print_info "Creating a new GPG key for backup encryption..."
print_warning "You'll be prompted for:"
print_warning "1. Key type (choose RSA and RSA - option 1)"
print_warning "2. Key size (4096 bits recommended)"
print_warning "3. Expiration (0 = never expire, or set to 2-5 years)"
print_warning "4. Your name and email"
print_warning "5. A passphrase (IMPORTANT: Remember this!)"

echo
read -p "Press Enter to continue with key generation..."

# Generate GPG key with batch mode for easier setup
cat > /tmp/gpg_batch_config << EOF
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: $(whoami) Backup Key
Name-Email: $(whoami)@$(hostname)
Expire-Date: 2y
Passphrase: 
%commit
%echo GPG key generation complete
EOF

print_status "Generating GPG key..."
print_warning "You'll be prompted to enter a passphrase. Choose a strong one and remember it!"

# Use interactive mode for better user experience
gpg --full-generate-key

print_status "GPG key generation completed!"

# Show the new key
print_info "Your GPG keys:"
gpg --list-secret-keys --keyid-format LONG

print_header "GPG Setup Complete!"
print_status "You can now use encrypted backups with:"
print_status "  ./scripts/backup_env.sh"
print_status ""
print_warning "IMPORTANT: Remember your GPG passphrase!"
print_warning "Without it, you cannot decrypt your backups."
print_status ""
print_info "Test your setup:"
print_info "  1. Run: ./scripts/backup_env.sh"
print_info "  2. Choose 'y' for encryption when prompted"
print_info "  3. Test restore: ./scripts/restore_env.sh"

# Clean up
rm -f /tmp/gpg_batch_config
