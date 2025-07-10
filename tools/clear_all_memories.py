#!/usr/bin/env python3
"""
Clear All Memories Script

A wrapper script that calls the memory cleaner module from the personal_agent package.

This script provides a unified interface to clear:
1. Semantic Memory System (SQLite + LanceDB) - local user memories
2. LightRAG Graph Memory System (Knowledge Graph) - relationship-based memories

Usage:
  From the project root directory, run:
  `python tools/clear_all_memories.py [OPTIONS]`

Options:
  --dry-run                   Show what would be cleared without actually clearing
  --no-confirm                Skip confirmation prompts
  --semantic-only             Clear only the semantic memory system
  --lightrag-only             Clear only the LightRAG graph memory system
  --verify                    Verify that memories have been cleared
  --user-id <USER_ID>         Specify user ID (default: from config)
  --verbose                   Enable verbose logging

Examples:
  # Clear both memory systems with confirmation
  python tools/clear_all_memories.py

  # Dry run to see what would be cleared
  python tools/clear_all_memories.py --dry-run

  # Clear both systems without confirmation
  python tools/clear_all_memories.py --no-confirm

  # Clear only semantic memories
  python tools/clear_all_memories.py --semantic-only

  # Clear only LightRAG graph memories
  python tools/clear_all_memories.py --lightrag-only

  # Verify clearing was successful
  python tools/clear_all_memories.py --verify
"""

import sys
from pathlib import Path

# Add the src directory to the path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import and run the main function from the package-level module
from personal_agent.tools.memory_cleaner import main

if __name__ == "__main__":
    # This script requires asyncio to run
    import asyncio
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
