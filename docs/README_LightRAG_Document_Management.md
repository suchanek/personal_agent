# LightRAG Document Management

This document explains how to safely manage documents in your LightRAG database.

## ⚠️ CRITICAL WARNING ⚠️

**DANGEROUS ENDPOINT**: `DELETE /documents` 
- This endpoint **DELETES ALL DOCUMENTS** in the database
- Never use this endpoint unless you want to completely clear the database
- Always use the individual document deletion endpoint instead

## Safe Document Deletion

### Correct Endpoint for Individual Document Deletion
- **Endpoint**: `POST /documents/delete_document`
- **Method**: POST
- **Payload**: `{"doc_id": "document_id_here"}`

### Using the Script

The `delete_lightrag_documents.py` script has been corrected to use the safe endpoint.

#### List all documents:
```bash
python delete_lightrag_documents.py --list
```

#### Delete only failed documents:
```bash
python delete_lightrag_documents.py --delete-failed
```

#### Delete specific documents by ID:
```bash
python delete_lightrag_documents.py --delete-ids doc-123abc doc-456def
```

#### Skip confirmation prompts:
```bash
python delete_lightrag_documents.py --delete-failed --no-confirm
```

## What Happened

During the initial troubleshooting, the script accidentally used the `DELETE /documents` endpoint which removed ALL documents from the database, including the successfully processed ones. This was corrected to use the proper individual document deletion endpoint.

## API Endpoints Summary

| Endpoint | Method | Purpose | Safety |
|----------|--------|---------|--------|
| `/documents` | GET | List all documents | ✅ Safe |
| `/documents/delete_document` | POST | Delete individual document | ✅ Safe |
| `/documents` | DELETE | **DELETE ALL DOCUMENTS** | ⚠️ DANGEROUS |

## Recovery

If you accidentally deleted all documents:
1. The database is now empty (`{"statuses": {}}`)
2. You'll need to re-upload any documents you want to keep
3. The failed documents that were causing parsing issues are gone, so new uploads should work properly

## Future Use

The corrected script now safely deletes only the specified documents without affecting others in the database.
