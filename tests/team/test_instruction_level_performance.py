#!/usr/bin/env python3
"""
Test script to compare response performance across different instruction sophistication levels.

This script creates AgnoPersonalAgent instances with different InstructionLevel settings,
asks the same question to each, times the responses, and prints a comparison.
"""
# pylint: disable=C0413,C0301
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from src.personal_agent.config import LLM_MODEL, OLLAMA_URL
from src.personal_agent.core.agno_agent import AgnoPersonalAgent, InstructionLevel
from src.personal_agent.utils import setup_logging

# Configure logging
logger = setup_logging(__name__)
logging.getLogger().setLevel(logging.WARNING)

# LLM_MODEL = "llama3.1:8b-instruct-q8_0"
LLM_MODEL = "qwen3:1.7B"


# Configuration
WARMUP_QUESTION = "Hello!"
TEST_QUESTIONS = [
    "What's the weather like today and what should I wear?",
    "What's the current stock price of NVDA and should I buy it?",
]
MEMORY_TEST_QUESTIONS = [
    "Remember that I love hiking and my favorite trail is the Blue Ridge Trail.",
    "What do you remember about my hobbies?",
]
MODELS_TO_TEST = [LLM_MODEL]  # Use the current configured model
INSTRUCTION_LEVELS = list(InstructionLevel)


async def _test_agent_with_level(
    instruction_level: InstructionLevel,
    question: str,
    model_name: str = LLM_MODEL,
    console: Console = None,
    enable_memory: bool = False,
) -> Tuple[str, float, bool]:
    """
    Test an agent with a specific instruction level.

    Args:
        instruction_level: The InstructionLevel to test
        question: The question to ask the agent
        model_name: The model name to use
        console: Rich console for output

    Returns:
        Tuple of (response_content, response_time, success)
    """
    if console:
        console.print(f"[cyan]Testing {instruction_level.name}...[/cyan]")

    start_time = time.time()

    try:
        # Create agent with specific instruction level
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=model_name,
            enable_memory=enable_memory,  # Memory setting based on test type
            enable_mcp=False,  # Disable MCP for cleaner testing
            debug=False,  # Disable debug for cleaner output
            ollama_base_url=OLLAMA_URL,
            user_id=f"test_user_{instruction_level.name.lower()}_{'mem' if enable_memory else 'nomem'}",
            instruction_level=instruction_level,
            seed=42,  # Fixed seed for consistency
        )

        # Initialize the agent
        success = await agent.initialize()
        if not success:
            return (
                f"Failed to initialize agent with {instruction_level.name}",
                0.0,
                False,
            )

        # Warmup the model with a simple question (don't time this)
        if console:
            console.print("[dim]Running warmup question...[/dim]")
        await agent.run(WARMUP_QUESTION)

        # Now ask the actual question and time it
        actual_start_time = time.time()
        response = await agent.run(question)
        end_time = time.time()
        response_time = end_time - actual_start_time

        # Clean up
        await agent.cleanup()

        return response, response_time, True

    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        error_msg = f"Error with {instruction_level.name}: {str(e)}"
        if console:
            console.print(f"[red]{error_msg}[/red]")
        return error_msg, response_time, False


async def run_instruction_level_comparison():
    """
    Run the instruction level comparison test.
    """
    console = Console()

    console.print(
        Panel(
            "[bold magenta]Instruction Level Performance Comparison[/bold magenta]\n"
            f"Current Model: [yellow]{LLM_MODEL}[/yellow]\n"
            f"Ollama URL: [cyan]{OLLAMA_URL}[/cyan]\n"
            f"Warmup Question: [dim]{WARMUP_QUESTION}[/dim]\n"
            f"Standard Questions: [green]{len(TEST_QUESTIONS)}[/green]\n"
            f"Memory Questions: [blue]{len(MEMORY_TEST_QUESTIONS)}[/blue]",
            title="Test Configuration",
            border_style="magenta",
        )
    )

    all_results: List[Dict] = []

    # Test standard questions (no memory)
    console.print(f"\n[bold red]{'='*80}[/bold red]")
    console.print("[bold red]STANDARD TESTS (Memory Disabled)[/bold red]")
    console.print(f"[bold red]{'='*80}[/bold red]")

    for question_idx, question in enumerate(TEST_QUESTIONS, 1):
        console.print(f"\n[bold yellow]{'='*80}[/bold yellow]")
        console.print(
            f"[bold yellow]STANDARD QUESTION {question_idx}: {question}[/bold yellow]"
        )
        console.print(f"[bold yellow]{'='*80}[/bold yellow]")

        question_results: List[Dict] = []

        # Test each instruction level for this question
        for level in INSTRUCTION_LEVELS:
            console.print(
                f"\n[bold blue]--- Testing {level.name} (No Memory) ---[/bold blue]"
            )

            response, response_time, success = await _test_agent_with_level(
                instruction_level=level,
                question=question,
                model_name=LLM_MODEL,
                console=console,
                enable_memory=False,
            )

            result = {
                "question": question,
                "question_idx": question_idx,
                "question_type": "standard",
                "level": level.name,
                "response": response,
                "time": response_time,
                "success": success,
                "response_length": len(response) if response else 0,
                "memory_enabled": False,
            }

            question_results.append(result)
            all_results.append(result)

            # Print immediate results
            status = "✅ Success" if success else "❌ Failed"
            console.print(f"Status: {status}")
            console.print(f"Time: [green]{response_time:.2f}s[/green]")
            console.print(
                f"Response length: [yellow]{len(response) if response else 0} chars[/yellow]"
            )

            if success and response:
                # Show first 200 chars of response
                preview = response[:200] + "..." if len(response) > 200 else response
                console.print(f"Response preview: [white]{preview}[/white]")

            console.print("-" * 60)

        # Print summary table for this question
        console.print(
            f"\n[bold green]Performance Summary for Standard Question {question_idx}[/bold green]"
        )
        print_question_summary(console, question_results)

    # Test memory questions (memory enabled)
    console.print(f"\n[bold purple]{'='*80}[/bold purple]")
    console.print("[bold purple]MEMORY TESTS (Memory Enabled)[/bold purple]")
    console.print(f"[bold purple]{'='*80}[/bold purple]")

    for question_idx, question in enumerate(MEMORY_TEST_QUESTIONS, 1):
        console.print(f"\n[bold yellow]{'='*80}[/bold yellow]")
        console.print(
            f"[bold yellow]MEMORY QUESTION {question_idx}: {question}[/bold yellow]"
        )
        console.print(f"[bold yellow]{'='*80}[/bold yellow]")

        question_results: List[Dict] = []

        # Test each instruction level for this question
        for level in INSTRUCTION_LEVELS:
            console.print(
                f"\n[bold blue]--- Testing {level.name} (With Memory) ---[/bold blue]"
            )

            response, response_time, success = await _test_agent_with_level(
                instruction_level=level,
                question=question,
                model_name=LLM_MODEL,
                console=console,
                enable_memory=True,
            )

            result = {
                "question": question,
                "question_idx": len(TEST_QUESTIONS) + question_idx,
                "question_type": "memory",
                "level": level.name,
                "response": response,
                "time": response_time,
                "success": success,
                "response_length": len(response) if response else 0,
                "memory_enabled": True,
            }

            question_results.append(result)
            all_results.append(result)

            # Print immediate results
            status = "✅ Success" if success else "❌ Failed"
            console.print(f"Status: {status}")
            console.print(f"Time: [green]{response_time:.2f}s[/green]")
            console.print(
                f"Response length: [yellow]{len(response) if response else 0} chars[/yellow]"
            )

            if success and response:
                # Show first 200 chars of response
                preview = response[:200] + "..." if len(response) > 200 else response
                console.print(f"Response preview: [white]{preview}[/white]")

            console.print("-" * 60)

        # Print summary table for this question
        console.print(
            f"\n[bold green]Performance Summary for Memory Question {question_idx}[/bold green]"
        )
        print_question_summary(console, question_results)

    # Print overall summary
    console.print(f"\n[bold magenta]{'='*80}[/bold magenta]")
    console.print("[bold magenta]OVERALL PERFORMANCE SUMMARY[/bold magenta]")
    console.print(f"[bold magenta]{'='*80}[/bold magenta]")

    # Group results by question type and question for comparison
    console.print("\n[bold cyan]STANDARD QUESTIONS SUMMARY[/bold cyan]")
    for question_idx in range(1, len(TEST_QUESTIONS) + 1):
        question_results = [
            r
            for r in all_results
            if r["question_idx"] == question_idx and r["question_type"] == "standard"
        ]
        if question_results:
            question = question_results[0]["question"]
            console.print(
                f"\n[bold cyan]Standard Question {question_idx}: {question}[/bold cyan]"
            )
            print_question_summary(console, question_results)

    console.print("\n[bold purple]MEMORY QUESTIONS SUMMARY[/bold purple]")
    for question_idx in range(
        len(TEST_QUESTIONS) + 1, len(TEST_QUESTIONS) + len(MEMORY_TEST_QUESTIONS) + 1
    ):
        question_results = [
            r
            for r in all_results
            if r["question_idx"] == question_idx and r["question_type"] == "memory"
        ]
        if question_results:
            question = question_results[0]["question"]
            memory_q_num = question_idx - len(TEST_QUESTIONS)
            console.print(
                f"\n[bold purple]Memory Question {memory_q_num}: {question}[/bold purple]"
            )
            print_question_summary(console, question_results)

    # Print detailed responses for all questions
    console.print(f"\n[bold yellow]{'='*80}[/bold yellow]")
    console.print("[bold yellow]DETAILED RESPONSES[/bold yellow]")
    console.print(f"[bold yellow]{'='*80}[/bold yellow]")

    # Standard questions detailed responses
    console.print("\n[bold cyan]STANDARD QUESTIONS DETAILED RESPONSES[/bold cyan]")
    for question_idx in range(1, len(TEST_QUESTIONS) + 1):
        question_results = [
            r
            for r in all_results
            if r["question_idx"] == question_idx and r["question_type"] == "standard"
        ]
        if question_results:
            question = question_results[0]["question"]
            console.print(
                f"\n[bold cyan]Standard Question {question_idx}: {question}[/bold cyan]"
            )

            for result in question_results:
                if result["success"]:
                    console.print(
                        f"\n[bold white]--- {result['level']} Response (No Memory) ---[/bold white]"
                    )
                    console.print(f"[white]{result['response']}[/white]")
                    console.print(
                        f"[dim]Time: {result['time']:.2f}s | Length: {result['response_length']} chars[/dim]"
                    )
                    console.print("-" * 80)

    # Memory questions detailed responses
    console.print("\n[bold purple]MEMORY QUESTIONS DETAILED RESPONSES[/bold purple]")
    for question_idx in range(
        len(TEST_QUESTIONS) + 1, len(TEST_QUESTIONS) + len(MEMORY_TEST_QUESTIONS) + 1
    ):
        question_results = [
            r
            for r in all_results
            if r["question_idx"] == question_idx and r["question_type"] == "memory"
        ]
        if question_results:
            question = question_results[0]["question"]
            memory_q_num = question_idx - len(TEST_QUESTIONS)
            console.print(
                f"\n[bold purple]Memory Question {memory_q_num}: {question}[/bold purple]"
            )

            for result in question_results:
                if result["success"]:
                    console.print(
                        f"\n[bold white]--- {result['level']} Response (With Memory) ---[/bold white]"
                    )
                    console.print(f"[white]{result['response']}[/white]")
                    console.print(
                        f"[dim]Time: {result['time']:.2f}s | Length: {result['response_length']} chars[/dim]"
                    )
                    console.print("-" * 80)

    # Calculate and show overall statistics
    print_overall_statistics(console, all_results)


def print_question_summary(console: Console, results: List[Dict]) -> None:
    """Print a summary table for a single question's results."""
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Instruction Level", style="cyan", width=15)
    table.add_column("Status", style="white", width=10)
    table.add_column("Time (s)", style="green", justify="right", width=10)
    table.add_column("Response Length", style="yellow", justify="right", width=15)
    table.add_column("Chars/Second", style="magenta", justify="right", width=12)

    for result in results:
        status_icon = "✅" if result["success"] else "❌"
        chars_per_sec = (
            result["response_length"] / result["time"]
            if result["time"] > 0 and result["success"]
            else 0
        )

        table.add_row(
            result["level"],
            status_icon,
            f"{result['time']:.2f}",
            str(result["response_length"]),
            f"{chars_per_sec:.1f}",
        )

    console.print(table)


def print_overall_statistics(console: Console, all_results: List[Dict]) -> None:
    """Print overall statistics across all questions and instruction levels."""
    successful_results = [r for r in all_results if r["success"]]
    if not successful_results:
        console.print("[red]No successful results to analyze[/red]")
        return

    # Separate standard and memory results
    standard_results = [
        r for r in successful_results if r["question_type"] == "standard"
    ]
    memory_results = [r for r in successful_results if r["question_type"] == "memory"]

    # Calculate statistics by instruction level for standard questions
    console.print("\n")
    console.print(
        Panel(
            "[bold white]Standard Questions Statistics by Instruction Level[/bold white]",
            border_style="cyan",
        )
    )

    if standard_results:
        print_stats_table(console, standard_results, "Standard")

    # Calculate statistics by instruction level for memory questions
    console.print("\n")
    console.print(
        Panel(
            "[bold white]Memory Questions Statistics by Instruction Level[/bold white]",
            border_style="purple",
        )
    )

    if memory_results:
        print_stats_table(console, memory_results, "Memory")

    # Overall comparison
    console.print("\n")
    console.print(
        Panel("[bold white]Overall Comparison[/bold white]", border_style="white")
    )

    # Overall fastest/slowest
    fastest = min(successful_results, key=lambda x: x["time"])
    slowest = max(successful_results, key=lambda x: x["time"])

    console.print(
        f"[bold green]Fastest Overall:[/bold green] {fastest['level']} ({fastest['time']:.2f}s) - {fastest['question_type']} question"
    )
    console.print(
        f"[bold red]Slowest Overall:[/bold red] {slowest['level']} ({slowest['time']:.2f}s) - {slowest['question_type']} question"
    )
    console.print(
        f"[bold yellow]Total Tests:[/bold yellow] {len(all_results)} ({len(successful_results)} successful)"
    )
    console.print(
        f"[bold cyan]Standard Tests:[/bold cyan] {len(standard_results)} successful"
    )
    console.print(
        f"[bold purple]Memory Tests:[/bold purple] {len(memory_results)} successful"
    )


def print_stats_table(console: Console, results: List[Dict], test_type: str) -> None:
    """Print statistics table for a specific test type."""
    level_stats = {}
    for result in results:
        level = result["level"]
        if level not in level_stats:
            level_stats[level] = {"times": [], "lengths": []}
        level_stats[level]["times"].append(result["time"])
        level_stats[level]["lengths"].append(result["response_length"])

    stats_table = Table(show_header=True, header_style="bold blue")
    stats_table.add_column("Level", style="cyan")
    stats_table.add_column("Avg Time (s)", style="green", justify="right")
    stats_table.add_column("Avg Length", style="yellow", justify="right")
    stats_table.add_column("Avg Chars/Sec", style="magenta", justify="right")

    for level, stats in level_stats.items():
        avg_time = sum(stats["times"]) / len(stats["times"])
        avg_length = sum(stats["lengths"]) / len(stats["lengths"])
        avg_chars_per_sec = avg_length / avg_time if avg_time > 0 else 0

        stats_table.add_row(
            level, f"{avg_time:.2f}", f"{avg_length:.0f}", f"{avg_chars_per_sec:.1f}"
        )

    console.print(stats_table)


def main():
    """
    Main function to run the instruction level comparison.
    """
    try:
        asyncio.run(run_instruction_level_comparison())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError running test: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
