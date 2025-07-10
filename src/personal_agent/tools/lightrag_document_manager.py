#!/usr/bin/env python3
"""
LightRAG Document Manager Package Module

A modernized document management tool for LightRAG that uses the LightRAG server
API for stable and reliable operations. This version uses HTTP API calls to the
LightRAG server instead of direct library usage.

Key Features:
- Uses LightRAG server API endpoints for all operations, ensuring stability.
- Deletion is handled by the `/documents/delete_document` API endpoint.
- No server restarts required - all operations are API-based.
- Deletion is always persistent.
- More robust, as it uses the official API interface.
- Supports retry operations for failed documents.
- Comprehensive verification and status reporting.
"""

import asyncio
import fnmatch
import os
import sys
from typing import Any, Dict, List, Optional
import aiohttp
import json
from pathlib import Path

from ..config import settings


class LightRAGDocumentManager:
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

    async def retry_documents(self, doc_ids: List[str], all_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Retries failed documents by deleting their server entry and triggering a new scan."""
        results = {
            "total_requested": len(doc_ids),
            "retried_successfully": 0,
            "not_found": 0,
            "not_failed": 0,
            "source_file_missing": 0,
            "errors": [],
        }

        docs_to_retry = []
        docs_by_id = {doc["id"]: doc for doc in all_docs}

        print("🔍 Phase 1: Identifying documents to retry")
        for doc_id in doc_ids:
            if doc_id not in docs_by_id:
                print(f"   - ⚠️ Document '{doc_id}' not found on server. Skipping.")
                results["not_found"] += 1
                continue

            doc_info = docs_by_id[doc_id]
            if doc_info.get("status") != "failed":
                print(f"   - ⚠️ Document '{doc_id}' is not in 'failed' state (status: {doc_info.get('status')}). Skipping.")
                results["not_failed"] += 1
                continue
            
            source_path_relative = doc_info.get("file_path")
            if not source_path_relative:
                print(f"   - ❌ Source file path is missing for doc '{doc_id}'. Cannot retry.")
                results["source_file_missing"] += 1
                continue

            # The file_path from the server is relative. We construct the full path
            # by assuming it's within an 'inputs' directory inside the main storage path.
            full_source_path = self.storage_dir / "inputs" / source_path_relative
            
            print(f"     (Checking for source file at: {full_source_path})")

            if not full_source_path.exists():
                print(f"   - ❌ Source file for doc '{doc_id}' not found.")
                results["source_file_missing"] += 1
                continue
            
            print(f"   - ✅ Document '{doc_id}' ({source_path_relative}) is eligible for retry.")
            docs_to_retry.append(doc_info)

        if not docs_to_retry:
            print("\nNo valid documents to retry.")
            return results

        # Phase 2: Delete the failed document entries from LightRAG, one by one.
        print("\n🗑️ Phase 2: Deleting failed document entries from LightRAG (one by one)")
        deleted_count = 0
        for doc_info in docs_to_retry:
            doc_id = doc_info["id"]
            print(f"   - Deleting document: {doc_id} ({doc_info.get('file_path', 'N/A')})")
            delete_payload = {"doc_ids": [doc_id]}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.delete(
                        f"{self.server_url}/documents/delete_document",
                        json=delete_payload,
                        timeout=60
                    ) as resp:
                        if resp.status == 200:
                            print(f"     ✅ Successfully deleted.")
                            deleted_count += 1
                            print("     ⏱️ Waiting 1 second...")
                            await asyncio.sleep(1)  # Delay after each deletion
                        else:
                            error_text = await resp.text()
                            msg = f"Server error during deletion of {doc_id}: {resp.status} - {error_text}"
                            print(f"     ❌ {msg}")
                            results["errors"].append(msg)
            except Exception as e:
                msg = f"An exception occurred during deletion of {doc_id}: {e}"
                print(f"   ❌ {msg}")
                results["errors"].append(msg)
        
        print(f"\n   ✅ Deletion phase complete. Successfully deleted {deleted_count}/{len(docs_to_retry)} documents.")

        # Add a delay to give the server time to process the deletions before scanning.
        print("\n⏱️ Waiting 5 seconds for server to process deletions...")
        await asyncio.sleep(5)

        # Phase 3: Trigger a server-side scan to re-discover and process the files
        print("\n🔄 Phase 3: Triggering server scan to re-process files")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.server_url}/documents/scan", timeout=30) as resp:
                    if resp.status == 200:
                        print("   ✅ Server scan initiated successfully.")
                        print("      Documents will be re-processed in the background.")
                        results["retried_successfully"] = len(docs_to_retry)
                    else:
                        error_text = await resp.text()
                        msg = f"Failed to trigger server scan: {resp.status} - {error_text}"
                        print(f"   ❌ {msg}")
                        results["errors"].append(msg)
            except Exception as e:
                msg = f"An exception occurred while triggering scan: {e}"
                print(f"   ❌ {msg}")
                results["errors"].append(msg)

        return results

    async def finalize(self):
        """No cleanup needed for API-based approach."""
        print("\n✅ Document manager finalized.")

    def get_status_summary(self, all_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a summary of document statuses."""
        status_counts = {}
        for doc in all_docs:
            status = doc.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_documents": len(all_docs),
            "status_breakdown": status_counts,
            "server_url": self.server_url,
            "storage_dir": str(self.storage_dir)
        }

    def filter_documents_by_status(self, all_docs: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
        """Filter documents by their status."""
        return [d for d in all_docs if d.get("status") == status.lower()]

    def filter_documents_by_ids(self, all_docs: List[Dict[str, Any]], doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Filter documents by their IDs."""
        docs_by_id = {doc["id"]: doc for doc in all_docs}
        return [docs_by_id[doc_id] for doc_id in doc_ids if doc_id in docs_by_id]

    def filter_documents_by_name_pattern(self, all_docs: List[Dict[str, Any]], pattern: str) -> List[Dict[str, Any]]:
        """Filter documents by file name pattern (glob-style)."""
        return [
            d for d in all_docs
            if d.get("file_path") and fnmatch.fnmatch(d["file_path"], pattern)
        ]

    async def verify_deletion(self, original_doc_ids: List[str]) -> Dict[str, Any]:
        """Verify that documents have been successfully deleted."""
        remaining_docs = await self.get_all_docs()
        remaining_ids = {doc["id"] for doc in remaining_docs}
        deleted_ids = set(original_doc_ids)

        verified_deleted_count = len(deleted_ids - remaining_ids)
        still_present_count = len(deleted_ids & remaining_ids)

        return {
            "total_targeted": len(original_doc_ids),
            "verified_deleted": verified_deleted_count,
            "still_present": still_present_count,
            "deletion_successful": still_present_count == 0
        }


async def main():
    """Main function to handle command-line interface and execute document management operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LightRAG Document Manager")
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
    parser.add_argument("--retry-all", action="store_true", help="Retry all failed documents")
    
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

    if args.retry and args.retry_all:
        print("❌ Please use either --retry <IDs> or --retry-all, not both.")
        return 1

    # Initialize the document manager
    manager = LightRAGDocumentManager(args.server_url)
    if not await manager.initialize():
        return 1

    # Get all documents
    all_docs = await manager.get_all_docs()
    docs_by_id = {doc["id"]: doc for doc in all_docs}

    # Handle status command
    if args.status:
        print("\n🔍 System Status Check")
        print("-" * 40)
        server_status = await manager.check_server_status()
        print(f"Server Status: {'🟢 Online' if server_status else '🔴 Offline'}")
        print(f"  URL: {manager.server_url}")
        
        status_summary = manager.get_status_summary(all_docs)
        print(f"Documents Found: {status_summary['total_documents']}")
        
        # Count by status
        for status, count in status_summary['status_breakdown'].items():
            print(f"  - {status}: {count}")
        return 0

    # Handle list command
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

    # Handle list-names command
    if args.list_names:
        names = sorted(
            list(set(d.get("file_path") for d in all_docs if d.get("file_path")))
        )
        print("\n📄 Document Names:")
        print("-" * 40)
        for name in names:
            print(f"  - {name}")
        return 0

    # Handle retry logic
    if args.retry:
        print(f"\n🔄 Retrying {len(args.retry)} documents...")
        results = await manager.retry_documents(args.retry, all_docs)
        print("\n" + "=" * 60)
        print("🔄 RETRY SUMMARY")
        print("=" * 60)
        print(f"Total documents targeted: {results['total_requested']}")
        print(f"Retried successfully (re-queued via scan): {results['retried_successfully']}")
        print(f"Not found on server: {results['not_found']}")
        print(f"Not in 'failed' state: {results['not_failed']}")
        print(f"Source file missing: {results['source_file_missing']}")
        if results["errors"]:
            print(f"Errors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"  ❌ {error}")
        await manager.finalize()
        return 0

    if args.retry_all:
        print("\n🔄 Finding all failed documents to retry...")
        failed_docs = manager.filter_documents_by_status(all_docs, "failed")
        
        if not failed_docs:
            print("✅ No failed documents found. Nothing to do.")
            return 0
            
        failed_doc_ids = [d["id"] for d in failed_docs]
        print(f"🎯 Found {len(failed_doc_ids)} failed documents to retry.")

        if not args.no_confirm:
            response = input(f"\nProceed with retrying all {len(failed_doc_ids)} failed documents? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("❌ Retry cancelled.")
                return 0

        results = await manager.retry_documents(failed_doc_ids, all_docs)
        print("\n" + "=" * 60)
        print("🔄 RETRY ALL SUMMARY")
        print("=" * 60)
        print(f"Total documents targeted: {results['total_requested']}")
        print(f"Retried successfully (re-queued via scan): {results['retried_successfully']}")
        print(f"Not found on server: {results['not_found']}")
        print(f"Not in 'failed' state: {results['not_failed']}")
        print(f"Source file missing: {results['source_file_missing']}")
        if results["errors"]:
            print(f"Errors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"  ❌ {error}")
        await manager.finalize()
        return 0

    # Handle deletion logic
    docs_to_delete = []
    confirm = not args.no_confirm
    delete_source = args.delete_source
    verify = args.verify

    if args.nuke:
        print("☢️  --nuke option activated: High-impact deletion mode.")
        confirm = False
        delete_source = True
        verify = True

    # Determine which documents to delete based on the action
    if args.delete_processing:
        docs_to_delete = manager.filter_documents_by_status(all_docs, "processing")
    elif args.delete_failed:
        docs_to_delete = manager.filter_documents_by_status(all_docs, "failed")
    elif args.delete_status:
        docs_to_delete = manager.filter_documents_by_status(all_docs, args.delete_status)
    elif args.delete_ids:
        docs_to_delete = manager.filter_documents_by_ids(all_docs, args.delete_ids)
    elif args.delete_name:
        docs_to_delete = manager.filter_documents_by_name_pattern(all_docs, args.delete_name)

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

    # Store original doc IDs for verification
    original_doc_ids = [doc["id"] for doc in docs_to_delete]

    # Perform deletion
    results = await manager.delete_documents(docs_to_delete, delete_source)

    # Perform verification if requested
    if verify:
        print("\n🔍 Verification Phase")
        verification_results = await manager.verify_deletion(original_doc_ids)
        print(
            f"✅ Verified {verification_results['verified_deleted']}/{verification_results['total_targeted']} documents are deleted."
        )
        results["verified_deleted"] = verification_results["verified_deleted"]

    # Print summary
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
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
