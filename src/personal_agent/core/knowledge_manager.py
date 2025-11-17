"""
Knowledge Storage Manager for Personal Agent.

This module provides file system and LightRAG server operations for document storage.
It handles server health monitoring, document management, and local file operations.

IMPORTANT: This manager handles DOCUMENT STORAGE and SERVER OPERATIONS, not fact management.
For user facts and preferences, use AgentFactManager.

Manages: LightRAG Knowledge Server (port 9621) and local knowledge directory
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests

from ..config import settings
from ..utils import setup_logging

logger = setup_logging(__name__)


class KnowledgeStorageManager:
    """
    Manages document storage operations for the Personal AI Agent.

    This class provides:
    - LightRAG server health monitoring and status checks
    - Local knowledge directory file management
    - Document tracking and deletion
    - Pipeline status monitoring

    IMPORTANT: This handles STORAGE OPERATIONS, not content ingestion or fact management.
    - For document ingestion: Use KnowledgeTools
    - For user facts: Use AgentFactManager

    Targets: LightRAG Knowledge Server (port 9621) and local file system
    """

    def __init__(
        self,
        user_id: str,
        knowledge_dir: Optional[str] = None,
        lightrag_url: Optional[str] = None,
    ):
        """Initialize the knowledge storage manager.

        :param user_id: User identifier for knowledge operations
        :param knowledge_dir: Directory for knowledge files (defaults to AGNO_KNOWLEDGE_DIR)
        :param lightrag_url: URL for LightRAG API (defaults to LIGHTRAG_URL)
        """
        self.user_id = user_id
        self.knowledge_dir = Path(knowledge_dir or settings.AGNO_KNOWLEDGE_DIR)
        self.lightrag_url = lightrag_url or settings.LIGHTRAG_URL
        
        # Ensure knowledge directory exists
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Knowledge manager initialized for user {user_id}")
        logger.info(f"Knowledge directory: {self.knowledge_dir}")
        logger.info(f"LightRAG URL: {self.lightrag_url}")

    async def check_server_status(self) -> bool:
        """Check if LightRAG server is accessible.

        Returns:
            True if server is accessible, False otherwise.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lightrag_url}/health", timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.warning(f"Cannot connect to LightRAG server: {e}")
            return False

    async def get_pipeline_status(self) -> Dict:
        """Get the current processing pipeline status from LightRAG.

        Returns:
            Dictionary with pipeline status information.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lightrag_url}/documents/pipeline_status", timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"status": "error", "message": f"HTTP {resp.status}"}
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {"status": "error", "message": str(e)}

    async def wait_for_pipeline_idle(self, timeout: int = 300) -> bool:
        """Wait for the LightRAG processing pipeline to become idle.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if pipeline became idle, False if timeout occurred.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = await self.get_pipeline_status()
                
                # Check if pipeline is idle (no pending or processing documents)
                if status.get("status") == "idle" or (
                    status.get("pending", 0) == 0 and 
                    status.get("processing", 0) == 0
                ):
                    logger.info("Pipeline is idle")
                    return True
                    
                logger.debug(f"Pipeline status: {status}")
                await asyncio.sleep(2)  # Wait 2 seconds before checking again
                
            except Exception as e:
                logger.warning(f"Error checking pipeline status: {e}")
                await asyncio.sleep(5)  # Wait longer on error
        
        logger.warning(f"Pipeline did not become idle within {timeout} seconds")
        return False

    async def get_knowledge_stats(self) -> Dict:
        """Get statistics about the knowledge base.

        Returns:
            Dictionary with knowledge base statistics.
        """
        try:
            stats = {
                "local_files": 0,
                "local_size_mb": 0.0,
                "server_documents": 0,
                "server_status": "unknown",
                "pipeline_status": "unknown"
            }

            # Count local files
            if self.knowledge_dir.exists():
                local_files = list(self.knowledge_dir.glob("*"))
                local_files = [f for f in local_files if f.is_file()]
                stats["local_files"] = len(local_files)
                
                # Calculate total size
                total_size = sum(f.stat().st_size for f in local_files)
                stats["local_size_mb"] = total_size / (1024 * 1024)

            # Get server statistics
            try:
                async with aiohttp.ClientSession() as session:
                    # Check server status
                    async with session.get(f"{self.lightrag_url}/health", timeout=10) as resp:
                        stats["server_status"] = "online" if resp.status == 200 else "offline"
                    
                    # Get document count
                    async with session.get(f"{self.lightrag_url}/documents", timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            # Count documents from different status categories
                            total_docs = 0
                            if isinstance(data, dict) and "statuses" in data:
                                for status_name, docs_list in data["statuses"].items():
                                    if isinstance(docs_list, list):
                                        total_docs += len(docs_list)
                            elif isinstance(data, dict) and "documents" in data:
                                total_docs = len(data["documents"])
                            elif isinstance(data, list):
                                total_docs = len(data)
                            
                            stats["server_documents"] = total_docs
                    
                    # Get pipeline status
                    pipeline_status = await self.get_pipeline_status()
                    stats["pipeline_status"] = pipeline_status.get("status", "unknown")
                    
            except Exception as e:
                logger.warning(f"Error getting server statistics: {e}")
                stats["server_status"] = "error"

            return stats

        except Exception as e:
            logger.error(f"Error getting knowledge statistics: {e}")
            return {"error": str(e)}

    async def scan_for_new_documents(self) -> Dict:
        """Trigger LightRAG to scan for new documents in the inputs directory.

        Returns:
            Dictionary with scan results.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.lightrag_url}/documents/scan", timeout=30) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info("Document scan triggered successfully")
                        return result
                    else:
                        error_text = await resp.text()
                        logger.error(f"Document scan failed: {error_text}")
                        return {"status": "error", "message": error_text}
        except Exception as e:
            logger.error(f"Error triggering document scan: {e}")
            return {"status": "error", "message": str(e)}

    async def clear_knowledge_base(self) -> Dict:
        """Clear all documents from the knowledge base.

        Returns:
            Dictionary with clearing results.
        """
        try:
            results = {
                "local_files_deleted": 0,
                "server_documents_deleted": 0,
                "errors": []
            }

            # Clear local files
            try:
                if self.knowledge_dir.exists():
                    local_files = list(self.knowledge_dir.glob("*"))
                    local_files = [f for f in local_files if f.is_file()]
                    
                    for file_path in local_files:
                        try:
                            file_path.unlink()
                            results["local_files_deleted"] += 1
                        except OSError as e:
                            results["errors"].append(f"Failed to delete {file_path.name}: {e}")
                    
                    logger.info(f"Deleted {results['local_files_deleted']} local knowledge files")
            except Exception as e:
                results["errors"].append(f"Error clearing local files: {e}")

            # Clear server documents
            try:
                async with aiohttp.ClientSession() as session:
                    # Get all documents first
                    async with session.get(f"{self.lightrag_url}/documents", timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            all_docs = []
                            
                            # Extract documents from response
                            if isinstance(data, dict) and "statuses" in data:
                                for status_name, docs_list in data["statuses"].items():
                                    if isinstance(docs_list, list):
                                        all_docs.extend(docs_list)
                            elif isinstance(data, dict) and "documents" in data:
                                all_docs = data["documents"]
                            elif isinstance(data, list):
                                all_docs = data

                            if all_docs:
                                # Delete all documents
                                doc_ids = [doc["id"] for doc in all_docs]
                                payload = {"doc_ids": doc_ids, "delete_file": True}

                                async with session.delete(
                                    f"{self.lightrag_url}/documents/delete_document",
                                    json=payload,
                                    timeout=60,
                                ) as del_resp:
                                    if del_resp.status == 200:
                                        results["server_documents_deleted"] = len(doc_ids)
                                        logger.info(f"Deleted {len(doc_ids)} server documents")
                                    else:
                                        error_text = await del_resp.text()
                                        results["errors"].append(f"Server deletion failed: {error_text}")
                            else:
                                logger.info("No server documents found to delete")
                        else:
                            error_text = await resp.text()
                            results["errors"].append(f"Failed to get server documents: {error_text}")
            except Exception as e:
                results["errors"].append(f"Error clearing server documents: {e}")

            return results

        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            return {"error": str(e)}

    def get_local_knowledge_files(self) -> List[Dict]:
        """Get information about local knowledge files.

        Returns:
            List of dictionaries with file information.
        """
        try:
            files_info = []
            
            if self.knowledge_dir.exists():
                for file_path in self.knowledge_dir.glob("*"):
                    if file_path.is_file():
                        stat = file_path.stat()
                        files_info.append({
                            "name": file_path.name,
                            "path": str(file_path),
                            "size_bytes": stat.st_size,
                            "size_mb": stat.st_size / (1024 * 1024),
                            "modified": stat.st_mtime,
                            "extension": file_path.suffix.lower()
                        })
            
            # Sort by modification time (newest first)
            files_info.sort(key=lambda x: x["modified"], reverse=True)
            
            return files_info

        except Exception as e:
            logger.error(f"Error getting local knowledge files: {e}")
            return []

    async def validate_knowledge_sync(self) -> Dict:
        """Validate that local files are properly synced with the server.

        Returns:
            Dictionary with sync validation results.
        """
        try:
            results = {
                "local_files": 0,
                "server_documents": 0,
                "sync_issues": [],
                "recommendations": []
            }

            # Get local files
            local_files = self.get_local_knowledge_files()
            results["local_files"] = len(local_files)

            # Get server documents
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.lightrag_url}/documents", timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            # Count server documents
                            total_docs = 0
                            if isinstance(data, dict) and "statuses" in data:
                                for status_name, docs_list in data["statuses"].items():
                                    if isinstance(docs_list, list):
                                        total_docs += len(docs_list)
                            elif isinstance(data, dict) and "documents" in data:
                                total_docs = len(data["documents"])
                            elif isinstance(data, list):
                                total_docs = len(data)
                            
                            results["server_documents"] = total_docs
                        else:
                            results["sync_issues"].append("Cannot access server documents")
            except Exception as e:
                results["sync_issues"].append(f"Server communication error: {e}")

            # Analyze sync status
            if results["local_files"] > results["server_documents"]:
                results["sync_issues"].append("More local files than server documents")
                results["recommendations"].append("Run document scan to sync missing files")
            elif results["local_files"] < results["server_documents"]:
                results["sync_issues"].append("More server documents than local files")
                results["recommendations"].append("Some documents may have been uploaded directly")

            # Check pipeline status
            pipeline_status = await self.get_pipeline_status()
            if pipeline_status.get("status") != "idle":
                results["sync_issues"].append("Pipeline is not idle - processing may be ongoing")
                results["recommendations"].append("Wait for pipeline to complete processing")

            return results

        except Exception as e:
            logger.error(f"Error validating knowledge sync: {e}")
            return {"error": str(e)}


# Backward compatibility alias
KnowledgeManager = KnowledgeStorageManager
