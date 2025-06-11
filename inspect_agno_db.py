#!/usr/bin/env python3
"""
Script to inspect the Agno SQLite database and knowledge base.

This script helps debug issues with knowledge base storage and retrieval
by examining the database contents directly.
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import DATA_DIR


def inspect_sqlite_file(db_path: str) -> None:
    """Inspect a SQLite database file and show its contents.

    :param db_path: Path to the SQLite database file
    """
    if not Path(db_path).exists():
        print(f"❌ Database file not found: {db_path}")
        return

    print(f"📁 Inspecting database: {db_path}")
    print("=" * 60)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("📭 No tables found in database")
            return

        print(f"📊 Found {len(tables)} tables:")
        for table_name in tables:
            print(f"  - {table_name[0]}")
        print()

        # Inspect each table
        for table_name in tables:
            table = table_name[0]
            print(f"🔍 Table: {table}")
            print("-" * 40)

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()

            print("Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")

            # Show sample rows
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 5;")
                rows = cursor.fetchall()

                print(f"\nSample rows (showing first {min(len(rows), 5)}):")
                for i, row in enumerate(rows, 1):
                    print(f"  Row {i}: {row}")

                # If this looks like a document/knowledge table, show more details
                if any(
                    keyword in table.lower()
                    for keyword in ["document", "knowledge", "chunk", "text"]
                ):
                    print(f"\n📝 Detailed content from {table}:")
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
                    detailed_rows = cursor.fetchall()

                    for i, row in enumerate(detailed_rows, 1):
                        print(f"\n--- Record {i} ---")
                        for j, col in enumerate(columns):
                            col_name = col[1]
                            value = row[j]
                            if isinstance(value, str) and len(value) > 100:
                                value = value[:100] + "..."
                            print(f"{col_name}: {value}")

            print("\n")

    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
    finally:
        if "conn" in locals():
            conn.close()


def find_agno_databases() -> List[str]:
    """Find all Agno-related SQLite databases.

    :return: List of database file paths
    """
    search_paths = [
        Path(DATA_DIR) / "agno",
        Path("./data/agno"),
        Path("./tmp"),
        Path("."),
    ]

    db_files = []

    for search_path in search_paths:
        if search_path.exists():
            # Look for .db files
            for db_file in search_path.rglob("*.db"):
                db_files.append(str(db_file))

    return db_files


def inspect_lancedb_directory(lance_path: str) -> None:
    """Inspect a LanceDB directory structure.

    :param lance_path: Path to the LanceDB directory
    """
    lance_dir = Path(lance_path)
    if not lance_dir.exists():
        print(f"❌ LanceDB directory not found: {lance_path}")
        return

    print(f"🗂️ Inspecting LanceDB directory: {lance_path}")
    print("=" * 60)

    # Check for LanceDB files and structure
    all_files = list(lance_dir.rglob("*"))

    if not all_files:
        print("📭 Directory is empty")
        return

    print(f"📊 Found {len(all_files)} files/directories:")

    # Group by file types
    file_types: Dict[str, List[Path]] = {}

    for file_path in all_files:
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if not ext:
                ext = "(no extension)"
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(file_path)

    for ext, files in file_types.items():
        print(f"\n{ext} files ({len(files)}):")
        for file_path in files[:5]:  # Show first 5
            size = file_path.stat().st_size
            print(f"  - {file_path.name} ({size} bytes)")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")


def main():
    """Main function to inspect all Agno databases."""
    print("🔍 Agno Database Inspector")
    print("=" * 60)

    # Find all database files
    db_files = find_agno_databases()

    if not db_files:
        print("❌ No database files found")
        print("\nSearched in:")
        print(f"  - {DATA_DIR}/agno")
        print("  - ./data/agno")
        print("  - ./tmp")
        print("  - .")
        return

    print(f"📁 Found {len(db_files)} database files:")
    for db_file in db_files:
        print(f"  - {db_file}")
    print()

    # Inspect each database
    for db_file in db_files:
        inspect_sqlite_file(db_file)
        print("\n" + "=" * 60 + "\n")

    # Look for LanceDB directories
    lance_paths = [
        Path(DATA_DIR) / "agno" / "knowledge_base",
        Path("./data/agno/knowledge_base"),
        Path(DATA_DIR) / "agno" / "lancedb",
        Path("./data/agno/lancedb"),
    ]

    for lance_path in lance_paths:
        if lance_path.exists():
            inspect_lancedb_directory(str(lance_path))
            print("\n" + "=" * 60 + "\n")

    print("✅ Database inspection complete!")


if __name__ == "__main__":
    main()
