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

# Import configuration
from .config import LLM_MODEL, USE_MCP
from .config.settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    USER_ID,
)

# Import core components
from .core.agno_agent import AgnoPersonalAgent, create_agno_agent

# Import utilities
from .utils import (
    configure_all_rich_logging,
    inject_dependencies,
    register_cleanup_handlers,
    setup_logging,
)

# Import agno web interface (Streamlit-based)
from .web.agno_interface import initialize_agent
from .web.agno_interface import main as streamlit_main

# Global variables for cleanup
agno_agent: Optional[AgnoPersonalAgent] = None
logger: Optional[logging.Logger] = setup_logging()


async def initialize_agno_system(
    use_remote_ollama: bool = False, complexity_level: int = 4
):
    """
    Initialize all system components for agno framework.

    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :param complexity_level: Instruction complexity level (0=minimal, 4=full)
    :return: Tuple of (agno_agent, memory_functions)
    """
    global logger

    # Set up Rich logging for all components including agno
    configure_all_rich_logging()
    logger = setup_logging()
    logger.info("Starting Personal AI Agent with agno framework...")

    # Update Ollama URL if requested
    ollama_url = OLLAMA_URL
    if use_remote_ollama:
        ollama_url = REMOTE_OLLAMA_URL
        os.environ["OLLAMA_URL"] = ollama_url
        logger.info(f"Using remote Ollama server at: {ollama_url}")
    else:
        logger.info(f"Using local Ollama server at: {ollama_url}")

    # Create agno agent with native storage
    logger.info("Creating agno agent with native storage...")
    global agno_agent

    agno_agent = await create_agno_agent(
        model_provider="ollama",  # Default to Ollama
        model_name=LLM_MODEL,  # Use configured model
        enable_memory=True,  # Enable native Agno memory
        enable_mcp=USE_MCP,  # Use configured MCP setting
        storage_dir=AGNO_STORAGE_DIR,
        knowledge_dir=AGNO_KNOWLEDGE_DIR,
        debug=True,
        user_id=USER_ID,
        ollama_base_url=ollama_url,  # Pass the selected Ollama URL
        complexity_level=complexity_level,  # Pass the instruction complexity level
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
        logger.info("Legacy memory function called - Agno handles this automatically")
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
    )


def run_agno_web(use_remote_ollama: bool = False):
    """
    Run the agno web application using Streamlit.

    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    """
    import subprocess
    import sys

    # Set up Rich logging for all components including agno
    configure_all_rich_logging()
    logger_instance = setup_logging()

    # Initialize agno system (run async initialization)
    agno_agent_instance, query_kb_func, store_int_func, clear_kb_func = asyncio.run(
        initialize_agno_system(use_remote_ollama)
    )

    # Initialize the Streamlit interface with the agent
    initialize_agent(
        agno_agent_instance,
        query_kb_func,
        store_int_func,
        clear_kb_func,
    )

    # Register cleanup handlers
    register_cleanup_handlers()

    logger_instance.info("Agno Streamlit application ready!")

    # Print startup information
    print("\n🚀 Starting Personal AI Agent with Agno Framework...")
    print("🌐 Streamlit interface will be available at: http://localhost:8501")
    print("📚 Features: Native MCP integration, Async operations, Enhanced memory")
    print("⚡ Framework: Agno with native MCP + Ollama")
    if use_remote_ollama:
        print("🖥️  Using remote Ollama at: http://tesla.local:11434")
    else:
        print("🖥️  Using local Ollama at: http://localhost:11434")
    print("🔧 Mode: Modern async agent with advanced capabilities")
    print("\nPress Ctrl+C to stop the server.\n")

    # Run Streamlit
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                __file__.replace("agno_main.py", "web/agno_interface.py"),
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
            ]
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        logger_instance.error(f"Error running Streamlit: {e}")
        print(f"Error: {e}")
        print("You can also run the interface directly with:")
        print(
            f"streamlit run {__file__.replace('agno_main.py', 'web/agno_interface.py')}"
        )


async def run_agno_cli(
    query: str = None,
    use_remote_ollama: bool = False,
    show_reasoning: bool = False,
    stream: bool = True,
    stream_steps: bool = False,
    instruction_level: int = 4,
):
    """
    Run agno agent in CLI mode with configurable streaming and reasoning.

    :param query: Initial query to run
    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :param show_reasoning: Whether to show full reasoning (thinking tags)
    :param stream: Whether to enable streaming responses
    :param stream_steps: Whether to stream intermediate steps
    :param instruction_level: Instruction complexity level (0=minimal, 4=full)
    """
    print("\n🤖 Personal AI Agent - Agno CLI Mode")
    print("=" * 50)

    if use_remote_ollama:
        print("🖥️  Using remote Ollama at: http://tesla.local:11434")
    else:
        print("🖥️  Using local Ollama at: http://localhost:11434")

    # Display response configuration
    print(f"🧠 Show reasoning: {'✅' if show_reasoning else '❌'}")
    print(f"📡 Streaming: {'✅' if stream else '❌'}")
    print(f"🔄 Stream steps: {'✅' if stream_steps else '❌'}")
    print(
        f"📝 Instruction level: {instruction_level} ({'minimal' if instruction_level == 0 else 'basic' if instruction_level == 1 else 'moderate' if instruction_level == 2 else 'complex' if instruction_level == 3 else 'full'})"
    )

    # Initialize system
    agent, query_kb, store_int, clear_kb = await initialize_agno_system(
        use_remote_ollama, complexity_level=instruction_level
    )

    # Print formatted agent info
    console = Console()
    console.print("✅ [bold green]Agent Successfully Initialized![/bold green]")
    agent.print_agent_info(console)

    print("\nEnter your queries (type 'quit' to exit):")
    if query is not None:
        # response = await agent.agent.arun(query)
        print(f"🤖 Assistant:")
        await agent.aprint_response(query, stream=stream, show_full_reasoning=True)
        # print(f"🤖 Assistant: {response}")
        return

    try:
        while True:
            query = input("\n👤 You: ").strip()
            if query.lower() in ["quit", "exit", "q"]:
                break

            if not query:
                continue
            try:
                if show_reasoning:
                    # Use agno's async print_response with full reasoning
                    await agent.agent.aprint_response(
                        query,
                        stream=stream,
                        show_full_reasoning=True,
                        stream_intermediate_steps=stream_steps,
                    )
                else:
                    # Get response and clean it to remove thinking tags
                    print("🤖 Assistant: ")
                    await agent.agent.aprint_response(query, user_id=agent.user_id)

                # Memory is handled automatically by Agno - no manual storage needed

            except Exception as e:
                print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


def cli_main():
    """
    Main entry point for CLI mode (used by poetry scripts).
    """
    # Set up Rich logging for all components including agno

    configure_all_rich_logging()
    logger = setup_logging()

    parser = argparse.ArgumentParser(
        description="Run the Personal AI Agent with Agno Framework"
    )
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument(
        "--web", action="store_true", help="Run in web mode (Streamlit)"
    )
    parser.add_argument(
        "--remote-ollama", action="store_true", help="Use remote Ollama server"
    )

    # Response control arguments
    parser.add_argument(
        "--show-reasoning",
        action="store_true",
        default=False,
        help="Show full reasoning including thinking tags (default: False)",
    )
    parser.add_argument(
        "--no-show-reasoning",
        dest="show_reasoning",
        action="store_false",
        help="Hide reasoning and thinking tags",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        default=True,
        help="Enable streaming responses (default: True)",
    )
    parser.add_argument(
        "--no-stream",
        dest="stream",
        action="store_false",
        help="Disable streaming responses",
    )
    parser.add_argument(
        "--stream-steps",
        action="store_true",
        default=False,
        help="Stream intermediate steps (default: False)",
    )
    parser.add_argument(
        "--no-stream-steps",
        dest="stream_steps",
        action="store_false",
        help="Disable streaming intermediate steps",
    )

    # Instruction complexity arguments
    parser.add_argument(
        "--instruction-level",
        type=int,
        choices=[0, 1, 2, 3, 4],
        default=4,
        help="Instruction complexity level: 0=minimal, 1=basic tools, 2=moderate, 3=complex, 4=full (default: 4)",
    )

    args = parser.parse_args()

    # Determine mode based on arguments
    if args.web:
        logger.info("Starting Personal AI Agent in web mode (Streamlit)")
        run_agno_web(use_remote_ollama=args.remote_ollama)
    else:
        # Default to CLI mode
        logger.info("Starting Personal AI Agent in CLI mode")
        asyncio.run(
            run_agno_cli(
                use_remote_ollama=args.remote_ollama,
                show_reasoning=args.show_reasoning,
                stream=args.stream,
                stream_steps=args.stream_steps,
                instruction_level=args.instruction_level,
            )
        )


if __name__ == "__main__":
    cli_main()
