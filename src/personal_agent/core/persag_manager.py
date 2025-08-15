"""
Personal Agent Configuration Manager

Manages ~/.persag directory structure and user configuration.
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..config.settings import PERSAG_HOME
from ..config.user_id_mgr import load_user_from_file, get_userid

logger = logging.getLogger(__name__)


class PersagManager:
    """Manages ~/.persag directory structure and configuration"""

    def __init__(self):
        self.persag_dir = Path(PERSAG_HOME)
        self.userid_file = self.persag_dir / "env.userid"
        self.backup_dir = self.persag_dir / "backups"

    def initialize_persag_directory(
        self, project_root: Optional[Path] = None
    ) -> Tuple[bool, str]:
        """
        Ensure PERSAG_HOME structure exists and migrate project docker dirs if requested.

        Args:
            project_root: Path to project root for optional migration (optional)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Initialize ~/.persag (or PERSAG_HOME) and USER_ID via central manager
            current_user_id = load_user_from_file()

            # Ensure backups directory exists
            self.backup_dir.mkdir(exist_ok=True)

            # Optionally migrate docker directories if project_root provided
            if project_root:
                success, message = self.migrate_docker_directories(project_root)
                if not success:
                    return False, f"Docker migration failed: {message}"

            return True, f"{self.persag_dir} initialized successfully with USER_ID={current_user_id}"

        except Exception as e:
            logger.error(f"Failed to initialize {self.persag_dir}: {e}")
            return False, str(e)

    def get_userid(self) -> str:
        """
        Get current user ID using centralized user_id_mgr.
        """
        return get_userid()

    def set_userid(self, user_id: str) -> bool:
        """
        Set user ID in env.userid under PERSAG_HOME

        Args:
            user_id: New user ID to set

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.persag_dir.mkdir(exist_ok=True)

            # Write new user ID
            with open(self.userid_file, "w", encoding="utf-8") as f:
                f.write(f'USER_ID="{user_id}"\n')

            os.environ["USER_ID"] = user_id  # keep process env consistent
            logger.info(f"Set USER_ID to '{user_id}' in {self.userid_file}")
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
                    backup_name = (
                        f"{dir_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                    backup_path = self.backup_dir / backup_name
                    shutil.copytree(source_dir, backup_path)

                    # Copy to ~/.persag
                    shutil.copytree(source_dir, target_dir)
                    migrated.append(dir_name)

                    logger.info(
                        f"Migrated {dir_name} to {self.persag_dir} (backup: {backup_path})"
                    )

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
        Validate PERSAG_HOME directory structure

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            issues = []

            # Check base directory
            if not self.persag_dir.exists():
                issues.append(f"{self.persag_dir} directory does not exist")

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
                return True, f"{self.persag_dir} structure is valid"

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

