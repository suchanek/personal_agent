"""
User Manager

Orchestrates user management with LightRAG service integration.
Combines UserRegistry and LightRAGManager for complete user switching.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from .lightrag_manager import LightRAGManager
from .user_model import User
from .user_registry import UserRegistry


class UserManager:
    """Complete user management with LightRAG integration."""

    def __init__(
        self,
        data_dir: str = None,
        storage_backend: str = None,
        project_root: str = None,
    ):
        """
        Initialize the user manager.

        Args:
            data_dir: Data directory path (defaults to config DATA_DIR)
            storage_backend: Storage backend (defaults to config STORAGE_BACKEND)
            project_root: Project root directory (deprecated, LightRAGManager now uses PERSAG_HOME)
        """
        # Store the configuration for use in methods
        if data_dir is None or storage_backend is None:
            from personal_agent.config import DATA_DIR, STORAGE_BACKEND

            self.data_dir = data_dir or DATA_DIR
            self.storage_backend = storage_backend or STORAGE_BACKEND
        else:
            self.data_dir = data_dir
            self.storage_backend = storage_backend

        self.registry = UserRegistry(self.data_dir, self.storage_backend)
        # LightRAGManager now uses PERSAG_HOME internally, project_root parameter is deprecated
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
            user["is_current"] = user["user_id"] == current_user_id

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

    def create_user(
        self,
        user_id: str,
        user_name: str = None,
        user_type: str = "Standard",
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
            user_id: Unique user identifier
            user_name: Display name for the user (defaults to user_id)
            user_type: User type (Standard, Admin, Guest)
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
            # Validate input
            if not user_id:
                return {"success": False, "error": "User ID is required"}

            if not user_name:
                user_name = user_id

            # Add user to registry with extended fields
            if self.registry.add_user(
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
            ):
                return {
                    "success": True,
                    "message": f"User '{user_id}' created successfully",
                    "user_id": user_id,
                }
            else:
                return {"success": False, "error": f"User '{user_id}' already exists"}

        except Exception as e:
            return {"success": False, "error": f"Error creating user: {str(e)}"}

    def switch_user(
        self,
        user_id: str,
        restart_lightrag: bool = True,
        update_global_config: bool = True,
    ) -> Dict[str, Any]:
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
                "config_refresh": {},
            }

            # Update global environment variable and persistent user file
            if update_global_config:
                os.environ["USER_ID"] = user_id
                results["actions_performed"].append(
                    "Updated global USER_ID environment variable"
                )

                # Write to ~/.persagent/env.userid to persist the change
                try:
                    from ..core.persag_manager import get_persag_manager

                    persag_manager = get_persag_manager()
                    success = persag_manager.set_userid(user_id)
                    if success:
                        results["actions_performed"].append(
                            f"Persisted current user to ~/.persagent/env.userid"
                        )
                    else:
                        results["warnings"].append(
                            "Could not write to ~/.persagent/env.userid"
                        )
                except Exception as e:
                    results["warnings"].append(
                        f"Could not write to ~/.persagent/env.userid: {e}"
                    )

                # Refresh user-dependent configuration settings
                from personal_agent.config import refresh_user_dependent_settings

                refreshed_settings = refresh_user_dependent_settings()
                results["config_refresh"] = refreshed_settings
                results["actions_performed"].append(
                    "Refreshed user-dependent configuration settings"
                )

            # Restart LightRAG services with new user ID
            if restart_lightrag:
                lightrag_result = self.lightrag_manager.restart_lightrag_services(
                    user_id
                )
                results["lightrag_status"] = lightrag_result

                if lightrag_result["success"]:
                    results["actions_performed"].append("Restarted LightRAG services")
                    if lightrag_result["services_restarted"]:
                        results["actions_performed"].append(
                            f"Services restarted: {', '.join(lightrag_result['services_restarted'])}"
                        )
                else:
                    results["warnings"].append("LightRAG restart had issues")
                    if lightrag_result["errors"]:
                        results["warnings"].extend(lightrag_result["errors"])

            # Update user's last_seen timestamp
            self.registry.update_last_seen(user_id)
            results["actions_performed"].append("Updated user last_seen timestamp")

            return results

        except Exception as e:
            return {"success": False, "error": f"Error switching user: {str(e)}"}

    def delete_user(
        self,
        user_id: str,
        delete_data: bool = True,
        backup_data: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
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
                    "total_size_mb": 0.0,
                },
                "backup_info": {},
                "warnings": [],
                "errors": [],
            }

            # Get user data directory path
            user_data_dir = None
            if delete_data:
                user_data_dir = Path(self.data_dir) / self.storage_backend / user_id

                if dry_run:
                    # In dry-run mode, analyze what would be deleted
                    if user_data_dir.exists():
                        size_info = self._calculate_directory_size(user_data_dir)
                        results["data_deleted"]["directories_removed"] = [
                            str(user_data_dir)
                        ]
                        results["data_deleted"]["files_removed"] = size_info[
                            "file_count"
                        ]
                        results["data_deleted"]["total_size_mb"] = size_info["size_mb"]
                        results["actions_performed"].append(
                            f"[DRY RUN] Would delete user data directory: {user_data_dir}"
                        )
                        results["actions_performed"].append(
                            f"[DRY RUN] Would remove {size_info['file_count']} files ({size_info['size_mb']:.2f} MB)"
                        )
                    else:
                        results["actions_performed"].append(
                            f"[DRY RUN] User data directory does not exist: {user_data_dir}"
                        )

                    results["actions_performed"].append(
                        f"[DRY RUN] Would remove user '{user_id}' from registry"
                    )
                    return results

            # Backup data if requested
            if backup_data and user_data_dir and user_data_dir.exists():
                backup_result = self._backup_user_data(user_id, user_data_dir)
                results["backup_info"] = backup_result
                if backup_result["success"]:
                    results["actions_performed"].append(
                        f"Backed up user data to: {backup_result['backup_path']}"
                    )
                else:
                    results["warnings"].append(
                        f"Backup failed: {backup_result['error']}"
                    )

            # Delete user data directory
            if delete_data and user_data_dir:
                try:
                    if user_data_dir.exists():
                        # Calculate size before deletion for reporting
                        size_info = self._calculate_directory_size(user_data_dir)

                        # Remove the directory and all contents
                        shutil.rmtree(user_data_dir)

                        results["data_deleted"]["data_directory"] = True
                        results["data_deleted"]["directories_removed"] = [
                            str(user_data_dir)
                        ]
                        results["data_deleted"]["files_removed"] = size_info[
                            "file_count"
                        ]
                        results["data_deleted"]["total_size_mb"] = size_info["size_mb"]
                        results["actions_performed"].append(
                            f"Deleted user data directory: {user_data_dir}"
                        )
                        results["actions_performed"].append(
                            f"Removed {size_info['file_count']} files ({size_info['size_mb']:.2f} MB)"
                        )
                    else:
                        results["warnings"].append(
                            f"User data directory does not exist: {user_data_dir}"
                        )
                        results["actions_performed"].append(
                            "No user data directory to delete"
                        )

                except PermissionError as e:
                    results["errors"].append(
                        f"Permission denied deleting data directory: {str(e)}"
                    )
                    results["success"] = False
                except Exception as e:
                    results["errors"].append(f"Error deleting data directory: {str(e)}")
                    results["success"] = False

            # Remove user from registry (always attempt this, even if data deletion failed)
            try:
                if self.registry.remove_user(user_id):
                    results["data_deleted"]["registry"] = True
                    results["actions_performed"].append(
                        f"Removed user '{user_id}' from registry"
                    )
                else:
                    results["errors"].append(
                        f"Failed to remove user '{user_id}' from registry"
                    )
                    results["success"] = False
            except Exception as e:
                results["errors"].append(f"Error removing user from registry: {str(e)}")
                results["success"] = False

            # Set final message
            if results["success"]:
                if delete_data:
                    results["message"] = (
                        f"User '{user_id}' and all associated data deleted successfully"
                    )
                else:
                    results["message"] = (
                        f"User '{user_id}' deleted from registry successfully"
                    )
            else:
                results["message"] = f"User '{user_id}' deletion completed with errors"

            return results

        except Exception as e:
            return {"success": False, "error": f"Error deleting user: {str(e)}"}

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

            for path in directory.rglob("*"):
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
                "file_count": file_count,
            }
        except Exception:
            return {"size_bytes": 0, "size_mb": 0.0, "file_count": 0}

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
                "timestamp": timestamp,
            }

        except Exception as e:
            return {"success": False, "error": f"Backup failed: {str(e)}"}

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
            return {"success": False, "error": f"Error restarting LightRAG: {str(e)}"}

    def get_lightrag_status(self) -> Dict[str, Any]:
        """
        Get current LightRAG service status.

        Returns:
            Dictionary with service status information
        """
        try:
            return self.lightrag_manager.get_service_status()
        except Exception as e:
            return {"error": f"Error getting LightRAG status: {str(e)}"}

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
                    "message": f"User '{user_id}' updated successfully",
                }
            else:
                return {"success": False, "error": f"User '{user_id}' not found"}
        except Exception as e:
            return {"success": False, "error": f"Error updating user: {str(e)}"}

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

        user_details["is_current"] = user_id == get_current_user_id()

        # Add LightRAG status if this is the current user
        if user_details["is_current"]:
            try:
                lightrag_status = self.get_lightrag_status()
                user_details["lightrag_status"] = lightrag_status
            except Exception:
                user_details["lightrag_status"] = {
                    "error": "Could not get LightRAG status"
                }

        # Add profile completion summary
        try:
            user_obj = self.registry.get_user_object(user_id)
            if user_obj:
                user_details["profile_summary"] = user_obj.get_profile_summary()
        except Exception:
            user_details["profile_summary"] = {"error": "Could not get profile summary"}

        return user_details

    def get_user_object(self, user_id: str) -> Optional[User]:
        """
        Get a specific user as a User dataclass object.

        Args:
            user_id: User identifier

        Returns:
            User object or None if not found
        """
        return self.registry.get_user_object(user_id)

    def update_user_profile(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update user profile with detailed validation and results.

        Args:
            user_id: User identifier
            **kwargs: Profile fields to update (email, phone, address, cognitive_state, user_name, user_type)

        Returns:
            Dictionary containing detailed update results
        """
        try:
            result = self.registry.update_user_profile(user_id, **kwargs)

            if result["success"]:
                result["message"] = f"User '{user_id}' profile updated successfully"
                result["updated_fields_count"] = len(result["updated_fields"])
            else:
                result["message"] = f"Failed to update user '{user_id}' profile"

            return result

        except Exception as e:
            return {
                "success": False,
                "updated_fields": [],
                "errors": [f"Error updating user profile: {str(e)}"],
                "message": f"Error updating user '{user_id}' profile",
            }

    def update_cognitive_state(
        self, user_id: str, cognitive_state: int
    ) -> Dict[str, Any]:
        """
        Update a user's cognitive state with validation.

        Args:
            user_id: User identifier
            cognitive_state: New cognitive state (0-100)

        Returns:
            Dictionary containing result information
        """
        return self.update_user_profile(user_id, cognitive_state=cognitive_state)

    def update_contact_info(
        self, user_id: str, email: str = None, phone: str = None, address: str = None
    ) -> Dict[str, Any]:
        """
        Update a user's contact information.

        Args:
            user_id: User identifier
            email: New email address
            phone: New phone number
            address: New address

        Returns:
            Dictionary containing result information
        """
        update_fields = {}
        if email is not None:
            update_fields["email"] = email
        if phone is not None:
            update_fields["phone"] = phone
        if address is not None:
            update_fields["address"] = address

        if not update_fields:
            return {
                "success": False,
                "error": "No contact information provided to update",
            }

        return self.update_user_profile(user_id, **update_fields)

    def get_user_profile_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of user's profile completeness.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with profile completion information
        """
        try:
            user_obj = self.registry.get_user_object(user_id)
            if not user_obj:
                return {"success": False, "error": f"User '{user_id}' not found"}

            summary = user_obj.get_profile_summary()
            summary["success"] = True
            summary["user_id"] = user_id

            return summary

        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting profile summary: {str(e)}",
            }

    def get_all_users_with_profiles(self) -> List[Dict[str, Any]]:
        """
        Get all users with their profile completion information.

        Returns:
            List of user dictionaries with profile summaries
        """
        users = self.get_all_users()

        for user in users:
            try:
                user_obj = self.registry.get_user_object(user["user_id"])
                if user_obj:
                    user["profile_summary"] = user_obj.get_profile_summary()
            except Exception:
                user["profile_summary"] = {"error": "Could not get profile summary"}

        return users

    def backup_user(self, user_id: str) -> Dict[str, Any]:
        """
        Create a backup of a user's data directory.

        Args:
            user_id: User ID to backup

        Returns:
            Dictionary containing backup result information
        """
        try:
            # Validate input
            if not user_id:
                return {"success": False, "error": "User ID is required"}

            # Check if user exists
            if not self.registry.user_exists(user_id):
                return {"success": False, "error": f"User '{user_id}' does not exist"}

            # Get user data directory path
            user_data_dir = Path(self.data_dir) / self.storage_backend / user_id

            # Check if user data directory exists
            if not user_data_dir.exists():
                return {
                    "success": False,
                    "error": f"User data directory does not exist: {user_data_dir}",
                }

            # Create backup using existing method
            backup_result = self._backup_user_data(user_id, user_data_dir)

            if backup_result["success"]:
                return {
                    "success": True,
                    "message": f"User '{user_id}' backed up successfully",
                    "user_id": user_id,
                    "backup_path": backup_result["backup_path"],
                    "backup_size_mb": backup_result["backup_size_mb"],
                    "files_backed_up": backup_result["files_backed_up"],
                    "timestamp": backup_result["timestamp"],
                }
            else:
                return {
                    "success": False,
                    "error": f"Backup failed for user '{user_id}': {backup_result['error']}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error backing up user '{user_id}': {str(e)}",
            }

    def restore_user(
        self, user_id: str, backup_dir: str, overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Restore a user's data from a backup directory.

        Args:
            user_id: User ID to restore
            backup_dir: Path to the backup directory (can be relative to ./backups/users or absolute path)
            overwrite_existing: Whether to overwrite existing user data (default: False)

        Returns:
            Dictionary containing restore result information
        """
        try:
            # Validate input
            if not user_id:
                return {"success": False, "error": "User ID is required"}

            if not backup_dir:
                return {"success": False, "error": "Backup directory is required"}

            # Convert backup_dir to Path and handle relative paths
            backup_path = Path(backup_dir)
            if not backup_path.is_absolute():
                # Try relative to ./backups/users first
                backup_path = Path("./backups/users") / backup_dir
                if not backup_path.exists():
                    # Try as relative to current directory
                    backup_path = Path(backup_dir)

            # Check if backup directory exists
            if not backup_path.exists():
                return {
                    "success": False,
                    "error": f"Backup directory does not exist: {backup_path}",
                }

            if not backup_path.is_dir():
                return {
                    "success": False,
                    "error": f"Backup path is not a directory: {backup_path}",
                }

            # Get target user data directory path
            user_data_dir = Path(self.data_dir) / self.storage_backend / user_id

            # Check if user data directory already exists
            if user_data_dir.exists() and not overwrite_existing:
                return {
                    "success": False,
                    "error": f"User data directory already exists: {user_data_dir}. Use overwrite_existing=True to overwrite.",
                }

            # Initialize result structure
            results = {
                "success": True,
                "user_id": user_id,
                "backup_path": str(backup_path),
                "restore_path": str(user_data_dir),
                "actions_performed": [],
                "data_restored": {
                    "files_restored": 0,
                    "total_size_mb": 0.0,
                    "overwrite_occurred": False,
                },
                "warnings": [],
                "errors": [],
            }

            # Calculate backup size for reporting
            backup_size_info = self._calculate_directory_size(backup_path)
            results["data_restored"]["files_restored"] = backup_size_info["file_count"]
            results["data_restored"]["total_size_mb"] = backup_size_info["size_mb"]

            # Remove existing directory if overwriting
            if user_data_dir.exists():
                try:
                    shutil.rmtree(user_data_dir)
                    results["data_restored"]["overwrite_occurred"] = True
                    results["actions_performed"].append(
                        f"Removed existing user data directory: {user_data_dir}"
                    )
                except Exception as e:
                    results["errors"].append(
                        f"Error removing existing directory: {str(e)}"
                    )
                    results["success"] = False
                    return results

            # Copy backup data to user directory
            try:
                shutil.copytree(backup_path, user_data_dir)
                results["actions_performed"].append(
                    f"Restored user data from backup: {backup_path}"
                )
                results["actions_performed"].append(
                    f"Restored {backup_size_info['file_count']} files ({backup_size_info['size_mb']:.2f} MB)"
                )
            except Exception as e:
                results["errors"].append(f"Error copying backup data: {str(e)}")
                results["success"] = False
                return results

            # Ensure user exists in registry (create if needed)
            if not self.registry.user_exists(user_id):
                try:
                    # Create user with basic information
                    create_result = self.create_user(user_id)
                    if create_result["success"]:
                        results["actions_performed"].append(
                            f"Created user '{user_id}' in registry"
                        )
                    else:
                        results["warnings"].append(
                            f"Could not create user in registry: {create_result.get('error', 'Unknown error')}"
                        )
                except Exception as e:
                    results["warnings"].append(
                        f"Error creating user in registry: {str(e)}"
                    )
            else:
                results["actions_performed"].append(
                    f"User '{user_id}' already exists in registry"
                )

            # Update user's last_seen timestamp
            try:
                self.registry.update_last_seen(user_id)
                results["actions_performed"].append("Updated user last_seen timestamp")
            except Exception as e:
                results["warnings"].append(
                    f"Could not update last_seen timestamp: {str(e)}"
                )

            # Set final message
            if results["success"]:
                results["message"] = (
                    f"User '{user_id}' restored successfully from backup"
                )
            else:
                results["message"] = f"User '{user_id}' restore completed with errors"

            return results

        except Exception as e:
            return {
                "success": False,
                "error": f"Error restoring user '{user_id}': {str(e)}",
            }

    def list_user_backups(self, user_id: str = None) -> Dict[str, Any]:
        """
        List available user backups.

        Args:
            user_id: Optional user ID to filter backups (if None, lists all backups)

        Returns:
            Dictionary containing backup listing information
        """
        try:
            backup_base = Path("./backups/users")

            if not backup_base.exists():
                return {
                    "success": True,
                    "backups": [],
                    "message": "No backup directory found",
                }

            backups = []

            for backup_dir in backup_base.iterdir():
                if backup_dir.is_dir():
                    # Parse backup directory name (format: user_id_timestamp)
                    parts = backup_dir.name.split("_")
                    if len(parts) >= 2:
                        backup_user_id = "_".join(
                            parts[:-1]
                        )  # Handle user IDs with underscores
                        timestamp = parts[-1]

                        # Filter by user_id if specified
                        if user_id and backup_user_id != user_id:
                            continue

                        # Calculate backup size
                        size_info = self._calculate_directory_size(backup_dir)

                        backup_info = {
                            "user_id": backup_user_id,
                            "timestamp": timestamp,
                            "backup_name": backup_dir.name,
                            "backup_path": str(backup_dir),
                            "size_mb": size_info["size_mb"],
                            "file_count": size_info["file_count"],
                        }

                        # Try to parse timestamp for better formatting
                        try:
                            from datetime import datetime

                            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                            backup_info["formatted_date"] = dt.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        except ValueError:
                            backup_info["formatted_date"] = timestamp

                        backups.append(backup_info)

            # Sort backups by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)

            return {
                "success": True,
                "backups": backups,
                "total_backups": len(backups),
                "message": f"Found {len(backups)} backup(s)"
                + (f" for user '{user_id}'" if user_id else ""),
            }

        except Exception as e:
            return {"success": False, "error": f"Error listing backups: {str(e)}"}
