#!/bin/bash

# .env Restore Script
# Restores .env file from backup with safety checks

set -e

# Configuration
BACKUP_DIR="backups"
ENV_FILE=".env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    print_error "Backup directory '$BACKUP_DIR' not found!"
    exit 1
fi

# List available backups
print_info "Available backups:"
echo "----------------------------------------"
backup_files=($(ls -t "$BACKUP_DIR"/.env.backup.* 2>/dev/null || true))
encrypted_files=($(ls -t "$BACKUP_DIR"/.env.backup.*.gpg 2>/dev/null || true))

if [ ${#backup_files[@]} -eq 0 ] && [ ${#encrypted_files[@]} -eq 0 ]; then
    print_error "No backup files found!"
    exit 1
fi

# Display regular backups
counter=1
declare -A file_map
for file in "${backup_files[@]}"; do
    basename_file=$(basename "$file")
    timestamp=$(echo "$basename_file" | sed 's/.env.backup.//' | sed 's/\([0-9]\{8\}\)_\([0-9]\{6\}\)/\1 \2/')
    formatted_date=$(date -j -f "%Y%m%d %H%M%S" "$timestamp" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$timestamp")
    echo "$counter) $basename_file ($formatted_date)"
    file_map[$counter]="$file"
    ((counter++))
done

# Display encrypted backups
for file in "${encrypted_files[@]}"; do
    basename_file=$(basename "$file")
    timestamp=$(echo "$basename_file" | sed 's/.env.backup.//' | sed 's/.gpg//' | sed 's/\([0-9]\{8\}\)_\([0-9]\{6\}\)/\1 \2/')
    formatted_date=$(date -j -f "%Y%m%d %H%M%S" "$timestamp" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$timestamp")
    echo "$counter) $basename_file ($formatted_date) [ENCRYPTED]"
    file_map[$counter]="$file"
    ((counter++))
done

echo "----------------------------------------"

# Get user selection
read -p "Select backup to restore (1-$((counter-1))): " selection

if [[ ! "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -ge "$counter" ]; then
    print_error "Invalid selection!"
    exit 1
fi

selected_file="${file_map[$selection]}"
print_info "Selected: $(basename "$selected_file")"

# Check if current .env exists and create backup
if [ -f "$ENV_FILE" ]; then
    print_warning "Current .env file exists!"
    read -p "Create backup of current .env before restoring? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        current_backup="${BACKUP_DIR}/.env.backup.current.$(date +"%Y%m%d_%H%M%S")"
        cp "$ENV_FILE" "$current_backup"
        print_status "Current .env backed up to: $(basename "$current_backup")"
    fi
fi

# Handle encrypted files
if [[ "$selected_file" == *.gpg ]]; then
    if ! command -v gpg &> /dev/null; then
        print_error "GPG not found! Cannot decrypt encrypted backup."
        exit 1
    fi
    
    print_status "Decrypting backup..."
    temp_file=$(mktemp)
    if gpg --decrypt --output "$temp_file" "$selected_file"; then
        cp "$temp_file" "$ENV_FILE"
        rm "$temp_file"
        print_status "Encrypted backup restored successfully!"
    else
        print_error "Failed to decrypt backup!"
        rm -f "$temp_file"
        exit 1
    fi
else
    # Regular backup
    cp "$selected_file" "$ENV_FILE"
    print_status "Backup restored successfully!"
fi

print_status "Current .env file has been restored from backup."
print_info "Backup source: $(basename "$selected_file")"
