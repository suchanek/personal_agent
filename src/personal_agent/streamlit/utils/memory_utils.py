"""
Memory Utilities

Utility functions for managing memories in the Personal Agent system.
"""

import os
import json
import csv
import io
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import project modules
from personal_agent.core.agno_agent import AgnoPersonalAgent


def get_all_memories(
    memory_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get a list of all memories in the system.
    
    Args:
        memory_type: Optional filter for memory type
        start_date: Optional filter for start date
        end_date: Optional filter for end date
        limit: Maximum number of memories to return
        
    Returns:
        List of dictionaries containing memory information
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, you would get this from the agent's memory system
        
        # Create a list of sample memories
        memories = [
            {
                "id": "mem_001",
                "type": "conversation",
                "content": "User asked about the weather in San Francisco",
                "created_at": "2023-07-01 09:15:00",
                "metadata": {
                    "source": "chat",
                    "importance": "medium"
                }
            },
            {
                "id": "mem_002",
                "type": "document",
                "content": "Annual report for 2023 fiscal year",
                "created_at": "2023-07-01 10:30:00",
                "metadata": {
                    "source": "file_upload",
                    "importance": "high",
                    "filename": "annual_report_2023.pdf"
                }
            },
            {
                "id": "mem_003",
                "type": "tool",
                "content": "Calendar event created for team meeting",
                "created_at": "2023-07-01 11:45:00",
                "metadata": {
                    "source": "calendar_tool",
                    "importance": "medium",
                    "event_id": "evt_123456"
                }
            },
            {
                "id": "mem_004",
                "type": "system",
                "content": "System updated to version 2.0.0",
                "created_at": "2023-07-01 12:00:00",
                "metadata": {
                    "source": "system",
                    "importance": "high",
                    "version": "2.0.0"
                }
            }
        ]
        
        # Apply filters
        filtered_memories = memories
        
        if memory_type:
            filtered_memories = [m for m in filtered_memories if m["type"] == memory_type]
        
        if start_date:
            start_date_str = start_date.strftime("%Y-%m-%d")
            filtered_memories = [m for m in filtered_memories if m["created_at"] >= start_date_str]
        
        if end_date:
            end_date_str = end_date.strftime("%Y-%m-%d")
            filtered_memories = [m for m in filtered_memories if m["created_at"] <= end_date_str]
        
        # Apply limit
        filtered_memories = filtered_memories[:limit]
        
        return filtered_memories
    
    except Exception as e:
        st.error(f"Error getting memories: {str(e)}")
        return []


def search_memories(
    query: str,
    search_type: str = "keyword",
    max_results: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for memories matching a query.
    
    Args:
        query: Search query
        search_type: Type of search (keyword, semantic, hybrid)
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries containing memory information
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, you would use the agent's memory search capabilities
        
        # Get all memories
        all_memories = get_all_memories(limit=1000)
        
        # Perform search based on search type
        if search_type == "keyword":
            # Simple keyword search
            results = [m for m in all_memories if query.lower() in m["content"].lower()]
        elif search_type == "semantic":
            # Placeholder for semantic search
            # In a real implementation, you would use a vector database or embedding search
            results = all_memories[:max_results]  # Just return some results for now
        elif search_type == "hybrid":
            # Placeholder for hybrid search
            # In a real implementation, you would combine keyword and semantic search
            results = all_memories[:max_results]  # Just return some results for now
        else:
            # Default to keyword search
            results = [m for m in all_memories if query.lower() in m["content"].lower()]
        
        # Apply max_results limit
        results = results[:max_results]
        
        return results
    
    except Exception as e:
        st.error(f"Error searching memories: {str(e)}")
        return []


def delete_memory(memory_id: str) -> bool:
    """
    Delete a memory from the system.
    
    Args:
        memory_id: ID of the memory to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, you would delete the memory from the agent's memory system
        
        # Simulate successful deletion
        st.success(f"Memory {memory_id} deleted successfully!")
        return True
    
    except Exception as e:
        st.error(f"Error deleting memory: {str(e)}")
        return False


def sync_memories() -> Dict[str, Any]:
    """
    Synchronize memories between SQLite and LightRAG graph systems.
    
    Returns:
        Dictionary containing result information
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, you would use the agent's memory synchronization capabilities
        
        # Simulate successful synchronization
        return {
            "success": True,
            "synced": 42,
            "errors": 0
        }
    
    except Exception as e:
        st.error(f"Error synchronizing memories: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


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
        memories = get_all_memories(limit=1000)
        
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
                        memory["created_at"]
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
    Import memories from a file.
    
    Args:
        content: File content as a string
        format: Import format (json, csv)
        
    Returns:
        Dictionary containing result information
    """
    try:
        imported_count = 0
        
        if format == "json":
            # Import from JSON
            memories = json.loads(content)
            imported_count = len(memories)
        elif format == "csv":
            # Import from CSV
            reader = csv.DictReader(io.StringIO(content))
            memories = list(reader)
            imported_count = len(memories)
        else:
            return {
                "success": False,
                "error": f"Unsupported import format: {format}"
            }
        
        # In a real implementation, you would add these memories to the agent's memory system
        
        return {
            "success": True,
            "imported": imported_count
        }
    
    except Exception as e:
        st.error(f"Error importing memories: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_memory_stats() -> Dict[str, Any]:
    """
    Get statistics about the memory system.
    
    Returns:
        Dictionary containing memory statistics
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, you would get this from the agent's memory system
        
        return {
            "total_memories": 125,
            "by_type": {
                "conversation": 42,
                "document": 35,
                "tool": 28,
                "system": 20
            },
            "storage_size": "24.5 MB",
            "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        st.error(f"Error getting memory statistics: {str(e)}")
        return {}