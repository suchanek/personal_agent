#!/usr/bin/env python3
"""
User Switcher - Wrapper Script

Simple wrapper to call the user_switcher module.

Usage:
    ./switch-user.py "Eric Suchanek"
    ./switch-user.py alice.smith --no-restart
    ./switch-user.py "Charlie Brown" --user-type Admin
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.tools.user_switcher import main

if __name__ == "__main__":
    main()
