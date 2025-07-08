#!/usr/bin/env python3
"""
LightRAG Document Manager V2

A modernized document management tool for LightRAG that uses the core LightRAG
library for stable and reliable operations. This version replaces direct API calls
and manual file manipulation with the official `LightRAG` class methods.

Key Improvements from V1:
- Uses `lightrag.lightrag.LightRAG` for all operations, ensuring stability.
- Deletion is now handled by the canonical `adelete_by_doc_id` method.
- No longer requires server restarts (`--restart-server` is removed).
- Deletion is always persistent (`--persistent` is removed).
- More robust, as it can operate directly on storage without a running server.

Usage:
  From the project root directory, run:
  `python tools/lightrag_docmgr_v2.py [OPTIONS] [ACTIONS]`

Options:
  --working-dir <PATH>        Path to LightRAG working directory (default: from config)
  --verify                    Verify deletion after completion by checking storage
  --no-confirm                Skip confirmation prompts for deletion actions
  --delete-source             Delete the original source file from the inputs directory

Actions:
  --status                    Show LightRAG storage and document status
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
  # Check storage status
  python tools/lightrag_docmgr_v2.py --status

  # List all documents
  python tools/lightrag_docmgr_v2.py --list

  # Delete all 'failed' documents and verify
  python tools/lightrag_docmgr_v2.py --delete-failed --verify

  # Delete a specific document by ID and also delete the source file
  python tools/lightrag_docmgr_v2.py --delete-ids doc-12345 --delete-source

  # Delete all '.md' files comprehensively
  python tools/lightrag_docmgr_v2.py --nuke --delete-name '*.md'
"""

import argparse
import asyncio
import fnmatch
import os
import sys
from typing import Any, Dict, List, Optional

from lightrag.base import DeletionResult, DocStatus
from lightrag.lightrag import LightRAG
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

from personal_agent.config import settings


class LightRAGDocumentManagerV2:
    """Manages documents in LightRAG using the core library."""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.path.join(
            settings.AGNO_STORAGE_DIR, "rag_storage"
        )
        print(f"📁 Using LightRAG working directory: {self.working_dir}")
        self.rag: Optional[LightRAG] = None

        # Cache files that need to be cleared during deletion
        self.llm_cache_file = os.path.join(
            self.working_dir, "kv_store_llm_response_cache.json"
        )

    async def initialize(self) -> bool:
        """Initializes the LightRAG instance."""
        if not os.path.exists(self.working_dir):
            print(f"❌ Working directory not found: {self.working_dir}")
            print("   Please ensure LightRAG has been run at least once to create it.")
            return False
        try:
            # Use the function-based approach like the working examples
            embedding_func = EmbeddingFunc(
                embedding_dim=768,  # Match existing storage dimension
                max_token_size=8192,
                func=lambda texts: ollama_embed(
                    texts,
                    embed_model="nomic-embed-text",  # Using nomic-embed-text model
                    host=settings.OLLAMA_URL,
                ),
            )

            self.rag = LightRAG(
                working_dir=self.working_dir,
                llm_model_func=ollama_model_complete,
                llm_model_name=settings.LLM_MODEL,
                llm_model_max_token_size=8192,
                llm_model_kwargs={
                    "host": settings.OLLAMA_URL,
                    "options": {"num_ctx": 8192},
                    "timeout": 300,
                },
                embedding_func=embedding_func,
            )
            # Ensure storages are properly initialized
            await self.rag.initialize_storages()
            print("✅ LightRAG instance initialized successfully.")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize LightRAG: {e}")
            return False

    async def get_all_docs(self) -> List[Dict[str, Any]]:
        """Fetches all document statuses directly from storage."""
        if not self.rag:
            return []

        all_docs = []
        for status in list(DocStatus):
            try:
                docs = await self.rag.get_docs_by_status(status)
                for doc_id, doc_info in docs.items():
                    # Convert DocProcessingStatus to dict and add the ID
                    doc_dict = {
                        "id": doc_id,
                        "status": doc_info.status,
                        "content": doc_info.content,
                        "content_summary": doc_info.content_summary,
                        "content_length": doc_info.content_length,
                        "file_path": doc_info.file_path,
                        "created_at": doc_info.created_at,
                        "updated_at": doc_info.updated_at,
                        "chunks_count": getattr(doc_info, "chunks_count", None),
                        "chunks_list": getattr(doc_info, "chunks_list", []),
                        "error": doc_info.error,
                        "metadata": doc_info.metadata,
                    }
                    all_docs.append(doc_dict)
            except Exception as e:
                print(f"⚠️ Could not retrieve docs with status {status}: {e}")
        return all_docs

    async def delete_documents(
        self, docs_to_delete: List[Dict[str, Any]], delete_source: bool = False
    ) -> Dict[str, Any]:
        """Deletes a list of documents using adelete_by_doc_id."""
        if not self.rag:
            return {"errors": ["LightRAG not initialized."]}

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

        # Phase 2: Delete documents from LightRAG storage
        print("\n💾 Phase 2: Deleting documents from LightRAG storage")
        for doc_info in docs_to_delete:
            doc_id = doc_info["id"]
            print(f"   - Deleting {doc_id}...")
            try:
                result = await self.rag.adelete_by_doc_id(doc_id)
                if result.status == "success":
                    print(f"   ✅ Success: {result.message}")
                    results["deleted_successfully"] += 1
                elif result.status == "not_found":
                    print(f"   ⚠️ Not Found: {result.message}")
                    results["not_found"] += 1
                else:
                    print(f"   ❌ Failure: {result.message}")
                    results["errors"].append(result.message)
            except Exception as e:
                msg = f"An exception occurred while deleting {doc_id}: {e}"
                print(f"   ❌ {msg}")
                results["errors"].append(msg)

        # Phase 3: Clear LLM cache to prevent cached responses
        print("\n🧹 Phase 3: Clearing LLM cache")
        if os.path.exists(self.llm_cache_file):
            try:
                os.remove(self.llm_cache_file)
                print("✅ Deleted LLM cache file to prevent stale cached responses")
            except OSError as e:
                msg = f"Failed to delete LLM cache file: {e}"
                print(f"❌ {msg}")
                results["errors"].append(msg)
        else:
            print("⚠️ LLM cache file not found, skipping cache clear")

        print("✅ LightRAG deletion complete.")

        return results

    async def finalize(self):
        """Properly close the LightRAG instance."""
        if self.rag:
            await self.rag.finalize_storages()
            print("\n✅ LightRAG instance finalized.")


async def main():
    parser = argparse.ArgumentParser(description="LightRAG Document Manager V2")
    parser.add_argument("--working-dir", help="Path to LightRAG working directory")
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

    manager = LightRAGDocumentManagerV2(args.working_dir)
    if not await manager.initialize():
        return 1

    all_docs = await manager.get_all_docs()
    docs_by_id = {doc["id"]: doc for doc in all_docs}

    if args.status:
        print("\n🔍 System Status Check")
        print("-" * 40)
        print(
            f"Storage Path: {'🟢 Exists' if os.path.exists(manager.working_dir) else '🔴 Missing'}"
        )
        print(f"  Path: {manager.working_dir}")
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
        docs_to_delete = [d for d in all_docs if d.get("status") == "PROCESSING"]
    elif args.delete_failed:
        docs_to_delete = [d for d in all_docs if d.get("status") == "FAILED"]
    elif args.delete_status:
        docs_to_delete = [
            d for d in all_docs if d.get("status") == args.delete_status.upper()
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
    else:
        print("❌ No deletion action specified. Use --help for options.")
        return 1

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
