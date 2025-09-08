"""
Main CLI interface for the Personal AI Agent with Agno Framework.

This module contains the refactored CLI logic extracted from agno_main.py
for better organization and maintainability.
"""

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel

if TYPE_CHECKING:
    from ..core.agno_agent import AgnoPersonalAgent

from .command_parser import CommandParser


async def run_agno_cli(
    agent: "AgnoPersonalAgent", ollama_url: str, console: Console = None
):
    """
    Run agno agent in CLI mode with enhanced interface.

    :param agent: The initialized AgnoPersonalAgent instance
    :param ollama_url: The Ollama server URL being used
    :param console: Optional Rich console instance
    """
    if console is None:
        console = Console(force_terminal=True)

    # Initialize command parser
    command_parser = CommandParser()

    # Ensure agent is initialized before showing info
    console.print("✅ [bold green]Agent Successfully Initialized![/bold green]")
    # Trigger lazy initialization by calling a simple method
    await agent._ensure_initialized()
    agent.print_agent_info(console)

    # Display the welcome panel
    console.print("\n")  # Add some space
    console.print(
        Panel.fit(
            "🚀 Enhanced Personal AI Agent with Agno Framework\n\n"
            "This CLI provides an enhanced chat interface with memory management.\n\n"
            f"{command_parser.get_help_text()}",
            style="bold blue",
        )
    )

    console.print(f"🖥️  Using Ollama at: {ollama_url}")

    try:
        while True:
            # Get user input
            user_input = input("\n💬 You: ").strip()

            if not user_input:
                continue

            # Parse the command
            command_handler, remaining_text, kwargs = command_parser.parse_command(
                user_input
            )

            # Handle quit command specially
            if (
                command_handler
                and hasattr(command_handler, "__name__")
                and command_handler.__name__ == "_handle_quit"
            ):
                console.print("👋 Goodbye!")
                break

            # If it's a command, execute it
            if command_handler:
                try:
                    if remaining_text is not None:
                        await command_handler(agent, remaining_text, console)
                    else:
                        await command_handler(agent, console)
                    continue
                except Exception as e:
                    console.print(f"� Error executing command: {e}")
                    continue

            # If not a command, treat as regular chat
            try:
                # Get response from agent using streaming aprint_response
                console.print("🤖 Assistant:")
                await agent.aprint_response(
                    user_input,
                    stream=True,  # Use streaming for better responsiveness
                    show_tool_calls=True,  # Show tool calls in CLI
                )

            except Exception as e:
                console.print(f"💥 Error: {e}")

    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    finally:
        try:
            await agent.cleanup()
        except Exception as e:
            console.print(f"Warning during cleanup: {e}")
