#!/usr/bin/env python3
"""
Entry point script for the Personal AI Agent.

This script serves as the main entry point to start the agent system.
It uses the refactored modular architecture.
"""

import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import and run the main application
from personal_agent.main import main

if __name__ == "__main__":
    main()
