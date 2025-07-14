"""
User Manager

Orchestrates user management with LightRAG service integration.
Combines UserRegistry and LightRAGManager for complete user switching.
"""

import os
from typing import Dict, Any, List, Optional

from .user_registry import UserRegistry
from .lightrag_manager import LightRAGManager


class UserManager:
    """Complete user management with LightRAG integration."""
    
    def __init__(self, data_dir: str = None, storage_backend: str = None, project_root: str = None):
        """
        Initialize the user manager.
        
        Args:
            data_dir: Data directory path (defaults to config DATA_DIR)
            storage_backend: Storage backend (defaults to config STORAGE_BACKEND)
            project_root: Project root directory (defaults to current working directory)
        """
        self.registry = UserRegistry(data_dir, storage_backend)
        self.lightrag_manager = LightRAGManager(project_root)
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users from the registry.
        
        Returns:
            List of user dictionaries with current user marked
        """
        users = self.registry.get_all_users()
        
        # Mark current user
        from personal_agent.config import USER_ID
        current_user_id = USER_ID
        
        for user in users:
            user["is_current"] = (user["user_id"] == current_user_id)
        
        return users
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific user from the registry.
        
        Args:
            user_id: User identifier
            
        Returns:
            User dictionary or None if not found
        """
        return self.registry.get_user(user_id)
    
    def create_user(self, user_id: str, user_name: str = None, user_type: str = "Standard") -> Dict[str, Any]:
        """
        Create a new user in the system.
        
        Args:
            user_id: Unique user identifier
            user_name: Display name for the user (defaults to user_id)
            user_type: User type (Standard, Admin, Guest)
            
        Returns:
            Dictionary containing result information
        """
        try:
            # Validate input
            if not user_id:
                return {"success": False, "error": "User ID is required"}
            
            if not user_name:
                user_name = user_id
            
            # Add user to registry
            if self.registry.add_user(user_id, user_name, user_type):
                return {
                    "success": True,
                    "message": f"User '{user_id}' created successfully",
                    "user_id": user_id
                }
            else:
                return {
                    "success": False,
                    "error": f"User '{user_id}' already exists"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating user: {str(e)}"
            }
    
    def switch_user(self, user_id: str, restart_lightrag: bool = True, update_global_config: bool = True) -> Dict[str, Any]:
        """
        Switch to a different user with complete system integration.
        
        Args:
            user_id: User ID to switch to
            restart_lightrag: Whether to restart LightRAG services
            update_global_config: Whether to update global USER_ID configuration
            
        Returns:
            Dictionary containing result information
        """
        try:
            # Validate input
            if not user_id:
                return {"success": False, "error": "User ID is required"}
            
            # Check if user exists in registry
            if not self.registry.user_exists(user_id):
                return {"success": False, "error": f"User '{user_id}' does not exist"}
            
            # Get current user using dynamic function
            from personal_agent.config import get_current_user_id
            current_user = get_current_user_id()
            
            # Don't switch if already the current user
            if user_id == current_user:
                return {"success": False, "error": f"Already logged in as '{user_id}'"}
            
            results = {
                "success": True,
                "user_id": user_id,
                "previous_user": current_user,
                "actions_performed": [],
                "warnings": [],
                "lightrag_status": {},
                "config_refresh": {}
            }
            
            # Update global environment variable
            if update_global_config:
                os.environ["USER_ID"] = user_id
                results["actions_performed"].append("Updated global USER_ID environment variable")
                
                # Refresh user-dependent configuration settings
                from personal_agent.config import refresh_user_dependent_settings
                refreshed_settings = refresh_user_dependent_settings()
                results["config_refresh"] = refreshed_settings
                results["actions_performed"].append("Refreshed user-dependent configuration settings")
            
            # Restart LightRAG services with new user ID
            if restart_lightrag:
                lightrag_result = self.lightrag_manager.restart_lightrag_services(user_id)
                results["lightrag_status"] = lightrag_result
                
                if lightrag_result["success"]:
                    results["actions_performed"].append("Restarted LightRAG services")
                    if lightrag_result["services_restarted"]:
                        results["actions_performed"].append(f"Services restarted: {', '.join(lightrag_result['services_restarted'])}")
                else:
                    results["warnings"].append("LightRAG restart had issues")
                    if lightrag_result["errors"]:
                        results["warnings"].extend(lightrag_result["errors"])
            
            # Update user's last_seen timestamp
            self.registry.update_last_seen(user_id)
            results["actions_performed"].append("Updated user last_seen timestamp")
            
            return results
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error switching user: {str(e)}"
            }
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a user from the system.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            Dictionary containing result information
        """
        try:
            # Validate input
            if not user_id:
                return {"success": False, "error": "User ID is required"}
            
            # Check if user exists
            if not self.registry.user_exists(user_id):
                return {"success": False, "error": f"User '{user_id}' does not exist"}
            
            # Get current user
            from personal_agent.config import USER_ID
            current_user = USER_ID
            
            # Don't delete the current user
            if user_id == current_user:
                return {"success": False, "error": "Cannot delete the current user"}
            
            # Remove user from registry
            if self.registry.remove_user(user_id):
                return {
                    "success": True,
                    "message": f"User '{user_id}' deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete user '{user_id}'"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error deleting user: {str(e)}"
            }
    
    def restart_lightrag_for_current_user(self) -> Dict[str, Any]:
        """
        Restart LightRAG services for the current user.
        
        Returns:
            Dictionary containing result information
        """
        try:
            from personal_agent.config import USER_ID
            current_user = USER_ID
            
            # Ensure current user is registered
            self.registry.ensure_current_user_registered()
            
            # Restart LightRAG services
            result = self.lightrag_manager.restart_lightrag_services(current_user)
            
            if result["success"]:
                # Update user's last_seen timestamp
                self.registry.update_last_seen(current_user)
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error restarting LightRAG: {str(e)}"
            }
    
    def get_lightrag_status(self) -> Dict[str, Any]:
        """
        Get current LightRAG service status.
        
        Returns:
            Dictionary with service status information
        """
        try:
            return self.lightrag_manager.get_service_status()
        except Exception as e:
            return {
                "error": f"Error getting LightRAG status: {str(e)}"
            }
    
    def ensure_current_user_registered(self) -> bool:
        """
        Ensure the current USER_ID is registered in the registry.
        
        Returns:
            True if user was already registered or successfully added
        """
        return self.registry.ensure_current_user_registered()
    
    def update_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update user information.
        
        Args:
            user_id: User identifier
            **kwargs: Fields to update (user_name, user_type, etc.)
            
        Returns:
            Dictionary containing result information
        """
        try:
            if self.registry.update_user(user_id, **kwargs):
                return {
                    "success": True,
                    "message": f"User '{user_id}' updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"User '{user_id}' not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error updating user: {str(e)}"
            }
    
    def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific user.
        
        Args:
            user_id: User ID to get details for
            
        Returns:
            Dictionary containing user details
        """
        user = self.registry.get_user(user_id)
        if not user:
            return {}
        
        # Add additional details
        user_details = user.copy()
        
        # Add current user status
        from personal_agent.config import USER_ID
        user_details["is_current"] = (user_id == USER_ID)
        
        # Add LightRAG status if this is the current user
        if user_details["is_current"]:
            try:
                lightrag_status = self.get_lightrag_status()
                user_details["lightrag_status"] = lightrag_status
            except Exception:
                user_details["lightrag_status"] = {"error": "Could not get LightRAG status"}
        
        return user_details
