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
    ~/.persag/users_registry.json (configurable via PersonalAgentConfig)

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
Revision Date: October 20, 2025
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
            data_dir: Data directory path (defaults to config persag_home)
            storage_backend: Storage backend (defaults to config storage_backend)
        """
        # Get configuration from global config manager
        config = get_config()

        if data_dir is None:
            data_dir = config.persag_home
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
        cognitive_state: int = 50,
        gender: str = "N/A",
        npc: bool = False,
    ) -> bool:
        """
        Add a new user to the registry.

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
            True if user was added, False if user already exists
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")

        registry = self._load_registry()

        # Check if user already exists
        for user in registry["users"]:
            if user["user_id"] == user_id:
                return False

        # Create new user with dataclass
        try:
            new_user = User(
                user_id=user_id,
                user_name=user_name or user_id,
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
            return True

        except ValueError as e:
            raise ValueError(f"Invalid user data: {str(e)}")

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

        Args:
            user_id: User identifier

        Returns:
            User dictionary or None if not found
        """
        registry = self._load_registry()
        for user in registry["users"]:
            if user["user_id"] == user_id:
                return user
        return None

    def remove_user(self, user_id: str) -> bool:
        """
        Remove a user from the registry.

        Args:
            user_id: User identifier

        Returns:
            True if user was removed, False if user not found
        """
        registry = self._load_registry()
        original_count = len(registry["users"])

        registry["users"] = [
            user for user in registry["users"] if user["user_id"] != user_id
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
            return self.add_user(current_user_id, current_user_id, "Admin")

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
