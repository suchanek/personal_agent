"""
User Registry

Simple JSON-based registry for tracking users in the Personal Agent system.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from personal_agent.config import DATA_DIR, STORAGE_BACKEND
from personal_agent.config.user_id_mgr import get_current_user_id, get_userid


class UserRegistry:
    """Simple user registry for tracking Personal Agent users."""
    
    def __init__(self, data_dir: str = None, storage_backend: str = None):
        """
        Initialize the user registry.
        
        Args:
            data_dir: Data directory path (defaults to config DATA_DIR)
            storage_backend: Storage backend (defaults to config STORAGE_BACKEND)
        """
        if data_dir is None or storage_backend is None:
            data_dir = data_dir or DATA_DIR
            storage_backend = storage_backend or STORAGE_BACKEND
        
        self.registry_file = Path(data_dir) / storage_backend / "users_registry.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize registry file if it doesn't exist
        if not self.registry_file.exists():
            self._create_empty_registry()
    
    def _create_empty_registry(self):
        """Create an empty registry file."""
        empty_registry = {"users": []}
        with open(self.registry_file, 'w') as f:
            json.dump(empty_registry, f, indent=2)
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load the registry from file."""
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._create_empty_registry()
            return {"users": []}
    
    def _save_registry(self, registry: Dict[str, Any]):
        """Save the registry to file."""
        with open(self.registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def add_user(self, user_id: str, user_name: str = None, user_type: str = "Standard") -> bool:
        """
        Add a new user to the registry.
        
        Args:
            user_id: Unique user identifier
            user_name: Display name for the user (defaults to user_id)
            user_type: User type (Standard, Admin, Guest)
            
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
        
        # Add new user
        new_user = {
            "user_id": user_id,
            "user_name": user_name or user_id,
            "user_type": user_type,
            "created_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        
        registry["users"].append(new_user)
        self._save_registry(registry)
        return True
    
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
        
        registry["users"] = [user for user in registry["users"] if user["user_id"] != user_id]
        
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
        Update user information.
        
        Args:
            user_id: User identifier
            **kwargs: Fields to update (user_name, user_type, etc.)
            
        Returns:
            True if user was updated, False if user not found
        """
        registry = self._load_registry()
        
        for user in registry["users"]:
            if user["user_id"] == user_id:
                # Update allowed fields
                allowed_fields = {"user_name", "user_type"}
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        user[key] = value
                
                user["last_seen"] = datetime.now().isoformat()
                self._save_registry(registry)
                return True
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
        Get the current user from the single source of truth (user_id_mgr).
        
        Returns:
            Current user dictionary or None if not found
        """
        return self.get_user(get_current_user_id())
    
    def ensure_current_user_registered(self) -> bool:
        """
        Ensure the current USER_ID is registered in the registry.
        Auto-registers if not found.
        
        Returns:
            True if user was already registered or successfully added
        """
        current_user_id = get_userid()
        if self.user_exists(current_user_id):
            # Update last_seen for existing user
            self.update_last_seen(current_user_id)
            return True
        else:
            # Auto-register current user
            return self.add_user(current_user_id, current_user_id, "Admin")
