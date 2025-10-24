"""
LightRAG Manager

Python implementation of LightRAG Docker service management,
incorporating the functionality of restart-lightrag.sh directly.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class LightRAGManager:
    """Manages LightRAG Docker services with Python implementation of restart-lightrag.sh."""

    def __init__(self, project_root: str = None):
        """
        Initialize the LightRAG manager.

        Args:
            project_root: Project root directory (deprecated, now uses PERSAG_HOME)
        """
        # Import settings to get the correct PERSAG_HOME-based paths
        from personal_agent.config.settings import (
            LIGHTRAG_MEMORY_DIR,
            LIGHTRAG_SERVER_DIR,
        )

        # Use the centralized configuration paths from PERSAG_HOME
        self.lightrag_server_dir = Path(LIGHTRAG_SERVER_DIR)
        self.lightrag_memory_dir = Path(LIGHTRAG_MEMORY_DIR)

        # Keep project_root for backward compatibility, but it's no longer used for docker paths
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def update_docker_compose_user_id(self, user_id: str) -> Dict[str, Any]:
        """
        Update USER_ID in docker-compose .env files and docker-compose.yml files.

        Args:
            user_id: User ID to set in environment files

        Returns:
            Dictionary with operation results
        """
        results = {"success": True, "updated_files": [], "errors": []}

        # List of directories to update
        directories = [
            ("lightrag_server", self.lightrag_server_dir),
            ("lightrag_memory_server", self.lightrag_memory_dir),
        ]

        for dir_name, dir_path in directories:
            if not dir_path.exists():
                results["errors"].append(
                    f"Directory {dir_name} not found at {dir_path}"
                )
                continue

            # Update .env file
            env_file = dir_path / ".env"

            try:
                # Read existing .env file or create new one
                env_lines = []
                user_id_found = False

                if env_file.exists():
                    with open(env_file, "r") as f:
                        for line in f:
                            if line.startswith("USER_ID="):
                                env_lines.append(f"USER_ID={user_id}\n")
                                user_id_found = True
                            else:
                                env_lines.append(line)

                # Add USER_ID if not found
                if not user_id_found:
                    env_lines.append(f"USER_ID={user_id}\n")

                # Write updated .env file
                with open(env_file, "w") as f:
                    f.writelines(env_lines)

                results["updated_files"].append(str(env_file))

            except Exception as e:
                results["errors"].append(f"Error updating {env_file}: {str(e)}")
                results["success"] = False
                continue

            # Update docker-compose.yml to ensure USER_ID is passed as environment variable
            docker_compose_file = dir_path / "docker-compose.yml"

            try:
                if docker_compose_file.exists():
                    with open(docker_compose_file, "r") as f:
                        content = f.read()

                    # Parse and update USER_ID in docker-compose.yml properly
                    lines = content.split("\n")
                    new_lines = []
                    in_environment_section = False
                    user_id_updated = False

                    for line in lines:
                        if "environment:" in line and not line.strip().startswith("#"):
                            in_environment_section = True
                            new_lines.append(line)
                        elif in_environment_section and line.strip().startswith(
                            "- USER_ID="
                        ):
                            # Replace existing USER_ID line
                            new_lines.append(f"      - USER_ID={user_id}")
                            user_id_updated = True
                        elif in_environment_section and line.startswith("      - "):
                            # Other environment variables
                            new_lines.append(line)
                        elif (
                            in_environment_section
                            and not line.startswith("      ")
                            and line.strip()
                        ):
                            # End of environment section
                            if not user_id_updated:
                                # Add USER_ID if it wasn't found
                                new_lines.insert(-1, f"      - USER_ID={user_id}")
                            in_environment_section = False
                            new_lines.append(line)
                        else:
                            new_lines.append(line)

                    # If we're still in environment section at end of file and USER_ID wasn't updated
                    if in_environment_section and not user_id_updated:
                        new_lines.append(f"      - USER_ID={user_id}")

                    # Write updated docker-compose.yml
                    with open(docker_compose_file, "w") as f:
                        f.write("\n".join(new_lines))

                    results["updated_files"].append(str(docker_compose_file))

            except Exception as e:
                results["errors"].append(
                    f"Error updating {docker_compose_file}: {str(e)}"
                )
                # Don't fail the whole operation for docker-compose.yml issues

        return results

    def restart_lightrag_services(self, user_id: str = None) -> Dict[str, Any]:
        """
        Restart LightRAG services with smart restart logic to handle port conflicts.
        Implements the same logic as smart-restart-lightrag.sh.

        Args:
            user_id: User ID to set (optional, uses current USER_ID if not provided)

        Returns:
            Dictionary with operation results
        """
        if user_id is None:
            from personal_agent.config import get_userid

            user_id = get_userid()

        results = {
            "success": True,
            "user_id": user_id,
            "services_restarted": [],
            "errors": [],
            "status": {},
        }

        # Update USER_ID in docker-compose files
        update_result = self.update_docker_compose_user_id(user_id)
        if not update_result["success"]:
            results["errors"].extend(update_result["errors"])
            results["success"] = False
            return results

        # Smart restart services with port conflict handling
        services = [
            (
                "lightrag_server",
                self.lightrag_server_dir,
                os.getenv("LIGHTRAG_SERVER_PORT", 9621),
            ),
            (
                "lightrag_memory_server",
                self.lightrag_memory_dir,
                os.getenv("LIGHTRAG_MEMORY_PORT", 9622),
            ),
        ]

        # Step 1: Smart stop all services
        for dir_name, dir_path, port in services:
            if not dir_path.exists():
                results["errors"].append(f"Directory {dir_name} not found")
                continue

            try:
                original_cwd = os.getcwd()
                os.chdir(dir_path)

                # Graceful shutdown
                stop_result = subprocess.run(
                    ["docker-compose", "down"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if stop_result.returncode != 0:
                    results["errors"].append(
                        f"Failed to stop {dir_name}: {stop_result.stderr}"
                    )
                    results["success"] = False
                else:
                    # Wait for port to be released
                    self._wait_for_port_release(port, timeout=30)

                os.chdir(original_cwd)

            except Exception as e:
                results["errors"].append(f"Error stopping {dir_name}: {str(e)}")
                results["success"] = False
            finally:
                try:
                    os.chdir(original_cwd)
                except:
                    pass

        # Step 2: Wait for complete cleanup
        time.sleep(5)

        # Step 3: Clean up Docker networks
        try:
            subprocess.run(
                ["docker", "network", "prune", "-f"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception:
            # Network cleanup is optional
            pass

        # Step 4: Smart start all services
        for dir_name, dir_path, port in services:
            if not dir_path.exists():
                continue

            try:
                original_cwd = os.getcwd()
                os.chdir(dir_path)

                # Verify port is available before starting
                if not self._is_port_available(port):
                    results["errors"].append(
                        f"Port {port} is still in use for {dir_name}"
                    )
                    results["success"] = False
                    continue

                # Start service with retries
                for attempt in range(3):
                    start_result = subprocess.run(
                        ["docker-compose", "up", "-d"],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )

                    if start_result.returncode == 0:
                        # Wait for service to initialize
                        time.sleep(3)

                        # Verify container is running
                        if self._is_container_running(dir_name):
                            results["services_restarted"].append(dir_name)
                            break
                        else:
                            if attempt < 2:  # Not the last attempt
                                time.sleep(2)
                                continue
                            else:
                                results["errors"].append(
                                    f"Container for {dir_name} failed to start properly"
                                )
                                results["success"] = False
                    else:
                        if "port is already allocated" in start_result.stderr.lower():
                            # Port conflict - wait and retry
                            if attempt < 2:
                                time.sleep(5)
                                continue

                        results["errors"].append(
                            f"Failed to start {dir_name}: {start_result.stderr}"
                        )
                        results["success"] = False
                        break

                os.chdir(original_cwd)

            except Exception as e:
                results["errors"].append(f"Error starting {dir_name}: {str(e)}")
                results["success"] = False
            finally:
                try:
                    os.chdir(original_cwd)
                except:
                    pass

        # Get final service status
        if results["services_restarted"]:
            time.sleep(2)
            results["status"] = self.get_service_status()

        return results

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                return result != 0  # Port is available if connection fails
        except Exception:
            return True  # Assume available if we can't check

    def _wait_for_port_release(self, port: int, timeout: int = 30) -> bool:
        """Wait for a port to be released."""
        import socket

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", port))
                    if result != 0:  # Port is available
                        return True
            except Exception:
                return True  # Assume available if we can't check

            time.sleep(1)

        return False  # Timeout reached

    def _is_container_running(self, service_name: str) -> bool:
        """Check if a container is running."""
        try:
            # Map service names to container names
            container_map = {
                "lightrag_server": "lightrag_pagent",
                "lightrag_memory_server": "lightrag_memory",
            }

            container_name = container_map.get(service_name, service_name)

            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={container_name}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            return container_name in result.stdout

        except Exception:
            return False

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current docker-compose service status.
        Equivalent to: docker-compose ps

        Returns:
            Dictionary with service status information
        """
        status = {
            "lightrag_server": {},
            "lightrag_memory_server": {},
            "ollama_config": {},
        }

        # Check status for both directories
        directories = [
            ("lightrag_server", self.lightrag_server_dir),
            ("lightrag_memory_server", self.lightrag_memory_dir),
        ]

        for dir_name, dir_path in directories:
            if not dir_path.exists():
                status[dir_name] = {"error": "Directory not found"}
                continue

            try:
                original_cwd = os.getcwd()
                os.chdir(dir_path)

                # Get docker-compose status
                ps_result = subprocess.run(
                    ["docker-compose", "ps", "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if ps_result.returncode == 0:
                    try:
                        import json

                        services = (
                            json.loads(ps_result.stdout)
                            if ps_result.stdout.strip()
                            else []
                        )
                        status[dir_name] = {
                            "services": services,
                            "running": len(
                                [s for s in services if s.get("State") == "running"]
                            ),
                        }
                    except json.JSONDecodeError:
                        # Fallback to simple text parsing
                        status[dir_name] = {
                            "output": ps_result.stdout,
                            "running": "running" in ps_result.stdout.lower(),
                        }
                else:
                    status[dir_name] = {"error": ps_result.stderr}

                # Get Ollama configuration for lightrag_server
                if dir_name == "lightrag_server":
                    env_file = dir_path / ".env"
                    if env_file.exists():
                        try:
                            with open(env_file, "r") as f:
                                for line in f:
                                    if line.startswith("OLLAMA_URL="):
                                        ollama_url = line.split("=", 1)[1].strip()
                                        status["ollama_config"]["url"] = ollama_url

                                        # Determine mode
                                        if "host.docker.internal" in ollama_url:
                                            status["ollama_config"]["mode"] = "LOCAL"
                                        elif "100.100.248.61" in ollama_url:
                                            status["ollama_config"]["mode"] = "REMOTE"
                                        else:
                                            status["ollama_config"]["mode"] = "CUSTOM"
                                        break
                        except Exception as e:
                            status["ollama_config"]["error"] = str(e)

                os.chdir(original_cwd)

            except subprocess.TimeoutExpired:
                status[dir_name] = {"error": "Timeout getting status"}
            except Exception as e:
                status[dir_name] = {"error": str(e)}
            finally:
                try:
                    os.chdir(original_cwd)
                except:
                    pass

        return status

    def stop_services(self) -> Dict[str, Any]:
        """
        Stop all LightRAG services.

        Returns:
            Dictionary with operation results
        """
        results = {"success": True, "services_stopped": [], "errors": []}

        directories = [
            ("lightrag_server", self.lightrag_server_dir),
            ("lightrag_memory_server", self.lightrag_memory_dir),
        ]

        for dir_name, dir_path in directories:
            if not dir_path.exists():
                continue

            try:
                original_cwd = os.getcwd()
                os.chdir(dir_path)

                stop_result = subprocess.run(
                    ["docker-compose", "down"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if stop_result.returncode == 0:
                    results["services_stopped"].append(dir_name)
                else:
                    results["errors"].append(
                        f"Failed to stop {dir_name}: {stop_result.stderr}"
                    )
                    results["success"] = False

                os.chdir(original_cwd)

            except Exception as e:
                results["errors"].append(f"Error stopping {dir_name}: {str(e)}")
                results["success"] = False
            finally:
                try:
                    os.chdir(original_cwd)
                except:
                    pass

        return results

    def start_services(self, user_id: str = None) -> Dict[str, Any]:
        """
        Start all LightRAG services.

        Args:
            user_id: User ID to set before starting (optional)

        Returns:
            Dictionary with operation results
        """
        results = {"success": True, "services_started": [], "errors": []}

        # Update USER_ID if provided
        if user_id:
            update_result = self.update_docker_compose_user_id(user_id)
            if not update_result["success"]:
                results["errors"].extend(update_result["errors"])
                results["success"] = False
                return results

        directories = [
            ("lightrag_server", self.lightrag_server_dir),
            ("lightrag_memory_server", self.lightrag_memory_dir),
        ]

        for dir_name, dir_path in directories:
            if not dir_path.exists():
                continue

            try:
                original_cwd = os.getcwd()
                os.chdir(dir_path)

                start_result = subprocess.run(
                    ["docker-compose", "up", "-d"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if start_result.returncode == 0:
                    results["services_started"].append(dir_name)
                else:
                    results["errors"].append(
                        f"Failed to start {dir_name}: {start_result.stderr}"
                    )
                    results["success"] = False

                os.chdir(original_cwd)

            except Exception as e:
                results["errors"].append(f"Error starting {dir_name}: {str(e)}")
                results["success"] = False
            finally:
                try:
                    os.chdir(original_cwd)
                except:
                    pass

        return results
