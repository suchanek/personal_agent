#!/bin/bash
# Wrapper script for docmgr.py that suppresses Click deprecation warnings

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Use the Python from the virtual environment
PYTHON_PATH="$PROJECT_ROOT/.venv/bin/python"

# Run the Python script with warning filters
"$PYTHON_PATH" -W ignore::DeprecationWarning:click.parser "$SCRIPT_DIR/docmgr.py" "$@"