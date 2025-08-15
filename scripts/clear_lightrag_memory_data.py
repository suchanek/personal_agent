#!/usr/bin/env python3
"""
Clear LightRAG Data Script

This script clears LightRAG data files and deletes the knowledge graph file
from both LIGHTRAG_STORAGE_DIR and LIGHTRAG_MEMORY_STORAGE_DIR.

It properly gets the storage directories from the personal agent environment
settings and supports a --dry-run option to preview what would be deleted.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path to allow imports
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# Import settings from personal_agent
from src.personal_agent.config.settings import LIGHTRAG_MEMORY_STORAGE_DIR


def clear_json_file(file_path, dry_run=False):
    """Clears the content of a JSON file, making it an empty dictionary.

    Args:
        file_path: Path to the JSON file
        dry_run: If True, only print what would be done without making changes
    """
    if os.path.exists(file_path):
        if dry_run:
            print(f"[DRY RUN] Would clear {file_path}")
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            print(f"✅ Cleared {file_path}")
    else:
        print(f"ℹ️ File not found: {file_path}")


def delete_file(file_path, dry_run=False):
    """Deletes a file if it exists.

    Args:
        file_path: Path to the file to delete
        dry_run: If True, only print what would be done without making changes
    """
    if os.path.exists(file_path):
        if dry_run:
            print(f"[DRY RUN] Would delete {file_path}")
        else:
            os.remove(file_path)
            print(f"✅ Deleted {file_path}")
    else:
        print(f"ℹ️ File not found: {file_path}")


def main():
    """Main function to handle command-line arguments and execute clearing operations."""
    parser = argparse.ArgumentParser(
        description="Clear LightRAG data files and delete knowledge graph files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleared without actually clearing",
    )
    args = parser.parse_args()

    # Print header
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No actual clearing will be performed\n")
    else:
        print("\n🧹 CLEARING LIGHTRAG DATA\n")

    # Define files to clear in the memory storage directory
    files_to_clear = [
        "kv_store_doc_status.json",
        "kv_store_full_docs.json",
        "kv_store_llm_response_cache.json",
        "kv_store_text_chunks.json",
    ]

    # Define knowledge graph file name
    graph_file_name = "graph_chunk_entity_relation.graphml"

    # Print storage directories
    print(f"📁 LightRAG Storage Directory: {LIGHTRAG_STORAGE_DIR}")
    print(f"📁 LightRAG Memory Storage Directory: {LIGHTRAG_MEMORY_STORAGE_DIR}\n")

    # Clear JSON files in memory storage directory
    print("Clearing JSON files in memory storage directory:")
    for file_name in files_to_clear:
        clear_json_file(
            os.path.join(LIGHTRAG_MEMORY_STORAGE_DIR, file_name), args.dry_run
        )

    # Delete knowledge graph files from the memory storage directory only
    print("\nDeleting knowledge graph files:")
    graph_files = [os.path.join(LIGHTRAG_MEMORY_STORAGE_DIR, graph_file_name)]

    for graph_file in graph_files:
        delete_file(graph_file, args.dry_run)

    # Print footer
    if args.dry_run:
        print("\n🔍 DRY RUN COMPLETE - No files were modified")
    else:
        print("\n✅ CLEARING COMPLETE")


if __name__ == "__main__":
    main()
