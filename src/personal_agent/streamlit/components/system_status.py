"""
System Status Component

Displays system status information including:
- Docker container status
- Memory usage statistics
- User information
- System health metrics
"""

import os
import psutil
import streamlit as st
import pandas as pd
from datetime import datetime

# Import project modules
from personal_agent.core.docker_integration import DockerIntegrationManager
from personal_agent.streamlit.utils.docker_utils import get_container_status


def system_status_tab():
    """Render the system status tab."""
    st.title("System Status")
    
    # Create columns for layout
    col1, col2 = st.columns(2)
    
    with col1:
        _render_system_info()
        _render_memory_stats()
    
    with col2:
        _render_docker_status()
        _render_user_info()


def _render_system_info():
    """Display system information."""
    st.subheader("System Information")
    
    # Get system information
    system_info = {
        "CPU Usage": f"{psutil.cpu_percent()}%",
        "Memory Usage": f"{psutil.virtual_memory().percent}%",
        "Disk Usage": f"{psutil.disk_usage('/').percent}%",
        "Python Version": os.popen("python --version").read().strip(),
        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # Display as a table
    st.table(pd.DataFrame(list(system_info.items()), columns=["Metric", "Value"]))


def _render_memory_stats():
    """Display memory statistics."""
    st.subheader("Memory Statistics")
    
    try:
        # This would be replaced with actual memory stats from your system
        # For now, using placeholder data
        memory_stats = {
            "Total Memories": "125",
            "User Memories": "42",
            "System Memories": "83",
            "Memory DB Size": "24.5 MB",
            "Last Sync": "2 minutes ago",
        }
        
        st.table(pd.DataFrame(list(memory_stats.items()), columns=["Metric", "Value"]))
        
    except Exception as e:
        st.error(f"Error loading memory statistics: {str(e)}")


def _render_docker_status():
    """Display Docker container status."""
    st.subheader("Docker Container Status")
    
    try:
        # Get Docker container status
        docker_integration = DockerIntegrationManager()
        containers = get_container_status(docker_integration)
        
        if containers:
            # Create a DataFrame for display
            df = pd.DataFrame(containers)
            st.dataframe(df)
            
            # Count containers by status
            status_counts = df['Status'].value_counts().to_dict()
            st.caption(f"Running: {status_counts.get('running', 0)} | "
                      f"Stopped: {status_counts.get('exited', 0)} | "
                      f"Total: {len(containers)}")
        else:
            st.info("No Docker containers found.")
            
    except Exception as e:
        st.error(f"Error connecting to Docker: {str(e)}")
        st.info("Make sure Docker is running and you have the necessary permissions.")


def _render_user_info():
    """Display user information."""
    st.subheader("User Information")
    
    try:
        # This would be replaced with actual user data from your system
        # For now, using placeholder data
        from personal_agent.config.settings import USER_ID
        
        user_info = {
            "Current User": USER_ID,
            "User Directory": f"/home/{USER_ID}",
            "User Config": "Default",
            "Last Login": "Today at 09:15",
        }
        
        st.table(pd.DataFrame(list(user_info.items()), columns=["Metric", "Value"]))
        
    except Exception as e:
        st.error(f"Error loading user information: {str(e)}")
