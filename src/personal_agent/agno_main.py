"""
Agno-compatible main entry point for the Personal AI Agent.

This module orchestrates all components using the agno framework for modern
async agent operations while maintaining compatibility with existing infrastructure.

Refactored for better organization and maintainability.
"""

import argparse
import asyncio
import logging
from typing import Optional

from rich.console import Console

# Import core components
from .cli import run_agno_cli
from .core.agent_instruction_manager import InstructionLevel
from .core.agno_agent import AgnoPersonalAgent
from .core.agno_initialization import initialize_agno_system

# Global variables for cleanup
agno_agent: Optional[AgnoPersonalAgent] = None
logger: Optional[logging.Logger] = None


async def run_agno_cli_wrapper(
    query: str = None,  # noqa: ARG001
    use_remote_ollama: bool = False,
    recreate: bool = False,
    instruction_level: Optional[InstructionLevel] = None,
):
    """
    Wrapper function to initialize system and run CLI.

    :param query: Initial query to run (currently unused)
    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :param recreate: Whether to recreate the knowledge base
    :param instruction_level: The instruction level for the agent (None uses config default)
    """
    global agno_agent  # noqa: PLW0603

    # Initialize system
    agent, ollama_url = await initialize_agno_system(
        use_remote_ollama, recreate=recreate, instruction_level=instruction_level
    )

    agno_agent = agent

    # Create console for CLI
    console = Console(force_terminal=True)

    # Run the CLI
    await run_agno_cli(agent, ollama_url, console)


def cli_main():
    """
    Main entry point for CLI mode (used by poetry scripts).
    """
    parser = argparse.ArgumentParser(
        description="Run the Personal AI Agent with Agno Framework"
    )
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama server"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the knowledge base",
        default=False,
    )
    parser.add_argument(
        "--instruction-level",
        type=str,
        default=None,
        help="Set the instruction level for the agent (MINIMAL, CONCISE, STANDARD, EXPLICIT, EXPERIMENTAL). If not provided, uses config default.",
    )
    args = parser.parse_args()

    # Convert string instruction level to enum if provided
    instruction_level_enum = None
    if args.instruction_level:
        try:
            instruction_level_enum = InstructionLevel[args.instruction_level.upper()]
        except KeyError:
            valid_levels = [e.name for e in InstructionLevel]
            print(f"Error: Invalid instruction level '{args.instruction_level}'.")
            print(f"Valid options: {', '.join(valid_levels)}")
            return

    print("Starting Personal AI Agent in CLI mode...")
    asyncio.run(
        run_agno_cli_wrapper(
            use_remote_ollama=args.remote,
            recreate=args.recreate,
            instruction_level=instruction_level_enum,
        )
    )


if __name__ == "__main__":
    cli_main()
