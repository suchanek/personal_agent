#!/usr/bin/env python3
"""
LightRAG Document Manager V2

A modernized document management tool for LightRAG that uses the LightRAG server
API for stable and reliable operations. This version uses HTTP API calls to the
LightRAG server instead of direct library usage.

Key Improvements from V1:
- Uses LightRAG server API endpoints for all operations, ensuring stability.
- Deletion is now handled by the `/documents/delete_document` API endpoint.
- No longer requires server restarts (`--restart-server` is removed).
- Deletion is always persistent (`--persistent` is removed).
- More robust, as it uses the official API interface.

Usage:
  From the project root directory, run:
  `python tools/lightrag_docmgr_v2.py [OPTIONS] [ACTIONS]`

Options:
  --server-url <URL>          LightRAG server URL (default: from config)
  --verify                    Verify deletion after completion by checking server
  --no-confirm                Skip confirmation prompts for deletion actions
  --delete-source             Delete the original source file from the inputs directory
  --retry <ID1> [ID2...]      Retry specific failed documents by their unique IDs

Actions:
  --status                    Show LightRAG server and document status
  --list                      List all documents with detailed view (ID, file path, status, etc.)
  --list-names                List all document names (file paths only)
  --delete-processing         Delete all documents currently in 'processing' status
  --delete-failed             Delete all documents currently in 'failed' status
  --delete-status <STATUS>    Delete all documents with a specific custom status
  --delete-ids <ID1> [ID2...] Delete specific documents by their unique IDs
  --delete-name <PATTERN>     Delete documents whose file paths match a glob-style pattern (e.g., '*.pdf', 'my_doc.txt')
  --nuke                      Perform a comprehensive deletion. This implicitly sets:
                              --verify, --delete-source, and --no-confirm.
                              Must be used with a deletion action.

Examples:
  # Check server status
  python tools/lightrag_docmgr_v2.py --status

  # List all documents
  python tools/lightrag_docmgr_v2.py --list

  # Delete all 'failed' documents and verify
  python tools/lightrag_docmgr_v2.py --delete-failed --verify

  # Delete a specific document by ID and also delete the source file
  python tools/lightrag_docmgr_v2.py --delete-ids doc-12345 --delete-source

  # Delete all '.md' files comprehensively
  python tools/lightrag_docmgr_v2.py --nuke --delete-name '*.md'

  # Retry a failed document
  python tools/lightrag_docmgr_v2.py --retry doc-failed-123
"""

import argparse
import asyncio
import fnmatch
import os
import sys
from typing import Any, Dict, List, Optional
import aiohttp
import json
from pathlib import Path

from personal_agent.config import settings


class LightRAGDocumentManagerV2:
    """Manages documents in LightRAG using the server API."""

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or settings.LIGHTRAG_URL
        self.storage_dir = Path(settings.AGNO_STORAGE_DIR)
        self.status_file_path = self.storage_dir / "rag_storage" / "kv_store_doc_status.json"
        print(f"🌐 Using LightRAG server URL: {self.server_url}")
        print(f"🗄️ Using storage path: {self.storage_dir}")

    async def check_server_status(self) -> bool:
        """Check if LightRAG server is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/health", timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"❌ Cannot connect to LightRAG server: {e}")
            return False

    async def initialize(self) -> bool:
        """Check server connectivity."""
        if not await self.check_server_status():
            print(f"❌ LightRAG server not accessible at: {self.server_url}")
            print("   Please ensure the LightRAG server is running.")
            return False
        
        print("✅ LightRAG server is accessible.")
        return True

    async def get_all_docs(self) -> List[Dict[str, Any]]:
        """Fetches all documents from the LightRAG server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/documents", timeout=30) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(f"❌ Server error {resp.status}: {error_text}")
                        return []
                    
                    data = await resp.json()
                    all_docs = []
                    
                    # The API returns documents grouped by status in a "statuses" dict
                    if isinstance(data, dict) and "statuses" in data:
                        statuses = data["statuses"]
                        # Iterate through all status categories (processed, failed, etc.)
                        for status_name, docs_list in statuses.items():
                            if isinstance(docs_list, list):
                                all_docs.extend(docs_list)
                        return all_docs
                    elif isinstance(data, dict) and "documents" in data:
                        return data["documents"]
                    elif isinstance(data, list):
                        return data
                    else:
                        print(f"⚠️ Unexpected response format: {type(data)}")
                        print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        return []
        except Exception as e:
            print(f"❌ Error fetching documents: {e}")
            return []

    async def delete_documents(
        self, docs_to_delete: List[Dict[str, Any]], delete_source: bool = False
    ) -> Dict[str, Any]:
        """Deletes a list of documents using the server API."""
        results = {
            "total_requested": len(docs_to_delete),
            "deleted_successfully": 0,
            "source_files_deleted": 0,
            "not_found": 0,
            "errors": [],
        }

        # Phase 1: Delete source files if requested
        if delete_source:
            print("\n🗑️ Phase 1: Deleting source files")
            for doc_info in docs_to_delete:
                source_path = doc_info.get("file_path")
                if source_path and os.path.exists(source_path):
                    try:
                        os.remove(source_path)
                        print(f"✅ Deleted source file: {source_path}")
                        results["source_files_deleted"] += 1
                    except OSError as e:
                        msg = f"Failed to delete source file {source_path}: {e}"
                        print(f"❌ {msg}")
                        results["errors"].append(msg)
                else:
                    print(f"⚠️ Source file not found, skipping: {source_path}")
            print(f"✅ Source file deletion complete.")

        # Phase 2: Delete documents from LightRAG server
        print("\n💾 Phase 2: Deleting documents from LightRAG server")
        if docs_to_delete:
            # Collect all document IDs for batch deletion
            doc_ids = [doc_info["id"] for doc_info in docs_to_delete]
            print(f"   - Deleting {len(doc_ids)} documents in batch...")
            
            async with aiohttp.ClientSession() as session:
                try:
                    # Use the DELETE /documents/delete_document endpoint with proper format
                    payload = {
                        "doc_ids": doc_ids,
                        "delete_file": delete_source
                    }
                    async with session.delete(
                        f"{self.server_url}/documents/delete_document",
                        json=payload,
                        timeout=60  # Longer timeout for batch operations
                    ) as resp:
                        if resp.status == 200:
                            result_data = await resp.json()
                            status = result_data.get("status", "unknown")
                            message = result_data.get("message", "No message")
                            
                            if status == "deletion_started":
                                print(f"   ✅ Success: {message}")
                                results["deleted_successfully"] = len(doc_ids)
                            elif status == "busy":
                                print(f"   ⚠️ Server Busy: {message}")
                                results["errors"].append(f"Server busy: {message}")
                            elif status == "not_allowed":
                                print(f"   ❌ Not Allowed: {message}")
                                results["errors"].append(f"Not allowed: {message}")
                            else:
                                print(f"   ⚠️ Unknown Status '{status}': {message}")
                                results["errors"].append(f"Unknown status: {message}")
                        else:
                            error_text = await resp.text()
                            msg = f"Server error {resp.status}: {error_text}"
                            print(f"   ❌ {msg}")
                            results["errors"].append(msg)
                except Exception as e:
                    msg = f"An exception occurred during batch deletion: {e}"
                    print(f"   ❌ {msg}")
                    results["errors"].append(msg)

        # Phase 3: Clear cache using the server API
        print("\n🧹 Phase 3: Clearing server cache")
        try:
            async with aiohttp.ClientSession() as session:
                # Clear all cache modes
                payload = {"modes": None}  # None clears all cache
                async with session.post(
                    f"{self.server_url}/documents/clear_cache", 
                    json=payload,
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        print("✅ Server cache cleared successfully")
                    else:
                        error_text = await resp.text()
                        msg = f"Failed to clear server cache: {resp.status} - {error_text}"
                        print(f"❌ {msg}")
                        results["errors"].append(msg)
        except Exception as e:
            msg = f"Failed to clear server cache: {e}"
            print(f"❌ {msg}")
            results["errors"].append(msg)

        print("✅ LightRAG server deletion complete.")
        return results

    async def retry_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Retries failed documents by updating their status to 'pending' in the status file."""
        results = {
            "total_requested": len(doc_ids),
            "retried_successfully": 0,
            "not_found": 0,
            "not_failed": 0,
            "errors": [],
        }

        if not self.status_file_path.exists():
            msg = f"Status file not found at {self.status_file_path}"
            print(f"❌ {msg}")
            results["errors"].append(msg)
            return results

        try:
            with open(self.status_file_path, "r+") as f:
                doc_statuses = json.load(f)

                for doc_id in doc_ids:
                    if doc_id in doc_statuses:
                        if doc_statuses[doc_id].get("status") == "failed":
                            doc_statuses[doc_id]["status"] = "pending"
                            print(f"✅ Re-queued document '{doc_id}' for processing.")
                            results["retried_successfully"] += 1
                        else:
                            print(f"⚠️ Document '{doc_id}' is not in 'failed' state. Skipping.")
                            results["not_failed"] += 1
                    else:
                        print(f"⚠️ Document '{doc_id}' not found in status file. Skipping.")
                        results["not_found"] += 1
                
                # Write the changes back to the file
                f.seek(0)
                json.dump(doc_statuses, f, indent=2)
                f.truncate()

        except (IOError, json.JSONDecodeError) as e:
            msg = f"Error accessing status file: {e}"
            print(f"❌ {msg}")
            results["errors"].append(msg)

        return results

    async def finalize(self):
        """No cleanup needed for API-based approach."""
        print("\n✅ Document manager finalized.")


async def main():
    parser = argparse.ArgumentParser(description="LightRAG Document Manager V2")
    parser.add_argument("--server-url", help="LightRAG server URL")
    # Actions
    parser.add_argument(
        "--status", action="store_true", help="Show storage and document status"
    )
    parser.add_argument("--list", action="store_true", help="List all documents")
    parser.add_argument(
        "--list-names", action="store_true", help="List all document names"
    )
    parser.add_argument(
        "--delete-processing", action="store_true", help="Delete 'processing' documents"
    )
    parser.add_argument(
        "--delete-failed", action="store_true", help="Delete 'failed' documents"
    )
    parser.add_argument(
        "--delete-status", help="Delete documents with a specific status"
    )
    parser.add_argument("--delete-ids", nargs="*", help="Delete documents by ID")
    parser.add_argument(
        "--delete-name", help="Delete documents matching a name pattern"
    )
    parser.add_argument("--retry", nargs="+", help="Retry documents by ID")
    # Options
    parser.add_argument(
        "--nuke", action="store_true", help="Comprehensive deletion mode"
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify deletion after completion"
    )
    parser.add_argument(
        "--no-confirm", action="store_true", help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--delete-source", action="store_true", help="Delete the original source file"
    )

    args = parser.parse_args()

    manager = LightRAGDocumentManagerV2(args.server_url)
    if not await manager.initialize():
        return 1

    all_docs = await manager.get_all_docs()
    docs_by_id = {doc["id"]: doc for doc in all_docs}

    if args.status:
        print("\n🔍 System Status Check")
        print("-" * 40)
        server_status = await manager.check_server_status()
        print(f"Server Status: {'🟢 Online' if server_status else '🔴 Offline'}")
        print(f"  URL: {manager.server_url}")
        print(f"Documents Found: {len(all_docs)}")
        # Count by status
        status_counts = {}
        for doc in all_docs:
            status = doc.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        return 0

    if args.list:
        print(f"\n📊 Found {len(all_docs)} total documents")
        print("-" * 60)
        for doc in sorted(all_docs, key=lambda x: x.get("file_path", "")):
            print(f"  ID: {doc.get('id')}")
            print(f"    File Path: {doc.get('file_path', 'N/A')}")
            print(f"    Status: {doc.get('status', 'N/A')}")
            print(f"    Created: {doc.get('created_at', 'N/A')}")
            print()
        return 0

    if args.list_names:
        names = sorted(
            list(set(d.get("file_path") for d in all_docs if d.get("file_path")))
        )
        print("\n📄 Document Names:")
        print("-" * 40)
        for name in names:
            print(f"  - {name}")
        return 0

    # --- Deletion Logic ---
    docs_to_delete = []
    confirm = not args.no_confirm
    delete_source = args.delete_source
    verify = args.verify

    if args.nuke:
        print("☢️  --nuke option activated: High-impact deletion mode.")
        confirm = False
        delete_source = True
        verify = True

    if args.delete_processing:
        docs_to_delete = [d for d in all_docs if d.get("status") == "processing"]
    elif args.delete_failed:
        docs_to_delete = [d for d in all_docs if d.get("status") == "failed"]
    elif args.delete_status:
        docs_to_delete = [
            d for d in all_docs if d.get("status") == args.delete_status.lower()
        ]
    elif args.delete_ids:
        docs_to_delete = [
            docs_by_id[doc_id] for doc_id in args.delete_ids if doc_id in docs_by_id
        ]
    elif args.delete_name:
        docs_to_delete = [
            d
            for d in all_docs
            if d.get("file_path") and fnmatch.fnmatch(d["file_path"], args.delete_name)
        ]

    if args.retry:
        print(f"\n🔄 Retrying {len(args.retry)} documents...")
        results = await manager.retry_documents(args.retry)
        print("\n" + "=" * 60)
        print("🔄 RETRY SUMMARY")
        print("=" * 60)
        print(f"Total documents targeted: {results['total_requested']}")
        print(f"Re-queued successfully: {results['retried_successfully']}")
        print(f"Not found: {results['not_found']}")
        print(f"Not in 'failed' state: {results['not_failed']}")
        if results["errors"]:
            print(f"Errors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"  ❌ {error}")
        await manager.finalize()
        return 0

    if not docs_to_delete:
        print("\n✅ No documents found matching the criteria. Nothing to do.")
        return 0

    print(f"\n🎯 Found {len(docs_to_delete)} documents to delete:")
    for doc in docs_to_delete:
        print(f"  - {doc.get('id')} ({doc.get('file_path', 'N/A')})")

    if confirm:
        response = input(f"\nProceed with deletion? (y/N): ")
        if response.lower() not in ["y", "yes"]:
            print("❌ Deletion cancelled.")
            return 0

    results = await manager.delete_documents(docs_to_delete, delete_source)

    if verify:
        print("\n🔍 Verification Phase")
        # Re-fetch the documents after deletion
        remaining_docs_list = await manager.get_all_docs()
        remaining_ids = {doc["id"] for doc in remaining_docs_list}
        deleted_ids = {doc["id"] for doc in docs_to_delete}

        verified_deleted_count = len(deleted_ids - remaining_ids)
        print(
            f"✅ Verified {verified_deleted_count}/{len(deleted_ids)} documents are deleted."
        )
        results["verified_deleted"] = verified_deleted_count

    # --- Summary ---
    print("\n" + "=" * 60)
    print("🎯 DELETION SUMMARY")
    print("=" * 60)
    print(f"Total documents targeted: {results['total_requested']}")
    print(f"Deleted successfully: {results['deleted_successfully']}")
    print(f"Not found during deletion: {results['not_found']}")
    if delete_source:
        print(f"Source files deleted: {results['source_files_deleted']}")
    if verify:
        print(f"Verified as deleted: {results.get('verified_deleted', 'N/A')}")
    if results["errors"]:
        print(f"Errors ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  ❌ {error}")

    await manager.finalize()
    return 0


if __name__ == "__main__":
    # This script requires asyncio to run.
    # Ensure you have the necessary dependencies:
    # poetry install
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
