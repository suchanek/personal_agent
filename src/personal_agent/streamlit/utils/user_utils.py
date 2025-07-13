"""
User Utilities

Utility functions for managing users in the Personal Agent system.
"""

import os
import json
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import project modules
from personal_agent.core.docker.user_sync import DockerUserSync


def get_all_users() -> List[Dict[str, Any]]:
    """
    Get a list of all users in the system.
    
    Returns:
        List of dictionaries containing user information
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, you would get this from a database or config file
        
        # Get current user
        from personal_agent.config.settings import USER_ID
        current_user = USER_ID
        
        # Create a list of sample users
        users = [
            {
                "user_id": current_user,
                "user_name": "Current User",
                "user_type": "Admin",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_current": True
            },
            {
                "user_id": "user1",
                "user_name": "User One",
                "user_type": "Standard",
                "created_at": "2023-01-01 12:00:00",
                "last_login": "2023-06-15 09:30:00",
                "is_current": False
            },
            {
                "user_id": "user2",
                "user_name": "User Two",
                "user_type": "Guest",
                "created_at": "2023-03-15 14:30:00",
                "last_login": "2023-07-01 16:45:00",
                "is_current": False
            }
        ]
        
        return users
    
    except Exception as e:
        st.error(f"Error getting users: {str(e)}")
        return []


def get_user_details(user_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific user.
    
    Args:
        user_id: ID of the user to get details for
        
    Returns:
        Dictionary containing user details
    """
    try:
        # Get all users
        users = get_all_users()
        
        # Find the specified user
        user = next((u for u in users if u["user_id"] == user_id), None)
        
        if user:
            # Add additional details
            user_details = user.copy()
            
            # Add memory statistics
            user_details["memory_count"] = 42  # Placeholder
            user_details["memory_size"] = "24.5 MB"  # Placeholder
            
            # Add Docker container information
            user_details["containers"] = [
                {
                    "name": "lightrag-server",
                    "status": "running"
                },
                {
                    "name": "ollama",
                    "status": "running"
                }
            ]
            
            return user_details
        
        return {}
    
    except Exception as e:
        st.error(f"Error getting user details: {str(e)}")
        return {}


def create_new_user(user_id: str, user_name: str, user_type: str, create_docker: bool = True) -> Dict[str, Any]:
    """
    Create a new user in the system.
    
    Args:
        user_id: Unique identifier for the user
        user_name: Display name for the user
        user_type: Type of user (Standard, Admin, Guest)
        create_docker: Whether to create Docker containers for this user
        
    Returns:
        Dictionary containing result information
    """
    try:
        # Validate input
        if not user_id:
            return {"success": False, "error": "User ID is required"}
        
        if not user_name:
            return {"success": False, "error": "User name is required"}
        
        # Check if user already exists
        users = get_all_users()
        if any(u["user_id"] == user_id for u in users):
            return {"success": False, "error": f"User '{user_id}' already exists"}
        
        # Create user directory
        user_dir = Path.home() / ".personal_agent" / "users" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Create user configuration file
        user_config = {
            "user_id": user_id,
            "user_name": user_name,
            "user_type": user_type,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(user_dir / "config.json", "w") as f:
            json.dump(user_config, f, indent=2)
        
        # Create Docker containers if requested
        if create_docker:
            docker_user_sync = DockerUserSync()
            docker_user_sync.sync_user_ids(force_restart=True)
        
        return {"success": True}
    
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return {"success": False, "error": str(e)}


def switch_user(user_id: str, restart_containers: bool = True) -> Dict[str, Any]:
    """
    Switch to a different user.
    
    Args:
        user_id: ID of the user to switch to
        restart_containers: Whether to restart Docker containers after switching
        
    Returns:
        Dictionary containing result information
    """
    try:
        # Validate input
        if not user_id:
            return {"success": False, "error": "User ID is required"}
        
        # Check if user exists
        users = get_all_users()
        if not any(u["user_id"] == user_id for u in users):
            return {"success": False, "error": f"User '{user_id}' does not exist"}
        
        # Get current user
        from personal_agent.config.settings import USER_ID
        current_user = USER_ID
        
        # Don't switch if already the current user
        if user_id == current_user:
            return {"success": False, "error": f"Already logged in as '{user_id}'"}
        
        # Update environment variable
        os.environ["USER_ID"] = user_id
        
        # Update Docker containers if requested
        if restart_containers:
            docker_user_sync = DockerUserSync()
            docker_user_sync.sync_user_ids(force_restart=True)
        
        return {"success": True}
    
    except Exception as e:
        st.error(f"Error switching user: {str(e)}")
        return {"success": False, "error": str(e)}


def delete_user(user_id: str, delete_data: bool = False) -> Dict[str, Any]:
    """
    Delete a user from the system.
    
    Args:
        user_id: ID of the user to delete
        delete_data: Whether to delete user data
        
    Returns:
        Dictionary containing result information
    """
    try:
        # Validate input
        if not user_id:
            return {"success": False, "error": "User ID is required"}
        
        # Check if user exists
        users = get_all_users()
        if not any(u["user_id"] == user_id for u in users):
            return {"success": False, "error": f"User '{user_id}' does not exist"}
        
        # Get current user
        from personal_agent.config.settings import USER_ID
        current_user = USER_ID
        
        # Don't delete the current user
        if user_id == current_user:
            return {"success": False, "error": "Cannot delete the current user"}
        
        # Delete user directory if requested
        if delete_data:
            user_dir = Path.home() / ".personal_agent" / "users" / user_id
            if user_dir.exists():
                import shutil
                shutil.rmtree(user_dir)
        
        return {"success": True}
    
    except Exception as e:
        st.error(f"Error deleting user: {str(e)}")
        return {"success": False, "error": str(e)}


def get_user_activity(user_id: str) -> List[Dict[str, Any]]:
    """
    Get activity history for a specific user.
    
    Args:
        user_id: ID of the user to get activity for
        
    Returns:
        List of dictionaries containing activity information
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, you would get this from a database or log file
        
        # Create a list of sample activities
        activities = [
            {
                "timestamp": "2023-07-01 09:15:00",
                "action": "Login",
                "details": "User logged in"
            },
            {
                "timestamp": "2023-07-01 09:20:00",
                "action": "Memory Creation",
                "details": "Created 3 new memories"
            },
            {
                "timestamp": "2023-07-01 10:05:00",
                "action": "Docker Container",
                "details": "Started lightrag-server container"
            },
            {
                "timestamp": "2023-07-01 11:30:00",
                "action": "Memory Search",
                "details": "Performed semantic search"
            },
            {
                "timestamp": "2023-07-01 12:45:00",
                "action": "Logout",
                "details": "User logged out"
            }
        ]
        
        return activities
    
    except Exception as e:
        st.error(f"Error getting user activity: {str(e)}")
        return []