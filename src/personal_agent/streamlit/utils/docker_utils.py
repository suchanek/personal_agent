"""
Docker Utilities

Utility functions for interacting with Docker containers.
"""

import os
import json
import docker
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import project modules
from personal_agent.core.docker_integration import DockerIntegrationManager


def get_docker_client():
    """Get a Docker client instance."""
    try:
        return docker.from_env()
    except Exception as e:
        st.error(f"Error connecting to Docker: {str(e)}")
        return None


def get_container_status(docker_integration: Optional[DockerIntegrationManager] = None) -> List[Dict[str, Any]]:
    """
    Get status information for all Docker containers.
    
    Args:
        docker_integration: Optional DockerIntegrationManager instance
        
    Returns:
        List of dictionaries containing container information
    """
    try:
        # Use provided DockerIntegrationManager or create a new one
        if docker_integration is None:
            docker_integration = DockerIntegrationManager()
        
        # Get Docker client
        client = get_docker_client()
        if not client:
            return []
        
        # Get all containers
        containers = client.containers.list(all=True)
        
        # Filter for lightrag_* containers only
        lightrag_containers = [c for c in containers if c.name.startswith('lightrag')]
        
        # Format container information
        container_info = []
        for container in lightrag_containers:
            # Get container status
            status = container.status
            
            # Get container creation time
            try:
                created_str = container.attrs['Created']
                if isinstance(created_str, str):
                    # Parse ISO format timestamp
                    from dateutil import parser
                    created_dt = parser.parse(created_str)
                    created = created_dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # Assume it's already a timestamp
                    created = datetime.fromtimestamp(created_str).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                created = "Unknown"
            
            # Get container ports
            ports = []
            port_bindings = container.attrs['HostConfig']['PortBindings'] or {}
            for container_port, host_bindings in port_bindings.items():
                if host_bindings:
                    for binding in host_bindings:
                        host_port = binding.get('HostPort', '')
                        ports.append(f"{host_port}:{container_port.split('/')[0]}")
            
            # Get container image
            image = container.image.tags[0] if container.image.tags else container.image.id[:12]
            
            # Get container environment variables
            env_vars = container.attrs['Config']['Env'] or []
            user_id = next((env.split('=')[1] for env in env_vars if env.startswith('USER_ID=')), 'N/A')
            
            # Add container information
            container_info.append({
                'Name': container.name,
                'Status': status,
                'Image': image,
                'Created': created,
                'Ports': ', '.join(ports) if ports else 'None',
                'USER_ID': user_id
            })
        
        return container_info
    
    except Exception as e:
        st.error(f"Error getting container status: {str(e)}")
        return []


def start_container(container_name: str) -> bool:
    """
    Start a Docker container.
    
    Args:
        container_name: Name of the container to start
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return False
        
        # Get container
        container = client.containers.get(container_name)
        
        # Start container
        container.start()
        
        return True
    
    except Exception as e:
        st.error(f"Error starting container '{container_name}': {str(e)}")
        return False


def stop_container(container_name: str) -> bool:
    """
    Stop a Docker container.
    
    Args:
        container_name: Name of the container to stop
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return False
        
        # Get container
        container = client.containers.get(container_name)
        
        # Stop container
        container.stop()
        
        return True
    
    except Exception as e:
        st.error(f"Error stopping container '{container_name}': {str(e)}")
        return False


def restart_container(container_name: str) -> bool:
    """
    Restart a Docker container.
    
    Args:
        container_name: Name of the container to restart
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return False
        
        # Get container
        container = client.containers.get(container_name)
        
        # Restart container
        container.restart()
        
        return True
    
    except Exception as e:
        st.error(f"Error restarting container '{container_name}': {str(e)}")
        return False


def get_container_logs(container_name: str, tail: int = 100) -> str:
    """
    Get logs from a Docker container.
    
    Args:
        container_name: Name of the container
        tail: Number of lines to return from the end of the logs
        
    Returns:
        Container logs as a string
    """
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return ""
        
        # Get container
        container = client.containers.get(container_name)
        
        # Get logs
        logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
        
        return logs
    
    except Exception as e:
        st.error(f"Error getting logs for container '{container_name}': {str(e)}")
        return ""


def get_container_stats() -> List[Dict[str, Any]]:
    """
    Get performance statistics for all running Docker containers.
    
    Returns:
        List of dictionaries containing container statistics
    """
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return []
        
        # Get running containers
        containers = client.containers.list()
        
        # Get container statistics
        container_stats = []
        for container in containers:
            # Get raw stats
            stats = container.stats(stream=False)
            
            # Calculate CPU usage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_usage = (cpu_delta / system_delta) * 100.0 * stats['cpu_stats']['online_cpus']
            
            # Calculate memory usage
            memory_usage = stats['memory_stats']['usage'] / (1024 * 1024)  # Convert to MB
            memory_limit = stats['memory_stats']['limit'] / (1024 * 1024)  # Convert to MB
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            # Calculate network I/O
            rx_bytes = 0
            tx_bytes = 0
            networks = stats.get('networks', {})
            if networks:
                for _, network_stats in networks.items():
                    rx_bytes += network_stats.get('rx_bytes', 0)
                    tx_bytes += network_stats.get('tx_bytes', 0)
            
            # Calculate block I/O
            read_bytes = 0
            write_bytes = 0
            blkio_stats = stats.get('blkio_stats', {})
            io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
            if io_service_bytes:
                for io_stat in io_service_bytes:
                    if io_stat.get('op') == 'Read':
                        read_bytes += io_stat.get('value', 0)
                    elif io_stat.get('op') == 'Write':
                        write_bytes += io_stat.get('value', 0)
            
            # Add container statistics
            container_stats.append({
                'Name': container.name,
                'CPU': f"{cpu_usage:.2f}",
                'Memory': f"{memory_usage:.2f}",
                'Memory %': f"{memory_percent:.2f}",
                'NetworkIO': f"{rx_bytes / (1024 * 1024):.2f} MB / {tx_bytes / (1024 * 1024):.2f} MB",
                'BlockIO': f"{read_bytes / (1024 * 1024):.2f} MB / {write_bytes / (1024 * 1024):.2f} MB"
            })
        
        return container_stats
    
    except Exception as e:
        st.error(f"Error getting container statistics: {str(e)}")
        return []


def update_container_env(container_name: str, env_vars: Dict[str, str]) -> bool:
    """
    Update environment variables for a Docker container.
    
    Args:
        container_name: Name of the container
        env_vars: Dictionary of environment variables to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return False
        
        # Get container
        container = client.containers.get(container_name)
        
        # Get current environment variables
        current_env = container.attrs['Config']['Env'] or []
        
        # Convert current environment variables to dictionary
        current_env_dict = {}
        for env in current_env:
            if '=' in env:
                key, value = env.split('=', 1)
                current_env_dict[key] = value
        
        # Update environment variables
        current_env_dict.update(env_vars)
        
        # Convert back to list format
        new_env = [f"{key}={value}" for key, value in current_env_dict.items()]
        
        # Update container configuration
        # Note: This requires stopping and recreating the container
        # This is a simplified version and may not work for all containers
        container.stop()
        container.remove()
        
        # Create new container with updated environment variables
        client.containers.run(
            container.image.tags[0] if container.image.tags else container.image.id,
            name=container_name,
            detach=True,
            environment=new_env,
            ports=container.attrs['HostConfig']['PortBindings'],
            volumes=container.attrs['HostConfig']['Binds']
        )
        
        return True
    
    except Exception as e:
        st.error(f"Error updating environment variables for container '{container_name}': {str(e)}")
        return False


def start_all_containers() -> tuple[bool, str]:
    """
    Start all LightRAG containers.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return False, "Failed to connect to Docker"
        
        # Get all containers
        containers = client.containers.list(all=True)
        
        # Filter for lightrag_* containers only
        lightrag_containers = [c for c in containers if c.name.startswith('lightrag')]
        
        if not lightrag_containers:
            return False, "No LightRAG containers found"
        
        # Start all containers
        started_containers = []
        failed_containers = []
        
        for container in lightrag_containers:
            try:
                if container.status != 'running':
                    container.start()
                    started_containers.append(container.name)
                else:
                    # Container already running
                    pass
            except Exception as e:
                failed_containers.append(f"{container.name}: {str(e)}")
        
        # Prepare result message
        if failed_containers:
            message = f"Started {len(started_containers)} containers. Failed: {', '.join(failed_containers)}"
            return len(started_containers) > 0, message
        else:
            if started_containers:
                message = f"Successfully started {len(started_containers)} containers: {', '.join(started_containers)}"
            else:
                message = "All containers were already running"
            return True, message
    
    except Exception as e:
        return False, f"Error starting containers: {str(e)}"


def stop_all_containers() -> tuple[bool, str]:
    """
    Stop all LightRAG containers.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return False, "Failed to connect to Docker"
        
        # Get all containers
        containers = client.containers.list(all=True)
        
        # Filter for lightrag_* containers only
        lightrag_containers = [c for c in containers if c.name.startswith('lightrag')]
        
        if not lightrag_containers:
            return False, "No LightRAG containers found"
        
        # Stop all containers
        stopped_containers = []
        failed_containers = []
        
        for container in lightrag_containers:
            try:
                if container.status == 'running':
                    container.stop()
                    stopped_containers.append(container.name)
                else:
                    # Container already stopped
                    pass
            except Exception as e:
                failed_containers.append(f"{container.name}: {str(e)}")
        
        # Prepare result message
        if failed_containers:
            message = f"Stopped {len(stopped_containers)} containers. Failed: {', '.join(failed_containers)}"
            return len(stopped_containers) > 0, message
        else:
            if stopped_containers:
                message = f"Successfully stopped {len(stopped_containers)} containers: {', '.join(stopped_containers)}"
            else:
                message = "All containers were already stopped"
            return True, message
    
    except Exception as e:
        return False, f"Error stopping containers: {str(e)}"


def get_docker_compose_services() -> List[str]:
    """
    Get a list of services defined in docker-compose.yml.
    
    Returns:
        List of service names
    """
    try:
        from personal_agent.streamlit.utils.system_utils import get_project_root
        
        # Get project root
        project_root = get_project_root()
        
        # Check if docker-compose.yml exists
        docker_compose_path = project_root / "docker-compose.yml"
        if not docker_compose_path.exists():
            return []
        
        # Parse docker-compose.yml
        import yaml
        with open(docker_compose_path, "r") as f:
            docker_compose = yaml.safe_load(f)
        
        # Get services
        services = docker_compose.get('services', {})
        
        return list(services.keys())
    
    except Exception as e:
        st.error(f"Error getting Docker Compose services: {str(e)}")
        return []
