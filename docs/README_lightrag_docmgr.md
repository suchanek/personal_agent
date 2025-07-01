# LightRAG Document Manager (`lightrag_docmgr.py`)

## 1. Overview

The `lightrag_docmgr.py` script is a powerful command-line utility designed for the comprehensive management of documents within the LightRAG system. It provides a robust set of tools for developers and administrators to inspect, manage, and clean up the document storage, addressing needs from temporary in-memory removal to permanent, persistent deletion.

The script is built to interact with both the LightRAG API server and its underlying persistent storage files, offering a multi-faceted approach to document management. It also integrates with Docker to safely manage the lifecycle of the LightRAG services during sensitive operations like persistent data deletion.

## 2. Key Features

- **System Status Check**: Quickly verify the status of the LightRAG API server, associated Docker containers, and the existence of the storage directory.
- **Dual Deletion Modes**:
    - **API-based Deletion**: Removes documents from the running server instance (in-memory). This is temporary and will be reverted on server restart if the data persists on disk.
    - **Persistent Storage Deletion**: Directly removes document data and associated chunks from the JSON storage files (`kv_store_*.json`). This is a permanent deletion that survives restarts.
- **Docker Service Integration**: Can automatically stop and restart the LightRAG Docker services to ensure that persistent storage modifications are safely applied and recognized by the server.
- **Targeted Deletion**: Delete documents based on their status (`processing`, `failed`, etc.) or by providing a specific list of document IDs.
- **Safety and Recovery**:
    - **Automatic Backups**: Automatically creates a timestamped backup of the entire storage directory before performing any persistent deletion.
    - **User Confirmation**: Prompts for user confirmation before executing destructive operations, preventing accidental data loss (can be disabled with `--no-confirm`).
- **Verification**: After a deletion operation, the script can query the server to verify that the documents have been successfully removed.

## 3. Usage

The script must be run from the project's root directory.

### 3.1. Command-Line Arguments

| Argument                | Shorthand | Description                                                                                             |
| ----------------------- | --------- | ------------------------------------------------------------------------------------------------------- |
| **Actions**             |           |                                                                                                         |
| `--status`              |           | Shows the current status of the LightRAG server, Docker services, and storage path.                     |
| `--list`                |           | Lists all documents currently indexed by the LightRAG API, grouped by status.                           |
| `--delete-processing`   |           | Deletes all documents with the status `processing`.                                                     |
| `--delete-failed`       |           | Deletes all documents with the status `failed`.                                                         |
| `--delete-status <STATUS>` |        | Deletes all documents that match the specified status string.                                           |
| `--delete-ids <ID ...>` |           | Deletes one or more documents by their specific IDs.                                                    |
| **Options**             |           |                                                                                                         |
| `--persistent`          |           | Performs a permanent deletion from the persistent storage files on disk.                                |
| `--restart-server`      |           | Automatically stops and restarts the Docker services. **Required for `--persistent` changes to take effect.** |
| `--verify`              |           | After deletion, queries the server to confirm the documents are no longer present.                      |
| `--no-confirm`          |           | Skips the interactive confirmation prompt for deletion operations.                                      |
| `--url <URL>`           |           | Overrides the default LightRAG server URL.                                                              |
| `--storage-path <PATH>` |           | Overrides the default path to the LightRAG storage directory.                                           |

### 3.2. Common Scenarios & Examples

**1. Check System Status**
```bash
python tools/lightrag_docmgr.py --status
```

**2. List All Documents by Status**
```bash
python tools/lightrag_docmgr.py --list
```

**3. Delete All Documents Stuck in "Processing" (API only)**
This is a temporary deletion that will be undone if the server restarts.
```bash
python tools/lightrag_docmgr.py --delete-processing
```

**4. Permanently Delete All "Failed" Documents**
This is the recommended workflow for a full, persistent cleanup.
- `--persistent`: Deletes from the JSON files on disk.
- `--restart-server`: Stops the server to safely modify files, then starts it again.
- `--verify`: Confirms the documents are gone after the restart.
```bash
python tools/lightrag_docmgr.py --delete-failed --persistent --restart-server --verify
```

**5. Permanently Delete Specific Documents by ID**
```bash
python tools/lightrag_docmgr.py --delete-ids doc_id_123 doc_id_456 --persistent --restart-server
```

## 4. Workflow for Persistent Deletion

When using the `--persistent` flag, the script follows a careful, multi-step process to ensure data integrity:

1.  **Stop Docker Services** (if `--restart-server` is used): The script executes `docker-compose down` to gracefully stop the LightRAG server, preventing file access conflicts.
2.  **Create Backup**: It copies the entire `rag_storage` directory to a new, timestamped backup folder (e.g., `rag_storage_backup_20231027_103000`).
3.  **Delete from Storage Files**: The script loads `kv_store_doc_status.json`, `kv_store_full_docs.json`, and `kv_store_text_chunks.json`, removes all data related to the target document IDs, and saves the modified files.
4.  **Start Docker Services** (if `--restart-server` is used): It executes `docker-compose up -d` to restart the services. The LightRAG server will now load the cleaned-up data from the modified JSON files.
5.  **Verify Deletion** (if `--verify` is used): After a brief pause to allow the server to initialize, it queries the `/documents` endpoint to confirm that the deleted documents are no longer reported by the API.