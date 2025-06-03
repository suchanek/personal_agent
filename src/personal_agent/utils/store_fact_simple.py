#!/usr/bin/env python3
"""Simple script to store facts in the knowledge base.

This script provides a convenient way to store facts directly without
using the full module import path.

Usage:
    cd /Users/egs/repos/personal_agent/src/personal_agent/utils
    python store_fact_simple.py "Your fact here"
    python store_fact_simple.py "Your fact here" --topic "science"
"""

import argparse
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.personal_agent.utils.store_fact import main
except ImportError:
    print("❌ Error: Could not import the store_fact module.")
    print("Make sure you're running this from the correct directory and that")
    print("the Personal AI Agent package is properly installed.")
    sys.exit(1)

if __name__ == "__main__":
    main()
