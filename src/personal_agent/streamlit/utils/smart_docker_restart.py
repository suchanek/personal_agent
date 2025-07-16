"""
Smart Docker Restart Utilities

Provides intelligent Docker restart functionality with proper port cleanup,
waiting periods, and error handling to prevent "port already allocated" errors.

Author: Personal Agent Development Team
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import docker
import streamlit as st

# Import project modules
from personal_agent.core.docker_integration import DockerIntegrationManager
from personal_agent.streamlit.utils.docker_utils import get_docker_client


class SmartDockerRestart:
    """Handles intelligent Docker container restarts with proper cleanup."""

    def __init__(self):
        """Initialize the smart restart manager."""
        self.client = get_docker_client()
        self.docker_integration = DockerIntegrationManager()

        # Use the same approach as DockerIntegrationManager for base directory
        self.base_dir = Path(__file__).parent.parent.parent.parent.parent

        # Configuration for different services
        self.service_configs = {
            "lightrag_server": {
                "directory": "lightrag_server",
                "container_name": "lightrag_pagent",
                "ports": [9621],
                "wait_time": 10,
                "max_retries": 3,
            },
            "lightrag_memory_server": {
                "directory": "lightrag_memory_server",
                "container_name": "lightrag_memory",
                "ports": [9622],
                "wait_time": 15,  # Memory server needs more time
                "max_retries": 3,
            },
        }

    def check_port_availability(self, port: int, timeout: int = 30) -> bool:
        """Check if a port is available (not in use).

        Args:
            port: Port number to check
            timeout: Maximum time to wait for port to become available

        Returns:
            True if port is available, False otherwise
        """
        import socket

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", port))
                    if result != 0:  # Port is not in use
                        return True
            except Exception:
                return True  # Assume available if we can't check

            time.sleep(1)

        return False

    def wait_for_container_stop(self, container_name: str, timeout: int = 30) -> bool:
        """Wait for a container to completely stop.

        Args:
            container_name: Name of the container
            timeout: Maximum time to wait

        Returns:
            True if container stopped, False if timeout
        """
        if not self.client:
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                container = self.client.containers.get(container_name)
                if container.status != "running":
                    return True
            except docker.errors.NotFound:
                # Container doesn't exist, consider it stopped
                return True
            except Exception:
                pass

            time.sleep(1)

        return False

    def force_kill_container(self, container_name: str) -> bool:
        """Force kill a container if it won't stop gracefully.

        Args:
            container_name: Name of the container to kill

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            container = self.client.containers.get(container_name)
            container.kill()
            st.warning(f"Force killed container: {container_name}")
            return True
        except docker.errors.NotFound:
            return True  # Already gone
        except Exception as e:
            st.error(f"Failed to force kill container {container_name}: {str(e)}")
            return False

    def cleanup_docker_networks(self) -> bool:
        """Clean up unused Docker networks.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "network", "prune", "-f"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            st.warning(f"Network cleanup failed: {e.stderr}")
            return False

    def smart_stop_service(self, service_name: str) -> Tuple[bool, str]:
        """Intelligently stop a Docker service with proper cleanup.

        Args:
            service_name: Name of the service to stop

        Returns:
            Tuple of (success, message)
        """
        if service_name not in self.service_configs:
            return False, f"Unknown service: {service_name}"

        config = self.service_configs[service_name]
        container_name = config["container_name"]
        ports = config["ports"]
        wait_time = config["wait_time"]

        try:
            # Step 1: Try graceful docker-compose down
            service_dir = self.base_dir / config["directory"]
            if not service_dir.exists():
                return False, f"Service directory not found: {service_dir}"

            st.info(f"Stopping {service_name} gracefully...")
            result = subprocess.run(
                ["docker-compose", "down"],
                cwd=service_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Step 2: Wait for container to stop
            if not self.wait_for_container_stop(container_name, timeout=15):
                st.warning(
                    f"Container {container_name} didn't stop gracefully, force killing..."
                )
                if not self.force_kill_container(container_name):
                    return False, f"Failed to stop container {container_name}"

            # Step 3: Wait for ports to be released
            st.info(f"Waiting for ports to be released...")
            for port in ports:
                if not self.check_port_availability(port, timeout=wait_time):
                    return False, f"Port {port} still in use after {wait_time} seconds"

            # Step 4: Clean up networks
            self.cleanup_docker_networks()

            return True, f"Successfully stopped {service_name}"

        except subprocess.TimeoutExpired:
            st.warning(
                f"Docker-compose down timed out for {service_name}, trying force kill..."
            )
            if self.force_kill_container(container_name):
                return True, f"Force stopped {service_name}"
            else:
                return False, f"Failed to stop {service_name}"
        except Exception as e:
            return False, f"Error stopping {service_name}: {str(e)}"

    def smart_start_service(self, service_name: str) -> Tuple[bool, str]:
        """Intelligently start a Docker service with proper verification.

        Args:
            service_name: Name of the service to start

        Returns:
            Tuple of (success, message)
        """
        if service_name not in self.service_configs:
            return False, f"Unknown service: {service_name}"

        config = self.service_configs[service_name]
        container_name = config["container_name"]
        ports = config["ports"]
        max_retries = config["max_retries"]

        try:
            service_dir = self.base_dir / config["directory"]
            if not service_dir.exists():
                return False, f"Service directory not found: {service_dir}"

            # Verify ports are available before starting
            for port in ports:
                if not self.check_port_availability(port, timeout=5):
                    return (
                        False,
                        f"Port {port} is still in use, cannot start {service_name}",
                    )

            # Try to start the service
            for attempt in range(max_retries):
                st.info(
                    f"Starting {service_name} (attempt {attempt + 1}/{max_retries})..."
                )

                result = subprocess.run(
                    ["docker-compose", "up", "-d"],
                    cwd=service_dir,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0:
                    # Wait a moment for the service to initialize
                    time.sleep(3)

                    # Verify the container is running
                    if self.client:
                        try:
                            container = self.client.containers.get(container_name)
                            if container.status == "running":
                                return True, f"Successfully started {service_name}"
                        except docker.errors.NotFound:
                            pass

                    # If we can't verify via Docker API, assume success if no error
                    return True, f"Started {service_name} (verification limited)"
                else:
                    st.warning(f"Attempt {attempt + 1} failed: {result.stderr}")
                    if attempt < max_retries - 1:
                        time.sleep(2)

            return False, f"Failed to start {service_name} after {max_retries} attempts"

        except subprocess.TimeoutExpired:
            return False, f"Timeout starting {service_name}"
        except Exception as e:
            return False, f"Error starting {service_name}: {str(e)}"

    def smart_restart_service(self, service_name: str) -> Tuple[bool, str]:
        """Perform a smart restart of a Docker service.

        Args:
            service_name: Name of the service to restart

        Returns:
            Tuple of (success, message)
        """
        st.info(f"🔄 Starting smart restart of {service_name}...")

        # Step 1: Smart stop
        stop_success, stop_message = self.smart_stop_service(service_name)
        if not stop_success:
            return False, f"Failed to stop service: {stop_message}"

        st.success(f"✅ {stop_message}")

        # Step 2: Additional wait time for cleanup
        config = self.service_configs.get(service_name, {})
        extra_wait = config.get("wait_time", 10) // 2
        st.info(f"⏳ Waiting {extra_wait} seconds for complete cleanup...")
        time.sleep(extra_wait)

        # Step 3: Smart start
        start_success, start_message = self.smart_start_service(service_name)
        if not start_success:
            return False, f"Failed to start service: {start_message}"

        st.success(f"✅ {start_message}")

        return True, f"Successfully restarted {service_name}"

    def smart_restart_all_services(self) -> Tuple[bool, str]:
        """Perform a smart restart of all configured services.

        Returns:
            Tuple of (success, message)
        """
        st.info("🔄 Starting smart restart of all services...")

        results = []

        # Stop all services first
        for service_name in self.service_configs.keys():
            stop_success, stop_message = self.smart_stop_service(service_name)
            results.append((service_name, "stop", stop_success, stop_message))
            if stop_success:
                st.success(f"✅ Stopped {service_name}")
            else:
                st.error(f"❌ Failed to stop {service_name}: {stop_message}")

        # Wait for all services to fully stop
        st.info("⏳ Waiting for all services to fully stop...")
        time.sleep(5)

        # Start all services
        for service_name in self.service_configs.keys():
            start_success, start_message = self.smart_start_service(service_name)
            results.append((service_name, "start", start_success, start_message))
            if start_success:
                st.success(f"✅ Started {service_name}")
            else:
                st.error(f"❌ Failed to start {service_name}: {start_message}")

        # Check overall success
        all_successful = all(success for _, _, success, _ in results)

        if all_successful:
            return True, "Successfully restarted all services"
        else:
            failed_operations = [
                f"{service} ({operation})"
                for service, operation, success, _ in results
                if not success
            ]
            return False, f"Some operations failed: {', '.join(failed_operations)}"


def get_smart_restart_manager() -> SmartDockerRestart:
    """Get a SmartDockerRestart instance.

    Returns:
        SmartDockerRestart instance
    """
    return SmartDockerRestart()
