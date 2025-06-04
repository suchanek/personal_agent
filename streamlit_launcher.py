#!/usr/bin/env python3
"""
Streamlit launcher for Personal AI Agent.

This script provides a simple way to launch the Streamlit interface
without import issues.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
repo_root = Path(__file__).parent.parent.parent
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

# Now import and run the application
from personal_agent.streamlit.app import main

if __name__ == "__main__":
    main()
