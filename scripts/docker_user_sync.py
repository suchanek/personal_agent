#!/usr/bin/env python3
"""
Docker User ID Synchronization Tool

This script ensures USER_ID consistency between the main personal agent system
and the Docker-based LightRAG servers by:
1. Detecting USER_ID mismatches between system config and Docker env files
2. Safely updating Docker environment files with correct USER_ID
3. Managing Docker container restarts when changes are needed
4. Providing validation and rollback capabilities

Author: Personal Agent Development Team
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from personal_agent.config.settings import USER_ID as SYSTEM_USER_ID
except ImportError:
    # Fallback if import fails
    SYSTEM_USER_ID = os.getenv("USER_ID", "default_user")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

class DockerUserSync:
    """Manages USER_ID synchronization between system and Docker containers."""
    
    def __init__(self, base_dir: Optional[Path] = None, dry_run: bool = False):
        """Initialize the Docker User Sync manager.
        
        Args:
            base_dir: Base directory of the project (auto-detected if None)
            dry_run: If True, show what would be done without making changes
        """
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.dry_run = dry_run
        
        # Docker server configurations
        self.docker_configs = {
            'lightrag_server': {
                'dir': self.base_dir / 'lightrag_server',
                'env_file': 'env.server',
                'container_name': 'lightrag_pagent',
                'compose_file': 'docker-compose.yml'
            },
            'lightrag_memory_server': {
                'dir': self.base_dir / 'lightrag_memory_server', 
                'env_file': 'env.memory_server',
                'container_name': 'lightrag_memory',
                'compose_file': 'docker-compose.yml'
            }
        }
        
        # Backup directory
        self.backup_dir = self.base_dir / 'backups' / 'docker_env_backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized DockerUserSync with base_dir: {self.base_dir}")
        logger.info(f"System USER_ID: {SYSTEM_USER_ID}")
        logger.info(f"Dry run mode: {self.dry_run}")

    def get_env_file_user_id(self, env_file_path: Path) -> Optional[str]:
        """Extract USER_ID from an environment file.
        
        Args:
            env_file_path: Path to the environment file
            
        Returns:
            USER_ID value or None if not found
        """
        if not env_file_path.exists():
            logger.warning(f"Environment file not found: {env_file_path}")
            return None
            
        try:
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('USER_ID=') and not line.startswith('#'):
                        return line.split('=', 1)[1].strip()
            return None
        except Exception as e:
            logger.error(f"Error reading {env_file_path}: {e}")
            return None

    def update_env_file_user_id(self, env_file_path: Path, new_user_id: str) -> bool:
        """Update USER_ID in an environment file.
        
        Args:
            env_file_path: Path to the environment file
            new_user_id: New USER_ID value to set
            
        Returns:
            True if successful, False otherwise
        """
        if not env_file_path.exists():
            logger.error(f"Environment file not found: {env_file_path}")
            return False
            
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update USER_ID to '{new_user_id}' in {env_file_path}")
            return True
            
        try:
            # Read current content
            with open(env_file_path, 'r') as f:
                lines = f.readlines()
            
            # Update USER_ID line
            updated = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('USER_ID=') and not stripped.startswith('#'):
                    lines[i] = f"USER_ID={new_user_id}\n"
                    updated = True
                    break
            
            if not updated:
                # Add USER_ID if not found
                lines.append(f"\n# User configuration\nUSER_ID={new_user_id}\n")
                logger.info(f"Added USER_ID={new_user_id} to {env_file_path}")
            
            # Write updated content
            with open(env_file_path, 'w') as f:
                f.writelines(lines)
                
