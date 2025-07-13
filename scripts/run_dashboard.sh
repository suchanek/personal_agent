#!/bin/bash
# Run the Memory & User Management Dashboard
# This script launches the Streamlit dashboard for the Personal Agent system

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Get the project root directory
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Change to the project root directory
cd "$PROJECT_ROOT"

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit is not installed. Installing required packages..."
    pip install streamlit pandas docker psutil plotly
fi

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run the dashboard
echo "Starting Memory & User Management Dashboard..."
streamlit run src/personal_agent/streamlit/dashboard.py "$@"