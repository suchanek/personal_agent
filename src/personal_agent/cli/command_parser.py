"""
Command parsing and routing for the Personal AI Agent CLI.

This module handles parsing user input and routing commands to appropriate handlers.
"""

from typing import Callable, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console
    from ..core.agno_agent import AgnoPersonalAgent

from .memory_commands import (
    clear_all_memories,
    delete_memories_by_topic_cli,
    delete_memory_by_id_cli,
    show_all_memories,
    show_all_memories_brief,
    show_memories_by_topic_cli,
    show_memory_analysis,
    show_memory_stats,
    store_immediate_memory,
)


class CommandParser:
    """Handles parsing and routing of CLI commands."""
    
    def __init__(self):
        self.commands: Dict[str, Callable] = {
            "memories": show_all_memories,
            "brief": show_all_memories_brief,
            "analysis": show_memory_analysis,
            "stats": show_memory_stats,
            "wipe": clear_all_memories,
            "help": self._handle_help,
            "clear": self._handle_clear,
            "examples": self._handle_examples,
        }
        
        # Commands that require additional parsing
        self.prefix_commands = {
            "delete memory ": self._handle_delete_memory,
            "delete topic ": self._handle_delete_topic,
            "!": self._handle_store_memory,
            "?": self._handle_query_memory,
        }
    
    def parse_command(self, user_input: str) -> Tuple[Optional[Callable], Optional[str], Optional[Dict]]:
        """
        Parse user input and return command handler, remaining text, and kwargs.
        
        Returns:
            Tuple of (command_handler, remaining_text, kwargs) or (None, None, None) if not a command
        """
        user_input = user_input.strip()
        
        # Check for quit commands
        if user_input.lower() in ["quit", "exit", "q"]:
            return self._handle_quit, None, {}
        
        # Check for direct commands
        if user_input.lower() in self.commands:
            return self.commands[user_input.lower()], None, {}
        
        # Check for prefix commands
        for prefix, handler in self.prefix_commands.items():
            if user_input.startswith(prefix):
                remaining = user_input[len(prefix):].strip()
                return handler, remaining, {}
        
        # Not a command - return None to indicate regular chat
        return None, user_input, {}
    
    async def _handle_delete_memory(self, agent: "AgnoPersonalAgent", memory_id: str, console: "Console"):
        """Handle delete memory command."""
        if memory_id:
            await delete_memory_by_id_cli(agent, memory_id, console)
        else:
            console.print("❌ Please provide a memory ID to delete.")
    
    async def _handle_delete_topic(self, agent: "AgnoPersonalAgent", topic: str, console: "Console"):
        """Handle delete topic command."""
        if topic:
            await delete_memories_by_topic_cli(agent, topic, console)
        else:
            console.print("❌ Please provide a topic to delete.")
    
    async def _handle_store_memory(self, agent: "AgnoPersonalAgent", content: str, console: "Console"):
        """Handle immediate memory storage command."""
        if content:
            await store_immediate_memory(agent, content, console)
        else:
            console.print("❌ Please provide content after '!' to store as memory")
    
    async def _handle_query_memory(self, agent: "AgnoPersonalAgent", query: str, console: "Console"):
        """Handle memory query command."""
        if query:
            await show_memories_by_topic_cli(agent, query, console)
        else:
            await show_all_memories(agent, console)
    
    def _handle_quit(self, *args, **kwargs):
        """Handle quit command - this is a special case handled by the main loop."""
        return "quit"
    
    async def _handle_help(self, agent: "AgnoPersonalAgent", console: "Console"):
        """Handle help command."""
        from rich.panel import Panel
        console.print("\n")
        console.print(
            Panel.fit(
                "🚀 Enhanced Personal AI Agent with Agno Framework\n\n"
                "This CLI provides an enhanced chat interface with memory management.\n\n"
                f"{self.get_help_text()}\n\n"
                "[bold yellow]Additional Commands:[/bold yellow]\n"
                "• 'help' - Show this help message\n"
                "• 'clear' - Clear the screen\n"
                "• 'examples' - Show example queries\n"
                "• 'quit' - Exit the agent",
                style="bold blue",
            )
        )
    
    async def _handle_clear(self, agent: "AgnoPersonalAgent", console: "Console"):
        """Handle clear command."""
        import os
        os.system("clear" if os.name == "posix" else "cls")
        console.print("🤖 Personal AI Agent")
        console.print("💬 Chat cleared. How can I help you?")
    
    async def _handle_examples(self, agent: "AgnoPersonalAgent", console: "Console"):
        """Handle examples command."""
        console.print("\n💡 [bold cyan]Example Queries:[/bold cyan]")
        console.print("  [yellow]Memory & Personal:[/yellow]")
        console.print("    - 'Remember that I love skiing and live in Colorado'")
        console.print("    - 'What do you remember about me?'")
        console.print("    - '! I work as a software engineer' (immediate storage)")
        console.print("    - '? work' (query memories about work)")
        console.print("    - 'memories' - Show all stored memories")
        console.print("    - 'brief' - Show brief list of all memories")
        console.print("    - 'analysis' - Show memory analysis")
        console.print("    - 'stats' - Show memory statistics")
        console.print("    - 'wipe' - Clear all memories (requires confirmation)")
        console.print("\n  [yellow]General Chat:[/yellow]")
        console.print("    - 'What's the weather like today?'")
        console.print("    - 'Help me write an email'")
        console.print("    - 'Explain quantum computing'")
        console.print("    - 'What are the latest AI developments?'")
    
    def get_help_text(self) -> str:
        """Return help text for available commands."""
        return """Commands:
• Type your message to chat
• Start with '!' to immediately store as memory
• Start with '?' to query memories by topic (e.g., `? work`)
• 'memories' - Show all memories
• 'brief' - Show brief list of all memories
• 'analysis' - Show memory analysis
• 'stats' - Show memory statistics
• 'wipe' - Clear all memories (requires confirmation)
• 'delete memory <id>' - Delete a memory by its ID
• 'delete topic <topic>' - Delete all memories for a topic
• 'help' - Show this help message
• 'clear' - Clear the screen
• 'examples' - Show example queries
• 'quit' - Exit the CLI"""
