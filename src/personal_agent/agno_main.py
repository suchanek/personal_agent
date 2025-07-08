"""
Agno-compatible main entry point for the Personal AI Agent.

This module orchestrates all components using the agno framework for modern
async agent operations while maintaining compatibility with existing infrastructure.
"""

import argparse
import asyncio
import logging
import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel

# Import configuration
from .config.settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    LOG_LEVEL,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    USE_MCP,
    USER_ID,
)

# Import core components
from .core.agno_agent import AgnoPersonalAgent, create_agno_agent

# Import utilities
from .utils import inject_dependencies, setup_logging

# The web interface is now handled by Streamlit in paga_streamlit_agno.py
# from .web.agno_interface import create_app, register_routes

# Global variables for cleanup
agno_agent: Optional[AgnoPersonalAgent] = None
logger: Optional[logging.Logger] = None


async def initialize_agno_system(
    use_remote_ollama: bool = False, recreate: bool = False
):
    """
    Initialize all system components for agno framework.

    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :return: Tuple of (agno_agent, memory_functions)
    """
    global logger
    from .utils.pag_logging import configure_all_rich_logging

    # Set up Rich logging for all components including agno
    configure_all_rich_logging()
    logger = setup_logging(level=LOG_LEVEL)
    logger.info("Starting Personal AI Agent with agno framework...")

    # Update Ollama URL if requested
    ollama_url = OLLAMA_URL
    if use_remote_ollama:
        ollama_url = REMOTE_OLLAMA_URL
        os.environ["OLLAMA_URL"] = ollama_url
        logger.info("Using remote Ollama server at: %s", ollama_url)
    else:
        logger.info("Using local Ollama server at: %s", ollama_url)

    # Create agno agent with native storage
    logger.info("Creating agno agent with native storage...")
    global agno_agent

    agno_agent = await create_agno_agent(
        model_provider="ollama",  # Default to Ollama
        model_name=LLM_MODEL,  # Use configured model
        enable_memory=True,  # Enable native Agno memory
        enable_mcp=USE_MCP,  # Use configured MCP setting
        storage_dir=AGNO_STORAGE_DIR,  # Pass the user-specific path
        knowledge_dir=AGNO_KNOWLEDGE_DIR,  # Pass the user-specific path
        debug=True,
        user_id=USER_ID,
        ollama_base_url=ollama_url,  # Pass the selected Ollama URL
        recreate=recreate,
    )

    agent_info = agno_agent.get_agent_info()
    logger.info(
        "Agno agent created successfully: %s servers, memory=%s",
        agent_info["mcp_servers"],
        agent_info["memory_enabled"],
    )

    # KB functions (legacy compatibility - Agno handles memory automatically)
    async def query_knowledge_base(query: str) -> str:
        """Query the knowledge base (legacy compatibility - not used)."""
        print("Legacy memory function called - Agno handles this automatically")
        return "Memory is handled automatically by Agno"

    async def store_interaction(query: str, response: str) -> bool:
        """Store interaction (legacy compatibility - not used)."""
        logger.info("Legacy memory function called - Agno handles this automatically")
        return True

    async def clear_knowledge_base() -> bool:
        """Clear the knowledge base (legacy compatibility - not used)."""
        logger.info("Legacy memory function called - Agno handles this automatically")
        return True

    # Inject dependencies for cleanup (simplified for Agno)
    inject_dependencies(None, None, None, logger)

    return (
        agno_agent,
        query_knowledge_base,
        store_interaction,
        clear_knowledge_base,
        ollama_url,
    )


# Flask web server functions are deprecated and have been removed.
# The web interface is now managed by Streamlit in `paga_streamlit_agno.py`.


async def run_agno_cli(
    query: str = None, use_remote_ollama: bool = False, recreate: bool = False
):
    """
    Run agno agent in CLI mode with enhanced interface based on the enhanced Ollama agent example.

    :param query: Initial query to run
    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :param recreate: Whether to recreate the knowledge base
    """
    # Initialize system FIRST (this sets up logging)
    agent, query_kb, store_int, clear_kb, ollama_url = await initialize_agno_system(
        use_remote_ollama, recreate=recreate
    )

    # NOW create console and display the panel AFTER ALL initialization is complete
    console = Console(force_terminal=True)

    # Print formatted agent info first
    console.print("✅ [bold green]Agent Successfully Initialized![/bold green]")
    agent.print_agent_info(console)

    # NOW display the welcome panel AFTER all the verbose output
    console.print("\n")  # Add some space
    console.print(
        Panel.fit(
            "🚀 Enhanced Personal AI Agent with Agno Framework\n\n"
            "This CLI provides an enhanced chat interface with memory management.\n\n"
            "Commands:\n"
            "• Type your message to chat\n"
            "• Start with '!' to immediately store as memory\n"
            "• Start with '?' to query memories by topic (e.g., `? work`)\n"
            "• 'memories' - Show all memories\n"
            "• 'analysis' - Show memory analysis\n"
            "• 'stats' - Show memory statistics\n"
            "• 'clear' - Clear all memories\n"
            "• 'delete memory <id>' - Delete a memory by its ID\n"
            "• 'delete topic <topic>' - Delete all memories for a topic\n"
            "• 'quit' - Exit the CLI",
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

            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("👋 Goodbye!")
                break
            elif user_input.lower() == "memories":
                await show_all_memories(agent, console)
                continue
            elif user_input.lower() == "analysis":
                await show_memory_analysis(agent, console)
                continue
            elif user_input.lower() == "stats":
                await show_memory_stats(agent, console)
                continue
            elif user_input.lower() == "clear":
                await clear_all_memories(agent, console)
                continue
            elif user_input.startswith("delete memory "):
                memory_id = user_input[len("delete memory ") :].strip()
                if memory_id:
                    await delete_memory_by_id_cli(agent, memory_id, console)
                else:
                    console.print("❌ Please provide a memory ID to delete.")
                continue
            elif user_input.startswith("delete topic "):
                topic = user_input[len("delete topic ") :].strip()
                if topic:
                    await delete_memories_by_topic_cli(agent, topic, console)
                else:
                    console.print("❌ Please provide a topic to delete.")
                continue
            elif user_input.startswith("!"):
                # Special command: immediately store as memory
                memory_content = user_input[1:].strip()
                if memory_content:
                    await store_immediate_memory(agent, memory_content, console)
                else:
                    console.print(
                        "❌ Please provide content after '!' to store as memory"
                    )
                continue
            elif user_input.startswith("?"):
                query_content = user_input[1:].strip()
                if query_content:
                    await show_memories_by_topic_cli(agent, query_content, console)
                else:
                    await show_all_memories(agent, console)
                continue

            try:
                # Get response from agent
                console.print("🤖 Assistant:")
                response = await agent.agent.arun(
                    user_input,
                    stream=False,  # Disable streaming for cleaner CLI output
                    show_tool_calls=agent.debug,  # Show tool calls in debug mode
                )

                # Print the final response content
                if response and hasattr(response, "content") and response.content:
                    console.print(response.content)
                elif response:
                    console.print(f"Response received but no content: {response}")
                else:
                    console.print("No response generated.")

            except Exception as e:
                console.print(f"💥 Error: {e}")

    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    finally:
        try:
            await agent.cleanup()
        except Exception as e:
            console.print(f"Warning during cleanup: {e}")


async def show_all_memories(agent, console):
    """Show all memories for the user."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        results = agent.agno_memory.memory_manager.get_memories_by_topic(
            db=agent.agno_memory.db,
            user_id=agent.user_id,
            topics=None,
            limit=None,
        )

        if not results:
            console.print("📝 No memories found")
            return

        console.print(f"📝 All memories ({len(results)}):")
        for i, memory in enumerate(results, 1):
            console.print(f"  {i}. {memory.memory}")
            if memory.topics:
                console.print(f"     Topics: {', '.join(memory.topics)}")

    except Exception as e:
        console.print(f"❌ Error retrieving memories: {e}")


async def show_memories_by_topic_cli(agent, topic, console):
    """Show memories by topic via the CLI."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        topics = [t.strip() for t in topic.split(",")]
        results = agent.agno_memory.memory_manager.get_memories_by_topic(
            db=agent.agno_memory.db,
            user_id=agent.user_id,
            topics=topics,
            limit=None,
        )

        if not results:
            console.print(f"📝 No memories found for topic(s): {topic}")
            return

        console.print(f"📝 Memories for topic(s) '{topic}' ({len(results)}):")
        for i, memory in enumerate(results, 1):
            console.print(f"  {i}. {memory.memory}")
            if memory.topics:
                console.print(f"     Topics: {', '.join(memory.topics)}")

    except Exception as e:
        console.print(f"❌ Error retrieving memories by topic: {e}")


async def show_memory_analysis(agent, console):
    """Show detailed memory analysis."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        stats = agent.agno_memory.memory_manager.get_memory_stats(
            db=agent.agno_memory.db, user_id=agent.user_id
        )

        if "error" in stats:
            console.print(f"❌ Error getting memory analysis: {stats['error']}")
            return

        console.print("📊 Memory Analysis:")
        console.print(f"Total memories: {stats.get('total_memories', 0)}")
        console.print(
            f"Average memory length: {stats.get('average_memory_length', 0):.1f} characters"
        )
        console.print(f"Recent memories (24h): {stats.get('recent_memories_24h', 0)}")

        if stats.get("most_common_topic"):
            console.print(f"Most common topic: {stats['most_common_topic']}")

        if stats.get("topic_distribution"):
            console.print("\nTopic distribution:")
            for topic, count in stats["topic_distribution"].items():
                console.print(f"  - {topic}: {count}")

    except Exception as e:
        console.print(f"❌ Error getting memory analysis: {e}")


async def show_memory_stats(agent, console):
    """Show memory statistics."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        stats = agent.agno_memory.memory_manager.get_memory_stats(
            db=agent.agno_memory.db, user_id=agent.user_id
        )

        if "error" in stats:
            console.print(f"❌ Error getting memory stats: {stats['error']}")
            return

        console.print(f"📊 Memory Stats: {stats}")

    except Exception as e:
        console.print(f"❌ Error getting memory stats: {e}")


async def clear_all_memories(agent, console):
    """Clear all memories for the user."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        success, message = agent.agno_memory.memory_manager.clear_memories(
            db=agent.agno_memory.db, user_id=agent.user_id
        )

        if success:
            console.print(f"✅ {message}")
        else:
            console.print(f"❌ Error clearing memories: {message}")

    except Exception as e:
        console.print(f"❌ Error clearing memories: {e}")


async def store_immediate_memory(agent, content, console):
    """Store content immediately as a memory."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        result = await agent.store_user_memory(content=content)
        console.print(f"✅ Stored memory: {result}")

    except Exception as e:
        console.print(f"❌ Error storing memory: {e}")


async def delete_memory_by_id_cli(agent, memory_id, console):
    """Delete a single memory by its ID via the CLI."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        success, message = agent.agno_memory.memory_manager.delete_memory(
            memory_id=memory_id, db=agent.agno_memory.db, user_id=agent.user_id
        )

        if success:
            console.print(f"✅ Successfully deleted memory: {memory_id}")
        else:
            console.print(f"❌ Error deleting memory: {message}")

    except Exception as e:
        console.print(f"❌ Error deleting memory: {e}")


async def delete_memories_by_topic_cli(agent, topic, console):
    """Delete memories by topic via the CLI."""
    try:
        if not agent.agno_memory:
            console.print("📝 No memory system available")
            return

        topics = [t.strip() for t in topic.split(",")]
        (
            success,
            message,
        ) = agent.agno_memory.memory_manager.delete_memories_by_topic(
            topics=topics, db=agent.agno_memory.db, user_id=agent.user_id
        )

        if success:
            console.print(f"✅ {message}")
        else:
            console.print(f"❌ Error deleting memories by topic: {message}")

    except Exception as e:
        console.print(f"❌ Error deleting memories by topic: {e}")


def cli_main():
    """
    Main entry point for CLI mode (used by poetry scripts).
    """
    # Set up Rich logging for all components including agno
    # from .utils import configure_all_rich_logging, setup_logging

    # configure_all_rich_logging()
    # logger = setup_logging()

    parser = argparse.ArgumentParser(
        description="Run the Personal AI Agent with Agno Framework"
    )
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama server"
    )
    parser.add_argument(
        "--recreate", action="store_true", help="Recreate the knowledge base"
    )
    args = parser.parse_args()

    # This file is now the dedicated CLI entry point.
    # logger.info("Starting Personal AI Agent in CLI mode...")
    print("Starting Personal AI Agent in CLI mode...")
    asyncio.run(run_agno_cli(use_remote_ollama=args.remote, recreate=args.recreate))


if __name__ == "__main__":
    cli_main()
