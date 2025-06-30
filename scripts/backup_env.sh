#!/bin/bash

# .env Backup Script
# Creates timestamped backups of .env file with optional encryption

set -e

# Configuration
BACKUP_DIR="backups"
ENV_FILE=".env"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/.env.backup.${TIMESTAMP}"
MAX_BACKUPS=10  # Keep only the 10 most recent backups

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found!"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
print_status "Creating backup: $BACKUP_FILE"
cp "$ENV_FILE" "$BACKUP_FILE"

# Optional: Create encrypted backup
if command -v gpg &> /dev/null; then
    read -p "Create encrypted backup? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Creating encrypted backup..."
        gpg --symmetric --cipher-algo AES256 --output "${BACKUP_FILE}.gpg" "$BACKUP_FILE"
        print_status "Encrypted backup created: ${BACKUP_FILE}.gpg"
        
        read -p "Remove unencrypted backup? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm "$BACKUP_FILE"
            print_status "Unencrypted backup removed"
        fi
    fi
fi

# Clean up old backups (keep only MAX_BACKUPS most recent)
print_status "Cleaning up old backups (keeping $MAX_BACKUPS most recent)..."
cd "$BACKUP_DIR"
ls -t .env.backup.* 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm
ls -t .env.backup.*.gpg 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm
cd ..

print_status "Backup completed successfully!"
print_status "Available backups:"
ls -la "$BACKUP_DIR"/.env.backup.*
