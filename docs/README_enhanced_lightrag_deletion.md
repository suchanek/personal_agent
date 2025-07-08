# Enhanced LightRAG Document Deletion Guide

This guide explains how to use the enhanced LightRAG document deletion system that properly handles both API-based and persistent storage deletion.

## Problem Background

The original `delete_lightrag_documents.py` script only performed API-based deletions, which are temporary and don't survive server restarts. Documents in "processing" or "uploaded" status would reappear after restarting the LightRAG server because they were still stored in persistent JSON files.

## Solution: Enhanced Script

The `tests/test_lightrag_document_deletion.py` script provides comprehensive deletion capabilities:

### Features
- **API-based deletion**: Immediate removal from memory (temporary)
- **Persistent storage deletion**: Permanent removal from storage files
- **Docker service management**: Safe stop/start operations
- **Automatic backups**: Creates backups before modifying storage
- **Verification**: Confirms successful deletion
- **Status checking**: Monitor system health

## Usage Examples

### 1. Check System Status
```bash
python delete_lightrag_documents_enhanced.py --status
```

### 2. List All Documents
```bash
python delete_lightrag_documents_enhanced.py --list
```

### 3. Simple API-Only Deletion (Temporary)
```bash
# Delete processing documents (API only - will come back after restart)
python delete_lightrag_documents_enhanced.py --delete-processing

# Delete failed documents (API only)
python delete_lightrag_documents_enhanced.py --delete-failed

# Delete by specific status
python delete_lightrag_documents_enhanced.py --delete-status uploaded
```

### 4. Permanent Deletion with Server Restart
```bash
# Delete processing documents permanently
python delete_lightrag_documents_enhanced.py --delete-processing --persistent --restart-server

# Delete with verification
python delete_lightrag_documents_enhanced.py --delete-processing --persistent --restart-server --verify

# Delete specific documents by ID
python delete_lightrag_documents_enhanced.py --delete-ids doc-abc123 doc-def456 --persistent --restart-server
```

### 5. Advanced Options
```bash
# Skip confirmation prompts
python delete_lightrag_documents_enhanced.py --delete-processing --persistent --restart-server --no-confirm

# Custom storage path
python delete_lightrag_documents_enhanced.py --delete-processing --storage-path /custom/path/to/storage
```

## Command Line Options

### Actions
- `--status`: Show server and Docker status
- `--list`: List all documents with counts by status
- `--delete-processing`: Delete all processing documents
- `--delete-failed`: Delete all failed documents
- `--delete-status STATUS`: Delete documents with specific status
- `--delete-ids ID1 ID2 ...`: Delete specific documents by ID

### Deletion Options
- `--persistent`: Delete from persistent storage (permanent)
- `--restart-server`: Restart Docker services (required for persistent deletion)
- `--verify`: Verify deletion after completion
- `--no-confirm`: Skip confirmation prompts

### Configuration
- `--url URL`: LightRAG server URL (default: http://localhost:9621)
- `--storage-path PATH`: Path to storage directory

## Deletion Strategies

### 1. API-Only Deletion (Default)
- **Use case**: Quick temporary removal while server is running
- **Persistence**: Documents will reappear after server restart
- **Safety**: Very safe, no permanent changes
- **Command**: `--delete-processing`

### 2. Persistent Deletion
- **Use case**: Permanent removal that survives restarts
- **Persistence**: Documents are permanently deleted
- **Safety**: Requires backup and server restart
- **Command**: `--delete-processing --persistent --restart-server`

### 3. Comprehensive Deletion (Recommended)
- **Use case**: Complete removal with verification
- **Features**: API + persistent + verification
- **Safety**: Maximum safety with backups and verification
- **Command**: `--delete-processing --persistent --restart-server --verify`

## Safety Features

### Automatic Backups
- Created before any persistent storage modifications
- Stored with timestamp: `rag_storage_backup_YYYYMMDD_HHMMSS`
- Can be used to restore if needed

### Server Management
- Safely stops Docker services before modifying storage files
- Waits for services to restart and become ready
- Monitors server health during operations

### Verification
- Confirms documents are actually deleted
- Checks both API and storage consistency
- Reports any documents that failed to delete

## Troubleshooting

### Server Not Responding
```bash
# Check status first
python delete_lightrag_documents_enhanced.py --status

# If server is down, you can still delete from storage
python delete_lightrag_documents_enhanced.py --delete-processing --persistent --restart-server
```

### Docker Issues
```bash
# Manual Docker management
docker-compose down
docker-compose up -d

# Check Docker status
docker-compose ps
```

### Storage File Issues
```bash
# Check if storage path exists
ls -la /Users/Shared/personal_agent_data/agno/rag_storage/

# Restore from backup if needed
cp -r /Users/Shared/personal_agent_data/agno/rag_storage_backup_TIMESTAMP/* /Users/Shared/personal_agent_data/agno/rag_storage/
```

## Migration from Original Script

### Old Way (Temporary Only)
```bash
python delete_lightrag_documents.py --delete-processing
```

### New Way (Permanent)
```bash
python delete_lightrag_documents_enhanced.py --delete-processing --persistent --restart-server --verify
```

## Best Practices

1. **Always use `--status` first** to check system health
2. **Use `--verify`** for important deletions
3. **Keep backups** - they're created automatically but check the path
4. **Use `--persistent --restart-server`** for permanent deletion
5. **Test with single documents** before bulk operations
6. **Monitor the output** for any error messages

## Example Workflow

```bash
# 1. Check system status
python delete_lightrag_documents_enhanced.py --status

# 2. List current documents
python delete_lightrag_documents_enhanced.py --list

# 3. Delete processing documents permanently
python delete_lightrag_documents_enhanced.py --delete-processing --persistent --restart-server --verify

# 4. Verify deletion worked
python delete_lightrag_documents_enhanced.py --list
```

## Files Modified

The enhanced script modifies these persistent storage files:
- `kv_store_doc_status.json` - Document status tracking
- `kv_store_full_docs.json` - Full document content
- `kv_store_text_chunks.json` - Document text chunks

## Integration with Existing Scripts

The enhanced script is designed to work alongside:
- `switch-ollama.sh` - For Ollama server management
- `restart-lightrag.sh` - For manual LightRAG restarts
- `fix_lightrag_persistent_storage.py` - For direct storage manipulation

This enhanced approach ensures that document deletions are truly permanent and won't reappear after server restarts.
