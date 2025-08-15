"""
System Utilities

General utility functions for the Streamlit dashboard.
"""

import os
import streamlit as st
import importlib.util
import subprocess
from pathlib import Path


def load_css():
    """Load custom CSS for the dashboard."""
    # Define custom CSS
    st.markdown("""
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #e6f0ff;
            border-bottom: 2px solid #4c78e0;
        }
        
        div.stButton > button:first-child {
            width: 100%;
        }
        
        div.stDownloadButton > button:first-child {
            width: 100%;
        }
        
        .metric-card {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
            background-color: #f9f9f9;
        }
        
        .warning {
            color: #ff9800;
            font-weight: bold;
        }
        
        .error {
            color: #f44336;
            font-weight: bold;
        }
        
        .success {
            color: #4caf50;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        "streamlit",
        "pandas",
        "docker",
        "plotly",
        "psutil"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if not importlib.util.find_spec(package):
            missing_packages.append(package)
    
    if missing_packages:
        st.warning(f"Missing required packages: {', '.join(missing_packages)}")
        st.info("Install missing packages with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def get_system_info():
    """Get system information."""
    import platform
    import psutil
    
    try:
        # Get system information
        system_info = {
            "OS": platform.system(),
            "OS Version": platform.version(),
            "Architecture": platform.machine(),
            "Python Version": platform.python_version(),
            "CPU Cores": psutil.cpu_count(logical=True),
            "Memory Total": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
            "Disk Total": f"{psutil.disk_usage('/').total / (1024**3):.2f} GB",
        }
        
        return system_info
    except Exception as e:
        st.error(f"Error getting system information: {str(e)}")
        return {}


def execute_command(command):
    """Execute a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return {
            "success": True,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "output": e.stdout,
            "error": e.stderr
        }


def get_project_root():
    """Get the project root directory."""
    # Assuming this file is in src/personal_agent/streamlit/utils/
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    return project_root


def get_project_version():
    """Get the project version."""
    try:
        from personal_agent import __version__
        return __version__
    except ImportError:
        # Try to get version from setup.py or pyproject.toml
        project_root = get_project_root()
        
        # Check setup.py
        setup_py = project_root / "setup.py"
        if setup_py.exists():
            with open(setup_py, "r") as f:
                content = f.read()
                import re
                version_match = re.search(r'version=[\'"]([^\'"]*)[\'"]', content)
                if version_match:
                    return version_match.group(1)
        
        # Check pyproject.toml
        pyproject_toml = project_root / "pyproject.toml"
        if pyproject_toml.exists():
            with open(pyproject_toml, "r") as f:
                content = f.read()
                import re
                version_match = re.search(r'version\s*=\s*[\'"]([^\'"]*)[\'"]', content)
                if version_match:
                    return version_match.group(1)
        
        return "Unknown"