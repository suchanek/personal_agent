#!/usr/bin/env python3
"""
Memory Cleaner Module

A comprehensive module to clear both semantic memories (local SQLite) and 
LightRAG graph memories (knowledge graph) to prevent drift between the two systems.

This module provides a unified interface to clear:
1. Semantic Memory System (SQLite + LanceDB) - local user memories
2. LightRAG Graph Memory System (Knowledge Graph) - relationship-based memories
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

import aiohttp
from ..config.settings import (
    AGNO_STORAGE_DIR,
    LIGHTRAG_MEMORY_URL,
    USER_ID,
)
from ..core.semantic_memory_manager import create_semantic_memory_manager
from agno.memory.v2.db.sqlite import SqliteMemoryDb


class MemoryClearingManager:
    """Manages the clearing of both semantic and LightRAG graph memories."""

    def __init__(
        self,
        user_id: str = USER_ID,
        storage_dir: str = AGNO_STORAGE_DIR,
        lightrag_memory_url: str = LIGHTRAG_MEMORY_URL,
        verbose: bool = False,
    ):
        self.user_id = user_id
        self.storage_dir = Path(storage_dir)
        self.lightrag_memory_url = lightrag_memory_url
        self.verbose = verbose

        # Initialize semantic memory components
        self.semantic_db_path = self.storage_dir / "semantic_memory.db"
        self.memory_db = None
        self.memory_manager = None

        print("🧠 Memory Clearing Manager initialized")
        print(f"   User ID: {self.user_id}")
        print(f"   Storage Directory: {self.storage_dir}")
        print(f"   LightRAG Memory URL: {self.lightrag_memory_url}")
        print(f"   Semantic DB Path: {self.semantic_db_path}")

    def _initialize_semantic_memory(self) -> bool:
        """Initialize semantic memory components."""
        try:
            # Create memory database connection
            self.memory_db = SqliteMemoryDb(
                table_name="semantic_memory",
                db_file=str(self.semantic_db_path),
            )

            # Create semantic memory manager
            self.memory_manager = create_semantic_memory_manager(
                similarity_threshold=0.8,
                debug_mode=self.verbose,
            )

            if self.verbose:
                print(f"✅ Semantic memory components initialized")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize semantic memory: {e}")
            return False

    async def _check_lightrag_server_status(self) -> bool:
        """Check if LightRAG memory server is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lightrag_memory_url}/health", timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            if self.verbose:
                print(f"❌ Cannot connect to LightRAG memory server: {e}")
            return False

    async def _get_lightrag_documents(self) -> list:
        """Get all documents from LightRAG memory server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lightrag_memory_url}/documents", timeout=30) as resp:
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
                        if self.verbose:
                            print(f"⚠️ Unexpected response format: {type(data)}")
                        return []
        except Exception as e:
            print(f"❌ Error fetching LightRAG documents: {e}")
            return []

    async def _clear_lightrag_documents(self, doc_ids: list, dry_run: bool = False) -> Dict[str, Any]:
        """Clear documents from LightRAG memory server."""
        if dry_run:
            return {
                "success": True,
                "message": f"DRY RUN: Would delete {len(doc_ids)} documents from LightRAG",
                "deleted_count": len(doc_ids),
            }

        if not doc_ids:
            return {
                "success": True,
                "message": "No documents to delete from LightRAG",
                "deleted_count": 0,
            }

        try:
            async with aiohttp.ClientSession() as session:
                # Delete documents using batch deletion
                payload = {
                    "doc_ids": doc_ids,
                    "delete_file": True  # DELETE source files to prevent rescan
                }
                async with session.delete(
                    f"{self.lightrag_memory_url}/documents/delete_document",
                    json=payload,
                    timeout=60
                ) as resp:
                    if resp.status == 200:
                        result_data = await resp.json()
                        status = result_data.get("status", "unknown")
                        message = result_data.get("message", "No message")

                        if status == "deletion_started":
                            # Clear cache after deletion
                            await self._clear_lightrag_cache()
                            return {
                                "success": True,
                                "message": f"Successfully deleted {len(doc_ids)} documents from LightRAG",
                                "deleted_count": len(doc_ids),
                            }
                        else:
                            return {
                                "success": False,
                                "message": f"LightRAG deletion status: {status} - {message}",
                                "deleted_count": 0,
                            }
                    else:
                        error_text = await resp.text()
                        return {
                            "success": False,
                            "message": f"Server error {resp.status}: {error_text}",
                            "deleted_count": 0,
                        }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error deleting LightRAG documents: {e}",
                "deleted_count": 0,
            }

    async def _clear_lightrag_cache(self) -> bool:
        """Clear LightRAG server cache."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"modes": None}  # Clear all cache modes
                async with session.post(
                    f"{self.lightrag_memory_url}/documents/clear_cache",
                    json=payload,
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        if self.verbose:
                            print("✅ LightRAG cache cleared successfully")
                        return True
                    else:
                        error_text = await resp.text()
                        print(f"❌ Failed to clear LightRAG cache: {resp.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Failed to clear LightRAG cache: {e}")
            return False

    def _get_semantic_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about semantic memories."""
        if not self.memory_manager or not self.memory_db:
            return {"error": "Semantic memory not initialized"}

        try:
            stats = self.memory_manager.get_memory_stats(
                db=self.memory_db,
                user_id=self.user_id
            )
            return stats
        except Exception as e:
            return {"error": str(e)}

    def _clear_semantic_memories(self, dry_run: bool = False) -> Tuple[bool, str]:
        """Clear all semantic memories for the user."""
        if not self.memory_manager or not self.memory_db:
            return False, "Semantic memory not initialized"

        if dry_run:
            stats = self._get_semantic_memory_stats()
            total_memories = stats.get("total_memories", 0)
            return True, f"DRY RUN: Would clear {total_memories} semantic memories"

        try:
            success, message = self.memory_manager.clear_memories(
                db=self.memory_db,
                user_id=self.user_id
            )
            return success, message
        except Exception as e:
            return False, f"Error clearing semantic memories: {e}"

    async def get_memory_status(self) -> Dict[str, Any]:
        """Get comprehensive status of both memory systems."""
        status = {
            "semantic_memory": {"available": False, "stats": {}},
            "lightrag_memory": {"available": False, "documents": []},
        }

        # Check semantic memory
        if self._initialize_semantic_memory():
            status["semantic_memory"]["available"] = True
            status["semantic_memory"]["stats"] = self._get_semantic_memory_stats()

        # Check LightRAG memory
        lightrag_available = await self._check_lightrag_server_status()
        status["lightrag_memory"]["available"] = lightrag_available

        if lightrag_available:
            documents = await self._get_lightrag_documents()
            status["lightrag_memory"]["documents"] = documents
            status["lightrag_memory"]["document_count"] = len(documents)

        return status

    async def clear_all_memories(
        self,
        dry_run: bool = False,
        semantic_only: bool = False,
        lightrag_only: bool = False,
    ) -> Dict[str, Any]:
        """Clear memories from both systems."""
        results = {
            "semantic_memory": {"attempted": False, "success": False, "message": ""},
            "lightrag_memory": {"attempted": False, "success": False, "message": ""},
            "overall_success": False,
        }

        # Clear semantic memories
        if not lightrag_only:
            results["semantic_memory"]["attempted"] = True
            if self._initialize_semantic_memory():
                success, message = self._clear_semantic_memories(dry_run)
                results["semantic_memory"]["success"] = success
                results["semantic_memory"]["message"] = message
            else:
                results["semantic_memory"]["message"] = "Failed to initialize semantic memory"

        # Clear LightRAG memories
        if not semantic_only:
            results["lightrag_memory"]["attempted"] = True
            lightrag_available = await self._check_lightrag_server_status()

            if lightrag_available:
                documents = await self._get_lightrag_documents()
                if documents:
                    doc_ids = [doc["id"] for doc in documents]
                    clear_result = await self._clear_lightrag_documents(doc_ids, dry_run)
                    results["lightrag_memory"]["success"] = clear_result["success"]
                    results["lightrag_memory"]["message"] = clear_result["message"]
                else:
                    results["lightrag_memory"]["success"] = True
                    results["lightrag_memory"]["message"] = "No LightRAG documents to clear"
            else:
                results["lightrag_memory"]["message"] = "LightRAG memory server not available"

        # Determine overall success
        attempted_systems = []
        successful_systems = []

        if results["semantic_memory"]["attempted"]:
            attempted_systems.append("semantic")
            if results["semantic_memory"]["success"]:
                successful_systems.append("semantic")

        if results["lightrag_memory"]["attempted"]:
            attempted_systems.append("lightrag")
            if results["lightrag_memory"]["success"]:
                successful_systems.append("lightrag")

        results["overall_success"] = len(successful_systems) == len(attempted_systems)

        return results

    async def verify_clearing(self) -> Dict[str, Any]:
        """Verify that memories have been successfully cleared."""
        verification = {
            "semantic_memory": {"cleared": False, "remaining_count": 0},
            "lightrag_memory": {"cleared": False, "remaining_count": 0},
            "fully_cleared": False,
        }

        # Verify semantic memory clearing
        if self._initialize_semantic_memory():
            stats = self._get_semantic_memory_stats()
            remaining_semantic = stats.get("total_memories", 0)
            verification["semantic_memory"]["remaining_count"] = remaining_semantic
            verification["semantic_memory"]["cleared"] = remaining_semantic == 0

        # Verify LightRAG memory clearing
        lightrag_available = await self._check_lightrag_server_status()
        if lightrag_available:
            documents = await self._get_lightrag_documents()
            remaining_lightrag = len(documents)
            verification["lightrag_memory"]["remaining_count"] = remaining_lightrag
            verification["lightrag_memory"]["cleared"] = remaining_lightrag == 0

        # Overall verification
        verification["fully_cleared"] = (
            verification["semantic_memory"]["cleared"] and
            verification["lightrag_memory"]["cleared"]
        )

        return verification


def print_status_report(status: Dict[str, Any]) -> None:
    """Print a comprehensive status report."""
    print("\n" + "=" * 60)
    print("🧠 MEMORY SYSTEMS STATUS REPORT")
    print("=" * 60)

    # Semantic Memory Status
    semantic = status["semantic_memory"]
    print(f"\n📊 Semantic Memory System:")
    print(f"   Available: {'✅' if semantic['available'] else '❌'}")

    if semantic["available"] and "stats" in semantic:
        stats = semantic["stats"]
        if "error" not in stats:
            print(f"   Total Memories: {stats.get('total_memories', 0)}")
            print(f"   Recent Memories (24h): {stats.get('recent_memories_24h', 0)}")
            if stats.get("most_common_topic"):
                print(f"   Most Common Topic: {stats['most_common_topic']}")
        else:
            print(f"   Error: {stats['error']}")

    # LightRAG Memory Status
    lightrag = status["lightrag_memory"]
    print(f"\n🌐 LightRAG Graph Memory System:")
    print(f"   Available: {'✅' if lightrag['available'] else '❌'}")

    if lightrag["available"]:
        doc_count = lightrag.get("document_count", 0)
        print(f"   Total Documents: {doc_count}")

        if doc_count > 0:
            documents = lightrag.get("documents", [])
            # Count by status
            status_counts = {}
            for doc in documents:
                status_name = doc.get("status", "unknown")
                status_counts[status_name] = status_counts.get(status_name, 0) + 1

            print("   Document Status Breakdown:")
            for status_name, count in status_counts.items():
                print(f"     - {status_name}: {count}")


def print_clearing_results(results: Dict[str, Any]) -> None:
    """Print the results of the clearing operation."""
    print("\n" + "=" * 60)
    print("🧹 MEMORY CLEARING RESULTS")
    print("=" * 60)

    # Semantic Memory Results
    semantic = results["semantic_memory"]
    if semantic["attempted"]:
        print(f"\n📊 Semantic Memory System:")
        print(f"   Status: {'✅ Success' if semantic['success'] else '❌ Failed'}")
        print(f"   Message: {semantic['message']}")

    # LightRAG Memory Results
    lightrag = results["lightrag_memory"]
    if lightrag["attempted"]:
        print("\n🌐 LightRAG Graph Memory System:")
        print(f"   Status: {'✅ Success' if lightrag['success'] else '❌ Failed'}")
        print(f"   Message: {lightrag['message']}")

    # Overall Result
    print(f"\n🎯 Overall Result: {'✅ SUCCESS' if results['overall_success'] else '❌ PARTIAL/FAILED'}")


def print_verification_results(verification: Dict[str, Any]) -> None:
    """Print the results of the verification."""
    print("\n" + "=" * 60)
    print("🔍 MEMORY CLEARING VERIFICATION")
    print("=" * 60)

    # Semantic Memory Verification
    semantic = verification["semantic_memory"]
    print("\n📊 Semantic Memory System:")
    print(f"   Cleared: {'✅' if semantic['cleared'] else '❌'}")
    print(f"   Remaining Memories: {semantic['remaining_count']}")

    # LightRAG Memory Verification
    lightrag = verification["lightrag_memory"]
    print(f"\n🌐 LightRAG Graph Memory System:")
    print(f"   Cleared: {'✅' if lightrag['cleared'] else '❌'}")
    print(f"   Remaining Documents: {lightrag['remaining_count']}")

    # Overall Verification
    print(f"\n🎯 Fully Cleared: {'✅ YES' if verification['fully_cleared'] else '❌ NO'}")


async def main():
    """Main function to handle command-line interface and execute clearing operations."""
    parser = argparse.ArgumentParser(description="Clear All Memories - Semantic and LightRAG")

    # Action options
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be cleared without actually clearing"
    )
    parser.add_argument(
        "--no-confirm", action="store_true", help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--semantic-only", action="store_true", help="Clear only the semantic memory system"
    )
    parser.add_argument(
        "--lightrag-only", action="store_true", help="Clear only the LightRAG graph memory system"
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify that memories have been cleared"
    )

    # Configuration options
    parser.add_argument(
        "--user-id", help="Specify user ID (default: from config)"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Validate mutually exclusive options
    if args.semantic_only and args.lightrag_only:
        print("❌ Error: Cannot specify both --semantic-only and --lightrag-only")
        return 1

    # Determine user ID
    user_id = args.user_id if args.user_id else USER_ID

    # Create memory clearing manager
    manager = MemoryClearingManager(
        user_id=user_id,
        verbose=args.verbose
    )

    try:
        # Handle verification mode
        if args.verify:
            print("🔍 Verifying memory clearing status...")
            verification = await manager.verify_clearing()
            print_verification_results(verification)
            return 0

        # Get current status
        print("📊 Checking current memory status...")
        status = await manager.get_memory_status()
        print_status_report(status)

        # Check if there's anything to clear
        semantic_count = 0
        lightrag_count = 0

        if status["semantic_memory"]["available"]:
            semantic_stats = status["semantic_memory"]["stats"]
            if "error" not in semantic_stats:
                semantic_count = semantic_stats.get("total_memories", 0)

        if status["lightrag_memory"]["available"]:
            lightrag_count = status["lightrag_memory"]["document_count"]

        # Determine what will be cleared
        systems_to_clear = []
        if not args.lightrag_only and semantic_count > 0:
            systems_to_clear.append(f"Semantic: {semantic_count} memories")
        if not args.semantic_only and lightrag_count > 0:
            systems_to_clear.append(f"LightRAG: {lightrag_count} documents")

        if not systems_to_clear:
            print("\n✅ No memories found to clear. Both systems are already empty.")
            return 0

        # Show what will be cleared
        print(f"\n🎯 Will clear: {', '.join(systems_to_clear)}")

        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No actual clearing will be performed")

        # Confirmation prompt
        if not args.no_confirm and not args.dry_run:
            response = input(f"\n⚠️  Are you sure you want to clear these memories? This action cannot be undone! (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("❌ Operation cancelled.")
                return 0

        # Perform clearing
        print(f"\n🧹 {'Simulating' if args.dry_run else 'Performing'} memory clearing...")
        results = await manager.clear_all_memories(
            dry_run=args.dry_run,
            semantic_only=args.semantic_only,
            lightrag_only=args.lightrag_only,
        )

        # Print results
        print_clearing_results(results)

        # Perform verification if clearing was successful and not a dry run
        if results["overall_success"] and not args.dry_run:
            print("\n🔍 Verifying clearing was successful...")
            verification = await manager.verify_clearing()
            print_verification_results(verification)

            if not verification["fully_cleared"]:
                print("\n⚠️  Warning: Verification indicates some memories may still remain.")
                return 1

        return 0 if results["overall_success"] else 1

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # This script requires asyncio to run
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
