#!/usr/bin/env python3
# Filter out all warnings from problematic packages before any imports
import warnings

# Suppress Click deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module='click')
warnings.filterwarnings("ignore", message="Importing 'parser.split_arg_string' is deprecated")

# Suppress all warnings from spacy and related packages
warnings.filterwarnings("ignore", category=DeprecationWarning, module="spacy")
warnings.filterwarnings("ignore", category=UserWarning, module="spacy")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weasel")
warnings.filterwarnings("ignore", category=UserWarning, module="weasel")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="thinc")
warnings.filterwarnings("ignore", category=UserWarning, module="thinc")

# Set environment variable to filter warnings at the Python interpreter level
import os
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning:click,ignore::DeprecationWarning:spacy,ignore::DeprecationWarning:weasel"

"""
LightRAG Document Manager Driver Script

A command-line interface for the LightRAG Document Manager package.
This script provides a convenient way to manage documents in LightRAG
using the server API for stable and reliable operations.

Usage:
  From the project root directory, run:
  `python tools/docmgr.py [OPTIONS] [ACTIONS]`

Options:
  --server-url <URL>          LightRAG server URL (default: from config)
  --verify                    Verify deletion after completion by checking server
  --no-confirm                Skip confirmation prompts for deletion actions
  --delete-source             Delete the original source file from the inputs directory
  --retry <ID1> [ID2...]      Retry specific failed documents by their unique IDs
  --retry-all                 Retry all documents currently in 'failed' status

Actions:
  --status                    Show LightRAG server and document status
  --list                      List all documents with detailed view (ID, file path, status, etc.)
  --list-names                List all document names (file paths only)
  --delete-processing         Delete all documents currently in 'processing' status
  --delete-failed             Delete all documents currently in 'failed' status
  --delete-status <STATUS>    Delete all documents with a specific custom status
  --delete-ids <ID1> [ID2...] Delete specific documents by their unique IDs
  --delete-name <PATTERN>     Delete documents whose file paths match a glob-style pattern (e.g., '*.pdf', 'my_doc.txt')
  --nuke                      Perform a comprehensive deletion. This implicitly sets:
                              --verify, --delete-source, and --no-confirm.
                              Must be used with a deletion action.

Examples:
  # Check server status
  python tools/docmgr.py --status

  # List all documents
  python tools/docmgr.py --list

  # Delete all 'failed' documents and verify
  python tools/docmgr.py --delete-failed --verify

  # Delete a specific document by ID and also delete the source file
  python tools/docmgr.py --delete-ids doc-12345 --delete-source

  # Delete all '.md' files comprehensively
  python tools/docmgr.py --nuke --delete-name '*.md'

  # Retry a failed document
  python tools/docmgr.py --retry doc-failed-123

  # Retry all failed documents
  python tools/docmgr.py --retry-all
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.tools.lightrag_document_manager import main


if __name__ == "__main__":
    # This script requires asyncio to run.
    # Ensure you have the necessary dependencies:
    # poetry install
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
