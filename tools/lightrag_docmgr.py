#!/usr/bin/env python3
"""
LightRAG Document Manager

This script provides comprehensive document management capabilities for the LightRAG server,
including API-based deletion, persistent storage management, Docker service control,
and verification of document states. It allows for granular control over document lifecycle
within the LightRAG knowledge base.

Usage:
  From the project root directory, run:
  `python tools/lightrag_docmgr.py [OPTIONS] [ACTIONS]`

Options:
  --url <URL>                 LightRAG server URL (default: from config or http://localhost:9621)
  --storage-path <PATH>       Path to LightRAG storage directory (default: from config)
  --persistent                Delete from persistent storage (permanent, requires --restart-server for immediate effect)
  --restart-server            Restart Docker services (required for persistent deletion to take effect)
  --verify                    Verify deletion after completion by checking server status
  --no-confirm                Skip confirmation prompts for deletion actions
  --delete-source             Delete the original source file from the inputs directory

Actions:
  --status                    Show LightRAG server and Docker service status
  --list                      List all documents with detailed view (ID, file path, status, etc.)
  --list-names                List all document names (file paths only)
  --delete-processing         Delete all documents currently in 'processing' status
  --delete-failed             Delete all documents currently in 'failed' status
  --delete-status <STATUS>    Delete all documents with a specific custom status
  --delete-ids <ID1> [ID2...] Delete specific documents by their unique IDs
  --delete-name <PATTERN>     Delete documents whose file paths match a glob-style pattern (e.g., '*.pdf', 'my_doc.txt')
  --nuke                      Perform a comprehensive deletion. This implicitly sets:
                              --persistent, --restart-server, --verify, --delete-source, and --no-confirm.
                              Must be used with a deletion action (e.g., --delete-processing, --delete-name).

Examples:
  # Check server status
  python tools/lightrag_docmgr.py --status

  # List all documents (detailed)
  python tools/lightrag_docmgr.py --list

  # List only document names
  python tools/lightrag_docmgr.py --list-names

  # Delete all 'processing' documents (API only, temporary)
  python tools/lightrag_docmgr.py --delete-processing

  # Delete all 'failed' documents persistently, restart server, and verify
  python tools/lightrag_docmgr.py --delete-failed --persistent --restart-server --verify

  # Delete a specific document by ID persistently, restart server, and delete source file
  python tools/lightrag_docmgr.py --delete-ids doc-12345 --persistent --restart-server --delete-source

  # Delete all documents matching a name pattern (e.g., all '.md' files) comprehensively
  python tools/lightrag_docmgr.py --nuke --delete-name '*.md'

  # Delete a specific document by name comprehensively
  python tools/lightrag_docmgr.py --nuke --delete-name 'my_important_document.pdf'
"""

import json
import os
import shutil
import subprocess
import sys
import fnmatch
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.config import settings


class EnhancedLightRAGDocumentManager:
    """Class that managers documents in the LightRAG server"""

    def __init__(
        self, base_url: Optional[str] = None, storage_path: Optional[str] = None
    ):
        # Load configuration from settings
        try:
            self.base_url = (base_url or settings.LIGHTRAG_SERVER).rstrip("/")

            # Build storage path from configuration
            if storage_path:
                self.storage_path = storage_path
            else:
                data_dir = settings.DATA_DIR
                storage_backend = settings.STORAGE_BACKEND
                self.storage_path = os.path.join(
                    data_dir, storage_backend, "rag_storage"
                )

            print(f"📁 Using storage path: {self.storage_path}")

        except Exception as e:
            print(f"⚠️  Could not load configuration: {e}")
            print("   Using default values...")
            self.base_url = (base_url or "http://localhost:9621").rstrip("/")
            self.storage_path = (
                storage_path or "/Users/Shared/personal_agent_data/agno/rag_storage"
            )

        self.doc_status_file = os.path.join(
            self.storage_path, "kv_store_doc_status.json"
        )
        self.full_docs_file = os.path.join(self.storage_path, "kv_store_full_docs.json")
        self.text_chunks_file = os.path.join(
            self.storage_path, "kv_store_text_chunks.json"
        )
        self.llm_cache_file = os.path.join(
            self.storage_path, "kv_store_llm_response_cache.json"
        )

    def check_server_status(self) -> bool:
        """Check if LightRAG server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def check_docker_status(self) -> Dict[str, Any]:
        """Check Docker service status"""
        try:
            # Change to project root directory for docker-compose commands
            project_root = Path(__file__).parent.parent
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
                cwd=project_root,
            )
            services = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        services.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            lightrag_service = None
            for service in services:
                if "lightrag" in service.get("Service", "").lower():
                    lightrag_service = service
                    break

            return {
                "running": lightrag_service is not None
                and lightrag_service.get("State") == "running",
                "service": lightrag_service,
                "all_services": services,
            }
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"running": False, "service": None, "all_services": []}

    def stop_docker_services(self) -> bool:
        """Stop Docker services"""
        print("🛑 Stopping Docker services...")
        try:
            project_root = Path(__file__).parent.parent
            result = subprocess.run(
                ["docker-compose", "down"],
                capture_output=True,
                text=True,
                check=True,
                cwd=project_root,
            )
            print("✅ Docker services stopped successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stop Docker services: {e.stderr}")
            return False

    def start_docker_services(self) -> bool:
        """Start Docker services"""
        print("🚀 Starting Docker services...")
        try:
            project_root = Path(__file__).parent.parent
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True,
                text=True,
                check=True,
                cwd=project_root,
            )
            print("✅ Docker services started successfully")

            # Wait for services to initialize
            print("⏳ Waiting for services to initialize...")
            time.sleep(5)

            # Check if LightRAG is responding
            max_retries = 12  # 60 seconds total
            for i in range(max_retries):
                if self.check_server_status():
                    print("✅ LightRAG server is responding")
                    return True
                print(f"⏳ Waiting for LightRAG server... ({i+1}/{max_retries})")
                time.sleep(5)

            print("⚠️  LightRAG server started but may not be fully ready")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start Docker services: {e.stderr}")
            return False

    def backup_storage_files(self) -> Optional[str]:
        """Create backup of storage files"""
        if not os.path.exists(self.storage_path):
            print(f"❌ Storage path does not exist: {self.storage_path}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{self.storage_path}_backup_{timestamp}"

        try:
            print(f"📁 Creating backup at: {backup_dir}")
            shutil.copytree(self.storage_path, backup_dir)
            print(f"✅ Backup created successfully")
            return backup_dir
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return None

    def load_json_file(self, filepath: str) -> Dict[str, Any]:
        """Safely load a JSON file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
            return {}

    def save_json_file(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Safely save a JSON file"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving {filepath}: {e}")
            return False

    def get_documents(self) -> Dict[str, Any]:
        """Fetch all documents from the LightRAG server"""
        try:
            response = requests.get(f"{self.base_url}/documents")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching documents: {e}")
            return {}

    def get_documents_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get documents by specific status"""
        data = self.get_documents()
        if isinstance(data, dict) and "statuses" in data:
            return data["statuses"].get(status, [])
        return []

    def get_documents_by_status_from_storage(self, status: str) -> List[Dict[str, Any]]:
        """Get documents by status from storage files"""
        doc_status_data = self.load_json_file(self.doc_status_file)
        full_docs_data = self.load_json_file(self.full_docs_file) # Load full docs data

        documents = []
        for doc_id, doc_info in doc_status_data.items():
            if doc_info.get("status") == status:
                doc_info["id"] = doc_id
                # Add file_path from full_docs_data if available
                if doc_id in full_docs_data:
                    doc_info["file_path"] = full_docs_data[doc_id].get("metadata", {}).get("file_path")
                documents.append(doc_info)

        return documents

    def delete_document_api(self, doc_id: str) -> bool:
        """Delete a document via API (temporary deletion)"""
        try:
            response = requests.delete(
                f"{self.base_url}/documents/delete_document", json={"doc_id": doc_id}
            )

            if response.status_code in [200, 204]:
                print(f"✅ API deletion successful: {doc_id}")
                return True
            elif response.status_code == 404:
                print(f"⚠️  Document not found in API: {doc_id}")
                return False
            else:
                print(
                    f"❌ API deletion failed for {doc_id}: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ API deletion error for {doc_id}: {e}")
            return False

    def delete_document_from_storage(self, doc_id: str) -> bool:
        """Delete a document from persistent storage files"""
        success = True

        # Remove from doc status
        doc_status_data = self.load_json_file(self.doc_status_file)
        if doc_id in doc_status_data:
            del doc_status_data[doc_id]
            if self.save_json_file(self.doc_status_file, doc_status_data):
                print(f"✅ Removed {doc_id} from doc_status")
            else:
                success = False
        else:
            print(f"⚠️  Document {doc_id} not found in doc_status")

        # Remove from full docs
        full_docs_data = self.load_json_file(self.full_docs_file)
        if doc_id in full_docs_data:
            del full_docs_data[doc_id]
            if self.save_json_file(self.full_docs_file, full_docs_data):
                print(f"✅ Removed {doc_id} from full_docs")
            else:
                success = False
        else:
            print(f"⚠️  Document {doc_id} not found in full_docs")

        # Remove from text chunks
        text_chunks_data = self.load_json_file(self.text_chunks_file)
        chunks_removed = 0
        chunks_to_remove = []

        for chunk_id, chunk_data in text_chunks_data.items():
            if chunk_data.get("full_doc_id") == doc_id:
                chunks_to_remove.append(chunk_id)

        for chunk_id in chunks_to_remove:
            del text_chunks_data[chunk_id]
            chunks_removed += 1

        if chunks_removed > 0:
            if self.save_json_file(self.text_chunks_file, text_chunks_data):
                print(f"✅ Removed {chunks_removed} chunks for {doc_id}")
            else:
                success = False
        else:
            print(f"⚠️  No chunks found for document {doc_id}")

        return success

    def get_source_file_path(self, doc_id: str) -> Optional[str]:
        """Get the source file path from the document metadata"""
        full_docs_data = self.load_json_file(self.full_docs_file)
        doc_info = full_docs_data.get(doc_id)
        if doc_info:
            return doc_info.get("metadata", {}).get("file_path")
        return None

    def list_document_names(self) -> List[str]:
        """List all document names (file paths) from the LightRAG server"""
        documents = self.get_documents()
        names = []
        if isinstance(documents, dict) and "statuses" in documents:
            for status_docs in documents["statuses"].values():
                for doc in status_docs:
                    file_path = doc.get("file_path")
                    if file_path:
                        names.append(file_path)
        return sorted(list(set(names))) # Return unique and sorted names

    def delete_documents_comprehensive(
        self,
        docs_to_delete: List[Dict[str, Any]],  # Now accepts list of dicts with doc_id and file_path
        use_persistent: bool = False,
        restart_server: bool = False,
        verify: bool = False,
        delete_source: bool = False,
    ) -> Dict[str, Any]:
        """
        Comprehensive document deletion with multiple strategies
        """
        doc_ids = [doc["id"] for doc in docs_to_delete]
        results = {
            "total_requested": len(doc_ids),
            "api_deleted": 0,
            "storage_deleted": 0,
            "source_files_deleted": 0,
            "verified_deleted": 0,
            "errors": [],
            "backup_path": None,
        }

        if not doc_ids:
            results["errors"].append("No document IDs provided")
            return results

        print(f"🎯 Starting comprehensive deletion of {len(doc_ids)} documents")
        print(f"   Persistent storage: {'Yes' if use_persistent else 'No'}")
        print(f"   Server restart: {'Yes' if restart_server else 'No'}")
        print(f"   Verification: {'Yes' if verify else 'No'}")
        print(f"   Delete source file: {'Yes' if delete_source else 'No'}")
        print()

        # Phase 1: Delete source files first if requested
        if delete_source:
            print("🗑️ Phase 1: Deleting source files")
            for doc_info in docs_to_delete:
                doc_id = doc_info["id"]
                source_file_path = doc_info.get("file_path") # Use file_path directly from doc_info
                if source_file_path:
                    try:
                        if os.path.exists(source_file_path):
                            os.remove(source_file_path)
                            print(f"✅ Deleted source file: {source_file_path}")
                            results["source_files_deleted"] += 1
                        else:
                            print(
                                f"⚠️  Source file not found, cannot delete: {source_file_path}"
                            )
                    except Exception as e:
                        error_msg = (
                            f"Failed to delete source file {source_file_path}: {e}"
                        )
                        print(f"❌ {error_msg}")
                        results["errors"].append(error_msg)
                else:
                    print(f"⚠️  Could not find source file path for doc_id: {doc_id}")
            print(
                f"✅ Source file deletion complete: {results['source_files_deleted']}/{len(doc_ids)}"
            )
            print()

        # Phase 2: API deletion (if server is running)
        if self.check_server_status():
            print("📡 Phase 2: API-based deletion")
            for doc_id in doc_ids:
                if self.delete_document_api(doc_id):
                    results["api_deleted"] += 1
            print(f"✅ API deletion complete: {results['api_deleted']}/{len(doc_ids)}")
            print()
        else:
            print("⚠️  Server not running, skipping API deletion")
            print()

        # Phase 3: Persistent storage deletion
        if use_persistent:
            print("💾 Phase 3: Persistent storage deletion")

            # Stop server if restart is requested
            if restart_server:
                if not self.stop_docker_services():
                    results["errors"].append("Failed to stop Docker services")
                    return results

            # Create backup
            backup_path = self.backup_storage_files()
            if backup_path:
                results["backup_path"] = backup_path
            else:
                results["errors"].append("Failed to create backup")
                if restart_server:
                    self.start_docker_services()  # Try to restart anyway
                return results

            # Delete the LLM cache file
            if os.path.exists(self.llm_cache_file):
                os.remove(self.llm_cache_file)
                print("✅ Deleted LLM cache file")

            # Delete from storage
            for doc_id in doc_ids:
                if self.delete_document_from_storage(doc_id):
                    results["storage_deleted"] += 1

            print(
                f"✅ Storage deletion complete: {results['storage_deleted']}/{len(doc_ids)}"
            )
            print()

            # Restart server if requested
            if restart_server:
                if not self.start_docker_services():
                    results["errors"].append("Failed to restart Docker services")
                    return results

        # Phase 4: Verification
        if verify:
            print("🔍 Phase 4: Verification")
            time.sleep(2)  # Give server time to stabilize

            if self.check_server_status():
                remaining_docs = self.get_documents()
                all_doc_ids = set()

                if isinstance(remaining_docs, dict) and "statuses" in remaining_docs:
                    for status_docs in remaining_docs["statuses"].values():
                        for doc in status_docs:
                            all_doc_ids.add(doc.get("id"))

                verified_deleted = 0
                for doc_id in doc_ids:
                    if doc_id not in all_doc_ids:
                        verified_deleted += 1
                    else:
                        print(f"⚠️  Document still exists: {doc_id}")

                results["verified_deleted"] = verified_deleted
                print(
                    f"✅ Verification complete: {verified_deleted}/{len(doc_ids)} confirmed deleted"
                )
            else:
                results["errors"].append("Cannot verify - server not responding")
                print("❌ Cannot verify deletion - server not responding")

        return results

    def delete_documents_by_status_comprehensive(
        self,
        status: str,
        use_persistent: bool = False,
        restart_server: bool = False,
        verify: bool = False,
        delete_source: bool = False,
        confirm: bool = True,
    ) -> Dict[str, Any]:
        """Delete all documents with a specific status using comprehensive approach"""

        # Get documents from appropriate source
        if use_persistent and not self.check_server_status():
            docs = self.get_documents_by_status_from_storage(status)
            print(f"📁 Found {len(docs)} documents with status '{status}' in storage")
        else:
            docs = self.get_documents_by_status(status)
            print(f"📡 Found {len(docs)} documents with status '{status}' via API")

        if not docs:
            return {
                "total_requested": 0,
                "api_deleted": 0,
                "storage_deleted": 0,
                "source_files_deleted": 0,
                "verified_deleted": 0,
                "errors": [],
                "backup_path": None,
            }

        # Show documents to be deleted
        print("\nDocuments to be deleted:")
        print("-" * 60)
        for doc in docs:
            doc_id = doc.get("id", "Unknown ID")
            file_path = doc.get("file_path", "Unknown")
            content_length = doc.get("content_length", "Unknown")
            print(f"  🗑️  {doc_id}")
            print(f"      File: {file_path}")
            print(f"      Length: {content_length}")
            print()

        # Confirmation
        if confirm:
            response = input(
                f"Delete these {len(docs)} documents with status '{status}'? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("❌ Deletion cancelled")
                return {
                    "total_requested": 0,
                    "api_deleted": 0,
                    "storage_deleted": 0,
                    "source_files_deleted": 0,
                    "verified_deleted": 0,
                    "errors": ["User cancelled"],
                    "backup_path": None,
                }

        # Extract document IDs and perform deletion
        docs_to_delete_info = [
            {"id": doc.get("id"), "file_path": doc.get("file_path")}
            for doc in docs
            if doc.get("id")
        ]
        return self.delete_documents_comprehensive(
            docs_to_delete_info, use_persistent, restart_server, verify, delete_source
        )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LightRAG Document Manager")
    parser.add_argument(
        "--url",
        default=None,
        help="LightRAG server URL (default: from config or http://localhost:9621)",
    )
    parser.add_argument(
        "--storage-path",
        default=None,
        help="Path to LightRAG storage directory (default: from config)",
    )

    # Actions
    parser.add_argument("--list", action="store_true", help="List all documents (detailed view)")
    parser.add_argument("--list-names", action="store_true", help="List all document names (file paths only)")
    parser.add_argument(
        "--status", action="store_true", help="Show server and Docker status"
    )
    parser.add_argument(
        "--delete-processing",
        action="store_true",
        help="Delete all processing documents",
    )
    parser.add_argument(
        "--delete-failed", action="store_true", help="Delete all failed documents"
    )
    parser.add_argument(
        "--delete-status", type=str, help="Delete all documents with specific status"
    )
    parser.add_argument(
        "--delete-ids", nargs="+", help="Delete specific documents by ID"
    )
    parser.add_argument(
        "--delete-name", type=str, help="Delete documents matching a name pattern (e.g., 'my_doc.pdf' or '*.txt')"
    )

    # Comprehensive Nuke Option
    parser.add_argument(
        "--nuke",
        action="store_true",
        help="Perform a comprehensive deletion: persistent, restart server, verify, delete source, and no confirmation.",
    )

    # Options
    parser.add_argument(
        "--persistent",
        action="store_true",
        help="Delete from persistent storage (permanent)",
    )
    parser.add_argument(
        "--restart-server",
        action="store_true",
        help="Restart Docker services (required for persistent deletion)",
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify deletion after completion"
    )
    parser.add_argument(
        "--no-confirm", action="store_true", help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--delete-source",
        action="store_true",
        help="Delete the original source file from the inputs directory",
    )

    args = parser.parse_args()

    try:
        manager = EnhancedLightRAGDocumentManager(args.url, args.storage_path)
    except Exception as e:
        print(f"❌ Failed to initialize manager: {e}")
        return 1

    if args.status:
        print("🔍 System Status Check")
        print("-" * 40)

        # Server status
        server_running = manager.check_server_status()
        print(
            f"LightRAG Server: {'🟢 Running on ' + manager.base_url if server_running else '🔴 Not responding'}"
        )

        # Docker status
        docker_status = manager.check_docker_status()
        print(
            f"Docker Services: {'🟢 Running' if docker_status['running'] else '🔴 Not running'}"
        )

        if docker_status["service"]:
            service = docker_status["service"]
            print(f"  Service: {service.get('Service', 'Unknown')}")
            print(f"  State: {service.get('State', 'Unknown')}")
            print(f"  Status: {service.get('Status', 'Unknown')}")

        # Storage path
        storage_exists = os.path.exists(manager.storage_path)
        print(f"Storage Path: {'🟢 Exists' if storage_exists else '🔴 Missing'}")
        if storage_exists:
            print(f"  Path: {manager.storage_path}")

        return 0

    if args.list:
        if manager.check_server_status():
            data = manager.get_documents()
            if isinstance(data, dict) and "statuses" in data:
                total_docs = sum(len(docs) for docs in data["statuses"].values())
                print(f"📊 Found {total_docs} total documents")
                print("-" * 40)
                for status, docs in data["statuses"].items():
                    print(f"{status}: {len(docs)} documents")
            else:
                print("❌ No documents found or invalid response")
        else:
            print("❌ Cannot list documents - server not responding")
        return 0

    elif args.list_names:
        if manager.check_server_status():
            names = manager.list_document_names()
            if names:
                print("Document Names:")
                print("-" * 40)
                for name in names:
                    print(f"  - {name}")
            else:
                print("No document names found.")
        else:
            print("❌ Cannot list document names - server not responding")
        return 0

    # Deletion operations
    use_persistent = args.persistent
    restart_server = args.restart_server
    verify = args.verify
    delete_source = args.delete_source
    confirm = not args.no_confirm

    if args.nuke:
        print("☢️  --nuke option activated: Performing comprehensive deletion.")
        use_persistent = True
        restart_server = True
        verify = True
        delete_source = True
        confirm = False  # No confirmation for nuke

    # Validate options
    if use_persistent and not restart_server:
        print(
            "⚠️  Warning: Persistent deletion without server restart may not take effect immediately"
        )
        print("   Consider using --restart-server for immediate effect")
        print()

    results = None

    deletion_action_specified = (
        args.delete_processing
        or args.delete_failed
        or args.delete_status
        or args.delete_ids
        or args.delete_name
    )

    if args.nuke and not deletion_action_specified:
        print("❌ Error: --nuke option requires a deletion action (e.g., --delete-processing, --delete-ids, --delete-name).")
        return 1

    if args.delete_processing:
        results = manager.delete_documents_by_status_comprehensive(
            "processing", use_persistent, restart_server, verify, delete_source, confirm
        )
    elif args.delete_failed:
        results = manager.delete_documents_by_status_comprehensive(
            "failed", use_persistent, restart_server, verify, delete_source, confirm
        )
    elif args.delete_status:
        results = manager.delete_documents_by_status_comprehensive(
            args.delete_status,
            use_persistent,
            restart_server,
            verify,
            delete_source,
            confirm,
        )
    elif args.delete_ids:
        if confirm:
            print(f"Preparing to delete {len(args.delete_ids)} specific documents:")
            for doc_id in args.delete_ids:
                print(f"  - {doc_id}")
            response = input(f"Proceed with deletion? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("❌ Deletion cancelled")
                return 0

        results = manager.delete_documents_comprehensive(
            args.delete_ids, use_persistent, restart_server, verify, delete_source
        )
    elif args.delete_name:
        import fnmatch # Import fnmatch here to avoid circular dependency issues

        if not manager.check_server_status():
            print("❌ Cannot delete by name - server not responding")
            return 1

        all_docs = manager.get_documents()
        matching_docs = []
        name_pattern = args.delete_name

        if isinstance(all_docs, dict) and "statuses" in all_docs:
            for status_docs in all_docs["statuses"].values():
                for doc in status_docs:
                    file_path = doc.get("file_path")
                    if file_path and fnmatch.fnmatch(file_path, name_pattern):
                        matching_docs.append({"id": doc.get("id"), "file_path": file_path})
        
        if not matching_docs:
            print(f"No documents found matching name pattern: '{name_pattern}'")
            return 0

        print(f"Found {len(matching_docs)} documents matching '{name_pattern}':")
        for doc in matching_docs:
            print(f"  - {doc.get("file_path")} (ID: {doc.get("id")})")

        if confirm:
            response = input(f"Delete these {len(matching_docs)} documents? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("❌ Deletion cancelled")
                return 0

        results = manager.delete_documents_comprehensive(
            matching_docs, use_persistent, restart_server, verify, delete_source
        )
    else:
        print("❌ No action specified. Use --help for available options.")
        print("\nQuick examples:")
        print("  python lightrag_docmgr.py --status")
        print("  python lightrag_docmgr.py --list")
        print("  python lightrag_docmgr.py --list-names")
        print("  python lightrag_docmgr.py --delete-processing")
        print("  python lightrag_docmgr.py --delete-name '*.txt'")
        print(
            "  python lightrag_docmgr.py --delete-processing --persistent --restart-server --verify"
        )
        return 0

    # Show results
    if results:
        print("\n" + "=" * 60)
        print("🎯 DELETION SUMMARY")
        print("=" * 60)
        print(f"Total requested: {results['total_requested']}")
        print(f"API deleted: {results['api_deleted']}")
        print(f"Storage deleted: {results['storage_deleted']}")
        print(f"Source files deleted: {results['source_files_deleted']}")
        if verify:
            print(f"Verified deleted: {results['verified_deleted']}")
        if results["backup_path"]:
            print(f"Backup created: {results['backup_path']}")
        if results["errors"]:
            print(f"Errors: {len(results['errors'])}")
            for error in results["errors"]:
                print(f"  ❌ {error}")

        if results["total_requested"] > 0:
            if verify and results["verified_deleted"] == results["total_requested"]:
                print("\n🎉 All documents successfully deleted and verified!")
            elif results["storage_deleted"] > 0 or results["api_deleted"] > 0:
                print("\n✅ Deletion completed successfully!")
            else:
                print("\n⚠️  No documents were deleted")

    return 0


if __name__ == "__main__":
    sys.exit(main())
