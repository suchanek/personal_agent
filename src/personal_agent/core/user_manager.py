"""
User Manager

Orchestrates user management with LightRAG service integration.
Combines UserRegistry and LightRAGManager for complete user switching.
"""

import os
import shutil
from pathlib import Path
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
        # Store the configuration for use in methods
        if data_dir is None or storage_backend is None:
            from personal_agent.config import DATA_DIR, STORAGE_BACKEND
            self.data_dir = data_dir or DATA_DIR
            self.storage_backend = storage_backend or STORAGE_BACKEND
        else:
            self.data_dir = data_dir
            self.storage_backend = storage_backend
            
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
        from personal_agent.config import get_current_user_id
        current_user_id = get_current_user_id()
        
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
            
            # Update global environment variable and persistent user file
            if update_global_config:
                os.environ["USER_ID"] = user_id
                results["actions_performed"].append("Updated global USER_ID environment variable")

                # Write to ~/.persag/env.userid to persist the change
                try:
                    from ..core.persag_manager import get_persag_manager
                    persag_manager = get_persag_manager()
                    success = persag_manager.set_userid(user_id)
                    if success:
                        results["actions_performed"].append(f"Persisted current user to ~/.persag/env.userid")
                    else:
                        results["warnings"].append("Could not write to ~/.persag/env.userid")
                except Exception as e:
                    results["warnings"].append(f"Could not write to ~/.persag/env.userid: {e}")

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
    
    def delete_user(self, user_id: str, delete_data: bool = True, backup_data: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """
        Delete a user from the system with comprehensive data cleanup.
        
        Args:
            user_id: User ID to delete
            delete_data: Whether to delete persistent data directory (default: True)
            backup_data: Whether to backup data before deletion (default: False)
            dry_run: Preview mode - show what would be deleted without deleting (default: False)
            
        Returns:
            Dictionary containing detailed result information
        """
        try:
            # Validate input
            if not user_id:
                return {"success": False, "error": "User ID is required"}
            
            # Check if user exists
            if not self.registry.user_exists(user_id):
                return {"success": False, "error": f"User '{user_id}' does not exist"}
            
            # Get current user
            from personal_agent.config import get_current_user_id
            current_user = get_current_user_id()
            
            # Don't delete the current user
            if user_id == current_user:
                return {"success": False, "error": "Cannot delete the current user"}
            
            # Initialize result structure
            results = {
                "success": True,
                "user_id": user_id,
                "dry_run": dry_run,
                "actions_performed": [],
                "data_deleted": {
                    "registry": False,
                    "data_directory": False,
                    "directories_removed": [],
                    "files_removed": 0,
                    "total_size_mb": 0.0
                },
                "backup_info": {},
                "warnings": [],
                "errors": []
            }
            
            # Get user data directory path
            user_data_dir = None
            if delete_data:
                user_data_dir = Path(self.data_dir) / self.storage_backend / user_id
                
                if dry_run:
                    # In dry-run mode, analyze what would be deleted
                    if user_data_dir.exists():
                        size_info = self._calculate_directory_size(user_data_dir)
                        results["data_deleted"]["directories_removed"] = [str(user_data_dir)]
                        results["data_deleted"]["files_removed"] = size_info["file_count"]
                        results["data_deleted"]["total_size_mb"] = size_info["size_mb"]
                        results["actions_performed"].append(f"[DRY RUN] Would delete user data directory: {user_data_dir}")
                        results["actions_performed"].append(f"[DRY RUN] Would remove {size_info['file_count']} files ({size_info['size_mb']:.2f} MB)")
                    else:
                        results["actions_performed"].append(f"[DRY RUN] User data directory does not exist: {user_data_dir}")
                    
                    results["actions_performed"].append(f"[DRY RUN] Would remove user '{user_id}' from registry")
                    return results
            
            # Backup data if requested
            if backup_data and user_data_dir and user_data_dir.exists():
                backup_result = self._backup_user_data(user_id, user_data_dir)
                results["backup_info"] = backup_result
                if backup_result["success"]:
                    results["actions_performed"].append(f"Backed up user data to: {backup_result['backup_path']}")
                else:
                    results["warnings"].append(f"Backup failed: {backup_result['error']}")
            
            # Delete user data directory
            if delete_data and user_data_dir:
                try:
                    if user_data_dir.exists():
                        # Calculate size before deletion for reporting
                        size_info = self._calculate_directory_size(user_data_dir)
                        
                        # Remove the directory and all contents
                        shutil.rmtree(user_data_dir)
                        
                        results["data_deleted"]["data_directory"] = True
                        results["data_deleted"]["directories_removed"] = [str(user_data_dir)]
                        results["data_deleted"]["files_removed"] = size_info["file_count"]
                        results["data_deleted"]["total_size_mb"] = size_info["size_mb"]
                        results["actions_performed"].append(f"Deleted user data directory: {user_data_dir}")
                        results["actions_performed"].append(f"Removed {size_info['file_count']} files ({size_info['size_mb']:.2f} MB)")
                    else:
                        results["warnings"].append(f"User data directory does not exist: {user_data_dir}")
                        results["actions_performed"].append("No user data directory to delete")
                        
                except PermissionError as e:
                    results["errors"].append(f"Permission denied deleting data directory: {str(e)}")
                    results["success"] = False
                except Exception as e:
                    results["errors"].append(f"Error deleting data directory: {str(e)}")
                    results["success"] = False
            
            # Remove user from registry (always attempt this, even if data deletion failed)
            try:
                if self.registry.remove_user(user_id):
                    results["data_deleted"]["registry"] = True
                    results["actions_performed"].append(f"Removed user '{user_id}' from registry")
                else:
                    results["errors"].append(f"Failed to remove user '{user_id}' from registry")
                    results["success"] = False
            except Exception as e:
                results["errors"].append(f"Error removing user from registry: {str(e)}")
                results["success"] = False
            
            # Set final message
            if results["success"]:
                if delete_data:
                    results["message"] = f"User '{user_id}' and all associated data deleted successfully"
                else:
                    results["message"] = f"User '{user_id}' deleted from registry successfully"
            else:
                results["message"] = f"User '{user_id}' deletion completed with errors"
            
            return results
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error deleting user: {str(e)}"
            }
    
    def _calculate_directory_size(self, directory: Path) -> Dict[str, Any]:
        """
        Calculate the total size and file count of a directory.
        
        Args:
            directory: Path to the directory
            
        Returns:
            Dictionary with size information
        """
        try:
            total_size = 0
            file_count = 0
            
            for path in directory.rglob('*'):
                if path.is_file():
                    file_count += 1
                    try:
                        total_size += path.stat().st_size
                    except (OSError, IOError):
                        # Skip files we can't access
                        pass
            
            return {
                "size_bytes": total_size,
                "size_mb": total_size / (1024 * 1024),
                "file_count": file_count
            }
        except Exception:
            return {
                "size_bytes": 0,
                "size_mb": 0.0,
                "file_count": 0
            }
    
    def _backup_user_data(self, user_id: str, user_data_dir: Path) -> Dict[str, Any]:
        """
        Create a backup of user data before deletion.
        
        Args:
            user_id: User ID being backed up
            user_data_dir: Path to user's data directory
            
        Returns:
            Dictionary with backup result information
        """
        try:
            from datetime import datetime
            
            # Create backup directory
            backup_base = Path("./backups/users")
            backup_base.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{user_id}_{timestamp}"
            backup_path = backup_base / backup_name
            
            # Copy the entire user directory
            shutil.copytree(user_data_dir, backup_path)
            
            # Calculate backup size
            size_info = self._calculate_directory_size(backup_path)
            
            return {
                "success": True,
                "backup_path": str(backup_path),
                "backup_size_mb": size_info["size_mb"],
                "files_backed_up": size_info["file_count"],
                "timestamp": timestamp
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Backup failed: {str(e)}"
            }
    
    def restart_lightrag_for_current_user(self) -> Dict[str, Any]:
        """
        Restart LightRAG services for the current user.
        
        Returns:
            Dictionary containing result information
        """
        try:
            from personal_agent.config import get_current_user_id
            current_user = get_current_user_id()
            
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
        from personal_agent.config import get_current_user_id
        user_details["is_current"] = (user_id == get_current_user_id())
        
        # Add LightRAG status if this is the current user
        if user_details["is_current"]:
            try:
                lightrag_status = self.get_lightrag_status()
                user_details["lightrag_status"] = lightrag_status
            except Exception:
                user_details["lightrag_status"] = {"error": "Could not get LightRAG status"}
        
        return user_details
