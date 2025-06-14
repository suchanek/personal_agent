#!/usr/bin/env python3
"""
Memory Manager Tool for Personal AI Agent

This tool provides comprehensive memory database management capabilities including:
- List all users in the memory database
- View memories by user
- Search memories by content
- Delete specific memories or all memories for a user
- Database statistics and health checks
- Export memories to JSON

Usage:
    python memory_manager_tool.py                                       # Interactive mode (default)
    python memory_manager_tool.py interactive                           # Interactive mode (explicit)
    python memory_manager_tool.py --help
    python memory_manager_tool.py list-users
    python memory_manager_tool.py list-memories --user-id test_user
    python memory_manager_tool.py search --query "hiking" --user-id test_user
    python memory_manager_tool.py delete-memory --memory-id <id>
    python memory_manager_tool.py clear-user --user-id test_user
    python memory_manager_tool.py stats
    python memory_manager_tool.py export --user-id test_user --output memories.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.memory.v2.schema import UserMemory
from agno.models.ollama import Ollama
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.utils import setup_logging

# Configure logging
logger = setup_logging(__name__)
console = Console()


class MemoryManager:
    """Memory database manager with comprehensive inspection and management capabilities."""

    def __init__(self, db_path: str = None):
        """Initialize the memory manager.

        :param db_path: Path to the SQLite memory database. If None, uses the configured path from settings.
        """
        if db_path is None:
            # Use the proper database path from configuration
            db_path = f"{AGNO_STORAGE_DIR}/agent_memory.db"

        self.db_path = Path(db_path)
        self.db = SqliteMemoryDb(
            table_name="personal_agent_memory",  # Use the same table name as the actual agent
            db_file=str(self.db_path),
        )
        self.memory = Memory(model=Ollama(id="llama3.1:8b"), db=self.db)

        console.print(
            f"[green]Memory Manager initialized with database:[/green] {self.db_path}"
        )

        if not self.db_path.exists():
            console.print(
                f"[yellow]Warning: Database file does not exist: {self.db_path}[/yellow]"
            )

    def list_users(self) -> List[str]:
        """List all unique user IDs in the memory database.

        :return: List of user IDs
        """
        try:
            memories = self.db.read_memories()
            user_ids = list(
                set(memory.user_id for memory in memories if memory.user_id)
            )

            if not user_ids:
                console.print("[yellow]No users found in the database[/yellow]")
                return []

            # Create table
            table = Table(title="👥 Users in Memory Database")
            table.add_column("User ID", style="cyan")
            table.add_column("Memory Count", style="green", justify="right")

            for user_id in sorted(user_ids):
                user_memories = [m for m in memories if m.user_id == user_id]
                table.add_row(user_id, str(len(user_memories)))

            console.print(table)
            return user_ids

        except Exception as e:
            console.print(f"[red]Error listing users: {e}[/red]")
            return []

    def list_memories(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[UserMemory]:
        """List memories for a specific user.

        :param user_id: User ID to filter by
        :param limit: Maximum number of memories to return
        :return: List of user memories
        """
        try:
            memories = self.memory.search_user_memories(
                user_id=user_id, limit=limit or 100, retrieval_method="last_n"
            )

            if not memories:
                console.print(f"[yellow]No memories found for user: {user_id}[/yellow]")
                return []

            # Create table
            table = Table(title=f"🧠 Memories for User: {user_id}")
            table.add_column("ID", style="dim", width=12)
            table.add_column("Memory", style="white", width=60)
            table.add_column("Topics", style="blue", width=20)
            table.add_column("Created", style="green", width=12)

            for memory in memories:
                # Truncate long memories
                memory_text = memory.memory
                if len(memory_text) > 60:
                    memory_text = memory_text[:57] + "..."

                # Format topics
                topics_str = ", ".join(memory.topics) if memory.topics else "None"
                if len(topics_str) > 20:
                    topics_str = topics_str[:17] + "..."

                # Format created date
                created_str = "N/A"
                if hasattr(memory, "created_at") and memory.created_at:
                    if isinstance(memory.created_at, datetime):
                        created_str = memory.created_at.strftime("%m/%d %H:%M")
                    else:
                        created_str = str(memory.created_at)[:10]

                table.add_row(
                    str(memory.memory_id)[:12] if memory.memory_id else "N/A",
                    memory_text,
                    topics_str,
                    created_str,
                )

            console.print(table)
            console.print(f"\n[green]Total memories: {len(memories)}[/green]")
            return memories

        except Exception as e:
            console.print(f"[red]Error listing memories: {e}[/red]")
            return []

    def search_memories(
        self, query: str, user_id: Optional[str] = None, limit: int = 10
    ) -> List[UserMemory]:
        """Search memories by content.

        :param query: Search query
        :param user_id: Optional user ID to filter by
        :param limit: Maximum number of results
        :return: List of matching memories
        """
        try:
            if user_id:
                memories = self.memory.search_user_memories(
                    user_id=user_id,
                    query=query,
                    retrieval_method="agentic",
                    limit=limit,
                )
            else:
                # Search all memories - these are MemoryRow objects
                all_memories = self.db.read_memories()
                memories = []
                for m in all_memories:
                    # Check if the query is in the memory content
                    memory_content = (
                        m.memory.get("memory", "")
                        if hasattr(m.memory, "get")
                        else str(m.memory)
                    )
                    if query.lower() in memory_content.lower():
                        memories.append(m)
                memories = memories[:limit]

            if not memories:
                console.print(f"[yellow]No memories found matching: '{query}'[/yellow]")
                return []

            # Create table
            title = f"🔍 Search Results for: '{query}'"
            if user_id:
                title += f" (User: {user_id})"

            table = Table(title=title)
            table.add_column("ID", style="dim", width=12)
            table.add_column("User", style="cyan", width=15)
            table.add_column("Memory", style="white", width=50)
            table.add_column("Topics", style="blue", width=15)

            for memory in memories:
                # Handle both UserMemory and MemoryRow objects
                if hasattr(memory, "memory_id"):  # UserMemory object
                    memory_id = (
                        str(memory.memory_id)[:12] if memory.memory_id else "N/A"
                    )
                    memory_text = memory.memory
                    topics = memory.topics
                    display_user_id = user_id or "N/A"
                else:  # MemoryRow object
                    memory_id = str(memory.id)[:12] if memory.id else "N/A"
                    memory_text = (
                        memory.memory.get("memory", "")
                        if hasattr(memory.memory, "get")
                        else str(memory.memory)
                    )
                    topics = (
                        memory.memory.get("topics", [])
                        if hasattr(memory.memory, "get")
                        else []
                    )
                    display_user_id = memory.user_id or "N/A"

                # Truncate long memory text
                if len(memory_text) > 50:
                    memory_text = memory_text[:47] + "..."

                topics_str = ", ".join(topics) if topics else "None"
                if len(topics_str) > 15:
                    topics_str = topics_str[:12] + "..."

                table.add_row(
                    memory_id,
                    display_user_id,
                    memory_text,
                    topics_str,
                )

            console.print(table)
            console.print(f"\n[green]Found {len(memories)} matching memories[/green]")
            return memories

        except Exception as e:
            console.print(f"[red]Error searching memories: {e}[/red]")
            return []

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory by ID.

        :param memory_id: Memory ID to delete
        :return: True if successful, False otherwise
        """
        try:
            # Find the memory first
            all_memories = self.db.read_memories()
            memory_to_delete = None

            for memory in all_memories:
                if (
                    str(memory.id) == memory_id
                    or str(memory.id).startswith(memory_id)
                    or (
                        hasattr(memory.memory, "get")
                        and memory.memory.get("memory_id") == memory_id
                    )
                    or (
                        hasattr(memory.memory, "get")
                        and str(memory.memory.get("memory_id", "")).startswith(
                            memory_id
                        )
                    )
                ):
                    memory_to_delete = memory
                    break

            if not memory_to_delete:
                console.print(f"[red]Memory not found with ID: {memory_id}[/red]")
                return False

            # Show memory details
            console.print(
                Panel(
                    f"[bold]Memory to delete:[/bold]\n"
                    f"ID: {memory_to_delete.id}\n"
                    f"User: {memory_to_delete.user_id}\n"
                    f"Content: {memory_to_delete.memory.get('memory', 'N/A')[:100] if hasattr(memory_to_delete.memory, 'get') else str(memory_to_delete.memory)[:100]}...\n"
                    f"Topics: {memory_to_delete.memory.get('topics', []) if hasattr(memory_to_delete.memory, 'get') else 'N/A'}",
                    title="⚠️  Confirm Deletion",
                )
            )

            if not Confirm.ask("Are you sure you want to delete this memory?"):
                console.print("[yellow]Deletion cancelled[/yellow]")
                return False

            # Delete the memory
            self.db.delete(memory_to_delete.id)
            console.print(f"[green]✅ Successfully deleted memory: {memory_id}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Error deleting memory: {e}[/red]")
            return False

    def clear_user_memories(self, user_id: str) -> bool:
        """Delete all memories for a specific user.

        :param user_id: User ID to clear memories for
        :return: True if successful, False otherwise
        """
        try:
            # Get user memories
            user_memories = [m for m in self.db.read_memories() if m.user_id == user_id]

            if not user_memories:
                console.print(f"[yellow]No memories found for user: {user_id}[/yellow]")
                return False

            console.print(
                f"[yellow]Found {len(user_memories)} memories for user: {user_id}[/yellow]"
            )

            if not Confirm.ask(
                f"Are you sure you want to delete ALL {len(user_memories)} memories for user '{user_id}'?"
            ):
                console.print("[yellow]Deletion cancelled[/yellow]")
                return False

            # Delete all user memories
            deleted_count = 0
            for memory in user_memories:
                try:
                    self.db.delete(memory.id)
                    deleted_count += 1
                except Exception as e:
                    console.print(f"[red]Error deleting memory {memory.id}: {e}[/red]")

            console.print(
                f"[green]✅ Successfully deleted {deleted_count} memories for user: {user_id}[/green]"
            )
            return True

        except Exception as e:
            console.print(f"[red]Error clearing user memories: {e}[/red]")
            return False

    def get_stats(self) -> Dict:
        """Get database statistics.

        :return: Dictionary with database statistics
        """
        try:
            all_memories = self.db.read_memories()

            if not all_memories:
                console.print("[yellow]Database is empty[/yellow]")
                return {}

            # Calculate statistics
            users = list(set(m.user_id for m in all_memories if m.user_id))
            total_memories = len(all_memories)

            # Memory count by user
            user_counts = {}
            for user in users:
                user_counts[user] = len([m for m in all_memories if m.user_id == user])

            # Topic analysis
            topic_counts = {}
            for memory in all_memories:
                if hasattr(memory.memory, "get") and memory.memory.get("topics"):
                    for topic in memory.memory.get("topics", []):
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1

            stats = {
                "total_memories": total_memories,
                "total_users": len(users),
                "users": users,
                "user_memory_counts": user_counts,
                "topic_counts": topic_counts,
                "database_path": str(self.db_path),
                "database_size": (
                    self.db_path.stat().st_size if self.db_path.exists() else 0
                ),
            }

            # Display statistics
            console.print(
                Panel(
                    f"[bold]Database Statistics[/bold]\n\n"
                    f"📊 Total Memories: {total_memories}\n"
                    f"👥 Total Users: {len(users)}\n"
                    f"📁 Database Size: {stats['database_size']:,} bytes\n"
                    f"📍 Database Path: {self.db_path}",
                    title="📈 Memory Database Stats",
                )
            )

            # User breakdown table
            if user_counts:
                table = Table(title="Memory Count by User")
                table.add_column("User ID", style="cyan")
                table.add_column("Memory Count", style="green", justify="right")

                for user, count in sorted(
                    user_counts.items(), key=lambda x: x[1], reverse=True
                ):
                    table.add_row(user, str(count))

                console.print(table)

            # Top topics table
            if topic_counts:
                table = Table(title="Top Topics")
                table.add_column("Topic", style="blue")
                table.add_column("Count", style="green", justify="right")

                for topic, count in sorted(
                    topic_counts.items(), key=lambda x: x[1], reverse=True
                )[:10]:
                    table.add_row(topic, str(count))

                console.print(table)

            return stats

        except Exception as e:
            console.print(f"[red]Error getting stats: {e}[/red]")
            return {}

    def export_memories(
        self, user_id: Optional[str] = None, output_file: str = "memories_export.json"
    ) -> bool:
        """Export memories to JSON file.

        :param user_id: Optional user ID to filter by
        :param output_file: Output file path
        :return: True if successful, False otherwise
        """
        try:
            all_memories = self.db.read_memories()

            if user_id:
                memories_to_export = [m for m in all_memories if m.user_id == user_id]
                title = f"Memories for user: {user_id}"
            else:
                memories_to_export = all_memories
                title = "All memories"

            if not memories_to_export:
                console.print(f"[yellow]No memories to export[/yellow]")
                return False

            # Convert to exportable format
            export_data = {
                "export_date": datetime.now().isoformat(),
                "export_type": title,
                "total_memories": len(memories_to_export),
                "memories": [],
            }

            for memory in memories_to_export:
                memory_data = {
                    "id": str(memory.id) if memory.id else None,
                    "user_id": memory.user_id,
                    "memory": (
                        memory.memory.get("memory", "N/A")
                        if hasattr(memory.memory, "get")
                        else str(memory.memory)
                    ),
                    "topics": (
                        memory.memory.get("topics", [])
                        if hasattr(memory.memory, "get")
                        else []
                    ),
                    "created_at": (
                        memory.last_updated.isoformat()
                        if hasattr(memory, "last_updated") and memory.last_updated
                        else None
                    ),
                }
                export_data["memories"].append(memory_data)

            # Write to file
            output_path = Path(output_file)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            console.print(
                f"[green]✅ Exported {len(memories_to_export)} memories to: {output_path}[/green]"
            )
            return True

        except Exception as e:
            console.print(f"[red]Error exporting memories: {e}[/red]")
            return False


def interactive_mode(manager: MemoryManager):
    """Run the memory manager in interactive mode with a menu-driven interface.

    :param manager: MemoryManager instance to use
    """
    console.print("\n[bold green]🧠 Memory Manager - Interactive Mode[/bold green]")

    while True:
        try:
            # Display menu
            console.print("\n[bold cyan]Available Commands:[/bold cyan]")
            console.print(
                "  [cyan]1.[/cyan] list-users     - List all users in the database"
            )
            console.print(
                "  [cyan]2.[/cyan] list-memories  - List memories for a specific user"
            )
            console.print(
                "  [cyan]3.[/cyan] search         - Search memories by content"
            )
            console.print(
                "  [cyan]4.[/cyan] delete-memory  - Delete a specific memory by ID"
            )
            console.print(
                "  [cyan]5.[/cyan] clear-user     - Delete all memories for a user"
            )
            console.print("  [cyan]6.[/cyan] stats          - Show database statistics")
            console.print(
                "  [cyan]7.[/cyan] export         - Export memories to JSON file"
            )
            console.print("  [cyan]8.[/cyan] help           - Show detailed help")
            console.print("  [cyan]9.[/cyan] quit           - Exit interactive mode")

            choice = Prompt.ask(
                "\n[bold yellow]Enter your choice (1-9 or command name)[/bold yellow]",
                default="6",
            )

            # Convert number choices to command names
            if choice == "1":
                choice = "list-users"
            elif choice == "2":
                choice = "list-memories"
            elif choice == "3":
                choice = "search"
            elif choice == "4":
                choice = "delete-memory"
            elif choice == "5":
                choice = "clear-user"
            elif choice == "6":
                choice = "stats"
            elif choice == "7":
                choice = "export"
            elif choice == "8":
                choice = "help"
            elif choice == "9":
                choice = "quit"

            if choice == "quit":
                console.print("[yellow]Goodbye![/yellow]")
                break

            elif choice == "help":
                show_help()

            elif choice == "list-users":
                manager.list_users()

            elif choice == "list-memories":
                user_id = Prompt.ask("[cyan]Enter User ID[/cyan]")
                limit_str = Prompt.ask(
                    "[cyan]Enter limit (optional)[/cyan]", default=""
                )
                limit = int(limit_str) if limit_str.isdigit() else None
                manager.list_memories(user_id=user_id, limit=limit)

            elif choice == "search":
                query = Prompt.ask("[cyan]Enter search query[/cyan]")
                user_id = Prompt.ask(
                    "[cyan]Enter User ID (optional)[/cyan]", default=""
                )
                limit_str = Prompt.ask("[cyan]Enter limit[/cyan]", default="10")
                limit = int(limit_str) if limit_str.isdigit() else 10
                user_id = user_id if user_id else None
                manager.search_memories(query=query, user_id=user_id, limit=limit)

            elif choice == "delete-memory":
                memory_id = Prompt.ask("[cyan]Enter Memory ID to delete[/cyan]")
                manager.delete_memory(memory_id=memory_id)

            elif choice == "clear-user":
                user_id = Prompt.ask("[cyan]Enter User ID to clear all memories[/cyan]")
                manager.clear_user_memories(user_id=user_id)

            elif choice == "stats":
                manager.get_stats()

            elif choice == "export":
                user_id = Prompt.ask(
                    "[cyan]Enter User ID (optional)[/cyan]", default=""
                )
                output_file = Prompt.ask(
                    "[cyan]Enter output filename[/cyan]", default="memories_export.json"
                )
                user_id = user_id if user_id else None
                manager.export_memories(user_id=user_id, output_file=output_file)

        except KeyboardInterrupt:
            console.print(
                "\n[yellow]Operation cancelled. Type 'quit' to exit.[/yellow]"
            )
        except EOFError:
            console.print("\n[yellow]EOF detected. Exiting interactive mode.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def show_help():
    """Display help information for interactive mode."""
    help_text = """
[bold]Available Commands:[/bold]

[cyan]list-users[/cyan]     - List all users in the database
[cyan]list-memories[/cyan]  - List memories for a specific user
[cyan]search[/cyan]         - Search memories by content
[cyan]delete-memory[/cyan]  - Delete a specific memory by ID
[cyan]clear-user[/cyan]     - Delete all memories for a user
[cyan]stats[/cyan]          - Show database statistics
[cyan]export[/cyan]         - Export memories to JSON file
[cyan]help[/cyan]           - Show this help message
[cyan]quit[/cyan]           - Exit interactive mode

[bold]Examples:[/bold]
• Use [cyan]list-users[/cyan] to see all users, then [cyan]list-memories[/cyan] to view their memories
• Use [cyan]search[/cyan] to find memories containing specific words
• Use [cyan]stats[/cyan] to get an overview of your memory database
"""
    console.print(help_text)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Memory Manager Tool for Personal AI Agent"
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Path to memory database (default: uses global AGNO_STORAGE_DIR configuration)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List users command
    subparsers.add_parser("list-users", help="List all users in the database")

    # List memories command
    list_parser = subparsers.add_parser(
        "list-memories", help="List memories for a user"
    )
    list_parser.add_argument(
        "--user-id", required=True, help="User ID to list memories for"
    )
    list_parser.add_argument(
        "--limit", type=int, help="Maximum number of memories to show"
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="Search memories by content")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--user-id", help="Optional user ID to filter by")
    search_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of results"
    )

    # Delete memory command
    delete_parser = subparsers.add_parser(
        "delete-memory", help="Delete a specific memory"
    )
    delete_parser.add_argument("--memory-id", required=True, help="Memory ID to delete")

    # Clear user command
    clear_parser = subparsers.add_parser(
        "clear-user", help="Delete all memories for a user"
    )
    clear_parser.add_argument(
        "--user-id", required=True, help="User ID to clear memories for"
    )

    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export memories to JSON")
    export_parser.add_argument("--user-id", help="Optional user ID to filter by")
    export_parser.add_argument(
        "--output", default="memories_export.json", help="Output file path"
    )

    # Interactive command
    subparsers.add_parser("interactive", help="Run in interactive mode")

    args = parser.parse_args()

    # If no command is provided, default to interactive mode
    if not args.command:
        console.print(
            "[yellow]No command specified. Starting interactive mode...[/yellow]"
        )
        manager = MemoryManager(db_path=args.db_path)
        interactive_mode(manager)
        return

    # Initialize memory manager
    manager = MemoryManager(db_path=args.db_path)

    # Execute command
    try:
        if args.command == "list-users":
            manager.list_users()

        elif args.command == "list-memories":
            manager.list_memories(user_id=args.user_id, limit=args.limit)

        elif args.command == "search":
            manager.search_memories(
                query=args.query, user_id=args.user_id, limit=args.limit
            )

        elif args.command == "delete-memory":
            manager.delete_memory(memory_id=args.memory_id)

        elif args.command == "clear-user":
            manager.clear_user_memories(user_id=args.user_id)

        elif args.command == "stats":
            manager.get_stats()

        elif args.command == "export":
            manager.export_memories(user_id=args.user_id, output_file=args.output)

        elif args.command == "interactive":
            interactive_mode(manager)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error("Command failed", exc_info=True)


if __name__ == "__main__":
    main()
