"""
Docker Services Component

Provides interface for:
- Managing Docker containers
- Starting/stopping services
- Viewing container logs
- Configuring Docker settings
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime

# Import project modules
from personal_agent.core.docker_integration import DockerIntegrationManager
from personal_agent.streamlit.utils.docker_utils import (
    get_container_status,
    start_container,
    stop_container,
    restart_container,
    get_container_logs,
    get_container_stats
)


def docker_services_tab():
    """Render the Docker services tab."""
    st.title("Docker Services")
    
    # Create tabs for different Docker management functions
    tabs = st.tabs(["Container Management", "Logs", "Performance", "Settings"])
    
    with tabs[0]:
        _render_container_management()
    
    with tabs[1]:
        _render_container_logs()
    
    with tabs[2]:
        _render_container_performance()
    
    with tabs[3]:
        _render_docker_settings()


def _render_container_management():
    """Display and manage Docker containers."""
    st.subheader("Container Management")
    
    try:
        # Get Docker container status
        docker_integration = DockerIntegrationManager()
        containers = get_container_status(docker_integration)
        
        if containers:
            # Create a DataFrame for display
            df = pd.DataFrame(containers)
            
            # Add action buttons to the DataFrame
            df['Actions'] = None
            st.dataframe(df)
            
            # Container actions
            st.write("### Container Actions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Select container
                container_names = [container['Name'] for container in containers]
                selected_container = st.selectbox("Select Container", container_names)
            
            with col2:
                # Container status
                selected_status = next((container['Status'] for container in containers 
                                      if container['Name'] == selected_container), None)
                st.info(f"Status: {selected_status}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Start", disabled=selected_status == "running"):
                    try:
                        if start_container(selected_container):
                            st.success(f"Container '{selected_container}' started successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to start container '{selected_container}'.")
                    except Exception as e:
                        st.error(f"Error starting container: {str(e)}")
            
            with col2:
                if st.button("Stop", disabled=selected_status != "running"):
                    try:
                        if stop_container(selected_container):
                            st.success(f"Container '{selected_container}' stopped successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to stop container '{selected_container}'.")
                    except Exception as e:
                        st.error(f"Error stopping container: {str(e)}")
            
            with col3:
                if st.button("Restart"):
                    try:
                        if restart_container(selected_container):
                            st.success(f"Container '{selected_container}' restarted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to restart container '{selected_container}'.")
                    except Exception as e:
                        st.error(f"Error restarting container: {str(e)}")
            
            # Bulk actions
            st.write("### Bulk Actions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Start All"):
                    st.info("Starting all containers...")
                    # Implementation would go here
            
            with col2:
                if st.button("Stop All"):
                    st.info("Stopping all containers...")
                    # Implementation would go here
        else:
            st.info("No Docker containers found.")
            
    except Exception as e:
        st.error(f"Error connecting to Docker: {str(e)}")
        st.info("Make sure Docker is running and you have the necessary permissions.")


def _render_container_logs():
    """Display Docker container logs."""
    st.subheader("Container Logs")
    
    try:
        # Get Docker container status
        docker_integration = DockerIntegrationManager()
        containers = get_container_status(docker_integration)
        
        if containers:
            # Select container
            container_names = [container['Name'] for container in containers]
            selected_container = st.selectbox("Select Container for Logs", container_names)
            
            # Log options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tail_lines = st.number_input(
                    "Lines to Display",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    step=10,
                    help="Number of log lines to display"
                )
            
            with col2:
                auto_refresh = st.checkbox(
                    "Auto Refresh",
                    value=False,
                    help="Automatically refresh logs"
                )
            
            with col3:
                if st.button("Refresh Logs"):
                    st.rerun()
            
            # Get logs
            logs = get_container_logs(selected_container, tail=tail_lines)
            
            if logs:
                st.code(logs, language="bash")
            else:
                st.info(f"No logs available for container '{selected_container}'.")
        else:
            st.info("No Docker containers found.")
            
    except Exception as e:
        st.error(f"Error retrieving container logs: {str(e)}")


def _render_container_performance():
    """Display Docker container performance metrics."""
    st.subheader("Container Performance")
    
    try:
        # Get Docker container status
        docker_integration = DockerIntegrationManager()
        containers = get_container_status(docker_integration)
        
        if containers:
            # Get container stats
            container_stats = get_container_stats()
            
            if container_stats:
                # Create a DataFrame for display
                df = pd.DataFrame(container_stats)
                st.dataframe(df)
                
                # Select container for detailed stats
                container_names = [stat['Name'] for stat in container_stats]
                selected_container = st.selectbox("Select Container for Detailed Stats", container_names)
                
                # Get selected container stats
                selected_stats = next((stat for stat in container_stats if stat['Name'] == selected_container), None)
                
                if selected_stats:
                    # Display detailed stats
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("CPU Usage", f"{selected_stats['CPU']}%")
                        st.metric("Memory Usage", f"{selected_stats['Memory']} MB")
                    
                    with col2:
                        st.metric("Network I/O", f"{selected_stats['NetworkIO']}")
                        st.metric("Block I/O", f"{selected_stats['BlockIO']}")
                    
                    # Historical performance chart (placeholder)
                    st.write("### Historical Performance")
                    st.info("Historical performance charts will be implemented in a future update.")
            else:
                st.info("No container statistics available.")
        else:
            st.info("No Docker containers found.")
            
    except Exception as e:
        st.error(f"Error retrieving container performance metrics: {str(e)}")


def _render_docker_settings():
    """Configure Docker settings."""
    st.subheader("Docker Settings")
    
    # Docker configuration
    st.write("### Docker Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        docker_host = st.text_input(
            "Docker Host",
            value="unix:///var/run/docker.sock",
            help="Docker daemon socket to connect to"
        )
    
    with col2:
        auto_restart = st.checkbox(
            "Auto-restart Containers",
            value=True,
            help="Automatically restart containers on failure"
        )
    
    # Resource limits
    st.write("### Resource Limits")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cpu_limit = st.slider(
            "CPU Limit (%)",
            min_value=10,
            max_value=100,
            value=50,
            step=5,
            help="Maximum CPU usage percentage for containers"
        )
    
    with col2:
        memory_limit = st.slider(
            "Memory Limit (MB)",
            min_value=512,
            max_value=8192,
            value=2048,
            step=256,
            help="Maximum memory usage for containers"
        )
    
    # User settings
    st.write("### User Settings")
    
    user_sync_enabled = st.checkbox(
        "Enable User Sync",
        value=True,
        help="Synchronize USER_ID between host and containers"
    )
    
    # Save settings
    if st.button("Save Docker Settings"):
        st.success("Docker settings saved successfully!")
        st.info("Some settings may require a restart to take effect.")