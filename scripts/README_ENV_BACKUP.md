# .env Backup System

This directory contains scripts to safely backup and restore your `.env` file containing sensitive API keys and configuration.

## Scripts Overview

### 1. `backup_env.sh` - Interactive Backup
Creates timestamped backups with optional GPG encryption.

**Features:**
- Timestamped backups (format: `.env.backup.YYYYMMDD_HHMMSS`)
- Optional GPG encryption for extra security
- Automatic cleanup of old backups (keeps 10 most recent)
- Interactive prompts for encryption options

**Usage:**
```bash
./scripts/backup_env.sh
```

### 2. `auto_backup_env.sh` - Automated Backup
Silent backup script suitable for cron jobs or regular automation.

**Features:**
- No user interaction required
- Keeps 20 most recent backups
- Logs backup activity to `backups/backup.log`
- Timestamped output for monitoring

**Usage:**
```bash
./scripts/auto_backup_env.sh
```

**Cron Job Example (daily at 2 AM):**
```bash
# Add to crontab with: crontab -e
0 2 * * * cd /Users/egs/repos/personal_agent && ./scripts/auto_backup_env.sh >> /tmp/env_backup.log 2>&1
```

### 3. `restore_env.sh` - Interactive Restore
Restores `.env` from any available backup with safety checks.

**Features:**
- Lists all available backups with timestamps
- Handles both regular and encrypted backups
- Creates backup of current `.env` before restoring
- Supports GPG decryption

**Usage:**
```bash
./scripts/restore_env.sh
```

## Security Considerations

### Current Setup
- ✅ `.env` is in `.gitignore` (not tracked in git)
- ✅ Backups are stored locally in `backups/` directory
- ✅ Backup directory should also be in `.gitignore`

### Recommended Security Practices

1. **Use Encryption for Sensitive Backups:**
   ```bash
   # The interactive backup script offers GPG encryption
   ./scripts/backup_env.sh
   # Choose 'y' when prompted for encryption
   ```

2. **Secure Backup Storage:**
   - Consider storing encrypted backups on secure cloud storage
   - Use external encrypted drives for critical backups
   - Never store unencrypted backups in cloud services

3. **Regular Backup Schedule:**
   ```bash
   # Add to crontab for daily backups
   crontab -e
   # Add: 0 2 * * * cd /Users/egs/repos/personal_agent && ./scripts/auto_backup_env.sh
   ```

4. **Backup Verification:**
   ```bash
   # Periodically test restore process
   ./scripts/restore_env.sh
   ```

## File Structure

```
personal_agent/
├── .env                    # Your main environment file (not in git)
├── .env.example           # Template file (safe to commit)
├── backups/               # Backup directory (should be in .gitignore)
│   ├── .env.backup.20250625_214109
│   ├── .env.backup.20250625_214038
│   ├── backup.log         # Automated backup log
│   └── *.gpg             # Encrypted backups
└── scripts/
    ├── backup_env.sh      # Interactive backup
    ├── auto_backup_env.sh # Automated backup
    ├── restore_env.sh     # Interactive restore
    └── README_ENV_BACKUP.md
```

## Quick Start

1. **Set up GPG for encryption (optional but recommended):**
   ```bash
   ./scripts/setup_gpg.sh
   ```

2. **Create a backup now:**
   ```bash
   ./scripts/backup_env.sh
   ```

3. **Set up automated daily backups:**
   ```bash
   crontab -e
   # Add this line:
   0 2 * * * cd /Users/egs/repos/personal_agent && ./scripts/auto_backup_env.sh
   ```

4. **Test restore process:**
   ```bash
   ./scripts/restore_env.sh
   ```

## Troubleshooting

### GPG Issues
If you encounter GPG errors:
```bash
# Install GPG on macOS
brew install gnupg

# Or use without encryption
# Just skip the encryption option in backup_env.sh
```

### Permission Issues
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Backup Directory Missing
The scripts will automatically create the `backups/` directory if it doesn't exist.

## API Keys in Your .env

Your current `.env` contains these sensitive keys:
- GitHub Personal Access Token
- Brave Search API Key
- ModelsLab API Key
- ElevenLabs API Key
- Giphy API Key

**Important:** Never commit these to git or share them publicly. Always use the backup scripts to maintain secure copies.
