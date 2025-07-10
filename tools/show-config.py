#!/usr/bin/env python3
"""
Personal Agent Configuration Display Tool - Wrapper Script

This is a wrapper script that calls the show_config module from the personal_agent package.
The actual implementation has been moved to src/personal_agent/tools/show_config.py

Usage:
    ./tools/show-config.py [options]

Options:
    -h, --help     Show this help message
    -v, --version  Show version information
    --no-color     Disable colored output
    --json         Output configuration as JSON
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to Python path so we can import our modules
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

try:
    from personal_agent.tools.show_config import show_config
except ImportError as e:
    print(f"Error: Could not import show_config module: {e}")
    print("Make sure you're running this script from the project root directory.")
    print("The module implementation is located at: src/personal_agent/tools/show_config.py")
    sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Display Personal Agent configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="Personal Agent Config Tool v1.0 (Wrapper)"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output configuration as JSON"
    )
    
    args = parser.parse_args()
    
    try:
        result = show_config(no_color=args.no_color, json_output=args.json)
        if args.json and result:
            print(result)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
