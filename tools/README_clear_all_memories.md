# Clear All Memories Script

A comprehensive script to clear both semantic memories (local SQLite) and LightRAG graph memories (knowledge graph) to prevent drift between the two systems.

## Overview

Your personal agent uses a **dual memory architecture**:

1. **Semantic Memory System** (SQLite + LanceDB) - Fast local semantic search for user facts
2. **LightRAG Graph Memory System** (Knowledge Graph) - Relationship-based memory storage

Over time, these systems can drift apart, so this script provides a unified way to clear both systems simultaneously.

## Features

- ✅ **Dual System Clearing**: Clears both semantic and LightRAG memories
- ✅ **Safety Confirmations**: Requires explicit confirmation before clearing
- ✅ **Dry Run Mode**: See what would be cleared without actually doing it
- ✅ **Selective Clearing**: Clear only one system if needed
- ✅ **Verification**: Post-clearing verification to ensure success
- ✅ **User-Specific**: Respects user ID configuration for proper isolation
- ✅ **Comprehensive Reporting**: Detailed status and progress reporting
- ✅ **Error Handling**: Graceful failure handling with detailed error messages

## Usage

### Basic Usage

```bash
# Clear both memory systems (with confirmation)
python tools/clear_all_memories.py

# Clear both systems without confirmation
python tools/clear_all_memories.py --no-confirm

# See what would be cleared without actually clearing
python tools/clear_all_memories.py --dry-run
```

### Selective Clearing

```bash
# Clear only semantic memories (local SQLite)
python tools/clear_all_memories.py --semantic-only

# Clear only LightRAG graph memories
python tools/clear_all_memories.py --lightrag-only
```

### Verification

```bash
# Verify that memories have been cleared
python tools/clear_all_memories.py --verify
```

### Advanced Options

```bash
# Clear memories for a specific user
python tools/clear_all_memories.py --user-id john_doe

# Enable verbose logging for debugging
python tools/clear_all_memories.py --verbose

# Combine options
python tools/clear_all_memories.py --dry-run --verbose --user-id test_user
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be cleared without actually clearing |
| `--no-confirm` | Skip confirmation prompts |
| `--semantic-only` | Clear only the semantic memory system |
| `--lightrag-only` | Clear only the LightRAG graph memory system |
| `--verify` | Verify that memories have been cleared |
| `--user-id <USER_ID>` | Specify user ID (default: from config) |
| `--verbose` | Enable verbose logging |

## What Gets Cleared

### Semantic Memory System
- **Location**: `{AGNO_STORAGE_DIR}/semantic_memory.db`
- **Content**: User facts, topics, semantic embeddings
- **Method**: Uses `SemanticMemoryManager.clear_memories()`

### LightRAG Graph Memory System
- **Location**: LightRAG server at `{LIGHTRAG_MEMORY_URL}` (port 9622)
- **Content**: Knowledge graph entities, relationships, documents
- **Method**: Uses LightRAG server API `/documents/delete_document`
- **Storage**: Also clears `{AGNO_STORAGE_DIR}/memory_rag_storage/` directory

## Example Output

```
🧠 Memory Clearing Manager initialized
   User ID: Eric
   Storage Directory: /Users/Shared/personal_agent_data/agno/Eric
   LightRAG Memory URL: http://localhost:9622
   Semantic DB Path: /Users/Shared/personal_agent_data/agno/Eric/semantic_memory.db

📊 Checking current memory status...

============================================================
🧠 MEMORY SYSTEMS STATUS REPORT
============================================================

📊 Semantic Memory System:
   Available: ✅
   Total Memories: 15
   Recent Memories (24h): 3
   Most Common Topic: personal_info

🌐 LightRAG Graph Memory System:
   Available: ✅
   Total Documents: 8
   Document Status Breakdown:
     - processed: 6
     - failed: 2

🎯 Will clear: Semantic: 15 memories, LightRAG: 8 documents

⚠️  Are you sure you want to clear these memories? This action cannot be undone! (y/N): y

🧹 Performing memory clearing...

============================================================
🧹 MEMORY CLEARING RESULTS
============================================================

📊 Semantic Memory System:
   Status: ✅ Success
   Message: Cleared 15 memories successfully

🌐 LightRAG Graph Memory System:
   Status: ✅ Success
   Message: Successfully deleted 8 documents from LightRAG

🎯 Overall Result: ✅ SUCCESS

🔍 Verifying clearing was successful...

============================================================
🔍 MEMORY CLEARING VERIFICATION
============================================================

📊 Semantic Memory System:
   Cleared: ✅
   Remaining Memories: 0

🌐 LightRAG Graph Memory System:
   Cleared: ✅
   Remaining Documents: 0

🎯 Fully Cleared: ✅ YES
```

## Safety Features

1. **Confirmation Required**: By default, the script requires explicit confirmation before clearing memories
2. **Dry Run Mode**: Use `--dry-run` to see what would be cleared without actually doing it
3. **Verification**: Automatic post-clearing verification to ensure success
4. **Error Handling**: Graceful handling of server unavailability or other errors
5. **User Isolation**: Respects user ID configuration to prevent accidental cross-user clearing

## Troubleshooting

### LightRAG Server Not Available
If you see "LightRAG memory server not available", ensure the server is running:

```bash
# Start the LightRAG memory server
./restart-lightrag-memory.sh
```

### Semantic Memory Database Not Found
If the semantic memory database doesn't exist, the script will report 0 memories to clear. This is normal for new installations.

### Partial Clearing
If only one system clears successfully, the script will report partial success and show which system failed. You can then use the selective clearing options to retry the failed system.

## Integration with Existing Tools

This script integrates seamlessly with your existing infrastructure:

- Uses the same configuration system (`personal_agent.config.settings`)
- Follows the same patterns as `lightrag_docmgr_v2.py`
- Respects user ID and storage directory configurations
- Uses the same LightRAG server API endpoints

## When to Use

Use this script when you want to:

- **Prevent Memory Drift**: Clear both systems to ensure they stay synchronized
- **Fresh Start**: Reset all memories for testing or development
- **User Cleanup**: Clear memories for a specific user
- **System Maintenance**: Clean up failed or corrupted memories
- **Development Testing**: Reset state between test runs

## Related Tools

- `tools/lightrag_docmgr_v2.py` - Manage LightRAG documents specifically
- `scripts/send_to_lightrag.py` - Add documents to LightRAG
- Memory tools in the agent interface - Query and manage memories interactively
