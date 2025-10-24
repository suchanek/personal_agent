"""
System Utilities

General utility functions for the Streamlit dashboard.
"""

import os
import streamlit as st
import importlib.util
import subprocess
from pathlib import Path


def load_css(dark_mode=False):
    """Load custom CSS for the dashboard with optional dark mode support."""
    # Get dark mode state from session if available
    if hasattr(st, 'session_state') and 'dark_theme' in st.session_state:
        dark_mode = st.session_state['dark_theme']
    
    # Define base CSS that works for both themes
    base_css = """
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        div.stButton > button:first-child {
            width: 100%;
        }
        
        div.stDownloadButton > button:first-child {
            width: 100%;
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
    """
    
    # Add theme-specific CSS
    if dark_mode:
        theme_css = """
        /* Dark mode comprehensive styling */
        .stApp {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background-color: #0e1117 !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #2b2b2b !important;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
            color: #fafafa !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #4c78e0 !important;
            border-bottom: 2px solid #4c78e0;
            color: white !important;
        }
        
        .stTabs [data-baseweb="tab-panel"] {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        
        /* More aggressive tab targeting for nested tabs */
        .stTabs [data-baseweb="tab-list"] button,
        .stTabs [data-baseweb="tab-list"] > div,
        .stTabs [data-baseweb="tab-list"] > div > div,
        .stTabs [data-baseweb="tab-list"] > div > div > button,
        .stTabs [role="tablist"],
        .stTabs [role="tablist"] button,
        .stTabs [role="tab"],
        div[role="tablist"],
        div[role="tablist"] button,
        div[role="tab"] {
            background-color: #2b2b2b !important;
            color: #fafafa !important;
            border-color: #4a4a4a !important;
        }
        
        /* Target specific white backgrounds in tab areas only */
        .stTabs *[style*="background-color: rgb(255, 255, 255)"],
        .stTabs *[style*="background-color: white"],
        .stTabs *[style*="background: white"],
        .stTabs *[style*="background: rgb(255, 255, 255)"] {
            background-color: #2b2b2b !important;
            color: #fafafa !important;
        }
        
        .metric-card {
            border: 1px solid #4a4a4a;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
            background-color: #1e1e1e;
            color: #fafafa;
        }
        
        /* Tables and DataFrames - Critical for readability */
        .stDataFrame,
        .stTable,
        [data-testid="stTable"],
        [data-testid="stDataFrame"] {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
        }
        
        .stDataFrame table,
        .stTable table,
        [data-testid="stTable"] table,
        [data-testid="stDataFrame"] table {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
        }
        
        .stDataFrame th,
        .stTable th,
        .stDataFrame td,
        .stTable td,
        [data-testid="stTable"] th,
        [data-testid="stTable"] td,
        [data-testid="stDataFrame"] th,
        [data-testid="stDataFrame"] td {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border-color: #4a4a4a !important;
        }
        
        .stDataFrame thead th,
        .stTable thead th,
        [data-testid="stTable"] thead th,
        [data-testid="stDataFrame"] thead th {
            background-color: #2d2d2d !important;
            color: #fafafa !important;
            border-color: #4a4a4a !important;
        }
        
        /* Text elements */
        .stMarkdown,
        .stText,
        .stSubheader,
        .stHeader,
        h1, h2, h3, h4, h5, h6,
        p, div, span, label {
            color: #fafafa !important;
        }
        
        /* Forms */
        .stForm {
            background-color: #1e1e1e !important;
            border: 1px solid #4a4a4a !important;
            border-radius: 5px;
        }
        
        /* Input elements */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div,
        input, textarea, select {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #4f4f4f !important;
        }
        
        /* Alert messages */
        .stInfo,
        [data-testid="stInfo"] {
            background-color: #1a3a5c !important;
            color: #e3f2fd !important;
        }
        
        .stWarning,
        [data-testid="stWarning"] {
            background-color: #5c4a1a !important;
            color: #fff3cd !important;
        }
        
        .stError,
        [data-testid="stError"] {
            background-color: #5c1a1a !important;
            color: #f8d7da !important;
        }
        
        .stSuccess,
        [data-testid="stSuccess"] {
            background-color: #1a5c2e !important;
            color: #d4edda !important;
        }
        """
    else:
        theme_css = """
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
        
        .metric-card {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
            background-color: #f9f9f9;
        }
        """
    
    # Combine and apply CSS
    full_css = base_css + theme_css + "</style>"
    st.markdown(full_css, unsafe_allow_html=True)


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