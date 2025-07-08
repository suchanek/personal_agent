#!/usr/bin/env python3
"""
Agent Status Display Script

This script properly initializes the Personal AI Agent and displays the overall 
status of the system. It sets the log level to WARNING to minimize output spam
while still showing important information.

Usage:
    python scripts/agent_status_display.py [--remote] [--recreate] [--user-id USER_ID]
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Set up logging BEFORE any other imports to suppress early log messages
logging.getLogger().setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s', force=True)

# Suppress the specific package initialization logger BEFORE importing
logging.getLogger('personal_agent').setLevel(logging.WARNING)
logging.getLogger('personal_agent.utils.pag_logging').setLevel(logging.WARNING)

# Add the src directory to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import the agent components
from personal_agent.core.agno_agent import create_agno_agent
from personal_agent.config.settings import USER_ID, AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR
from personal_agent.config import LLM_MODEL, OLLAMA_URL, REMOTE_OLLAMA_URL, USE_MCP


def setup_warning_logging():
    """Set up logging to WARNING level to reduce spam output."""
    # Set root logger to WARNING FIRST
    logging.getLogger().setLevel(logging.WARNING)
    
    # Configure basic logging format BEFORE setting specific loggers
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s',
        force=True
    )
    
    # Set specific loggers that tend to be verbose to WARNING
    verbose_loggers = [
        'agno',
        'personal_agent',
        'personal_agent.utils',
        'personal_agent.utils.pag_logging',
        'personal_agent.core',
        'personal_agent.core.agno_agent',
        'personal_agent.core.agno_storage',
        'personal_agent.core.semantic_memory_manager',
        'personal_agent.core.knowledge_coordinator',
        'lightrag',
        'httpx',
        'urllib3',
        'asyncio',
        'aiohttp',
        'mcp',
        'ollama'
    ]
    
    for logger_name in verbose_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Also suppress the specific logger that's showing up in the output
    logging.getLogger('personal_agent.utils.pag_logging').setLevel(logging.ERROR)


async def initialize_and_display_status(
    use_remote_ollama: bool = False,
    recreate: bool = False,
    user_id: str = None
):
    """
    Initialize the agent and display comprehensive status information.
    
    Args:
        use_remote_ollama: Whether to use remote Ollama server
        recreate: Whether to recreate the knowledge base
        user_id: Custom user ID (defaults to configured USER_ID)
    """
    console = Console(force_terminal=True)
    
    # Display header
    console.print(Panel.fit(
        "🤖 Personal AI Agent - System Status Display\n"
        "Initializing agent and displaying comprehensive status...",
        style="bold blue"
    ))
    
    # Use provided user_id or default
    if user_id is None:
        user_id = USER_ID
    
    # Determine Ollama URL
    ollama_url = REMOTE_OLLAMA_URL if use_remote_ollama else OLLAMA_URL
    if use_remote_ollama:
        os.environ["OLLAMA_URL"] = ollama_url
    
    console.print(f"🔧 Using Ollama server: [cyan]{ollama_url}[/cyan]")
    console.print(f"👤 User ID: [cyan]{user_id}[/cyan]")
    console.print(f"🧠 Model: [cyan]{LLM_MODEL}[/cyan]")
    console.print()
    
    try:
        # Initialize the agent
        console.print("🚀 [bold yellow]Initializing Personal AI Agent...[/bold yellow]")
        
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            enable_memory=True,
            enable_mcp=USE_MCP,
            storage_dir=AGNO_STORAGE_DIR,
            knowledge_dir=AGNO_KNOWLEDGE_DIR,
            debug=False,  # Disable debug to reduce output
            user_id=user_id,
            ollama_base_url=ollama_url,
            recreate=recreate,
        )
        
        console.print("✅ [bold green]Agent initialized successfully![/bold green]")
        console.print()
        
        # Display comprehensive agent information
        agent.print_agent_info(console)
        
        # Display system status
        await display_system_status(agent, console)
        
        # Display memory status if enabled
        if agent.enable_memory:
            await display_memory_status(agent, console)
        
        # Test basic functionality
        await test_basic_functionality(agent, console)
        
        # Cleanup
        await agent.cleanup()
        
        console.print()
        console.print("🎉 [bold green]Status display completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Error during initialization: {str(e)}[/bold red]")
        raise


async def display_system_status(agent, console):
    """Display system status information."""
    console.print()
    
    status_table = Table(
        title="🖥️ System Status",
        show_header=True,
        header_style="bold cyan"
    )
    status_table.add_column("Component", style="yellow")
    status_table.add_column("Status", style="green")
    status_table.add_column("Details", style="white")
    
    # Agent status
    status_table.add_row(
        "Agent Framework",
        "✅ Active" if agent.agent else "❌ Inactive",
        f"Agno-based agent with {agent.model_name}"
    )
    
    # Memory status
    memory_status = "✅ Enabled" if agent.enable_memory else "❌ Disabled"
    memory_details = f"Storage: {agent.storage_dir}" if agent.enable_memory else "Not configured"
    status_table.add_row("Memory System", memory_status, memory_details)
    
    # Knowledge base status
    kb_status = "✅ Loaded" if agent.agno_knowledge else "❌ Not loaded"
    kb_details = f"Knowledge: {agent.knowledge_dir}" if agent.agno_knowledge else "No knowledge files"
    status_table.add_row("Knowledge Base", kb_status, kb_details)
    
    # LightRAG status
    lightrag_status = "✅ Available" if agent.lightrag_knowledge_enabled else "❌ Unavailable"
    lightrag_details = "Graph-based knowledge system" if agent.lightrag_knowledge_enabled else "Not configured"
    status_table.add_row("LightRAG Knowledge", lightrag_status, lightrag_details)
    
    # MCP status
    mcp_status = "✅ Enabled" if agent.enable_mcp else "❌ Disabled"
    mcp_count = len(agent.mcp_servers) if agent.enable_mcp else 0
    mcp_details = f"{mcp_count} servers configured" if agent.enable_mcp else "Not configured"
    status_table.add_row("MCP Integration", mcp_status, mcp_details)
    
    console.print(status_table)


async def display_memory_status(agent, console):
    """Display memory system status and statistics."""
    if not agent.enable_memory or not agent.agno_memory:
        return
    
    console.print()
    
    try:
        # Get memory statistics
        stats = agent.agno_memory.memory_manager.get_memory_stats(
            db=agent.agno_memory.db,
            user_id=agent.user_id
        )
        
        memory_table = Table(
            title="🧠 Memory System Status",
            show_header=True,
            header_style="bold magenta"
        )
        memory_table.add_column("Metric", style="cyan")
        memory_table.add_column("Value", style="green", justify="right")
        
        if "error" not in stats:
            memory_table.add_row("Total Memories", str(stats.get('total_memories', 0)))
            memory_table.add_row("Average Length", f"{stats.get('average_memory_length', 0):.1f} chars")
            memory_table.add_row("Recent (24h)", str(stats.get('recent_memories_24h', 0)))
            
            if stats.get('most_common_topic'):
                memory_table.add_row("Top Topic", stats['most_common_topic'])
            
            console.print(memory_table)
            
            # Display topic distribution if available
            if stats.get('topic_distribution'):
                console.print()
                topic_table = Table(
                    title="📊 Topic Distribution",
                    show_header=True,
                    header_style="bold blue"
                )
                topic_table.add_column("Topic", style="yellow")
                topic_table.add_column("Count", style="green", justify="right")
                
                for topic, count in stats['topic_distribution'].items():
                    topic_table.add_row(topic, str(count))
                
                console.print(topic_table)
        else:
            console.print(f"❌ Memory stats error: {stats['error']}")
            
    except Exception as e:
        console.print(f"❌ Error getting memory status: {str(e)}")


async def test_basic_functionality(agent, console):
    """Test basic agent functionality."""
    console.print()
    console.print("🧪 [bold yellow]Testing Basic Functionality...[/bold yellow]")
    
    test_table = Table(
        title="🔬 Functionality Tests",
        show_header=True,
        header_style="bold green"
    )
    test_table.add_column("Test", style="cyan")
    test_table.add_column("Result", style="white")
    
    # Test 1: Agent response
    try:
        response = await agent.agent.arun("Hello! Can you tell me what you are?", stream=False)
        if response and hasattr(response, 'content') and response.content:
            test_table.add_row("Agent Response", "✅ Working")
        else:
            test_table.add_row("Agent Response", "❌ No response")
    except Exception as e:
        test_table.add_row("Agent Response", f"❌ Error: {str(e)[:50]}...")
    
    # Test 2: Memory system (if enabled)
    if agent.enable_memory and agent.agno_memory:
        try:
            # Test memory storage
            result = await agent.store_user_memory("Test memory for status check", ["test"])
            if "✅" in result:
                test_table.add_row("Memory Storage", "✅ Working")
            else:
                test_table.add_row("Memory Storage", f"⚠️ {result[:50]}...")
        except Exception as e:
            test_table.add_row("Memory Storage", f"❌ Error: {str(e)[:50]}...")
    else:
        test_table.add_row("Memory Storage", "⏭️ Disabled")
    
    # Test 3: Tool availability
    tool_count = len(agent.agent.tools) if agent.agent and hasattr(agent.agent, 'tools') else 0
    if tool_count > 0:
        test_table.add_row("Tools Available", f"✅ {tool_count} tools loaded")
    else:
        test_table.add_row("Tools Available", "❌ No tools loaded")
    
    console.print(test_table)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Initialize Personal AI Agent and display system status"
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Use remote Ollama server instead of local"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the knowledge base from scratch"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="Custom user ID (defaults to configured USER_ID)"
    )
    
    args = parser.parse_args()
    
    # Set up logging to WARNING level
    setup_warning_logging()
    
    # Run the async function
    try:
        asyncio.run(initialize_and_display_status(
            use_remote_ollama=args.remote,
            recreate=args.recreate,
            user_id=args.user_id
        ))
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
