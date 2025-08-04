"""
Docker User ID Synchronization Module

This module provides the DockerUserSync class for ensuring USER_ID consistency
between the main personal agent system and Docker-based LightRAG servers.

Author: Personal Agent Development Team
"""

import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
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
        self.base_dir = base_dir or Path(__file__).parent.parent.parent.parent.parent
        self.dry_run = dry_run
        
        # Import USER_ID from settings
        try:
            from ...config.settings import USER_ID as SYSTEM_USER_ID
        except ImportError:
            # Fallback if import fails
            SYSTEM_USER_ID = os.getenv("USER_ID", "default_user")
        
        self.system_user_id = SYSTEM_USER_ID
        
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
        logger.info(f"System USER_ID: {self.system_user_id}")
        logger.info(f"Dry run mode: {self.dry_run}")
        
        # Diagnostic logging for path validation
        for server_name, config in self.docker_configs.items():
            env_file_path = config['dir'] / config['env_file']
            logger.info(f"Docker config {server_name}: env_file_path = {env_file_path}")
            logger.info(f"Docker config {server_name}: exists = {env_file_path.exists()}")

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
                
            logger.info(f"Updated USER_ID to '{new_user_id}' in {env_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating {env_file_path}: {e}")
            return False

    def backup_env_file(self, env_file_path: Path, server_name: str) -> Optional[Path]:
        """Create a backup of an environment file.
        
        Args:
            env_file_path: Path to the environment file to backup
            server_name: Name of the server (for backup naming)
            
        Returns:
            Path to backup file or None if failed
        """
        if not env_file_path.exists():
            logger.warning(f"Cannot backup non-existent file: {env_file_path}")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{server_name}_{env_file_path.name}_{timestamp}.backup"
        backup_path = self.backup_dir / backup_filename
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would backup {env_file_path} to {backup_path}")
            return backup_path
            
        try:
            shutil.copy2(env_file_path, backup_path)
            logger.info(f"Backed up {env_file_path} to {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error backing up {env_file_path}: {e}")
            return None

    def is_container_running(self, container_name: str) -> bool:
        """Check if a Docker container is running.
        
        Args:
            container_name: Name of the container to check
            
        Returns:
            True if container is running, False otherwise
        """
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True, text=True, check=True
            )
            return container_name in result.stdout
        except subprocess.CalledProcessError:
            return False

    def stop_docker_service(self, server_config: Dict) -> bool:
        """Stop a Docker service using docker-compose.
        
        Args:
            server_config: Configuration dictionary for the server
            
        Returns:
            True if successful, False otherwise
        """
        server_dir = server_config['dir']
        compose_file = server_config['compose_file']
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would stop Docker service in {server_dir}")
            return True
            
        try:
            result = subprocess.run(
                ['docker-compose', '-f', compose_file, 'down'],
                cwd=server_dir, capture_output=True, text=True, check=True
            )
            logger.info(f"Stopped Docker service in {server_dir}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error stopping Docker service in {server_dir}: {e.stderr}")
            return False

    def start_docker_service(self, server_config: Dict) -> bool:
        """Start a Docker service using docker-compose.
        
        Args:
            server_config: Configuration dictionary for the server
            
        Returns:
            True if successful, False otherwise
        """
        server_dir = server_config['dir']
        compose_file = server_config['compose_file']
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would start Docker service in {server_dir}")
            return True
            
        try:
            result = subprocess.run(
                ['docker-compose', '-f', compose_file, 'up', '-d'],
                cwd=server_dir, capture_output=True, text=True, check=True
            )
            logger.info(f"Started Docker service in {server_dir}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error starting Docker service in {server_dir}: {e.stderr}")
            return False

    def check_user_id_consistency(self) -> Dict[str, Dict]:
        """Check USER_ID consistency across all Docker configurations.
        
        Returns:
            Dictionary with consistency check results for each server
        """
        results = {}
        
        print(f"\n{Colors.BLUE}🔍 Checking USER_ID Consistency{Colors.NC}")
        print(f"{Colors.CYAN}System USER_ID: {self.system_user_id}{Colors.NC}")
        print("=" * 60)
        
        for server_name, config in self.docker_configs.items():
            env_file_path = config['dir'] / config['env_file']
            docker_user_id = self.get_env_file_user_id(env_file_path)
            is_running = self.is_container_running(config['container_name'])
            
            consistent = docker_user_id == self.system_user_id
            
            results[server_name] = {
                'env_file_path': env_file_path,
                'docker_user_id': docker_user_id,
                'system_user_id': self.system_user_id,
                'consistent': consistent,
                'container_running': is_running,
                'config': config
            }
            
            # Display results
            status_icon = f"{Colors.GREEN}✅" if consistent else f"{Colors.RED}❌"
            running_icon = f"{Colors.GREEN}🟢" if is_running else f"{Colors.YELLOW}🟡"
            
            print(f"{status_icon} {server_name}:{Colors.NC}")
            print(f"   Docker USER_ID: {docker_user_id or 'NOT FOUND'}")
            print(f"   Container: {running_icon} {'Running' if is_running else 'Stopped'}{Colors.NC}")
            print(f"   Config: {env_file_path}")
            
            if not consistent:
                print(f"   {Colors.RED}⚠️  MISMATCH DETECTED{Colors.NC}")
            print()
        
        return results

    def sync_user_ids(self, force_restart: bool = False) -> bool:
        """Synchronize USER_IDs across all Docker configurations.
        
        Args:
            force_restart: If True, restart containers even if they're not running
            
        Returns:
            True if all synchronizations successful, False otherwise
        """
        print(f"\n{Colors.PURPLE}🔄 Starting USER_ID Synchronization{Colors.NC}")
        print("=" * 60)
        
        # Check current state
        consistency_results = self.check_user_id_consistency()
        
        # Find servers that need updates
        servers_to_update = []
        for server_name, result in consistency_results.items():
            if not result['consistent']:
                servers_to_update.append(server_name)
        
        # If force_restart is True, we need to process all servers even if consistent
        if force_restart:
            servers_to_process = list(consistency_results.keys())
            if not servers_to_update:
                print(f"{Colors.GREEN}✅ All USER_IDs are already consistent!{Colors.NC}")
                print(f"{Colors.YELLOW}🔄 Force restart requested - processing all servers...{Colors.NC}")
            else:
                print(f"{Colors.YELLOW}📝 Servers requiring USER_ID updates: {', '.join(servers_to_update)}{Colors.NC}")
                print(f"{Colors.YELLOW}🔄 Force restart requested - processing all servers...{Colors.NC}")
        else:
            servers_to_process = servers_to_update
            if not servers_to_update:
                print(f"{Colors.GREEN}✅ All USER_IDs are already consistent!{Colors.NC}")
                return True
            print(f"{Colors.YELLOW}📝 Servers requiring USER_ID updates: {', '.join(servers_to_update)}{Colors.NC}")
        
        # Process each server
        all_successful = True
        
        for server_name in servers_to_process:
            result = consistency_results[server_name]
            config = result['config']
            env_file_path = result['env_file_path']
            container_running = result['container_running']
            needs_user_id_update = not result['consistent']
            
            print(f"\n{Colors.CYAN}🔧 Processing {server_name}...{Colors.NC}")
            
            # Step 1: Backup current environment file (only if we're updating it)
            if needs_user_id_update:
                backup_path = self.backup_env_file(env_file_path, server_name)
                if not backup_path and not self.dry_run:
                    logger.error(f"Failed to backup {env_file_path}, skipping {server_name}")
                    all_successful = False
                    continue
            
            # Step 2: Stop container if running or force restart
            if container_running or force_restart:
                print(f"   🛑 Stopping container...")
                if not self.stop_docker_service(config):
                    logger.error(f"Failed to stop {server_name}, skipping")
                    all_successful = False
                    continue
            
            # Step 3: Update environment file (only if needed)
            if needs_user_id_update:
                print(f"   📝 Updating USER_ID to '{self.system_user_id}'...")
                if not self.update_env_file_user_id(env_file_path, self.system_user_id):
                    logger.error(f"Failed to update {env_file_path}")
                    all_successful = False
                    continue
            else:
                print(f"   ✅ USER_ID already consistent - no update needed")
            
            # Step 4: Start container if it was running or force restart
            if container_running or force_restart:
                print(f"   🚀 Starting container...")
                if not self.start_docker_service(config):
                    logger.error(f"Failed to start {server_name}")
                    all_successful = False
                    continue
            
            action_type = "synchronized" if needs_user_id_update else "restarted"
            print(f"   {Colors.GREEN}✅ {server_name} {action_type} successfully{Colors.NC}")
        
        # Final consistency check
        print(f"\n{Colors.BLUE}🔍 Final Consistency Check{Colors.NC}")
        final_results = self.check_user_id_consistency()
        
        all_consistent = all(result['consistent'] for result in final_results.values())
        
        if all_consistent:
            print(f"\n{Colors.GREEN}🎉 USER_ID synchronization completed successfully!{Colors.NC}")
            print(f"{Colors.GREEN}All Docker servers now use USER_ID: {self.system_user_id}{Colors.NC}")
        else:
            print(f"\n{Colors.RED}❌ Some inconsistencies remain. Check the logs above.{Colors.NC}")
            all_successful = False
        
        return all_successful

    def validate_system_consistency(self) -> bool:
        """Perform comprehensive validation of USER_ID consistency.
        
        Returns:
            True if system is fully consistent, False otherwise
        """
        print(f"\n{Colors.WHITE}🔍 COMPREHENSIVE USER_ID VALIDATION{Colors.NC}")
        print("=" * 60)
        
        # Check Docker configurations
        consistency_results = self.check_user_id_consistency()
        docker_consistent = all(result['consistent'] for result in consistency_results.values())
        
        # Check storage directories
        print(f"\n{Colors.BLUE}📁 Storage Directory Validation{Colors.NC}")
        try:
            from ...config.settings import (
                AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR,
                LIGHTRAG_STORAGE_DIR, LIGHTRAG_MEMORY_STORAGE_DIR
            )
            
            storage_paths = {
                'AGNO_STORAGE_DIR': AGNO_STORAGE_DIR,
                'AGNO_KNOWLEDGE_DIR': AGNO_KNOWLEDGE_DIR,
                'LIGHTRAG_STORAGE_DIR': LIGHTRAG_STORAGE_DIR,
                'LIGHTRAG_MEMORY_STORAGE_DIR': LIGHTRAG_MEMORY_STORAGE_DIR,
            }
            
            storage_consistent = True
            for name, path in storage_paths.items():
                contains_user_id = self.system_user_id in str(path)
                icon = f"{Colors.GREEN}✅" if contains_user_id else f"{Colors.RED}❌"
                print(f"   {icon} {name}: {path}{Colors.NC}")
                if not contains_user_id:
                    storage_consistent = False
                    
        except ImportError:
            print(f"   {Colors.YELLOW}⚠️  Could not validate storage directories (import error){Colors.NC}")
            storage_consistent = True  # Don't fail validation for import issues
        
        # Overall result
        overall_consistent = docker_consistent and storage_consistent
        
        print(f"\n{Colors.WHITE}📊 VALIDATION SUMMARY{Colors.NC}")
        print("=" * 40)
        docker_icon = f"{Colors.GREEN}✅" if docker_consistent else f"{Colors.RED}❌"
        storage_icon = f"{Colors.GREEN}✅" if storage_consistent else f"{Colors.RED}❌"
        overall_icon = f"{Colors.GREEN}✅" if overall_consistent else f"{Colors.RED}❌"
        
        print(f"   {docker_icon} Docker Configurations: {'Consistent' if docker_consistent else 'Inconsistent'}{Colors.NC}")
        print(f"   {storage_icon} Storage Directories: {'Consistent' if storage_consistent else 'Inconsistent'}{Colors.NC}")
        print(f"   {overall_icon} Overall System: {'Consistent' if overall_consistent else 'Inconsistent'}{Colors.NC}")
        
        return overall_consistent
