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
from .core.agno_agent import AgnoPersonalAgent
from .core.agno_initialization import initialize_agno_system

# Global variables for cleanup
agno_agent: Optional[AgnoPersonalAgent] = None
logger: Optional[logging.Logger] = None


async def run_agno_cli_wrapper(
    query: str = None,
    use_remote_ollama: bool = False,
    recreate: bool = False,
    instruction_level: str = "NONE",
):
    """
    Wrapper function to initialize system and run CLI.

    :param query: Initial query to run (currently unused)
    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :param recreate: Whether to recreate the knowledge base
    :param instruction_level: The instruction level for the agent
    """
    global agno_agent

    # Initialize system
    agent, query_kb, store_int, clear_kb, ollama_url = await initialize_agno_system(
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
        "--recreate", action="store_true", help="Recreate the knowledge base"
    )
    parser.add_argument(
        "--instruction-level",
        type=str,
        default="STANDARD",
        help="Set the instruction level for the agent (MINIMAL, CONCISE, STANDARD, EXPLICIT, EXPERIMENTAL)",
    )
    args = parser.parse_args()

    print("Starting Personal AI Agent in CLI mode...")
    asyncio.run(
        run_agno_cli_wrapper(
            use_remote_ollama=args.remote,
            recreate=args.recreate,
            instruction_level=args.instruction_level,
        )
    )


if __name__ == "__main__":
    cli_main()
