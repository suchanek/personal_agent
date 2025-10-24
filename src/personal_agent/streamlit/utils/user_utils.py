"""
User Utilities

Utility functions for managing users in the Personal Agent system.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from personal_agent.core.docker.user_sync import DockerUserSync

# Import project modules
from personal_agent.core.user_manager import UserManager


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


def create_new_user(
    user_id: str,
    user_name: str,
    user_type: str,
    create_docker: bool = True,
    email: str = None,
    phone: str = None,
    address: str = None,
    birth_date: str = None,
    delta_year: int = None,
    cognitive_state: int = 50,
    gender: str = "N/A",
    npc: bool = False,
) -> Dict[str, Any]:
    """
    Create a new user in the system with extended profile information.

    Args:
        user_id: Unique identifier for the user
        user_name: Display name for the user
        user_type: Type of user (Standard, Admin, Guest)
        create_docker: Whether to create Docker containers for this user
        email: User's email address
        phone: User's phone number
        address: User's address
        birth_date: User's birth date (YYYY-MM-DD format)
        delta_year: Years from birth when writing memories (e.g., 6 for writing as 6-year-old)
        cognitive_state: User's cognitive state (0-100 scale)
        gender: User's gender (Male, Female, N/A)
        npc: Whether user is an NPC (Non-Player Character)

    Returns:
        Dictionary containing result information
    """
    try:
        user_manager = get_user_manager()
        return user_manager.create_user(
            user_id,
            user_name,
            user_type,
            email,
            phone,
            address,
            birth_date,
            delta_year,
            cognitive_state,
            gender,
            npc,
        )
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
        return user_manager.switch_user(
            user_id, restart_lightrag=restart_containers, update_global_config=True
        )
    except Exception as e:
        st.error(f"Error switching user: {str(e)}")
        return {"success": False, "error": str(e)}


def delete_user(
    user_id: str,
    delete_data: bool = True,
    backup_data: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Delete a user from the system with enhanced options.

    Args:
        user_id: ID of the user to delete
        delete_data: Whether to delete persistent data directory (default: True)
        backup_data: Whether to backup data before deletion (default: False)
        dry_run: Preview mode - show what would be deleted without deleting (default: False)

    Returns:
        Dictionary containing detailed result information
    """
    try:
        user_manager = get_user_manager()
        return user_manager.delete_user(
            user_id, delete_data=delete_data, backup_data=backup_data, dry_run=dry_run
        )
    except Exception as e:
        st.error(f"Error deleting user: {str(e)}")
        return {"success": False, "error": str(e)}


def update_user_profile(user_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update user profile with validation.

    Args:
        user_id: ID of the user to update
        **kwargs: Profile fields to update

    Returns:
        Dictionary containing result information
    """
    try:
        user_manager = get_user_manager()
        return user_manager.update_user_profile(user_id, **kwargs)
    except Exception as e:
        st.error(f"Error updating user profile: {str(e)}")
        return {"success": False, "error": str(e)}


def update_cognitive_state(user_id: str, cognitive_state: int) -> Dict[str, Any]:
    """
    Update a user's cognitive state.

    Args:
        user_id: ID of the user to update
        cognitive_state: New cognitive state (0-100)

    Returns:
        Dictionary containing result information
    """
    try:
        user_manager = get_user_manager()
        return user_manager.update_cognitive_state(user_id, cognitive_state)
    except Exception as e:
        st.error(f"Error updating cognitive state: {str(e)}")
        return {"success": False, "error": str(e)}


def update_contact_info(
    user_id: str,
    email: str = None,
    phone: str = None,
    address: str = None,
    birth_date: str = None,
    delta_year: int = None,
    gender: str = None,
    npc: bool = None,
) -> Dict[str, Any]:
    """
    Update a user's contact information.

    Args:
        user_id: ID of the user to update
        email: New email address
        phone: New phone number
        address: New address
        birth_date: New birth date (YYYY-MM-DD format)
        delta_year: Years from birth when writing memories (e.g., 6 for writing as 6-year-old)
        gender: User's gender (Male, Female, N/A)
        npc: Whether user is an NPC (Non-Player Character)

    Returns:
        Dictionary containing result information
    """
    try:
        user_manager = get_user_manager()
        # Build update fields dictionary
        update_fields = {}
        if email is not None:
            update_fields["email"] = email
        if phone is not None:
            update_fields["phone"] = phone
        if address is not None:
            update_fields["address"] = address
        if birth_date is not None:
            update_fields["birth_date"] = birth_date
        if delta_year is not None:
            update_fields["delta_year"] = delta_year
        if gender is not None:
            update_fields["gender"] = gender
        if npc is not None:
            update_fields["npc"] = npc

        if not update_fields:
            return {
                "success": False,
                "error": "No contact information provided to update",
            }

        return user_manager.update_user_profile(user_id, **update_fields)
    except Exception as e:
        st.error(f"Error updating contact info: {str(e)}")
        return {"success": False, "error": str(e)}


def get_user_profile_summary(user_id: str) -> Dict[str, Any]:
    """
    Get a summary of user's profile completeness.

    Args:
        user_id: ID of the user to get summary for

    Returns:
        Dictionary with profile completion information
    """
    try:
        user_manager = get_user_manager()
        return user_manager.get_user_profile_summary(user_id)
    except Exception as e:
        st.error(f"Error getting profile summary: {str(e)}")
        return {"success": False, "error": str(e)}


def get_all_users_with_profiles() -> List[Dict[str, Any]]:
    """
    Get all users with their profile completion information.

    Returns:
        List of user dictionaries with profile summaries
    """
    try:
        user_manager = get_user_manager()
        user_manager.ensure_current_user_registered()
        return user_manager.get_all_users_with_profiles()
    except Exception as e:
        st.error(f"Error getting users with profiles: {str(e)}")
        return []


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
                "details": "User logged in",
            },
            {
                "timestamp": "2023-07-01 09:20:00",
                "action": "Memory Creation",
                "details": "Created 3 new memories",
            },
            {
                "timestamp": "2023-07-01 10:05:00",
                "action": "Docker Container",
                "details": "Started lightrag-server container",
            },
            {
                "timestamp": "2023-07-01 11:30:00",
                "action": "Memory Search",
                "details": "Performed semantic search",
            },
            {
                "timestamp": "2023-07-01 12:45:00",
                "action": "Logout",
                "details": "User logged out",
            },
        ]

        return activities

    except Exception as e:
        st.error(f"Error getting user activity: {str(e)}")
        return []
