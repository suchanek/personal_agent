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
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


# ANSI color codes for output
class Colors:
    """ANSI color codes for terminal output formatting."""
    
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    NC = "\033[0m"  # No Color
    
    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text with automatic reset."""
        return f"{color}{text}{cls.NC}"


class DockerUserSync:
    """Manages USER_ID synchronization between system and Docker containers."""

    def __init__(self, dry_run: bool = False):
        """Initialize the Docker User Sync manager.

        Args:
            dry_run: If True, show what would be done without making changes
            
        Raises:
            ValueError: If system_user_id cannot be determined
        """
        from ..persag_manager import get_persag_manager
        
        self.dry_run = dry_run
        self.persag_manager = get_persag_manager()
        
        # Get system user ID from ~/.persag
        self.system_user_id = self.persag_manager.get_userid()
        if not self.system_user_id:
            raise ValueError("Could not determine system USER_ID from ~/.persag")

        # Docker server configurations - now using ~/.persag paths
        self.docker_configs = self.persag_manager.get_docker_config()

        # Backup directory in ~/.persag
        self.backup_dir = self.persag_manager.persag_dir / "backups" / "docker_env_backups"
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Failed to create backup directory %s: %s", self.backup_dir, e)
            raise ValueError(f"Cannot create backup directory: {e}")

        logger.info("Initialized DockerUserSync with ~/.persag")
        logger.info("System USER_ID: %s", self.system_user_id)
        logger.info("Dry run mode: %s", self.dry_run)

        # Diagnostic logging for path validation
        for server_name, config in self.docker_configs.items():
            env_file_path = config["dir"] / config["env_file"]
            logger.info(
                "Docker config %s: env_file_path = %s", server_name, env_file_path
            )
            logger.info(
                "Docker config %s: exists = %s", server_name, env_file_path.exists()
            )

    def _get_system_user_id(self) -> Optional[str]:
        """Get system USER_ID from ~/.persag (override parent method)"""
        return self.persag_manager.get_userid()

    def _is_valid_user_id(self, user_id: str) -> bool:
        """Validate USER_ID format.
        
        Args:
            user_id: The USER_ID string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not user_id or not isinstance(user_id, str):
            return False
        
        # Remove quotes if present
        user_id = user_id.strip('\'"')
        
        # Basic validation: non-empty, reasonable length, no dangerous characters
        if not user_id or len(user_id) > 100:
            return False
            
        # Check for potentially dangerous characters
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '{', '}', '[', ']']
        if any(char in user_id for char in dangerous_chars):
            return False
            
        return True

    def get_env_file_user_id(self, env_file_path: Path) -> Optional[str]:
        """Extract USER_ID from an environment file.

        Args:
            env_file_path: Path to the environment file

        Returns:
            USER_ID value or None if not found or invalid
            
        Raises:
            ValueError: If env_file_path is not a Path object
        """
        if not isinstance(env_file_path, Path):
            raise ValueError(f"env_file_path must be a Path object, got {type(env_file_path)}")
            
        if not env_file_path.exists():
            logger.warning("Environment file not found: %s", env_file_path)
            return None

        try:
            with open(env_file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line.startswith("USER_ID=") and not line.startswith("#"):
                        user_id = line.split("=", 1)[1].strip()
                        # Validate USER_ID format
                        if self._is_valid_user_id(user_id):
                            return user_id
                        else:
                            logger.warning("Invalid USER_ID format at line %d in %s: %s",
                                         line_num, env_file_path, user_id)
                            return None
            return None
        except (OSError, UnicodeDecodeError) as e:
            logger.error("Error reading %s: %s", env_file_path, e)
            return None
        except Exception as e:
            logger.error("Unexpected error reading %s: %s", env_file_path, e)
            return None

    def update_env_file_user_id(self, env_file_path: Path, new_user_id: str) -> bool:
        """Update USER_ID in an environment file.

        Args:
            env_file_path: Path to the environment file
            new_user_id: New USER_ID value to set

        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not isinstance(env_file_path, Path):
            raise ValueError(f"env_file_path must be a Path object, got {type(env_file_path)}")
        
        if not isinstance(new_user_id, str):
            raise ValueError(f"new_user_id must be a string, got {type(new_user_id)}")
            
        if not self._is_valid_user_id(new_user_id):
            raise ValueError(f"Invalid USER_ID format: {new_user_id}")

        if not env_file_path.exists():
            logger.error("Environment file not found: %s", env_file_path)
            return False

        if self.dry_run:
            logger.info(
                "[DRY RUN] Would update USER_ID to '%s' in %s",
                new_user_id,
                env_file_path,
            )
            return True

        try:
            # Read current content
            with open(env_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Update USER_ID line
            updated = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("USER_ID=") and not stripped.startswith("#"):
                    lines[i] = f"USER_ID={new_user_id}\n"
                    updated = True
                    break

            if not updated:
                # Add USER_ID if not found
                lines.append(f"\n# User configuration\nUSER_ID={new_user_id}\n")
                logger.info("Added USER_ID=%s to %s", new_user_id, env_file_path)

            # Write updated content atomically
            temp_path = env_file_path.with_suffix(f"{env_file_path.suffix}.tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            # Atomic move
            temp_path.replace(env_file_path)

            logger.info("Updated USER_ID to '%s' in %s", new_user_id, env_file_path)
            return True

        except (OSError, UnicodeDecodeError) as e:
            logger.error("Error updating %s: %s", env_file_path, e)
            return False
        except Exception as e:
            logger.error("Unexpected error updating %s: %s", env_file_path, e)
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
            logger.warning("Cannot backup non-existent file: %s", env_file_path)
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{server_name}_{env_file_path.name}_{timestamp}.backup"
        backup_path = self.backup_dir / backup_filename

        if self.dry_run:
            logger.info("[DRY RUN] Would backup %s to %s", env_file_path, backup_path)
            return backup_path

        try:
            # Ensure backup directory exists
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(env_file_path, backup_path)
            logger.info("Backed up %s to %s", env_file_path, backup_path)
            return backup_path
        except Exception as e:
            logger.error("Error backing up %s: %s", env_file_path, e)
            return None

    def is_container_running(self, container_name: str) -> bool:
        """Check if a Docker container is running.

        Args:
            container_name: Name of the container to check

        Returns:
            True if container is running, False otherwise
            
        Raises:
            ValueError: If container_name is invalid
        """
        if not isinstance(container_name, str):
            raise ValueError(f"container_name must be a string, got {type(container_name)}")
            
        if not container_name or not container_name.strip():
            raise ValueError("container_name cannot be empty or whitespace-only")
            
        container_name = container_name.strip()
        
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name=^{container_name}$",  # Exact match to avoid partial matches
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,  # Add timeout to prevent hanging
            )
            # Check for exact match in output
            running_containers = result.stdout.strip().split('\n')
            return container_name in running_containers
        except subprocess.TimeoutExpired:
            logger.error("Timeout checking container status for %s", container_name)
            return False
        except subprocess.CalledProcessError as e:
            logger.warning("Docker command failed for %s: %s", container_name, e.stderr)
            return False
        except Exception as e:
            logger.error("Unexpected error checking container %s: %s", container_name, e)
            return False

    def stop_docker_service(self, server_config: Dict) -> bool:
        """Stop a Docker service using docker-compose.

        Args:
            server_config: Configuration dictionary for the server

        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If server_config is invalid
        """
        if not isinstance(server_config, dict):
            raise ValueError(f"server_config must be a dictionary, got {type(server_config)}")
            
        required_keys = ["dir", "compose_file"]
        missing_keys = [key for key in required_keys if key not in server_config]
        if missing_keys:
            raise ValueError(f"server_config missing required keys: {missing_keys}")

        server_dir = Path(server_config["dir"])
        compose_file = server_config["compose_file"]
        compose_path = server_dir / compose_file

        # Check if server directory exists
        if not server_dir.exists():
            logger.error("Server directory does not exist: %s", server_dir)
            return False
            
        # Check if compose file exists
        if not compose_path.exists():
            logger.error("Docker compose file does not exist: %s", compose_path)
            return False

        if self.dry_run:
            logger.info("[DRY RUN] Would stop Docker service in %s", server_dir)
            return True

        try:
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "down", "--timeout", "30"],
                cwd=server_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,  # Overall timeout
            )
            logger.info("Stopped Docker service in %s", server_dir)
            logger.debug("Docker compose down output: %s", result.stdout)
            return True
        except subprocess.TimeoutExpired:
            logger.error("Timeout stopping Docker service in %s", server_dir)
            return False
        except subprocess.CalledProcessError as e:
            logger.error(
                "Error stopping Docker service in %s: %s", server_dir, e.stderr
            )
            return False
        except Exception as e:
            logger.error("Unexpected error stopping Docker service in %s: %s", server_dir, e)
            return False

    def start_docker_service(self, server_config: Dict) -> bool:
        """Start a Docker service using docker-compose.

        Args:
            server_config: Configuration dictionary for the server

        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If server_config is invalid
        """
        if not isinstance(server_config, dict):
            raise ValueError(f"server_config must be a dictionary, got {type(server_config)}")
            
        required_keys = ["dir", "compose_file"]
        missing_keys = [key for key in required_keys if key not in server_config]
        if missing_keys:
            raise ValueError(f"server_config missing required keys: {missing_keys}")

        server_dir = Path(server_config["dir"])
        compose_file = server_config["compose_file"]
        compose_path = server_dir / compose_file

        # Check if server directory exists
        if not server_dir.exists():
            logger.error("Server directory does not exist: %s", server_dir)
            return False
            
        # Check if compose file exists
        if not compose_path.exists():
            logger.error("Docker compose file does not exist: %s", compose_path)
            return False

        if self.dry_run:
            logger.info("[DRY RUN] Would start Docker service in %s", server_dir)
            return True

        try:
            # Get the environment file path and read the environment variables
            env_file_path = server_dir / server_config.get("env_file", ".env")
            docker_env = os.environ.copy()
            
            # Read environment variables from the env file and add them to the environment
            if env_file_path.exists():
                try:
                    with open(env_file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, value = line.split("=", 1)
                                key = key.strip()
                                value = value.strip().strip('\'"')
                                
                                # Remove inline comments from the value
                                if "#" in value:
                                    value = value.split("#")[0].strip()
                                
                                # Handle variable expansion for AGNO_STORAGE_DIR
                                if "${" in value:
                                    # Simple variable expansion for common patterns
                                    import re
                                    def expand_var(match):
                                        var_name = match.group(1)
                                        return docker_env.get(var_name, "")
                                    value = re.sub(r'\$\{([^}]+)\}', expand_var, value)
                                
                                docker_env[key] = value
                                logger.debug("Set environment variable %s=%s", key, value)
                except Exception as e:
                    logger.warning("Error reading environment file %s: %s", env_file_path, e)
            
            # Ensure critical environment variables are set
            if "AGNO_STORAGE_DIR" not in docker_env or not docker_env["AGNO_STORAGE_DIR"]:
                logger.error("AGNO_STORAGE_DIR not set in environment - Docker mount will fail")
                return False
            
            logger.info("Starting Docker service with AGNO_STORAGE_DIR=%s", docker_env.get("AGNO_STORAGE_DIR"))
            
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d", "--wait"],
                cwd=server_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=120,  # Longer timeout for startup
                env=docker_env,  # Pass the environment variables
            )
            logger.info("Started Docker service in %s", server_dir)
            logger.debug("Docker compose up output: %s", result.stdout)
            return True
        except subprocess.TimeoutExpired:
            logger.error("Timeout starting Docker service in %s", server_dir)
            return False
        except subprocess.CalledProcessError as e:
            logger.error(
                "Error starting Docker service in %s: %s", server_dir, e.stderr
            )
            return False
        except Exception as e:
            logger.error("Unexpected error starting Docker service in %s: %s", server_dir, e)
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
            env_file_path = config["dir"] / config["env_file"]
            docker_user_id = self.get_env_file_user_id(env_file_path)
            is_running = self.is_container_running(config["container_name"])

            consistent = docker_user_id == self.system_user_id

            results[server_name] = {
                "env_file_path": env_file_path,
                "docker_user_id": docker_user_id,
                "system_user_id": self.system_user_id,
                "consistent": consistent,
                "container_running": is_running,
                "config": config,
            }

            # Display results
            status_icon = f"{Colors.GREEN}✅" if consistent else f"{Colors.RED}❌"
            running_icon = f"{Colors.GREEN}🟢" if is_running else f"{Colors.YELLOW}🟡"

            print(f"{status_icon} {server_name}:{Colors.NC}")
            print(f"   Docker USER_ID: {docker_user_id or 'NOT FOUND'}")
            print(
                f"   Container: {running_icon} {'Running' if is_running else 'Stopped'}{Colors.NC}"
            )
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
            if not result["consistent"]:
                servers_to_update.append(server_name)

        # If force_restart is True, we need to process all servers even if consistent
        if force_restart:
            servers_to_process = list(consistency_results.keys())
            if not servers_to_update:
                print(
                    f"{Colors.GREEN}✅ All USER_IDs are already consistent!{Colors.NC}"
                )
                print(
                    f"{Colors.YELLOW}🔄 Force restart requested - processing all servers...{Colors.NC}"
                )
            else:
                print(
                    f"{Colors.YELLOW}📝 Servers requiring USER_ID updates: {', '.join(servers_to_update)}{Colors.NC}"
                )
                print(
                    f"{Colors.YELLOW}🔄 Force restart requested - processing all servers...{Colors.NC}"
                )
        else:
            servers_to_process = servers_to_update
            if not servers_to_update:
                print(
                    f"{Colors.GREEN}✅ All USER_IDs are already consistent!{Colors.NC}"
                )
                return True
            print(
                f"{Colors.YELLOW}📝 Servers requiring USER_ID updates: {', '.join(servers_to_update)}{Colors.NC}"
            )

        # Process each server
        all_successful = True

        for server_name in servers_to_process:
            result = consistency_results[server_name]
            config = result["config"]
            env_file_path = result["env_file_path"]
            container_running = result["container_running"]
            needs_user_id_update = not result["consistent"]

            print(f"\n{Colors.CYAN}🔧 Processing {server_name}...{Colors.NC}")

            # Step 1: Backup current environment file (only if we're updating it)
            if needs_user_id_update:
                backup_path = self.backup_env_file(env_file_path, server_name)
                if not backup_path and not self.dry_run:
                    logger.error(
                        "Failed to backup %s, skipping %s", env_file_path, server_name
                    )
                    all_successful = False
                    continue

            # Step 2: Stop container if running or force restart
            if container_running or force_restart:
                print(f"   🛑 Stopping container...")
                if not self.stop_docker_service(config):
                    logger.error("Failed to stop %s, skipping", server_name)
                    all_successful = False
                    continue

            # Step 3: Update environment file (only if needed)
            if needs_user_id_update:
                print(f"   📝 Updating USER_ID to '{self.system_user_id}'...")
                if not self.update_env_file_user_id(env_file_path, self.system_user_id):
                    logger.error("Failed to update %s", env_file_path)
                    all_successful = False
                    continue
            else:
                print(f"   ✅ USER_ID already consistent - no update needed")

            # Step 4: Start container if it was running or force restart
            if container_running or force_restart:
                print(f"   🚀 Starting container...")
                if not self.start_docker_service(config):
                    logger.error("Failed to start %s", server_name)
                    all_successful = False
                    continue

            action_type = "synchronized" if needs_user_id_update else "restarted"
            print(
                f"   {Colors.GREEN}✅ {server_name} {action_type} successfully{Colors.NC}"
            )

        # Final consistency check
        print(f"\n{Colors.BLUE}🔍 Final Consistency Check{Colors.NC}")
        final_results = self.check_user_id_consistency()

        all_consistent = all(result["consistent"] for result in final_results.values())

        if all_consistent:
            print(
                f"\n{Colors.GREEN}🎉 USER_ID synchronization completed successfully!{Colors.NC}"
            )
            print(
                f"{Colors.GREEN}All Docker servers now use USER_ID: {self.system_user_id}{Colors.NC}"
            )
        else:
            print(
                f"\n{Colors.RED}❌ Some inconsistencies remain. Check the logs above.{Colors.NC}"
            )
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
        docker_consistent = all(
            result["consistent"] for result in consistency_results.values()
        )

        # Check storage directories
        print(f"\n{Colors.BLUE}📁 Storage Directory Validation{Colors.NC}")
        try:
            from ...config.settings import (
                AGNO_KNOWLEDGE_DIR,
                AGNO_STORAGE_DIR,
                LIGHTRAG_MEMORY_STORAGE_DIR,
                LIGHTRAG_STORAGE_DIR,
            )

            storage_paths = {
                "AGNO_STORAGE_DIR": AGNO_STORAGE_DIR,
                "AGNO_KNOWLEDGE_DIR": AGNO_KNOWLEDGE_DIR,
                "LIGHTRAG_STORAGE_DIR": LIGHTRAG_STORAGE_DIR,
                "LIGHTRAG_MEMORY_STORAGE_DIR": LIGHTRAG_MEMORY_STORAGE_DIR,
            }

            storage_consistent = True
            for name, path in storage_paths.items():
                contains_user_id = self.system_user_id in str(path)
                icon = f"{Colors.GREEN}✅" if contains_user_id else f"{Colors.RED}❌"
                print(f"   {icon} {name}: {path}{Colors.NC}")
                if not contains_user_id:
                    storage_consistent = False

        except ImportError:
            print(
                f"   {Colors.YELLOW}⚠️  Could not validate storage directories (import error){Colors.NC}"
            )
            storage_consistent = True  # Don't fail validation for import issues

        # Overall result
        overall_consistent = docker_consistent and storage_consistent

        print(f"\n{Colors.WHITE}📊 VALIDATION SUMMARY{Colors.NC}")
        print("=" * 40)
        docker_icon = f"{Colors.GREEN}✅" if docker_consistent else f"{Colors.RED}❌"
        storage_icon = f"{Colors.GREEN}✅" if storage_consistent else f"{Colors.RED}❌"
        overall_icon = f"{Colors.GREEN}✅" if overall_consistent else f"{Colors.RED}❌"

        print(
            f"   {docker_icon} Docker Configurations: {'Consistent' if docker_consistent else 'Inconsistent'}{Colors.NC}"
        )
        print(
            f"   {storage_icon} Storage Directories: {'Consistent' if storage_consistent else 'Inconsistent'}{Colors.NC}"
        )
        print(
            f"   {overall_icon} Overall System: {'Consistent' if overall_consistent else 'Inconsistent'}{Colors.NC}"
        )

        return overall_consistent
