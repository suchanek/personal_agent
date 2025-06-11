#!/usr/bin/env python3
"""
Clear Memory Database Script

This script provides robust methods to clear all memory data from the SQLite database.
Use this before running memory tests to ensure clean state.
"""

import sqlite3
from pathlib import Path

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat

from src.personal_agent.config import LLM_MODEL, OLLAMA_URL


def clear_memory_database_direct(db_file: str, table_name: str = "user_memories") -> bool:
    """Clear all memory data from SQLite database using direct SQL.
    
    :param db_file: Path to SQLite database file
    :param table_name: Name of the memory table to clear
    :return: True if successful, False otherwise
    """
    if not Path(db_file).exists():
        print(f"ℹ️  Database file does not exist: {db_file}")
        return True
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        
        if cursor.fetchone():
            # Get count before deletion
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            before_count = cursor.fetchone()[0]
            
            # Delete all records from the table
            cursor.execute(f"DELETE FROM {table_name}")
            deleted_count = cursor.rowcount
            
            # Reset auto-increment counter
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
            
            conn.commit()
            print(f"✅ Cleared {deleted_count} records from {table_name} (was {before_count})")
            
            # Verify table is empty
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            remaining_count = cursor.fetchone()[0]
            
            if remaining_count == 0:
                print(f"✅ Table {table_name} is now empty")
                return True
            else:
                print(f"⚠️  Warning: {remaining_count} records still remain")
                return False
        else:
            print(f"ℹ️  Table {table_name} does not exist")
            return True
            
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def clear_user_memories_direct(db_file: str, user_id: str, table_name: str = "user_memories") -> bool:
    """Clear memories for a specific user using direct SQL.
    
    :param db_file: Path to SQLite database file
    :param user_id: User ID to clear memories for
    :param table_name: Name of the memory table
    :return: True if successful, False otherwise
    """
    if not Path(db_file).exists():
        print(f"ℹ️  Database file does not exist: {db_file}")
        return True
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        
        if cursor.fetchone():
            # Get count before deletion
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id = ?", (user_id,))
            before_count = cursor.fetchone()[0]
            
            # Delete records for specific user
            cursor.execute(f"DELETE FROM {table_name} WHERE user_id = ?", (user_id,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            print(f"✅ Cleared {deleted_count} memories for user '{user_id}' (was {before_count})")
            return True
        else:
            print(f"ℹ️  Table {table_name} does not exist")
            return True
            
    except Exception as e:
        print(f"❌ Error clearing user memories: {e}")
        return False
    finally:
        if conn:
            conn.close()


def inspect_database(db_file: str) -> None:
    """Inspect database contents and show statistics.
    
    :param db_file: Path to SQLite database file
    """
    if not Path(db_file).exists():
        print(f"❌ Database file does not exist: {db_file}")
        return
    
    print(f"🔍 Inspecting database: {db_file}")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("ℹ️  No tables found in database")
            return
        
        for table in tables:
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            print(f"📊 Table: {table}")
            print(f"   Records: {count}")
            
            if count > 0 and table == "user_memories":
                # Show memory details for user_memories table
                cursor.execute(f"SELECT DISTINCT user_id FROM {table}")
                users = [row[0] for row in cursor.fetchall()]
                print(f"   Users: {users}")
                
                # Show sample records
                cursor.execute(f"SELECT memory, topics, user_id FROM {table} LIMIT 5")
                rows = cursor.fetchall()
                
                for i, (memory, topics, user_id) in enumerate(rows):
                    memory_preview = memory[:50] + "..." if len(memory) > 50 else memory
                    print(f"   Sample {i+1}: User='{user_id}', Memory='{memory_preview}', Topics={topics}")
                
                if count > 5:
                    print(f"   ... and {count - 5} more records")
            print()
            
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
    finally:
        if conn:
            conn.close()


def clear_memory_database_comprehensive(db_file: str = "/tmp/agent.db", user_id: str = None) -> bool:
    """Clear the memory database using multiple methods to ensure complete cleanup.
    
    :param db_file: Path to the SQLite database file
    :param user_id: Specific user ID to clear, or None to clear all memories
    :return: True if successful, False otherwise
    """
    print(f"🗑️  Comprehensive memory database clearing: {db_file}")
    success = True
    
    # Method 1: Try using Agno's built-in clear method
    try:
        print("🔧 Method 1: Using Agno Memory.clear()...")
        memory = Memory(
            model=OpenAIChat(
                id=LLM_MODEL,
                api_key="ollama",
                base_url=f"{OLLAMA_URL}/v1",
            ),
            db=SqliteMemoryDb(table_name="user_memories", db_file=db_file),
        )
        
        if user_id:
            # Get memories before clearing
            before_count = len(memory.get_user_memories(user_id=user_id))
            print(f"   Memories before: {before_count}")
            
        # Clear using Agno's method
        memory.clear()
        
        if user_id:
            # Check if cleared
            after_count = len(memory.get_user_memories(user_id=user_id))
            print(f"   Memories after clear(): {after_count}")
            
            if after_count > 0:
                print("   ⚠️  Agno clear() did not remove all memories")
                success = False
            else:
                print("   ✅ Agno clear() successful")
        else:
            print("   ✅ Agno clear() completed")
            
    except Exception as e:
        print(f"   ❌ Agno clear() failed: {e}")
        success = False
    
    # Method 2: Direct SQL deletion
    print("🔧 Method 2: Direct SQL deletion...")
    if user_id:
        sql_success = clear_user_memories_direct(db_file, user_id)
    else:
        sql_success = clear_memory_database_direct(db_file)
    
    if not sql_success:
        success = False
    
    return success


def main():
    """Main function for interactive database clearing."""
    db_file = "/tmp/agent.db"
    user_id = "ava"
    
    print("🗑️  Memory Database Cleaner")
    print("=" * 40)
    
    # Inspect database first
    print("🔍 Initial database state:")
    inspect_database(db_file)
    
    # Ask user what to clear
    print("\nSelect clearing option:")
    print("1. Clear memories for specific user (ava)")
    print("2. Clear all memories")
    print("3. Inspect database only")
    print("4. Exit")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            print(f"\n🧹 Clearing memories for user: {user_id}")
            success = clear_memory_database_comprehensive(db_file, user_id)
        elif choice == "2":
            print("\n🧹 Clearing ALL memory data...")
            success = clear_memory_database_comprehensive(db_file)
        elif choice == "3":
            print("\n🔍 Database inspection complete")
            return
        elif choice == "4":
            print("👋 Exiting...")
            return
        else:
            print("❌ Invalid choice")
            return
        
        # Final inspection
        print("\n🔍 Final database state:")
        inspect_database(db_file)
        
        if success:
            print("\n✅ Database cleaning completed successfully!")
        else:
            print("\n⚠️  Database cleaning completed with some issues")
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
