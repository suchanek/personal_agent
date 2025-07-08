import asyncio
import sys
from pathlib import Path

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from rich.console import Console
from rich.panel import Panel

async def main():
    """
    Test program to exercise the enhanced LightRAG query interface.
    """
    console = Console()
    console.print(Panel("[bold cyan]🚀 Testing Enhanced LightRAG Query Interface 🚀[/bold cyan]", expand=False))

    # --- 1. Initialize the Agent ---
    console.print("\n[bold yellow]1. Initializing AgnoPersonalAgent...[/bold yellow]")
    try:
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            debug=True,
            enable_memory=True,
            enable_mcp=False, # Disable MCP for this test to speed up initialization
        )
        await agent.initialize()
        console.print("[green]✅ Agent initialized successfully.[/green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to initialize agent: {e}[/bold red]")
        return

    # --- 2. Define Test Queries ---
    console.print("\n[bold yellow]2. Defining Test Queries...[/bold yellow]")

    test_cases = [
        {
            "description": "Simple hybrid search with default parameters",
            "query": "What are the latest advancements in AI?",
            "params": {"mode": "hybrid"}
        },
        {
            "description": "Global search with a specific top_k",
            "query": "Explain the concept of photosynthesis.",
            "params": {"mode": "global", "top_k": 3}
        },
        {
            "description": "Local search requesting a single paragraph response",
            "query": "Summarize the plot of 'Dune'.",
            "params": {"mode": "local", "response_type": "Single Paragraph"}
        },
        {
            "description": "Mix search requesting bullet points",
            "query": "What are the main features of Python?",
            "params": {"mode": "mix", "response_type": "Bullet Points"}
        },
        {
            "description": "Naive search returning only the context",
            "query": "Who was Albert Einstein?",
            "params": {"mode": "naive", "only_need_context": True}
        },
        {
            "description": "Bypass search (if supported by your LightRAG setup)",
            "query": "What is the capital of France?",
            "params": {"mode": "bypass"}
        },
    ]
    console.print(f"[green]✅ Defined {len(test_cases)} test cases.[/green]")

    # --- 3. Execute Test Queries ---
    console.print("\n[bold yellow]3. Executing Test Queries...[/bold yellow]")

    for i, case in enumerate(test_cases):
        console.print(Panel(f"[bold]Test Case {i+1}: {case['description']}[/bold]", style="cyan", expand=False))
        console.print(f"[bold]   Query:[/bold] [italic]'{case['query']}'[/italic]")
        console.print(f"[bold]   Params:[/bold] {case['params']}")

        try:
            result = await agent.query_lightrag_knowledge_direct(case["query"], case["params"])
            console.print("[bold green]   Result:[/bold green]")
            console.print(f"   [dim]{result}[/dim]")
            console.print("[green]--------------------[/green]")

        except Exception as e:
            console.print(f"[bold red]   ❌ Test Case Failed: {e}[/bold red]")
            console.print("[red]--------------------[/red]")

    console.print("\n[bold green]✅ All test cases completed.[/bold green]")


if __name__ == "__main__":
    # To run this test, execute `python3 tests/test_lightrag_query_interface.py` from the project root.
    asyncio.run(main())
