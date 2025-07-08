#!/usr/bin/env python3
"""
Run the Personal AI Agent with Smolagents web interface.

This is the main entry point for running the smolagents-powered web interface.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from personal_agent.smol_main import run_smolagents_web

if __name__ == "__main__":
    run_smolagents_web()
