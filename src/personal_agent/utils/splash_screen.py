"""
This module provides a visually appealing splash screen for the Personal AI Agent,
displaying key configuration details upon initialization.
"""

import os

from rich.console import Console
from rich.padding import Padding
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


def display_splash_screen(agent_info: dict, agent_version: str) -> None:
    """
    Display a colorful and informative splash screen with agent configuration details.

    Args:
        agent_info (dict): A dictionary containing agent configuration details.
        agent_version (str): The current version of the agent.
    """
    console = Console()

    # --- Header ---
    console.print(
        Rule(
            "[bold magenta]🚀 Personal Agent Initializing...[/bold magenta]",
            style="magenta",
        )
    )
    console.print(
        Padding(
            Text(f"Version: {agent_version}", style="bold cyan", justify="center"),
            (1, 0),
        )
    )

    # --- Configuration Details Table ---
    table = Table(
        show_header=True,
        header_style="bold blue",
        border_style="dim",
        box=None,
        padding=(0, 1),
    )
    table.add_column("Category", style="bold yellow", width=20)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    # Core Agent Settings
    table.add_row("Core", "Framework", agent_info.get("framework", "N/A"))
    table.add_row(
        "Core",
        "Model",
        f"{agent_info.get('model_provider', 'N/A')}:{agent_info.get('model_name', 'N/A')}",
    )
    table.add_row("Core", "User ID", agent_info.get("user_id", "N/A"))
    table.add_row(
        "Core",
        "Debug Mode",
        "✅ Enabled" if agent_info.get("debug_mode") else "❌ Disabled",
    )
    table.add_section()

    # Memory & Knowledge Settings
    table.add_row(
        "Memory", "Memory Enabled", "✅" if agent_info.get("memory_enabled") else "❌"
    )
    table.add_row(
        "Memory",
        "Knowledge Enabled",
        "✅" if agent_info.get("knowledge_enabled") else "❌",
    )
    table.add_row(
        "Memory",
        "Storage Directory",
        Text(agent_info.get("storage_dir", "N/A"), style="dim green"),
    )
    table.add_row(
        "Memory",
        "Knowledge Directory",
        Text(agent_info.get("knowledge_dir", "N/A"), style="dim green"),
    )
    table.add_section()

    # Tool Settings
    tool_counts = agent_info.get("tool_counts", {})
    table.add_row(
        "Tools", "MCP Enabled", "✅" if agent_info.get("mcp_enabled") else "❌"
    )
    table.add_row("Tools", "Total Tools", str(tool_counts.get("total", 0)))
    table.add_row("Tools", "Built-in Tools", str(tool_counts.get("built_in", 0)))
    table.add_row("Tools", "MCP Tools", str(tool_counts.get("mcp", 0)))
    table.add_section()

    # Environment Configuration
    env_vars = [
        ("WEAVIATE_URL", "N/A"),
        ("OLLAMA_URL", "N/A"),
        ("REMOTE_OLLAMA_URL", "N/A"),
        ("USE_WEAVIATE", "False"),
        ("USE_MCP", "False"),
        ("ROOT_DIR", "/"),
        ("HOME_DIR", "/"),
        ("DATA_DIR", "N/A"),
        ("REPO_DIR", "N/A"),
        ("STORAGE_BACKEND", "N/A"),
        ("AGNO_STORAGE_DIR", "N/A"),
        ("AGNO_KNOWLEDGE_DIR", "N/A"),
        ("LOG_LEVEL", "INFO"),
        ("LLM_MODEL", "N/A"),
        ("USER_ID", "N/A"),
    ]
    for i, (var, default) in enumerate(env_vars):
        value = os.getenv(var, default)
        # Use dim style for path variables to reduce visual clutter
        style = "dim green" if "DIR" in var or "URL" in var else "green"
        table.add_row("Environment", var, Text(str(value), style=style))

    console.print(table)

    # --- Footer ---
    console.print(
        Rule("[bold green]Initialization Complete[/bold green]", style="green")
    )
    console.print(Padding(Text("Ready to assist!", justify="center"), (1, 0, 0, 0)))
