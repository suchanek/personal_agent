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

# Import agno web interface (will be created)
from .web.agno_interface import create_app, register_routes

# Global variables for cleanup
agno_agent: Optional[AgnoPersonalAgent] = None
logger: Optional[logging.Logger] = setup_logging()


async def initialize_agno_system(use_remote_ollama: bool = False, complexity_level: int = 4):
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


def create_agno_web_app(use_remote_ollama: bool = False):
    """
    Create and configure the Flask web application with agno.

    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :return: Configured Flask application
    """
    # Set up Rich logging for all components including agno
    configure_all_rich_logging()
    logger_instance = setup_logging()

    # Initialize agno system (run async initialization)
    agno_agent_instance, query_kb_func, store_int_func, clear_kb_func = asyncio.run(
        initialize_agno_system(use_remote_ollama)
    )

    # Create Flask app
    app = create_app()

    # Register routes with agno agent
    register_routes(
        app,
        agno_agent_instance,
        logger_instance,
        query_kb_func,
        store_int_func,
        clear_kb_func,
    )

    # Register cleanup handlers
    register_cleanup_handlers()

    logger_instance.info("Agno web application ready!")
    return app


def run_agno_web(use_remote_ollama: bool = False):
    """
    Run the agno web application.

    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    """
    app = create_agno_web_app(use_remote_ollama)

    # Run the app
    print("\n🚀 Starting Personal AI Agent with Agno Framework...")
    print("🌐 Web interface will be available at: http://127.0.0.1:5002")
    print("📚 Features: Native MCP integration, Async operations, Enhanced memory")
    print("⚡ Framework: Agno with native MCP + Ollama")
    if use_remote_ollama:
        print("🖥️  Using remote Ollama at: http://tesla.local:11434")
    else:
        print("🖥️  Using local Ollama at: http://localhost:11434")
    print("🔧 Mode: Modern async agent with advanced capabilities")
    print("\nPress Ctrl+C to stop the server.\n")

    app.run(host="127.0.0.1", port=5002, debug=False)


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
    print(f"📝 Instruction level: {instruction_level} ({'minimal' if instruction_level == 0 else 'basic' if instruction_level == 1 else 'moderate' if instruction_level == 2 else 'complex' if instruction_level == 3 else 'full'})")

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
        response = await agent.agent.arun(query)
        print(f"🤖 Assistant: {response}")
        try:
            await agent.cleanup()
        except Exception as e:
            print(f"Warning during cleanup: {e}")

        return

    try:
        while True:
            query = input("\n👤 You: ").strip()
            if query.lower() in ["quit", "exit", "q"]:
                break

            if not query:
                continue

            print("🤖 Assistant: ")
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
                    response = await agent.agent.arun(query, user_id=agent.user_id)
                    cleaned_response = agent._clean_response(response.content)
                    print(cleaned_response)

                # Memory is handled automatically by Agno - no manual storage needed

            except Exception as e:
                print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        try:
            await agent.cleanup()
        except Exception as e:
            print(f"Warning during cleanup: {e}")


def cli_main():
    """
    Main entry point for CLI mode (used by poetry scripts).
    """
    # Set up Rich logging for all components including agno
    from .utils import configure_all_rich_logging, setup_logging

    configure_all_rich_logging()
    logger = setup_logging()

    parser = argparse.ArgumentParser(
        description="Run the Personal AI Agent with Agno Framework"
    )
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument(
        "--remote-ollama", action="store_true", help="Use remote Ollama server"
    )
    
    # Response control arguments
    parser.add_argument(
        "--show-reasoning", 
        action="store_true", 
        default=False,
        help="Show full reasoning including thinking tags (default: False)"
    )
    parser.add_argument(
        "--no-show-reasoning", 
        dest="show_reasoning",
        action="store_false", 
        help="Hide reasoning and thinking tags"
    )
    parser.add_argument(
        "--stream", 
        action="store_true", 
        default=True,
        help="Enable streaming responses (default: True)"
    )
    parser.add_argument(
        "--no-stream", 
        dest="stream",
        action="store_false", 
        help="Disable streaming responses"
    )
    parser.add_argument(
        "--stream-steps", 
        action="store_true", 
        default=False,
        help="Stream intermediate steps (default: False)"
    )
    parser.add_argument(
        "--no-stream-steps", 
        dest="stream_steps",
        action="store_false", 
        help="Disable streaming intermediate steps"
    )
    
    # Instruction complexity arguments
    parser.add_argument(
        "--instruction-level",
        type=int,
        choices=[0, 1, 2, 3, 4],
        default=4,
        help="Instruction complexity level: 0=minimal, 1=basic tools, 2=moderate, 3=complex, 4=full (default: 4)"
    )
    
    args = parser.parse_args()

    # Check if this function is being called from the paga_cli script
    # If it is, or if the --cli flag is set, run in CLI mode
    # This simple approach should be sufficient for most cases

    # Always run in CLI mode when the function name is cli_main
    # Since this is specifically the CLI entry point in pyproject.toml
    logger.info("Starting Personal AI Agent in CLI mode")

    # Run in CLI mode
    asyncio.run(run_agno_cli(
        use_remote_ollama=args.remote_ollama,
        show_reasoning=args.show_reasoning,
        stream=args.stream,
        stream_steps=args.stream_steps,
        instruction_level=args.instruction_level,
    ))


if __name__ == "__main__":
    cli_main()
