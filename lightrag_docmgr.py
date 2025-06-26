#!/usr/bin/env python3
"""
LightRAG Document Management Script

This script connects to a LightRAG server and provides comprehensive document management
capabilities including deletion of failed documents, listing documents, and ingesting
new files from the default knowledge base location.
"""

import asyncio
import json
import logging
import logging.config
import os
import sys
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc, logger, set_verbose_debug

# Handle both direct execution and module import
try:
    from ..config.settings import DATA_DIR
except ImportError:
    # When run directly, add the parent directory to the path
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from personal_agent.config.settings import DATA_DIR

WORKING_DIR = DATA_DIR + "/knowledge"


def configure_logging():
    """Configure logging for the application"""

    # Reset any existing handlers to ensure clean configuration
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "lightrag"]:
        logger_instance = logging.getLogger(logger_name)
        logger_instance.handlers = []
        logger_instance.filters = []

    # Get log directory path from environment variable or use current directory
    log_dir = os.getenv("LOG_DIR", os.getcwd())
    log_file_path = os.path.abspath(os.path.join(log_dir, "lightrag_ollama_demo.log"))

    print(f"\nLightRAG compatible demo log file: {log_file_path}\n")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Get log file max size and backup count from environment variables
    log_max_bytes = int(os.getenv("LOG_MAX_BYTES", 10485760))  # Default 10MB
    log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", 5))  # Default 5 backups

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(levelname)s: %(message)s",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "file": {
                    "formatter": "detailed",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": log_file_path,
                    "maxBytes": log_max_bytes,
                    "backupCount": log_backup_count,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "lightrag": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    )

    # Set the logger level to INFO
    logger.setLevel(logging.INFO)
    # Enable verbose debug if needed
    set_verbose_debug(os.getenv("VERBOSE_DEBUG", "false").lower() == "true")


if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR, exist_ok=True)


class LightRAGDocumentManager:
    """Class manages interacting with LightRag"""

    def __init__(self, base_url: str = "http://localhost:9621"):
        self.base_url = base_url.rstrip("/")

    def get_documents(self) -> Dict[str, Any]:
        """Fetch all documents from the LightRAG server"""
        try:
            response = requests.get(f"{self.base_url}/documents")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching documents: {e}")
            return {}

    def get_failed_documents(self) -> List[Dict[str, Any]]:
        """Get only the documents with 'Failed' status"""
        data = self.get_documents()
        if isinstance(data, dict) and "statuses" in data:
            return data["statuses"].get("failed", [])
        return []

    def clear_cache(self, modes: List[str] = None) -> bool:
        """Clear cache data from the LLM response cache storage

        Args:
            modes: List of cache modes to clear. Valid modes include:
                   "default", "naive", "local", "global", "hybrid", "mix".
                   If None, clears all cache.

        Returns:
            bool: True if cache clearing was successful, False otherwise
        """
        try:
            # Prepare request body
            request_body = {}
            if modes:
                # Validate modes
                valid_modes = {"default", "naive", "local", "global", "hybrid", "mix"}
                invalid_modes = set(modes) - valid_modes
                if invalid_modes:
                    print(f"❌ Invalid cache modes: {invalid_modes}")
                    print(f"Valid modes are: {valid_modes}")
                    return False
                request_body["modes"] = modes

            response = requests.post(
                f"{self.base_url}/documents/clear_cache",
                json=request_body
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Cache cleared successfully: {result.get('message', 'Cache cleared')}")
                return True
            elif response.status_code == 400:
                print(f"❌ Invalid cache modes specified: {response.text}")
                return False
            elif response.status_code == 500:
                print(f"❌ Server error while clearing cache: {response.text}")
                return False
            else:
                print(f"❌ Error clearing cache: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error clearing cache: {e}")
            return False

    def delete_document(self, doc_id: str, clear_cache_after: bool = True) -> bool:
        """Delete a specific document by ID"""
        try:
            # Use the correct endpoint for individual document deletion
            response = requests.delete(
                f"{self.base_url}/documents/delete_document",
                json={"doc_id": doc_id}
            )

            if response.status_code in [200, 204]:
                print(f"✅ Successfully deleted document: {doc_id}")

                # Clear cache after successful deletion
                if clear_cache_after:
                    print("🧹 Clearing cache after deletion...")
                    self.clear_cache()

                return True
            elif response.status_code == 404:
                print(f"❌ Document {doc_id} not found")
                return False
            elif response.status_code == 405:
                print(f"❌ Method not allowed - trying alternative approach")
                # Try with DELETE method and doc_id as query parameter
                response = requests.delete(
                    f"{self.base_url}/documents/delete_document?doc_id={doc_id}"
                )
                if response.status_code in [200, 204]:
                    print(f"✅ Successfully deleted document: {doc_id}")

                    # Clear cache after successful deletion
                    if clear_cache_after:
                        print("🧹 Clearing cache after deletion...")
                        self.clear_cache()

                    return True
                else:
                    print(f"❌ Alternative method also failed: {response.status_code} - {response.text}")
                    return False
            else:
                print(
                    f"❌ Error deleting document {doc_id}: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting document {doc_id}: {e}")
            return False

    def delete_failed_documents(self, confirm: bool = True) -> int:
        """Delete all failed documents"""
        failed_docs = self.get_failed_documents()

        if not failed_docs:
            print("No failed documents found.")
            return 0

        print(f"Found {len(failed_docs)} failed documents:")
        for doc in failed_docs:
            doc_id = doc.get("id", "Unknown ID")
            summary = (
                doc.get("summary", "No summary")[:100] + "..."
                if len(doc.get("summary", "")) > 100
                else doc.get("summary", "No summary")
            )
            length = doc.get("length", "Unknown")
            print(f"  - ID: {doc_id}")
            print(f"    Summary: {summary}")
            print(f"    Length: {length}")
            print()

        if confirm:
            response = input(
                f"Do you want to delete these {len(failed_docs)} failed documents? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("Deletion cancelled.")
                return 0

        deleted_count = 0
        for doc in failed_docs:
            doc_id = doc.get("id")
            # Don't clear cache for each individual deletion to avoid redundant calls
            if doc_id and self.delete_document(doc_id, clear_cache_after=False):
                deleted_count += 1

        # Clear cache once after all deletions are complete
        if deleted_count > 0:
            print("🧹 Clearing cache after bulk deletion...")
            self.clear_cache()

        print(
            f"\n🎉 Successfully deleted {deleted_count} out of {len(failed_docs)} failed documents."
        )
        return deleted_count

    def delete_specific_documents(
        self, doc_ids: List[str], confirm: bool = True
    ) -> int:
        """Delete specific documents by their IDs"""
        if not doc_ids:
            print("No document IDs provided.")
            return 0

        print(f"Preparing to delete {len(doc_ids)} specific documents:")
        for doc_id in doc_ids:
            print(f"  - {doc_id}")

        if confirm:
            response = input(
                f"Do you want to delete these {len(doc_ids)} documents? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("Deletion cancelled.")
                return 0

        deleted_count = 0
        for doc_id in doc_ids:
            # Don't clear cache for each individual deletion to avoid redundant calls
            if self.delete_document(doc_id, clear_cache_after=False):
                deleted_count += 1

        # Clear cache once after all deletions are complete
        if deleted_count > 0:
            print("🧹 Clearing cache after bulk deletion...")
            self.clear_cache()

        print(
            f"\n🎉 Successfully deleted {deleted_count} out of {len(doc_ids)} documents."
        )
        return deleted_count

    def list_all_documents(self):
        """List all documents with their status"""
        data = self.get_documents()
        if not isinstance(data, dict) or "statuses" not in data:
            print("No documents found or invalid response format.")
            return

        statuses = data["statuses"]
        all_docs = []
        status_counts = {}

        # Collect all documents from different status categories
        for status_name, docs_list in statuses.items():
            if isinstance(docs_list, list):
                for doc in docs_list:
                    doc["status"] = status_name  # Ensure status is set
                    all_docs.append(doc)
                status_counts[status_name] = len(docs_list)

        if not all_docs:
            print("No documents found.")
            return

        print(f"Found {len(all_docs)} documents:")
        print("-" * 80)

        for doc in all_docs:
            doc_id = doc.get("id", "Unknown ID")
            status = doc.get("status", "Unknown")
            summary = (
                doc.get("content_summary", "No summary")[:50] + "..."
                if len(doc.get("content_summary", "")) > 50
                else doc.get("content_summary", "No summary")
            )
            length = doc.get("content_length", "Unknown")
            chunks = doc.get("chunks_count", "Unknown")
            file_path = doc.get("file_path", "Unknown")

            status_emoji = (
                "✅"
                if status.lower() == "processed"
                else "❌" if status.lower() == "failed" else "⏳"
            )

            print(f"{status_emoji} {doc_id}")
            print(f"   Status: {status} | Length: {length} | Chunks: {chunks}")
            print(f"   File: {file_path}")
            print(f"   Summary: {summary}")
            print()

        print("-" * 80)
        print("Status Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

    def scan_documents(self) -> bool:
        """Trigger scanning process for new documents"""
        try:
            response = requests.post(f"{self.base_url}/documents/scan")

            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result.get('message', 'Scanning initiated')}")
                return True
            else:
                print(f"❌ Error scanning documents: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error scanning documents: {e}")
            return False

    def upload_file_to_input_dir(self, file_path: str) -> bool:
        """Upload a file to the input directory and index it"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        if not os.path.isfile(file_path):
            print(f"❌ Path is not a file: {file_path}")
            return False

        try:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                response = requests.post(
                    f"{self.base_url}/documents/upload", files=files
                )

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ {result.get('message', f'File {filename} uploaded successfully')}")
                return True
            else:
                print(f"❌ Error uploading file: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error uploading file: {e}")
            return False

    def insert_text(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """Insert text into the RAG system"""
        try:
            request_body = {"text": text}
            if metadata:
                request_body["metadata"] = metadata

            response = requests.post(
                f"{self.base_url}/documents/text",
                json=request_body
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result.get('message', 'Text inserted successfully')}")
                return True
            else:
                print(f"❌ Error inserting text: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error inserting text: {e}")
            return False

    def insert_texts(self, texts: List[str], metadata_list: List[Dict[str, Any]] = None) -> bool:
        """Insert multiple texts into the RAG system"""
        try:
            request_body = {"texts": texts}
            if metadata_list:
                request_body["metadata_list"] = metadata_list

            response = requests.post(
                f"{self.base_url}/documents/texts",
                json=request_body
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result.get('message', f'Successfully inserted {len(texts)} texts')}")
                return True
            else:
                print(f"❌ Error inserting texts: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error inserting texts: {e}")
            return False

    def insert_file_direct(self, file_path: str) -> bool:
        """Insert a file directly into the RAG system"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        if not os.path.isfile(file_path):
            print(f"❌ Path is not a file: {file_path}")
            return False

        try:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                response = requests.post(
                    f"{self.base_url}/documents/file", files=files
                )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result.get('message', f'File {filename} processed successfully')}")
                return True
            else:
                print(f"❌ Error processing file: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error processing file: {e}")
            return False

    def insert_batch_files(self, file_paths: List[str]) -> bool:
        """Process multiple files in batch mode"""
        if not file_paths:
            print("❌ No file paths provided")
            return False

        # Validate all files exist
        missing_files = [fp for fp in file_paths if not os.path.exists(fp)]
        if missing_files:
            print(f"❌ Missing files: {missing_files}")
            return False

        try:
            files = []
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                files.append(("files", (filename, open(file_path, "rb"), "application/octet-stream")))

            response = requests.post(
                f"{self.base_url}/documents/file_batch", files=files
            )

            # Close all file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()

            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result.get('message', f'Batch processing completed for {len(file_paths)} files')}")
                return True
            else:
                print(f"❌ Error in batch processing: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error in batch processing: {e}")
            return False

    def clear_all_documents(self, confirm: bool = True) -> bool:
        """Clear all documents from the system"""
        if confirm:
            response = input("⚠️  This will delete ALL documents. Are you sure? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("Operation cancelled.")
                return False

        try:
            response = requests.delete(f"{self.base_url}/documents")

            if response.status_code in [200, 204]:
                result = response.json() if response.content else {}
                print(f"✅ {result.get('message', 'All documents cleared successfully')}")
                return True
            else:
                print(f"❌ Error clearing documents: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error clearing documents: {e}")
            return False

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get pipeline status information"""
        try:
            response = requests.get(f"{self.base_url}/documents/pipeline_status")

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error getting pipeline status: {response.status_code} - {response.text}")
                return {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting pipeline status: {e}")
            return {}

    def delete_entity(self, entity_name: str, confirm: bool = True) -> bool:
        """Delete an entity from the knowledge graph"""
        if confirm:
            response = input(f"Delete entity '{entity_name}'? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("Deletion cancelled.")
                return False

        try:
            response = requests.delete(
                f"{self.base_url}/documents/delete_entity",
                json={"entity_name": entity_name}
            )

            if response.status_code in [200, 204]:
                print(f"✅ Entity '{entity_name}' deleted successfully")
                return True
            else:
                print(f"❌ Error deleting entity: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting entity: {e}")
            return False

    def delete_relation(self, source_entity: str, target_entity: str, confirm: bool = True) -> bool:
        """Delete a relation between entities"""
        if confirm:
            response = input(f"Delete relation between '{source_entity}' and '{target_entity}'? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("Deletion cancelled.")
                return False

        try:
            response = requests.delete(
                f"{self.base_url}/documents/delete_relation",
                json={"source_entity": source_entity, "target_entity": target_entity}
            )

            if response.status_code in [200, 204]:
                print(f"✅ Relation between '{source_entity}' and '{target_entity}' deleted successfully")
                return True
            else:
                print(f"❌ Error deleting relation: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting relation: {e}")
            return False

    def query_text(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Query the RAG system"""
        try:
            request_body = {"query": query, "mode": mode}
            response = requests.post(
                f"{self.base_url}/query",
                json=request_body
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error querying: {response.status_code} - {response.text}")
                return {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying: {e}")
            return {}

    def ingest_file(self, filename: str, confirm: bool = True) -> bool:
        """Ingest a specific file from the default knowledge base location"""
        file_path = os.path.join(WORKING_DIR, filename)

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        if not os.path.isfile(file_path):
            print(f"❌ Path is not a file: {file_path}")
            return False

        file_size = os.path.getsize(file_path)
        print(f"Found file: {file_path}")
        print(f"File size: {file_size} bytes")

        if confirm:
            response = input(
                f"Do you want to ingest '{filename}' into the knowledge base? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("Ingestion cancelled.")
                return False

        return self.upload_file_to_input_dir(file_path)


async def process_pdf_with_retry(rag, pdf_path, max_retries=3):
    """Process PDF with retry logic and better error handling"""

    for attempt in range(max_retries):
        try:
            print(f"\nAttempt {attempt + 1}/{max_retries} to process PDF: {pdf_path}")

            # Read PDF content (you might need to install PyPDF2 or similar)
            try:
                import PyPDF2

                with open(pdf_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"

                print(f"Extracted {len(text_content)} characters from PDF")

                # Process in smaller chunks if the content is very large
                chunk_size = int(os.getenv("PDF_CHUNK_SIZE", "10000"))  # 10KB chunks

                if len(text_content) > chunk_size:
                    print(f"Processing PDF in chunks of {chunk_size} characters")
                    chunks = [
                        text_content[i : i + chunk_size]
                        for i in range(0, len(text_content), chunk_size)
                    ]

                    for i, chunk in enumerate(chunks):
                        print(f"Processing chunk {i+1}/{len(chunks)}")
                        await rag.ainsert(chunk)
                        # Small delay between chunks to avoid overwhelming Ollama
                        await asyncio.sleep(1)
                else:
                    await rag.ainsert(text_content)

                print(f"Successfully processed PDF: {pdf_path}")
                return True

            except ImportError:
                print("PyPDF2 not installed. Install with: pip install PyPDF2")
                # Fallback: try to read as text file (won't work for binary PDFs)
                with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    await rag.ainsert(content)
                return True

        except asyncio.TimeoutError:
            print(f"Timeout on attempt {attempt + 1}. Retrying...")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 30  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
            else:
                print("Max retries reached. PDF processing failed.")
                return False
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
            else:
                print("Max retries reached. PDF processing failed.")
                return False

    return False


def main():
    """Main function to handle command line arguments and execute operations"""
    import argparse

    parser = argparse.ArgumentParser(description="Manage LightRAG documents")
    parser.add_argument(
        "--url",
        default="http://localhost:9621",
        help="LightRAG server URL (default: http://localhost:9621)",
    )
    parser.add_argument("--list", action="store_true", help="List all documents")
    parser.add_argument(
        "--delete-failed", action="store_true", help="Delete all failed documents"
    )
    parser.add_argument(
        "--delete-ids", nargs="+", help="Delete specific documents by ID"
    )
    parser.add_argument(
        "--ingest-file",
        type=str,
        help="Ingest a specific file from the default knowledge base location",
    )
    parser.add_argument(
        "--clear-cache",
        nargs="*",
        help="Clear cache data. Optionally specify modes: default, naive, local, global, hybrid, mix. If no modes specified, clears all cache.",
    )
    parser.add_argument(
        "--scan", action="store_true", help="Trigger scanning for new documents"
    )
    parser.add_argument(
        "--upload-file", type=str, help="Upload a file to input directory"
    )
    parser.add_argument(
        "--insert-text", type=str, help="Insert text into the RAG system"
    )
    parser.add_argument(
        "--insert-file", type=str, help="Insert a file directly into RAG system"
    )
    parser.add_argument(
        "--batch-files", nargs="+", help="Process multiple files in batch mode"
    )
    parser.add_argument(
        "--clear-all", action="store_true", help="Clear ALL documents from the system"
    )
    parser.add_argument(
        "--pipeline-status", action="store_true", help="Get pipeline status"
    )
    parser.add_argument(
        "--delete-entity", type=str, help="Delete an entity from knowledge graph"
    )
    parser.add_argument(
        "--delete-relation", nargs=2, metavar=("SOURCE", "TARGET"),
        help="Delete relation between two entities"
    )
    parser.add_argument(
        "--query", type=str, help="Query the RAG system"
    )
    parser.add_argument(
        "--query-mode", type=str, default="hybrid",
        choices=["naive", "local", "global", "hybrid", "mix"],
        help="Query mode (default: hybrid)"
    )
    parser.add_argument(
        "--no-confirm", action="store_true", help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    manager = LightRAGDocumentManager(args.url)

    # Determine which action to take based on provided arguments
    action = None
    if args.list:
        action = "list"
    elif args.delete_failed:
        action = "delete_failed"
    elif args.delete_ids:
        action = "delete_ids"
    elif args.ingest_file:
        action = "ingest_file"
    elif args.clear_cache is not None:
        action = "clear_cache"
    elif args.scan:
        action = "scan"
    elif args.upload_file:
        action = "upload_file"
    elif args.insert_text:
        action = "insert_text"
    elif args.insert_file:
        action = "insert_file"
    elif args.batch_files:
        action = "batch_files"
    elif args.clear_all:
        action = "clear_all"
    elif args.pipeline_status:
        action = "pipeline_status"
    elif args.delete_entity:
        action = "delete_entity"
    elif args.delete_relation:
        action = "delete_relation"
    elif args.query:
        action = "query"
    else:
        action = "help"

    # Use match statement to handle different actions
    match action:
        case "list":
            manager.list_all_documents()
        
        case "delete_failed":
            manager.delete_failed_documents(confirm=not args.no_confirm)
        
        case "delete_ids":
            manager.delete_specific_documents(args.delete_ids, confirm=not args.no_confirm)
        
        case "ingest_file":
            manager.ingest_file(args.ingest_file, confirm=not args.no_confirm)
        
        case "clear_cache":
            # If --clear-cache is provided with no arguments, clear all cache
            # If --clear-cache is provided with arguments, clear specific modes
            modes = args.clear_cache if args.clear_cache else None
            manager.clear_cache(modes)
        
        case "scan":
            manager.scan_documents()
        
        case "upload_file":
            manager.upload_file_to_input_dir(args.upload_file)
        
        case "insert_text":
            manager.insert_text(args.insert_text)
        
        case "insert_file":
            manager.insert_file_direct(args.insert_file)
        
        case "batch_files":
            manager.insert_batch_files(args.batch_files)
        
        case "clear_all":
            manager.clear_all_documents(confirm=not args.no_confirm)
        
        case "pipeline_status":
            status = manager.get_pipeline_status()
            if status:
                print("📊 Pipeline Status:")
                print(json.dumps(status, indent=2))
        
        case "delete_entity":
            manager.delete_entity(args.delete_entity, confirm=not args.no_confirm)
        
        case "delete_relation":
            source, target = args.delete_relation
            manager.delete_relation(source, target, confirm=not args.no_confirm)
        
        case "query":
            result = manager.query_text(args.query, args.query_mode)
            if result:
                print("🔍 Query Result:")
                print(json.dumps(result, indent=2))
        
        case "help" | _:
            print("No action specified. Use --help for available options.")
            print("\n📚 Document Management:")
            print("  python lightrag_docmgr.py --list")
            print("  python lightrag_docmgr.py --scan")
            print("  python lightrag_docmgr.py --upload-file /path/to/file.pdf")
            print("  python lightrag_docmgr.py --insert-file /path/to/file.txt")
            print("  python lightrag_docmgr.py --batch-files file1.pdf file2.txt file3.docx")
            print("  python lightrag_docmgr.py --ingest-file document.pdf")
            print("  python lightrag_docmgr.py --insert-text 'Your text here'")
            print("\n🗑️  Deletion Operations:")
            print("  python lightrag_docmgr.py --delete-failed")
            print("  python lightrag_docmgr.py --delete-ids doc-123 doc-456")
            print("  python lightrag_docmgr.py --clear-all")
            print("  python lightrag_docmgr.py --delete-entity 'Entity Name'")
            print("  python lightrag_docmgr.py --delete-relation 'Source Entity' 'Target Entity'")
            print("\n🧹 Cache Management:")
            print("  python lightrag_docmgr.py --clear-cache")
            print("  python lightrag_docmgr.py --clear-cache default naive")
            print("\n🔍 Query & Status:")
            print("  python lightrag_docmgr.py --query 'What is machine learning?'")
            print("  python lightrag_docmgr.py --query 'AI concepts' --query-mode local")
            print("  python lightrag_docmgr.py --pipeline-status")
            print(f"\n📁 Default knowledge base location: {WORKING_DIR}")


if __name__ == "__main__":
    main()
