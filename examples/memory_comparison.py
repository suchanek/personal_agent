"""
Memory Decision Comparison: OpenAI vs Ollama

This script compares how OpenAI and Ollama models make memory storage decisions
to identify why Ollama creates duplicate memories.
"""

import logging
from uuid import uuid4

from agno.agent.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Configure logging to capture memory decisions
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("memory_decisions.log"), logging.StreamHandler()],
)

# Enable memory-specific logging
logging.getLogger("agno.memory").setLevel(logging.DEBUG)
logging.getLogger("agno.agent").setLevel(logging.DEBUG)


def test_model_memory_behavior(model_name: str, model_instance, test_input: str):
    """Test how a specific model handles memory creation."""

    console.print(Panel(f"Testing {model_name}", style="bold blue"))

    # Create separate memory for each model test
    memory_db = SqliteMemoryDb(
        table_name=f"memory_{model_name.lower()}",
        db_file=f"tmp/memory_comparison_{model_name.lower()}.db",
    )
    memory = Memory(db=memory_db)
    memory.clear()

    session_id = str(uuid4())
    user_id = "Eric"

    agent = Agent(
        model=model_instance,
        memory=memory,
        storage=SqliteStorage(
            table_name=f"sessions_{model_name.lower()}",
            db_file=f"tmp/sessions_{model_name.lower()}.db",
        ),
        enable_user_memories=True,
        debug_mode=True,
    )

    console.print(f"\n📝 Input: {test_input}")

    # Capture response
    with console.capture() as capture:
        agent.print_response(
            test_input,
            stream=True,
            user_id=user_id,
            session_id=session_id,
        )

    response_text = capture.get()

    # Get memories created
    memories = memory.get_user_memories(user_id=user_id)

    # Create results table
    table = Table(title=f"{model_name} Memory Results")
    table.add_column("Aspect", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Model", model_name)
    table.add_row("Total Memories", str(len(memories)))
    table.add_row("Response Length", str(len(response_text)))

    for i, mem in enumerate(memories, 1):
        table.add_row(f"Memory {i}", f"{mem.memory[:100]}...")
        table.add_row(f"Topics {i}", str(mem.topics))

    console.print(table)

    return {
        "model": model_name,
        "memories_count": len(memories),
        "memories": memories,
        "response": response_text,
    }


def main():
    console.print(
        Panel("Memory Decision Comparison: OpenAI vs Ollama", style="bold green")
    )

    # Test input that should create exactly one memory
    test_input = "My name is Eric and I live in Ohio. I prefer tea over coffee."

    results = []

    # Test OpenAI
    try:
        openai_model = OpenAIChat(id="gpt-4o-mini")
        openai_results = test_model_memory_behavior("OpenAI", openai_model, test_input)
        results.append(openai_results)
    except Exception as e:
        console.print(f"[red]OpenAI test failed: {e}[/red]")

    # Test Ollama
    try:
        ollama_model = Ollama(
            id="qwen3:1.7b", host="http://tesla.tail19187e.ts.net:11434"
        )
        ollama_results = test_model_memory_behavior("Ollama", ollama_model, test_input)
        results.append(ollama_results)
    except Exception as e:
        console.print(f"[red]Ollama test failed: {e}[/red]")

    # Comparison summary
    console.print("\n" + "=" * 50)
    console.print(Panel("COMPARISON SUMMARY", style="bold yellow"))

    comparison_table = Table()
    comparison_table.add_column("Model", style="cyan")
    comparison_table.add_column("Memory Count", style="white")
    comparison_table.add_column("Issue", style="red")

    for result in results:
        issue = (
            "✅ Normal"
            if result["memories_count"] <= 2
            else f"❌ Too many ({result['memories_count']})"
        )
        comparison_table.add_row(result["model"], str(result["memories_count"]), issue)

    console.print(comparison_table)

    # Detailed memory analysis
    console.print("\n")
    console.print(Panel("DETAILED MEMORY ANALYSIS", style="bold magenta"))

    for result in results:
        console.print(f"\n{result['model']} Memories:")
        for i, mem in enumerate(result["memories"], 1):
            console.print(f"  {i}. [cyan]{mem.memory}[/cyan]")
            console.print(f"     Topics: {mem.topics}")
            console.print(f"     ID: {mem.memory_id}")

    console.print(f"\n📝 Log file created: memory_decisions.log")
    console.print("Check the log file for detailed memory processing decisions.")


if __name__ == "__main__":
    main()
