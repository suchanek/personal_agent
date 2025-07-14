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
from personal_agent.core.user_manager import UserManager
from personal_agent.core.docker.user_sync import DockerUserSync


# Create a cached user manager instance
@st.cache_resource
def get_user_manager() -> UserManager:
    """Get a cached UserManager instance for Streamlit."""
    return UserManager()


def get_all_users() -> List[Dict[str, Any]]:
    """
    Get a list of all users in the personal agent system.
    
    Returns:
        List of dictionaries containing user information
    """
    try:
        user_manager = get_user_manager()
        # Ensure current user is registered
        user_manager.ensure_current_user_registered()
        return user_manager.get_all_users()
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
        user_manager = get_user_manager()
        return user_manager.get_user_details(user_id)
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
        user_manager = get_user_manager()
        return user_manager.create_user(user_id, user_name, user_type)
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
        user_manager = get_user_manager()
        return user_manager.switch_user(user_id, restart_lightrag=restart_containers, update_global_config=True)
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
        user_manager = get_user_manager()
        return user_manager.delete_user(user_id)
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
