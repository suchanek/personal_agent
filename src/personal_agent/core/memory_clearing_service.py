#!/usr/bin/env python3
"""
Centralized Memory Clearing Service

A unified service for all memory clearing operations across the personal agent system.
This service consolidates all deletion logic to avoid code duplication and ensure
consistent behavior across different entry points.

Key Features:
- Centralized clearing logic for all memory systems
- Clears semantic memories (SQLite)
- Clears LightRAG graph memories
- Clears memory_inputs directory (MISSING FUNCTIONALITY ADDED)
- Clears knowledge graph files
- Clears server cache
- Dry-run capability for testing
- Comprehensive error handling and logging
"""

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class ClearingResult:
    """Result of a memory clearing operation."""
    success: bool
    message: str
    items_cleared: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class ClearingOptions:
    """Options for memory clearing operations."""
    dry_run: bool = False
    semantic_only: bool = False
    lightrag_only: bool = False
    include_memory_inputs: bool = True
    include_knowledge_graph: bool = True
    include_cache: bool = True
    verbose: bool = False


class MemoryClearingService:
    """Centralized service for all memory clearing operations."""

    def __init__(
        self,
        user_id: str,
        agno_memory=None,
        lightrag_memory_url: Optional[str] = None,
        verbose: bool = False,
    ):
        """Initialize the memory clearing service.
        
        Args:
            user_id: User identifier for memory operations
            agno_memory: Optional initialized agno memory instance
            lightrag_memory_url: Optional URL for LightRAG Memory API
            verbose: Enable verbose logging
        """
        self.user_id = user_id
        self.agno_memory = agno_memory
        self.lightrag_memory_url = lightrag_memory_url
        self.verbose = verbose
        
        # Import settings for directory paths
        try:
            from ..config.settings import (
                LIGHTRAG_MEMORY_INPUTS_DIR,
                LIGHTRAG_MEMORY_STORAGE_DIR,
                LIGHTRAG_STORAGE_DIR
            )
            self.memory_inputs_dir = Path(LIGHTRAG_MEMORY_INPUTS_DIR)
            self.memory_storage_dirs = [
                Path(LIGHTRAG_MEMORY_STORAGE_DIR),
                Path(LIGHTRAG_STORAGE_DIR)
            ]
        except ImportError as e:
            logger.error(f"Failed to import settings: {e}")
            self.memory_inputs_dir = None
            self.memory_storage_dirs = []

    async def clear_memory_inputs_directory(self, dry_run: bool = False) -> ClearingResult:
        """Clear all files in the memory_inputs directory.
        
        This is the MISSING FUNCTIONALITY that was not being handled before.
        
        Args:
            dry_run: If True, only simulate the clearing without actually deleting
            
        Returns:
            ClearingResult with operation details
        """
        if not self.memory_inputs_dir:
            return ClearingResult(
                success=False,
                message="Memory inputs directory path not configured",
                errors=["LIGHTRAG_MEMORY_INPUTS_DIR not available"]
            )
        
        try:
            if not self.memory_inputs_dir.exists():
                if self.verbose:
                    logger.info(f"Memory inputs directory does not exist: {self.memory_inputs_dir}")
                return ClearingResult(
                    success=True,
                    message=f"Memory inputs directory does not exist: {self.memory_inputs_dir}",
                    items_cleared=0
                )
            
            # Get all files in the directory
            files_to_delete = []
            dirs_to_delete = []
            
            for item in self.memory_inputs_dir.iterdir():
                if item.is_file():
                    files_to_delete.append(item)
                elif item.is_dir():
                    dirs_to_delete.append(item)
            
            total_items = len(files_to_delete) + len(dirs_to_delete)
            
            if dry_run:
                message = f"DRY RUN: Would delete {len(files_to_delete)} files and {len(dirs_to_delete)} directories from {self.memory_inputs_dir}"
                if self.verbose:
                    logger.info(message)
                    for file_path in files_to_delete:
                        logger.info(f"  Would delete file: {file_path}")
                    for dir_path in dirs_to_delete:
                        logger.info(f"  Would delete directory: {dir_path}")
                return ClearingResult(
                    success=True,
                    message=message,
                    items_cleared=total_items
                )
            
            # Actually delete the files and directories
            deleted_count = 0
            errors = []
            
            # Delete files first
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    if self.verbose:
                        logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    error_msg = f"Failed to delete file {file_path}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Delete directories
            for dir_path in dirs_to_delete:
                try:
                    shutil.rmtree(dir_path)
                    deleted_count += 1
                    if self.verbose:
                        logger.info(f"Deleted directory: {dir_path}")
                except Exception as e:
                    error_msg = f"Failed to delete directory {dir_path}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            success = len(errors) == 0
            message = f"Cleared {deleted_count} items from memory inputs directory: {self.memory_inputs_dir}"
            
            if errors:
                message += f" (with {len(errors)} errors)"
            
            if self.verbose:
                logger.info(message)
            
            return ClearingResult(
                success=success,
                message=message,
                items_cleared=deleted_count,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Error clearing memory inputs directory: {e}"
            logger.error(error_msg)
            return ClearingResult(
                success=False,
                message=error_msg,
                errors=[str(e)]
            )

    async def clear_semantic_memories(self, dry_run: bool = False) -> ClearingResult:
        """Clear all semantic memories from SQLite database.
        
        Args:
            dry_run: If True, only simulate the clearing without actually deleting
            
        Returns:
            ClearingResult with operation details
        """
        if not self.agno_memory or not self.agno_memory.memory_manager:
            return ClearingResult(
                success=False,
                message="Semantic memory system not initialized",
                errors=["agno_memory not available"]
            )
        
        try:
            # Get count before clearing for verification
            pre_clear_stats = self.agno_memory.memory_manager.get_memory_stats(
                db=self.agno_memory.db,
                user_id=self.user_id
            )
            pre_clear_count = pre_clear_stats.get("total_memories", 0)
            
            if dry_run:
                message = f"DRY RUN: Would clear {pre_clear_count} semantic memories"
                if self.verbose:
                    logger.info(message)
                return ClearingResult(
                    success=True,
                    message=message,
                    items_cleared=pre_clear_count
                )
            
            # Clear memories using the memory manager
            success, message = self.agno_memory.memory_manager.clear_memories(
                db=self.agno_memory.db,
                user_id=self.user_id
            )
            
            if success:
                # Verify clearing was successful
                post_clear_stats = self.agno_memory.memory_manager.get_memory_stats(
                    db=self.agno_memory.db,
                    user_id=self.user_id
                )
                post_clear_count = post_clear_stats.get("total_memories", 0)
                
                if post_clear_count == 0:
                    final_message = f"Successfully cleared {pre_clear_count} semantic memories (verified)"
                    if self.verbose:
                        logger.info(final_message)
                    return ClearingResult(
                        success=True,
                        message=final_message,
                        items_cleared=pre_clear_count
                    )
                else:
                    error_msg = f"Clearing incomplete: {post_clear_count} memories still remain after clearing {pre_clear_count}"
                    logger.error(error_msg)
                    return ClearingResult(
                        success=False,
                        message=error_msg,
                        items_cleared=pre_clear_count - post_clear_count,
                        errors=[error_msg]
                    )
            else:
                logger.error(f"Failed to clear semantic memories: {message}")
                return ClearingResult(
                    success=False,
                    message=f"Failed to clear semantic memories: {message}",
                    errors=[message]
                )
                
        except Exception as e:
            error_msg = f"Error clearing semantic memories: {e}"
            logger.error(error_msg)
            return ClearingResult(
                success=False,
                message=error_msg,
                errors=[str(e)]
            )

    async def clear_lightrag_documents(self, dry_run: bool = False) -> ClearingResult:
        """Clear all documents from LightRAG memory server.
        
        Args:
            dry_run: If True, only simulate the clearing without actually deleting
            
        Returns:
            ClearingResult with operation details
        """
        if not self.lightrag_memory_url:
            return ClearingResult(
                success=False,
                message="LightRAG memory URL not configured",
                errors=["lightrag_memory_url not available"]
            )
        
        try:
            # Get all documents first
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lightrag_memory_url}/documents", timeout=30) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        error_msg = f"Failed to get documents from LightRAG: {error_text}"
                        logger.error(error_msg)
                        return ClearingResult(
                            success=False,
                            message=error_msg,
                            errors=[error_text]
                        )
                    
                    data = await resp.json()
                    all_docs = []
                    
                    # Extract documents from response
                    if isinstance(data, dict) and "statuses" in data:
                        statuses = data["statuses"]
                        for status_name, docs_list in statuses.items():
                            if isinstance(docs_list, list):
                                all_docs.extend(docs_list)
                    elif isinstance(data, dict) and "documents" in data:
                        all_docs = data["documents"]
                    elif isinstance(data, list):
                        all_docs = data
                    
                    if not all_docs:
                        message = "No LightRAG documents found to clear"
                        if self.verbose:
                            logger.info(message)
                        return ClearingResult(
                            success=True,
                            message=message,
                            items_cleared=0
                        )
                    
                    doc_count = len(all_docs)
                    
                    if dry_run:
                        message = f"DRY RUN: Would delete {doc_count} documents from LightRAG"
                        if self.verbose:
                            logger.info(message)
                            for doc in all_docs[:5]:  # Show first 5 docs
                                logger.info(f"  Would delete: {doc.get('id')} ({doc.get('file_path', 'N/A')})")
                            if doc_count > 5:
                                logger.info(f"  ... and {doc_count - 5} more documents")
                        return ClearingResult(
                            success=True,
                            message=message,
                            items_cleared=doc_count
                        )
                    
                    # Delete all documents
                    doc_ids = [doc["id"] for doc in all_docs]
                    payload = {"doc_ids": doc_ids, "delete_file": True}
                    
                    async with session.delete(
                        f"{self.lightrag_memory_url}/documents/delete_document",
                        json=payload,
                        timeout=60
                    ) as del_resp:
                        if del_resp.status == 200:
                            result_data = await del_resp.json()
                            status = result_data.get("status", "unknown")
                            message = result_data.get("message", "No message")
                            
                            if status == "deletion_started":
                                final_message = f"Successfully deleted {doc_count} documents from LightRAG"
                                if self.verbose:
                                    logger.info(final_message)
                                return ClearingResult(
                                    success=True,
                                    message=final_message,
                                    items_cleared=doc_count
                                )
                            else:
                                error_msg = f"LightRAG deletion status: {status} - {message}"
                                logger.error(error_msg)
                                return ClearingResult(
                                    success=False,
                                    message=error_msg,
                                    errors=[f"{status}: {message}"]
                                )
                        else:
                            error_text = await del_resp.text()
                            error_msg = f"Server error {del_resp.status}: {error_text}"
                            logger.error(error_msg)
                            return ClearingResult(
                                success=False,
                                message=error_msg,
                                errors=[error_text]
                            )
                            
        except Exception as e:
            error_msg = f"Error clearing LightRAG documents: {e}"
            logger.error(error_msg)
            return ClearingResult(
                success=False,
                message=error_msg,
                errors=[str(e)]
            )

    async def clear_knowledge_graph_files(self, dry_run: bool = False) -> ClearingResult:
        """Clear knowledge graph files from storage directories.
        
        Args:
            dry_run: If True, only simulate the clearing without actually deleting
            
        Returns:
            ClearingResult with operation details
        """
        if not self.memory_storage_dirs:
            return ClearingResult(
                success=False,
                message="Memory storage directories not configured",
                errors=["memory_storage_dirs not available"]
            )
        
        try:
            graph_files_found = []
            
            # Look for knowledge graph files in all storage directories
            for storage_dir in self.memory_storage_dirs:
                graph_file_path = storage_dir / "graph_chunk_entity_relation.graphml"
                if graph_file_path.exists():
                    graph_files_found.append(graph_file_path)
            
            if not graph_files_found:
                message = "No knowledge graph files found to delete"
                if self.verbose:
                    logger.info(message)
                return ClearingResult(
                    success=True,
                    message=message,
                    items_cleared=0
                )
            
            if dry_run:
                message = f"DRY RUN: Would delete {len(graph_files_found)} knowledge graph files"
                if self.verbose:
                    logger.info(message)
                    for file_path in graph_files_found:
                        logger.info(f"  Would delete: {file_path}")
                return ClearingResult(
                    success=True,
                    message=message,
                    items_cleared=len(graph_files_found)
                )
            
            # Delete the graph files
            deleted_count = 0
            errors = []
            
            for graph_file_path in graph_files_found:
                try:
                    graph_file_path.unlink()
                    deleted_count += 1
                    if self.verbose:
                        logger.info(f"Deleted knowledge graph file: {graph_file_path}")
                except Exception as e:
                    error_msg = f"Failed to delete knowledge graph file {graph_file_path}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            success = len(errors) == 0
            message = f"Deleted {deleted_count} knowledge graph files"
            
            if errors:
                message += f" (with {len(errors)} errors)"
            
            return ClearingResult(
                success=success,
                message=message,
                items_cleared=deleted_count,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Error clearing knowledge graph files: {e}"
            logger.error(error_msg)
            return ClearingResult(
                success=False,
                message=error_msg,
                errors=[str(e)]
            )

    async def clear_server_cache(self, dry_run: bool = False) -> ClearingResult:
        """Clear LightRAG server cache.
        
        Args:
            dry_run: If True, only simulate the clearing without actually clearing
            
        Returns:
            ClearingResult with operation details
        """
        if not self.lightrag_memory_url:
            return ClearingResult(
                success=False,
                message="LightRAG memory URL not configured",
                errors=["lightrag_memory_url not available"]
            )
        
        if dry_run:
            message = "DRY RUN: Would clear LightRAG server cache"
            if self.verbose:
                logger.info(message)
            return ClearingResult(
                success=True,
                message=message,
                items_cleared=1
            )
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"modes": None}  # Clear all cache modes
                async with session.post(
                    f"{self.lightrag_memory_url}/documents/clear_cache",
                    json=payload,
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        message = "LightRAG server cache cleared successfully"
                        if self.verbose:
                            logger.info(message)
                        return ClearingResult(
                            success=True,
                            message=message,
                            items_cleared=1
                        )
                    else:
                        error_text = await resp.text()
                        error_msg = f"Failed to clear LightRAG cache: {resp.status} - {error_text}"
                        logger.error(error_msg)
                        return ClearingResult(
                            success=False,
                            message=error_msg,
                            errors=[error_text]
                        )
                        
        except Exception as e:
            error_msg = f"Error clearing server cache: {e}"
            logger.error(error_msg)
            return ClearingResult(
                success=False,
                message=error_msg,
                errors=[str(e)]
            )

    async def clear_all_memories(self, options: ClearingOptions = None) -> Dict[str, Any]:
        """Clear all memories from all systems.
        
        Args:
            options: Clearing options to control what gets cleared
            
        Returns:
            Dictionary with detailed results from all clearing operations
        """
        if options is None:
            options = ClearingOptions()
        
        results = {
            "semantic_memory": {"attempted": False, "result": None},
            "lightrag_memory": {"attempted": False, "result": None},
            "memory_inputs": {"attempted": False, "result": None},
            "knowledge_graph": {"attempted": False, "result": None},
            "server_cache": {"attempted": False, "result": None},
            "overall_success": False,
            "summary": "",
        }
        
        successful_operations = []
        failed_operations = []
        
        # Clear semantic memories
        if not options.lightrag_only:
            results["semantic_memory"]["attempted"] = True
            semantic_result = await self.clear_semantic_memories(options.dry_run)
            results["semantic_memory"]["result"] = semantic_result
            
            if semantic_result.success:
                successful_operations.append(f"Semantic: {semantic_result.message}")
            else:
                failed_operations.append(f"Semantic: {semantic_result.message}")
        
        # Clear LightRAG documents
        if not options.semantic_only:
            results["lightrag_memory"]["attempted"] = True
            lightrag_result = await self.clear_lightrag_documents(options.dry_run)
            results["lightrag_memory"]["result"] = lightrag_result
            
            if lightrag_result.success:
                successful_operations.append(f"LightRAG: {lightrag_result.message}")
            else:
                failed_operations.append(f"LightRAG: {lightrag_result.message}")
        
        # Clear memory inputs directory (NEW FUNCTIONALITY)
        if not options.semantic_only and options.include_memory_inputs:
            results["memory_inputs"]["attempted"] = True
            inputs_result = await self.clear_memory_inputs_directory(options.dry_run)
            results["memory_inputs"]["result"] = inputs_result
            
            if inputs_result.success:
                successful_operations.append(f"Memory Inputs: {inputs_result.message}")
            else:
                failed_operations.append(f"Memory Inputs: {inputs_result.message}")
        
        # Clear knowledge graph files
        if not options.semantic_only and options.include_knowledge_graph:
            results["knowledge_graph"]["attempted"] = True
            graph_result = await self.clear_knowledge_graph_files(options.dry_run)
            results["knowledge_graph"]["result"] = graph_result
            
            if graph_result.success:
                successful_operations.append(f"Knowledge Graph: {graph_result.message}")
            else:
                failed_operations.append(f"Knowledge Graph: {graph_result.message}")
        
        # Clear server cache
        if not options.semantic_only and options.include_cache:
            results["server_cache"]["attempted"] = True
            cache_result = await self.clear_server_cache(options.dry_run)
            results["server_cache"]["result"] = cache_result
            
            if cache_result.success:
                successful_operations.append(f"Server Cache: {cache_result.message}")
            else:
                failed_operations.append(f"Server Cache: {cache_result.message}")
        
        # Determine overall success
        attempted_operations = sum(1 for r in results.values() if isinstance(r, dict) and r.get("attempted", False))
        successful_count = len(successful_operations)
        failed_count = len(failed_operations)
        
        results["overall_success"] = failed_count == 0 and successful_count > 0
        
        # Create summary
        if options.dry_run:
            results["summary"] = f"DRY RUN: {successful_count} operations would succeed, {failed_count} would fail"
        else:
            results["summary"] = f"{successful_count} operations succeeded, {failed_count} failed"
        
        if self.verbose:
            logger.info(f"Memory clearing completed: {results['summary']}")
            for success_msg in successful_operations:
                logger.info(f"  ✅ {success_msg}")
            for fail_msg in failed_operations:
                logger.error(f"  ❌ {fail_msg}")
        
        return results
