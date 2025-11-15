"""
User Registry - Multi-User Management for Personal Agent System
================================================================

This module provides comprehensive user registry management for the Personal Agent
system, supporting multiple users with complete profile information, validation,
and persistence. The registry serves as the single source of truth for all users
in the system and integrates seamlessly with the global configuration manager.

The UserRegistry class manages:
- User creation, retrieval, update, and deletion
- Profile information (email, phone, address, birth date, cognitive state, gender, NPC status)
- User validation using the User dataclass model
- Automatic current user registration and tracking
- JSON-based persistence with thread-safe operations
- Integration with PersonalAgent's global configuration system

Key Features:
- **Multi-User Support**: Complete isolation between users with separate data directories
- **Rich Profiles**: Extended user information including demographics and cognitive state
- **Validation**: Field-level validation through User dataclass integration
- **Auto-Registration**: Automatic registration of current user on first access
- **Configuration Integration**: Uses global configuration manager instead of environment variables
- **User Objects**: Conversion between dictionary and User dataclass representations

Architecture:
The registry stores all users in a single JSON file located at:
    ~/.persagent/users_registry.json (configurable via PersonalAgentConfig)

Each user entry contains:
- Basic info: user_id, user_name, user_type
- Contact: email, phone, address
- Personal: birth_date, delta_year, cognitive_state, gender
- System: created_at, last_seen, npc (bot user flag)

Usage:
    from personal_agent.core.user_registry import UserRegistry

    registry = UserRegistry()

    # Add a new user
    success = registry.add_user(
        user_id="john_doe",
        user_name="John Doe",
        email="john@example.com",
        gender="Male",
        cognitive_state=100
    )

    # Get current user
    current_user = registry.get_current_user()

    # Update user profile
    result = registry.update_user_profile(
        "john_doe",
        email="newemail@example.com",
        cognitive_state=95
    )

Author: Eric G. Suchanek, PhD
Revision Date: 2025-11-14 23:37:47
License: Apache 2.0

Copyright 2025 Eric G. Suchanek, PhD

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from personal_agent.config.runtime_config import get_config

from .user_model import User


class UserRegistry:
    """Simple user registry for tracking Personal Agent users."""

    def __init__(self, data_dir: str = None, storage_backend: str = None):
        """
        Initialize the user registry.

        Args:
            data_dir: Data directory path (defaults to config persag_root - the shared data directory)
            storage_backend: Storage backend (defaults to config storage_backend)
        """
        # Get configuration from global config manager
        config = get_config()

        if data_dir is None:
            # Use persag_root (shared data directory) instead of persag_home (user config directory)
            # The user registry is shared across all users and belongs in the data directory
            data_dir = config.persag_root
        if storage_backend is None:
            storage_backend = config.storage_backend

        self.registry_file = Path(data_dir) / "users_registry.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize registry file if it doesn't exist
        if not self.registry_file.exists():
            self._create_empty_registry()

    def _create_empty_registry(self):
        """Create an empty registry file."""
        empty_registry = {"users": []}
        with open(self.registry_file, "w") as f:
            json.dump(empty_registry, f, indent=2)

    def _load_registry(self) -> Dict[str, Any]:
        """Load the registry from file."""
        try:
            with open(self.registry_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._create_empty_registry()
            return {"users": []}

    def _save_registry(self, registry: Dict[str, Any]):
        """Save the registry to file."""
        with open(self.registry_file, "w") as f:
            json.dump(registry, f, indent=2)

    def add_user(
        self,
        user_id: str,
        user_name: str = None,
        user_type: str = "Standard",
        email: str = None,
        phone: str = None,
        address: str = None,
        birth_date: str = None,
        delta_year: int = None,
        cognitive_state: int = 100,
        gender: str = "N/A",
        npc: bool = False,
    ) -> Optional[str]:
        """
        Add a new user to the registry.

        user_id is normalized to lowercase and used for:
        - Unique identification
        - Directory/file paths
        - Case-insensitive login

        user_name is the display name (preserves case, spaces allowed)

        Args:
            user_id: Unique user identifier (will be normalized to lowercase)
            user_name: Display name for the user (defaults to title-cased user_id)
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
            Normalized user_id if user was added, None if user already exists
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")

        # Normalize user_id to lowercase for consistency
        user_id = user_id.lower().strip()

        # Replace spaces with dots for filesystem compatibility
        user_id = user_id.replace(" ", ".")

        # Validate user_id format (alphanumeric, dots, underscores, hyphens only)
        import re

        if not re.match(r"^[a-z0-9._-]+$", user_id):
            raise ValueError(
                "user_id can only contain lowercase letters, numbers, dots, underscores, and hyphens"
            )

        registry = self._load_registry()

        # Check if user already exists (case-insensitive)
        user_id_lower = user_id.lower()
        for user in registry["users"]:
            if user["user_id"].lower() == user_id_lower:
                return None

        # Generate user_name from user_id if not provided
        if not user_name:
            # Convert "paula.smith" to "Paula Smith"
            user_name = (
                user_id.replace(".", " ").replace("_", " ").replace("-", " ").title()
            )

        # Create new user with dataclass
        try:
            new_user = User(
                user_id=user_id,  # Already normalized to lowercase
                user_name=user_name,
                user_type=user_type,
                email=email,
                phone=phone,
                address=address,
                birth_date=birth_date,
                delta_year=delta_year,
                cognitive_state=cognitive_state,
                gender=gender,
                npc=npc,
            )

            registry["users"].append(new_user.to_dict())
            self._save_registry(registry)
            return user_id  # Return the normalized user_id

        except ValueError as e:
            raise ValueError(f"Invalid user data: {str(e)}") from e

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users from the registry.

        Returns:
            List of user dictionaries
        """
        registry = self._load_registry()
        return registry.get("users", [])

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific user from the registry.

        Performs case-insensitive lookup to handle variations like "Paula" vs "paula".

        Args:
            user_id: User identifier (case-insensitive)

        Returns:
            User dictionary or None if not found
        """
        registry = self._load_registry()
        user_id_lower = user_id.lower()
        for user in registry["users"]:
            if user["user_id"].lower() == user_id_lower:
                return user
        return None

    def remove_user(self, user_id: str) -> bool:
        """
        Remove a user from the registry.

        Performs case-insensitive lookup to handle variations like "Paula" vs "paula".

        Args:
            user_id: User identifier (case-insensitive)

        Returns:
            True if user was removed, False if user not found
        """
        registry = self._load_registry()
        original_count = len(registry["users"])

        user_id_lower = user_id.lower()
        registry["users"] = [
            user
            for user in registry["users"]
            if user["user_id"].lower() != user_id_lower
        ]

        if len(registry["users"]) < original_count:
            self._save_registry(registry)
            return True
        return False

    def update_last_seen(self, user_id: str) -> bool:
        """
        Update the last_seen timestamp for a user.

        Args:
            user_id: User identifier

        Returns:
            True if user was updated, False if user not found
        """
        registry = self._load_registry()

        for user in registry["users"]:
            if user["user_id"] == user_id:
                user["last_seen"] = datetime.now().isoformat()
                self._save_registry(registry)
                return True
        return False

    def update_user(self, user_id: str, **kwargs) -> bool:
        """
        Update user information with validation.

        Args:
            user_id: User identifier
            **kwargs: Fields to update (user_name, user_type, email, phone, address, cognitive_state)

        Returns:
            True if user was updated, False if user not found
        """
        registry = self._load_registry()

        for user_data in registry["users"]:
            if user_data["user_id"] == user_id:
                # Create User object from existing data for validation
                try:
                    user = User.from_dict(user_data)

                    # Update fields using the User dataclass validation
                    update_result = user.update_profile(**kwargs)

                    if update_result["success"]:
                        # Replace the user data in registry with updated version
                        registry["users"][
                            registry["users"].index(user_data)
                        ] = user.to_dict()
                        self._save_registry(registry)
                        return True
                    else:
                        # Validation failed
                        error_msg = "; ".join(update_result["errors"])
                        raise ValueError(f"User update validation failed: {error_msg}")

                except ValueError as e:
                    raise ValueError(f"Invalid user update: {str(e)}")

        return False

    def user_exists(self, user_id: str) -> bool:
        """
        Check if a user exists in the registry.

        Args:
            user_id: User identifier

        Returns:
            True if user exists, False otherwise
        """
        return self.get_user(user_id) is not None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the current user from the global configuration manager.

        Returns:
            Current user dictionary or None if not found
        """
        config = get_config()
        return self.get_user(config.user_id)

    def ensure_current_user_registered(self) -> bool:
        """
        Ensure the current user_id is registered in the registry.
        Auto-registers if not found.

        Returns:
            True if user was already registered or successfully added
        """
        config = get_config()
        current_user_id = config.user_id
        if self.user_exists(current_user_id):
            # Update last_seen for existing user
            self.update_last_seen(current_user_id)
            return True
        else:
            # Auto-register current user
            return bool(self.add_user(current_user_id, current_user_id, "Admin"))

    def get_user_object(self, user_id: str) -> Optional[User]:
        """
        Get a specific user as a User dataclass object.

        Args:
            user_id: User identifier

        Returns:
            User object or None if not found
        """
        user_data = self.get_user(user_id)
        if user_data:
            return User.from_dict(user_data)
        return None

    def get_all_user_objects(self) -> List[User]:
        """
        Get all users as User dataclass objects.

        Returns:
            List of User objects
        """
        registry = self._load_registry()
        users = []
        for user_data in registry.get("users", []):
            try:
                users.append(User.from_dict(user_data))
            except Exception:
                # Skip invalid user data but continue processing others
                continue
        return users

    def update_user_profile(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update user profile with detailed validation results.

        Args:
            user_id: User identifier
            **kwargs: Fields to update

        Returns:
            Dictionary with detailed update results
        """
        registry = self._load_registry()

        for user_data in registry["users"]:
            if user_data["user_id"] == user_id:
                try:
                    user = User.from_dict(user_data)
                    update_result = user.update_profile(**kwargs)

                    if update_result["success"]:
                        # Replace the user data in registry with updated version
                        registry["users"][
                            registry["users"].index(user_data)
                        ] = user.to_dict()
                        self._save_registry(registry)

                    return update_result

                except ValueError as e:
                    return {
                        "success": False,
                        "updated_fields": [],
                        "errors": [f"User data validation failed: {str(e)}"],
                    }

        return {
            "success": False,
            "updated_fields": [],
            "errors": [f"User '{user_id}' not found"],
        }

    def discover_filesystem_users(self, data_root: str = None) -> List[Dict[str, Any]]:
        """
        Discover users from filesystem (agno directory structure).

        Scans the agno directory for user folders and returns basic info
        inferred from directory structure and metadata.

        Args:
            data_root: Root data directory (defaults to config persag_root)

        Returns:
            List of discovered user dictionaries with inferred metadata
        """
        config = get_config()
        data_root = data_root or config.persag_root
        agno_dir = Path(data_root) / "agno"

        if not agno_dir.exists():
            return []

        discovered = []
        for user_dir in agno_dir.iterdir():
            if user_dir.is_dir() and user_dir.name not in [".", ".."]:
                user_id = user_dir.name
                # Convert user_id to user_name (charlie.brown → Charlie Brown)
                user_name = user_id.replace(".", " ").replace("_", " ").title()

                # Get directory creation time
                stat_info = user_dir.stat()
                created_at = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                last_seen = datetime.fromtimestamp(stat_info.st_mtime).isoformat()

                discovered.append(
                    {
                        "user_id": user_id,
                        "user_name": user_name,
                        "user_type": "Standard",
                        "created_at": created_at,
                        "last_seen": last_seen,
                        "source": "filesystem",
                    }
                )

        return discovered

    def rebuild_registry(
        self, merge_existing: bool = True, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Rebuild user registry by merging existing registry data with filesystem discovery.

        This intelligent recovery method:
        1. Loads existing registry data (if available and valid)
        2. Scans filesystem for user directories
        3. Merges both sources, preserving known profile data
        4. Identifies orphaned users (in registry but no filesystem dir)
        5. Identifies new users (filesystem dir but not in registry)

        Args:
            merge_existing: If True, merge with existing registry; if False, rebuild from scratch
            dry_run: If True, return results without modifying registry

        Returns:
            Dictionary with rebuild results:
            {
                'success': bool,
                'preserved_users': List[str],  # Users with existing profile data
                'discovered_users': List[str], # Users discovered from filesystem
                'orphaned_users': List[str],   # Users in registry but no filesystem dir
                'total_users': int,
                'registry_backup': str,        # Path to backup file (if created)
            }
        """
        results = {
            "success": False,
            "preserved_users": [],
            "discovered_users": [],
            "orphaned_users": [],
            "total_users": 0,
            "registry_backup": None,
        }

        # Step 1: Load existing registry data
        existing_users = {}
        if merge_existing:
            try:
                registry = self._load_registry()
                for user_data in registry.get("users", []):
                    user_id = user_data.get("user_id")
                    if user_id:
                        existing_users[user_id] = user_data
            except Exception:
                # If registry is corrupted, continue with empty existing_users
                pass

        # Step 2: Discover users from filesystem
        filesystem_users = self.discover_filesystem_users()
        filesystem_user_ids = {u["user_id"] for u in filesystem_users}

        # Step 3: Create backup if we have existing data
        if existing_users and not dry_run:
            backup_path = str(self.registry_file) + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                import shutil

                shutil.copy2(self.registry_file, backup_path)
                results["registry_backup"] = backup_path
            except Exception:
                pass

        # Step 4: Build merged user list
        merged_users = []
        seen_user_ids = set()

        # First, add users from existing registry that have filesystem presence
        for user_id, user_data in existing_users.items():
            if user_id in filesystem_user_ids:
                # User exists in both - preserve full profile data
                merged_users.append(user_data)
                seen_user_ids.add(user_id)
                results["preserved_users"].append(user_id)
            else:
                # User in registry but no filesystem directory - orphaned
                results["orphaned_users"].append(user_id)

        # Second, add newly discovered users from filesystem
        for fs_user in filesystem_users:
            user_id = fs_user["user_id"]
            if user_id not in seen_user_ids:
                # New user discovered from filesystem
                try:
                    new_user = User(
                        user_id=user_id,
                        user_name=fs_user["user_name"],
                        user_type=fs_user.get("user_type", "Standard"),
                        created_at=fs_user.get("created_at"),
                        last_seen=fs_user.get("last_seen"),
                    )
                    merged_users.append(new_user.to_dict())
                    seen_user_ids.add(user_id)
                    results["discovered_users"].append(user_id)
                except Exception:
                    # Skip invalid user data
                    continue

        results["total_users"] = len(merged_users)

        # Step 5: Save merged registry (unless dry_run)
        if not dry_run:
            try:
                new_registry = {"users": merged_users}
                self._save_registry(new_registry)
                results["success"] = True
            except Exception as e:
                results["error"] = str(e)
                results["success"] = False
        else:
            results["success"] = True  # Dry run succeeded

        return results
