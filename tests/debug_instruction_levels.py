"""
Debug script for testing the various instruction sophistication levels
for the AgnoPersonalAgent.

This script iterates through each InstructionLevel, creates an agent instance,
generates the instruction string, and prints it to the console for review.
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Adjust the path to import from the src directory
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.personal_agent.core.agno_agent import AgnoPersonalAgent, InstructionLevel


def test_instruction_levels():
    """
    Tests and displays the generated instructions for each sophistication level.
    """
    console = Console()
    console.print(
        "[bold magenta]--- Testing Agent Instruction Sophistication Levels ---[/bold magenta]\n"
    )

    # Loop through each defined instruction level
    for level in InstructionLevel:
        console.print(
            Panel(
                f"[bold cyan]Testing Level: {level.name}[/bold cyan]",
                expand=False,
                border_style="cyan",
            )
        )

        # 1. Create an instance of the agent with the specific instruction level
        # We can use default parameters for other settings as they don't affect the instructions.
        agent = AgnoPersonalAgent(instruction_level=level, seed=12345)

        # 2. Generate the instructions by calling the (internal) method
        # In a real application, this is called during agent.initialize()
        instruction_string = agent._create_agent_instructions()

        # 3. Print the generated instructions for review
        console.print(f"[bold green]Generated Instructions for {level.name}:[/bold green]")

        # Use Rich's Syntax to pretty-print the markdown-like instructions
        syntax = Syntax(instruction_string, "markdown", theme="solarized-dark", line_numbers=True)
        console.print(syntax)
        console.print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    test_instruction_levels()