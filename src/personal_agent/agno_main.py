"""
Agno-compatible main entry point for the Personal AI Agent.

This module orchestrates all components using the agno framework for modern
async agent operations while maintaining compatibility with existing infrastructure.
"""

import asyncio
import logging
from typing import Optional

# Import configuration
from .config import LLM_MODEL, USE_MCP
from .config.settings import AGNO_KNOWLEDGE_DIR, AGNO_STORAGE_DIR

# Import core components
from .core.agno_agent import AgnoPersonalAgent, create_agno_agent

# Import utilities
from .utils import inject_dependencies, register_cleanup_handlers, setup_logging

# Import agno web interface (will be created)
from .web.agno_interface import create_app, register_routes

# Global variables for cleanup
agno_agent: Optional[AgnoPersonalAgent] = None
logger: Optional[logging.Logger] = None


async def initialize_agno_system():
    """
    Initialize all system components for agno framework.

    Returns:
        Tuple of (agno_agent, memory_functions)
    """
    global logger
    logger = setup_logging()
    logger.info("Starting Personal AI Agent with agno framework...")

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
        debug=False,
    )

    agent_info = agno_agent.get_agent_info()
    logger.info(
        "Agno agent created successfully: %s servers, memory=%s",
        agent_info["mcp_servers"],
        agent_info["memory_enabled"],
    )

    # Memory functions (legacy compatibility - Agno handles memory automatically)
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


def create_agno_web_app():
    """
    Create and configure the Flask web application with agno.

    Returns:
        Configured Flask application
    """
    # Get logger instance first
    logger_instance = setup_logging()

    # Initialize agno system (run async initialization)
    agno_agent_instance, query_kb_func, store_int_func, clear_kb_func = asyncio.run(
        initialize_agno_system()
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


def run_agno_web():
    """
    Run the agno web application.
    """
    app = create_agno_web_app()

    # Run the app
    print("\n🚀 Starting Personal AI Agent with Agno Framework...")
    print("🌐 Web interface will be available at: http://127.0.0.1:5002")
    print("📚 Features: Native MCP integration, Async operations, Enhanced memory")
    print("⚡ Framework: Agno with native MCP + Ollama")
    print("🔧 Mode: Modern async agent with advanced capabilities")
    print("\nPress Ctrl+C to stop the server.\n")

    app.run(host="127.0.0.1", port=5002, debug=False)


async def run_agno_cli(query: str = None):
    """
    Run agno agent in CLI mode with streaming and reasoning.
    """
    print("\n🤖 Personal AI Agent - Agno CLI Mode")
    print("=" * 50)

    # Initialize system
    agent, query_kb, store_int, clear_kb = await initialize_agno_system()

    print(f"✅ Agent initialized: {agent.get_agent_info()}")
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
                # Use agno's async print_response with streaming for better UX
                await agent.agent.aprint_response(
                    query,
                    stream=True,
                    show_full_reasoning=True,
                    stream_intermediate_steps=True,
                )

                # Since aprint_response already handles the output, we get response separately if needed
                response_result = await agent.agent.arun(query)
                response_content = (
                    response_result.content
                    if hasattr(response_result, "content")
                    else str(response_result)
                )

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
    asyncio.run(run_agno_cli())


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        # Run in CLI mode
        asyncio.run(run_agno_cli())
    else:
        # Run web interface
        run_agno_web()
