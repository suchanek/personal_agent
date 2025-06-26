#!/bin/bash

# Automated .env Backup Script
# Creates timestamped backups without user interaction

set -e

# Configuration
BACKUP_DIR="backups"
ENV_FILE=".env"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/.env.backup.${TIMESTAMP}"
MAX_BACKUPS=20  # Keep more backups for automated runs

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found!"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
print_status "Creating automated backup: $BACKUP_FILE"
cp "$ENV_FILE" "$BACKUP_FILE"

# Clean up old backups (keep only MAX_BACKUPS most recent)
print_status "Cleaning up old backups (keeping $MAX_BACKUPS most recent)..."
cd "$BACKUP_DIR"
ls -t .env.backup.* 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm
cd ..

print_status "Automated backup completed successfully!"

# Optional: Log to a backup log file
echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup created: $BACKUP_FILE" >> "${BACKUP_DIR}/backup.log"
