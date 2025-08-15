# LightRAG Document Manager V2 - Usage Guide

## Overview

The LightRAG Document Manager V2 is a modernized command-line tool for managing documents in your LightRAG knowledge base. This version uses the LightRAG server's REST API for all operations, making it more stable and reliable than previous versions that used direct library calls.

## Key Features

- **Server-Based Operations**: Uses LightRAG server API endpoints for all operations
- **Batch Document Deletion**: Efficiently deletes multiple documents in a single operation
- **Status Monitoring**: Check server health and document statistics
- **Flexible Filtering**: Delete documents by status, ID, filename patterns, or combinations
- **Verification**: Optional verification to confirm deletions were successful
- **Source File Management**: Optionally delete original source files along with database entries
- **Cache Management**: Automatically clears server cache after deletions

## Prerequisites

1. **LightRAG Server**: The LightRAG server must be running and accessible
2. **Python Environment**: Python 3.8+ with required dependencies (`aiohttp`, `personal_agent.config`)
3. **Network Access**: Ability to connect to the LightRAG server (default: `http://localhost:9621`)

## Installation

The script is included in the personal_agent project. Ensure you have the project dependencies installed:

```bash
poetry install
```

## Basic Usage

Run the script from the project root directory:

```bash
python tools/lightrag_docmgr_v2.py [OPTIONS] [ACTIONS]
```

## Command Line Options

### Server Configuration
- `--server-url <URL>`: Specify LightRAG server URL (default: from config, usually `http://localhost:9621`)

### Deletion Options
- `--verify`: Verify deletion after completion by re-checking the server
- `--no-confirm`: Skip confirmation prompts for deletion actions
- `--delete-source`: Delete the original source files from the inputs directory
- `--nuke`: Comprehensive deletion mode (implies `--verify`, `--delete-source`, and `--no-confirm`)

## Actions

### Information Actions

#### `--status`
Show LightRAG server status and document statistics.

```bash
python tools/lightrag_docmgr_v2.py --status
```

**Example Output:**
```
🔍 System Status Check
----------------------------------------
Server Status: 🟢 Online
  URL: http://localhost:9621
Documents Found: 14
  - processed: 12
  - failed: 2
```

#### `--list`
List all documents with detailed information (ID, file path, status, creation date).

```bash
python tools/lightrag_docmgr_v2.py --list
```

**Example Output:**
```
📊 Found 14 total documents
------------------------------------------------------------
  ID: doc-57925bffea615759798d5f38d63b2c34
    File Path: research_paper.pdf
    Status: processed
    Created: 2025-06-26T17:43:35.605007+00:00

  ID: doc-f35444a0dc245f2a50ee59d2a4b7d9e0
    File Path: api_documentation.md
    Status: failed
    Created: 2025-07-08T02:41:52.215794+00:00
```

#### `--list-names`
List only the document names (file paths) in a compact format.

```bash
python tools/lightrag_docmgr_v2.py --list-names
```

**Example Output:**
```
📄 Document Names:
----------------------------------------
  - research_paper.pdf
  - api_documentation.md
  - user_manual.docx
```

### Deletion Actions

#### `--delete-failed`
Delete all documents with "failed" status.

```bash
python tools/lightrag_docmgr_v2.py --delete-failed
```

#### `--delete-processing`
Delete all documents with "processing" status.

```bash
python tools/lightrag_docmgr_v2.py --delete-processing
```

#### `--delete-status <STATUS>`
Delete all documents with a specific status.

```bash
python tools/lightrag_docmgr_v2.py --delete-status failed
python tools/lightrag_docmgr_v2.py --delete-status processing
```

#### `--delete-ids <ID1> [ID2...]`
Delete specific documents by their unique IDs.

```bash
python tools/lightrag_docmgr_v2.py --delete-ids doc-12345 doc-67890
```

#### `--delete-name <PATTERN>`
Delete documents whose file paths match a glob-style pattern.

```bash
# Delete all PDF files
python tools/lightrag_docmgr_v2.py --delete-name "*.pdf"

# Delete a specific file
python tools/lightrag_docmgr_v2.py --delete-name "old_document.txt"

# Delete all files containing "temp"
python tools/lightrag_docmgr_v2.py --delete-name "*temp*"
```

## Common Usage Examples

### 1. Check System Status
```bash
python tools/lightrag_docmgr_v2.py --status
```

### 2. List All Documents
```bash
python tools/lightrag_docmgr_v2.py --list
```

### 3. Clean Up Failed Documents
```bash
python tools/lightrag_docmgr_v2.py --delete-failed --verify
```

### 4. Delete Specific Documents with Verification
```bash
python tools/lightrag_docmgr_v2.py --delete-ids doc-12345 doc-67890 --verify
```

### 5. Remove All Temporary Files
```bash
python tools/lightrag_docmgr_v2.py --delete-name "*temp*" --delete-source --verify
```

### 6. Nuclear Option - Remove All Failed Documents and Source Files
```bash
python tools/lightrag_docmgr_v2.py --nuke --delete-failed
```

### 7. Batch Delete Multiple Document Types
```bash
# First delete failed documents
python tools/lightrag_docmgr_v2.py --delete-failed --no-confirm

# Then delete old PDF files
python tools/lightrag_docmgr_v2.py --delete-name "old_*.pdf" --no-confirm
```

## Advanced Usage

### Using Custom Server URL
```bash
python tools/lightrag_docmgr_v2.py --server-url http://remote-server:9621 --status
```

### Comprehensive Cleanup with Verification
```bash
python tools/lightrag_docmgr_v2.py --delete-failed --delete-source --verify
```

### Silent Operation (No Prompts)
```bash
python tools/lightrag_docmgr_v2.py --delete-failed --no-confirm
```

## Understanding the Output

### Deletion Process Phases

The script performs deletion in three phases:

1. **Phase 1: Source File Deletion** (if `--delete-source` is used)
   - Removes original files from the file system
   - Only runs if source file deletion is requested

2. **Phase 2: LightRAG Server Deletion**
   - Sends deletion request to the LightRAG server
   - Uses batch deletion for efficiency
   - Handles background processing

3. **Phase 3: Cache Clearing**
   - Clears the server's cache to prevent stale responses
   - Ensures clean state after deletions

### Deletion Summary

After completion, you'll see a summary like:

```
============================================================
🎯 DELETION SUMMARY
============================================================
Total documents targeted: 5
Deleted successfully: 5
Not found during deletion: 0
Source files deleted: 3
Verified as deleted: 5
```

## Error Handling

The script handles various error conditions:

- **Server Unavailable**: Checks server connectivity before operations
- **Invalid Document IDs**: Skips non-existent documents
- **Permission Errors**: Reports file system permission issues
- **Network Timeouts**: Uses appropriate timeouts for server operations
- **API Errors**: Parses and reports server error messages

## Best Practices

### 1. Always Check Status First
```bash
python tools/lightrag_docmgr_v2.py --status
```

### 2. Use Verification for Important Operations
```bash
python tools/lightrag_docmgr_v2.py --delete-failed --verify
```

### 3. Test with Specific IDs Before Bulk Operations
```bash
# Test with one document first
python tools/lightrag_docmgr_v2.py --delete-ids doc-12345 --verify

# Then proceed with bulk operation
python tools/lightrag_docmgr_v2.py --delete-failed --verify
```

### 4. Use `--list-names` to Preview Deletions
```bash
# See what would be deleted
python tools/lightrag_docmgr_v2.py --list-names

# Then delete with pattern
python tools/lightrag_docmgr_v2.py --delete-name "*.tmp" --verify
```

### 5. Backup Important Data
Before performing large deletions, ensure you have backups of important documents.

## Troubleshooting

### Server Connection Issues
```bash
# Check if server is running
curl http://localhost:9621/health

# Check server status with the script
python tools/lightrag_docmgr_v2.py --status
```

### Permission Errors
Ensure the script has permission to delete source files if using `--delete-source`.

### Verification Failures
If verification shows documents weren't deleted, the server might be processing deletions in the background. Wait a moment and check status again.

### API Errors
Check the LightRAG server logs for detailed error information if the script reports API errors.

## Configuration

The script uses configuration from `personal_agent.config.settings`:

- `LIGHTRAG_URL`: Default server URL (usually `http://localhost:9621`)

You can override the server URL with the `--server-url` option.

## Safety Features

- **Confirmation Prompts**: By default, asks for confirmation before deletions
- **Verification**: Optional verification to ensure deletions completed
- **Batch Processing**: Efficient batch operations reduce server load
- **Error Reporting**: Detailed error messages for troubleshooting
- **Status Checking**: Verifies server connectivity before operations

## Integration with Other Tools

The script can be integrated into automation workflows:

```bash
#!/bin/bash
# Cleanup script example

# Check server status
if python tools/lightrag_docmgr_v2.py --status | grep -q "🟢 Online"; then
    echo "Server is online, proceeding with cleanup..."
    
    # Clean up failed documents
    python tools/lightrag_docmgr_v2.py --delete-failed --no-confirm --verify
    
    # Clean up old temporary files
    python tools/lightrag_docmgr_v2.py --delete-name "*temp*" --no-confirm --verify
    
    echo "Cleanup completed successfully"
else
    echo "Server is offline, skipping cleanup"
    exit 1
fi
```

## Version History

- **V2**: Complete rewrite using LightRAG server API
  - Improved stability and reliability
  - Batch deletion support
  - Better error handling
  - API-based operations instead of direct library calls

- **V1**: Original version using direct library calls (deprecated)
