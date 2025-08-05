"""
Personal Agent Configuration Manager

Manages ~/.persag directory structure and user configuration.
"""

import logging
import shutil
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PersagManager:
    """Manages ~/.persag directory structure and configuration"""
    
    def __init__(self):
        self.persag_dir = Path.home() / ".persag"
        self.userid_file = self.persag_dir / "env.userid"
        self.backup_dir = self.persag_dir / "backups"
        
    def initialize_persag_directory(self, project_root: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Create ~/.persag structure and migrate existing files if needed.
        
        Args:
            project_root: Path to project root for migration (optional)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create base directory
            self.persag_dir.mkdir(exist_ok=True)
            self.backup_dir.mkdir(exist_ok=True)
            
            # Create default env.userid if it doesn't exist
            if not self.userid_file.exists():
                default_user_id = "default_user"
                
                # Try to migrate from project root if provided
                if project_root:
                    old_userid_file = project_root / "env.userid"
                    if old_userid_file.exists():
                        # Read existing user ID
                        with open(old_userid_file, 'r') as f:
                            content = f.read().strip()
                            if content.startswith("USER_ID="):
                                default_user_id = content.split("=", 1)[1].strip().strip("'\"")
                
                # Create new env.userid
                with open(self.userid_file, 'w') as f:
                    f.write(f'USER_ID="{default_user_id}"\n')
                
                logger.info(f"Created ~/.persag/env.userid with USER_ID={default_user_id}")
            
            # Migrate docker directories if project_root provided
            if project_root:
                success, message = self.migrate_docker_directories(project_root)
                if not success:
                    return False, f"Docker migration failed: {message}"
            
            return True, "~/.persag directory initialized successfully"
            
        except Exception as e:
            logger.error(f"Failed to initialize ~/.persag directory: {e}")
            return False, str(e)
    
    def get_userid(self) -> str:
        """
        Get current user ID from ~/.persag/env.userid
        
        Returns:
            Current user ID or 'default_user' if not found
        """
        try:
            if self.userid_file.exists():
                with open(self.userid_file, 'r') as f:
                    content = f.read().strip()
                    if content.startswith("USER_ID="):
                        return content.split("=", 1)[1].strip().strip("'\"")
        except Exception as e:
            logger.warning(f"Failed to read user ID from ~/.persag/env.userid: {e}")
        
        # Fallback to environment variable for backward compatibility
        return os.getenv("USER_ID", "default_user")
    
    def set_userid(self, user_id: str) -> bool:
        """
        Set user ID in ~/.persag/env.userid
        
        Args:
            user_id: New user ID to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.persag_dir.mkdir(exist_ok=True)
            
            # Write new user ID
            with open(self.userid_file, 'w') as f:
                f.write(f'USER_ID="{user_id}"\n')
            
            logger.info(f"Set USER_ID to '{user_id}' in ~/.persag/env.userid")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set user ID: {e}")
            return False
    
    def migrate_docker_directories(self, project_root: Path) -> Tuple[bool, str]:
        """
        Migrate docker directories from project root to ~/.persag
        
        Args:
            project_root: Path to project root directory
            
        Returns:
            Tuple of (success, message)
        """
        try:
            docker_dirs = ["lightrag_server", "lightrag_memory_server"]
            migrated = []
            
            for dir_name in docker_dirs:
                source_dir = project_root / dir_name
                target_dir = self.persag_dir / dir_name
                
                if source_dir.exists() and not target_dir.exists():
                    # Create backup first
                    backup_name = f"{dir_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    backup_path = self.backup_dir / backup_name
                    shutil.copytree(source_dir, backup_path)
                    
                    # Copy to ~/.persag
                    shutil.copytree(source_dir, target_dir)
                    migrated.append(dir_name)
                    
                    logger.info(f"Migrated {dir_name} to ~/.persag (backup: {backup_path})")
            
            if migrated:
                return True, f"Migrated directories: {', '.join(migrated)}"
            else:
                return True, "No directories needed migration"
                
        except Exception as e:
            logger.error(f"Failed to migrate docker directories: {e}")
            return False, str(e)
    
    def get_docker_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Get docker configuration for ~/.persag directories
        
        Returns:
            Docker configuration dictionary
        """
        return {
            "lightrag_server": {
                "dir": self.persag_dir / "lightrag_server",
                "env_file": "env.server",
                "container_name": "lightrag_pagent",
                "compose_file": "docker-compose.yml",
            },
            "lightrag_memory_server": {
                "dir": self.persag_dir / "lightrag_memory_server",
                "env_file": "env.memory_server",
                "container_name": "lightrag_memory",
                "compose_file": "docker-compose.yml",
            },
        }
    
    def validate_persag_structure(self) -> Tuple[bool, str]:
        """
        Validate ~/.persag directory structure
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            issues = []
            
            # Check base directory
            if not self.persag_dir.exists():
                issues.append("~/.persag directory does not exist")
            
            # Check env.userid
            if not self.userid_file.exists():
                issues.append("env.userid file missing")
            else:
                user_id = self.get_userid()
                if not user_id or user_id == "default_user":
                    issues.append("Invalid or default user ID")
            
            # Check docker directories
            docker_config = self.get_docker_config()
            for name, config in docker_config.items():
                docker_dir = config["dir"]
                if not docker_dir.exists():
                    issues.append(f"{name} directory missing")
                else:
                    env_file = docker_dir / config["env_file"]
                    compose_file = docker_dir / config["compose_file"]
                    
                    if not env_file.exists():
                        issues.append(f"{name} env file missing")
                    if not compose_file.exists():
                        issues.append(f"{name} docker-compose.yml missing")
            
            if issues:
                return False, "; ".join(issues)
            else:
                return True, "~/.persag structure is valid"
                
        except Exception as e:
            return False, f"Validation error: {e}"


# Global instance
_persag_manager = None

def get_persag_manager() -> PersagManager:
    """Get global PersagManager instance"""
    global _persag_manager
    if _persag_manager is None:
        _persag_manager = PersagManager()
    return _persag_manager

def get_userid() -> str:
    """Get current user ID - replaces USER_ID constant"""
    return get_persag_manager().get_userid()