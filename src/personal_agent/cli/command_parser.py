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
            "analysis": show_memory_analysis,
            "stats": show_memory_stats,
            "clear": clear_all_memories,
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
    
    def get_help_text(self) -> str:
        """Return help text for available commands."""
        return """Commands:
• Type your message to chat
• Start with '!' to immediately store as memory
• Start with '?' to query memories by topic (e.g., `? work`)
• 'memories' - Show all memories
• 'analysis' - Show memory analysis
• 'stats' - Show memory statistics
• 'clear' - Clear all memories
• 'delete memory <id>' - Delete a memory by its ID
• 'delete topic <topic>' - Delete all memories for a topic
• 'quit' - Exit the CLI"""
