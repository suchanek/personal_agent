"""
Memory Utilities

Utility functions for managing memories in the Personal Agent system.
Uses StreamlitMemoryHelper for all operations (same as paga_streamlit_agno.py).
"""

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from personal_agent.streamlit.utils.agent_utils import get_agent_instance


def get_memory_helper():
    """Get a StreamlitMemoryHelper instance using the current agent."""
    agent = get_agent_instance()
    if not agent:
        return None

    from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper

    return StreamlitMemoryHelper(agent)


def get_all_memories(
    memory_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Get a list of all memories in the system using StreamlitMemoryHelper.

    Args:
        memory_type: Optional filter for memory type
        start_date: Optional filter for start date
        end_date: Optional filter for end date
        limit: Maximum number of memories to return

    Returns:
        List of dictionaries containing memory information
    """
    try:
        memory_helper = get_memory_helper()
        if not memory_helper:
            st.warning("Memory helper not available.")
            return []

        # Get all memories using the helper
        raw_memories = memory_helper.get_all_memories()

        if not raw_memories:
            return []

        # Convert raw memories to the expected format
        formatted_memories = []
        for memory in raw_memories:
            try:
                # Extract memory content and metadata
                memory_content = getattr(memory, "memory", str(memory))
                memory_id = getattr(
                    memory,
                    "memory_id",
                    getattr(memory, "id", f"mem_{len(formatted_memories) + 1}"),
                )
                created_at = getattr(
                    memory,
                    "last_updated",
                    getattr(memory, "created_at", datetime.now()),
                )

                # Get enhanced fields
                confidence = getattr(memory, "confidence", 1.0)
                is_proxy = getattr(memory, "is_proxy", False)
                proxy_agent = getattr(memory, "proxy_agent", None)

                # Format the created_at timestamp
                if isinstance(created_at, datetime):
                    created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    created_at_str = str(created_at)

                # Get topics if available
                topics = getattr(memory, "topics", [])
                memory_type_detected = topics[0] if topics else "conversation"

                formatted_memory = {
                    "id": str(memory_id),
                    "type": memory_type_detected,
                    "content": memory_content,
                    "created_at": created_at_str,
                    "metadata": (
                        {
                            "topics": topics,
                            "confidence": confidence,
                            "is_proxy": is_proxy,
                            "proxy_agent": proxy_agent,
                        }
                        if topics
                        else {
                            "confidence": confidence,
                            "is_proxy": is_proxy,
                            "proxy_agent": proxy_agent,
                        }
                    ),
                }

                formatted_memories.append(formatted_memory)

            except Exception as memory_error:
                st.warning(f"Error processing memory: {str(memory_error)}")
                continue

        # Apply filters
        filtered_memories = formatted_memories

        if memory_type and memory_type.lower() != "all":
            filtered_memories = [
                m for m in filtered_memories if m["type"].lower() == memory_type.lower()
            ]

        if start_date:
            start_date_str = start_date.strftime("%Y-%m-%d")
            filtered_memories = [
                m for m in filtered_memories if m["created_at"] >= start_date_str
            ]

        if end_date:
            end_date_str = end_date.strftime("%Y-%m-%d")
            filtered_memories = [
                m for m in filtered_memories if m["created_at"] <= end_date_str
            ]

        # Apply limit
        filtered_memories = filtered_memories[:limit]

        return filtered_memories

    except Exception as e:
        st.error(f"Error getting memories: {str(e)}")
        return []


def search_memories(
    query: str, search_type: str = "keyword", max_results: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for memories matching a query using StreamlitMemoryHelper.

    Args:
        query: Search query
        search_type: Type of search (keyword, semantic, hybrid)
        max_results: Maximum number of results to return

    Returns:
        List of dictionaries containing memory information
    """
    try:
        memory_helper = get_memory_helper()
        if not memory_helper:
            st.warning("Memory helper not available.")
            return []

        # Use the memory helper's search functionality
        search_results = memory_helper.search_memories(
            query=query,
            limit=max_results,
            similarity_threshold=0.3,  # Default threshold
        )

        if not search_results:
            return []

        # Convert search results to expected format
        formatted_results = []
        for memory, score in search_results:
            try:
                memory_content = getattr(memory, "memory", str(memory))
                memory_id = getattr(
                    memory,
                    "memory_id",
                    getattr(memory, "id", f"mem_{len(formatted_results) + 1}"),
                )
                created_at = getattr(
                    memory,
                    "last_updated",
                    getattr(memory, "created_at", datetime.now()),
                )

                # Get enhanced fields
                confidence = getattr(memory, "confidence", 1.0)
                is_proxy = getattr(memory, "is_proxy", False)
                proxy_agent = getattr(memory, "proxy_agent", None)

                if isinstance(created_at, datetime):
                    created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    created_at_str = str(created_at)

                topics = getattr(memory, "topics", [])
                memory_type_detected = topics[0] if topics else "conversation"

                formatted_result = {
                    "id": str(memory_id),
                    "type": memory_type_detected,
                    "content": memory_content,
                    "created_at": created_at_str,
                    "metadata": (
                        {
                            "topics": topics,
                            "similarity_score": score,
                            "confidence": confidence,
                            "is_proxy": is_proxy,
                            "proxy_agent": proxy_agent,
                        }
                        if topics
                        else {
                            "similarity_score": score,
                            "confidence": confidence,
                            "is_proxy": is_proxy,
                            "proxy_agent": proxy_agent,
                        }
                    ),
                }

                formatted_results.append(formatted_result)

            except Exception as memory_error:
                st.warning(f"Error processing search result: {str(memory_error)}")
                continue

        return formatted_results

    except Exception as e:
        st.error(f"Error searching memories: {str(e)}")
        return []


def delete_memory(memory_id: str) -> bool:
    """
    Delete a memory using StreamlitMemoryHelper.

    Args:
        memory_id: ID of the memory to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        memory_helper = get_memory_helper()
        if not memory_helper:
            st.error("Memory helper not available.")
            return False

        # Use the memory helper's delete functionality
        success, message = memory_helper.delete_memory(memory_id)

        if success:
            st.success(f"Memory {memory_id} deleted successfully!")
            return True
        else:
            st.error(f"Failed to delete memory: {message}")
            return False

    except Exception as e:
        st.error(f"Error deleting memory: {str(e)}")
        return False


def sync_memories() -> Dict[str, Any]:
    """
    Synchronize memories between SQLite and LightRAG graph systems using StreamlitMemoryHelper.

    Returns:
        Dictionary containing result information
    """
    try:
        memory_helper = get_memory_helper()
        if not memory_helper:
            return {"success": False, "error": "Memory helper not available"}

        # Get sync status using the helper
        sync_status = memory_helper.get_memory_sync_status()

        if "error" in sync_status:
            return {"success": False, "error": sync_status["error"]}

        # If out of sync, try to sync missing memories
        if sync_status.get("status") == "out_of_sync":
            local_memories = memory_helper.get_all_memories()
            synced_count = 0

            for memory in local_memories:
                try:
                    success, result = memory_helper.sync_memory_to_graph(
                        memory.memory, getattr(memory, "topics", None)
                    )
                    if success:
                        synced_count += 1
                except Exception as e:
                    st.warning(f"Error syncing memory: {e}")

            return {
                "success": True,
                "synced": synced_count,
                "errors": len(local_memories) - synced_count,
            }
        else:
            return {
                "success": True,
                "synced": 0,
                "errors": 0,
                "message": "Memories already synchronized",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def export_memories(format: str = "json") -> Optional[str]:
    """
    Export memories to a file.

    Args:
        format: Export format (json, csv)

    Returns:
        File content as a string, or None if export failed
    """
    try:
        # Get all memories
        memories = get_all_memories(limit=10000)

        if format == "json":
            # Export as JSON
            return json.dumps(memories, indent=2)
        elif format == "csv":
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            if memories:
                header = ["id", "type", "content", "created_at"]
                writer.writerow(header)

                # Write rows
                for memory in memories:
                    row = [
                        memory["id"],
                        memory["type"],
                        memory["content"],
                        memory["created_at"],
                    ]
                    writer.writerow(row)

            return output.getvalue()
        else:
            st.error(f"Unsupported export format: {format}")
            return None

    except Exception as e:
        st.error(f"Error exporting memories: {str(e)}")
        return None


def import_memories(content: str, format: str = "json") -> Dict[str, Any]:
    """
    Import memories from a file using StreamlitMemoryHelper.

    Args:
        content: File content as a string
        format: Import format (json, csv)

    Returns:
        Dictionary containing result information
    """
    try:
        memory_helper = get_memory_helper()
        if not memory_helper:
            return {"success": False, "error": "Memory helper not available"}

        imported_count = 0

        if format == "json":
            # Import from JSON
            memories = json.loads(content)
        elif format == "csv":
            # Import from CSV
            reader = csv.DictReader(io.StringIO(content))
            memories = list(reader)
        else:
            return {"success": False, "error": f"Unsupported import format: {format}"}

        # Add memories using the helper
        for memory_data in memories:
            try:
                content_text = memory_data.get("content", "")
                topics = memory_data.get("metadata", {}).get("topics", [])

                success, message, memory_id, _ = memory_helper.add_memory(
                    memory_text=content_text,
                    topics=topics,
                    input_text="Imported memory",
                )

                if success:
                    imported_count += 1

            except Exception as e:
                st.warning(f"Error importing memory: {e}")

        return {"success": True, "imported": imported_count}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_memory_stats() -> Dict[str, Any]:
    """
    Get statistics about the memory system using StreamlitMemoryHelper.

    Returns:
        Dictionary containing memory statistics
    """
    try:
        memory_helper = get_memory_helper()
        if not memory_helper:
            return {
                "total_memories": 0,
                "by_type": {},
                "storage_size": "0 MB",
                "last_sync": "Error",
            }

        # Get stats using the helper
        stats = memory_helper.get_memory_stats()

        if "error" in stats:
            return {
                "total_memories": 0,
                "by_type": {},
                "storage_size": "0 MB",
                "last_sync": "Error",
            }

        # Get all memories to calculate additional stats
        all_memories = get_all_memories(limit=10000)

        # Count by type
        type_counts = {}
        for memory in all_memories:
            memory_type = memory.get("type", "unknown")
            type_counts[memory_type] = type_counts.get(memory_type, 0) + 1

        # Estimate storage size
        total_content_length = sum(
            len(str(memory.get("content", ""))) for memory in all_memories
        )
        storage_size_mb = total_content_length / (1024 * 1024)
        storage_size = f"{storage_size_mb:.2f} MB"

        return {
            "total_memories": stats.get("total_memories", len(all_memories)),
            "by_type": type_counts,
            "storage_size": storage_size,
            "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "recent_memories_24h": stats.get("recent_memories_24h", 0),
            "average_memory_length": stats.get("average_memory_length", 0),
            "most_common_topic": stats.get("most_common_topic", ""),
            "topic_distribution": stats.get("topic_distribution", {}),
        }

    except Exception as e:
        st.error(f"Error getting memory statistics: {str(e)}")
        return {
            "total_memories": 0,
            "by_type": {},
            "storage_size": "0 MB",
            "last_sync": "Error",
        }
