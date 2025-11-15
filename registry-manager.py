#!/usr/bin/env python3
"""
User Registry Manager - CLI Wrapper

Command-line interface for user registry management operations.

Usage:
    ./registry-manager.py --rebuild                    # Rebuild registry from filesystem + existing data
    ./registry-manager.py --rebuild --dry-run          # Preview rebuild without changes
    ./registry-manager.py --discover                   # Show discovered users without rebuilding
    ./registry-manager.py --nuke --nuke-confirm        # Nuclear option (requires both flags)
    ./registry-manager.py --status                     # Show registry status

Author: Eric G. Suchanek, PhD
Last updated: 
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.tools.registry_manager import (
    show_status,
    show_discovery,
    rebuild_registry,
    nuke_all_data,
)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="User Registry Manager - Recovery and Nuclear Options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./registry-manager.py --status              # Show registry status
  ./registry-manager.py --discover            # Show discovered users
  ./registry-manager.py --rebuild             # Rebuild registry
  ./registry-manager.py --rebuild --dry-run   # Preview rebuild
  ./registry-manager.py --nuke --nuke-confirm # Nuclear option
        """,
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current registry status",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Show discovered users without rebuilding",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild registry from filesystem + existing data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview rebuild without making changes",
    )
    parser.add_argument(
        "--nuke",
        action="store_true",
        help="Nuclear option: destroy all user data (requires --nuke-confirm)",
    )
    parser.add_argument(
        "--nuke-confirm",
        action="store_true",
        help="Confirmation flag for nuclear option",
    )
    
    args = parser.parse_args()
    
    # Handle commands
    if args.nuke:
        nuke_all_data(confirm=args.nuke_confirm)
    elif args.rebuild:
        rebuild_registry(dry_run=args.dry_run)
    elif args.discover:
        show_discovery()
    elif args.status:
        show_status()
    else:
        # Default to status
        show_status()


if __name__ == "__main__":
    main()
