"""
Agno-compatible main entry point for the Personal AI Agent.

This module orchestrates all components using the agno framework for modern
async agent operations while maintaining compatibility with existing infrastructure.
"""

import asyncio
import logging
from typing import Optional

# Import configuration
from .config import LLM_MODEL, USE_MCP, USE_WEAVIATE, get_mcp_servers

# Import core components
from .core import setup_weaviate
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

    # Initialize Weaviate if enabled
    weaviate_client = None
    vector_store = None

    if USE_WEAVIATE:
        logger.info("Initializing Weaviate vector store...")
        success = setup_weaviate()
        if success:
            # Import the initialized components
            from .core.memory import vector_store as vs
            from .core.memory import weaviate_client as wc

            weaviate_client = wc
            vector_store = vs
            logger.info("Weaviate initialized successfully")
        else:
            logger.warning("Failed to initialize Weaviate")
    else:
        logger.warning("Weaviate is disabled, memory features will not work")

    # Create agno agent
    logger.info("Creating agno agent...")
    global agno_agent
    agno_agent = await create_agno_agent(
        weaviate_client=weaviate_client,
        vector_store=vector_store,
        model_provider="ollama",  # Default to Ollama
        model_name=LLM_MODEL,  # Use configured model
        debug=False,
    )

    agent_info = agno_agent.get_agent_info()
    logger.info(
        "Agno agent created successfully: %s servers, memory=%s",
        agent_info["mcp_servers"],
        agent_info["memory_enabled"],
    )

    # Memory functions (stubs for now - will be implemented)
    async def query_knowledge_base(query: str) -> str:
        """Query the knowledge base using the agno agent."""
        if not agno_agent:
            return "Agent not initialized"
        logger.info("Querying knowledge base: %s", query)
        return await agno_agent.run(f"Search my knowledge base for: {query}")

    async def store_interaction(query: str, response: str) -> bool:
        """Store interaction in memory."""
        if agno_agent and agno_agent.enable_memory:
            await agno_agent._store_interaction(query, response)
            logger.info("Interaction stored in memory")
            return True
        return False

    async def clear_knowledge_base() -> bool:
        """Clear the knowledge base."""
        logger.info("Knowledge base clearing requested (not implemented yet)")
        return True

    # Inject dependencies for cleanup
    inject_dependencies(weaviate_client, vector_store, None, logger)

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


async def run_agno_cli():
    """
    Run agno agent in CLI mode with streaming and reasoning.
    """
    print("\n🤖 Personal AI Agent - Agno CLI Mode")
    print("=" * 50)

    # Initialize system
    agent, query_kb, store_int, clear_kb = await initialize_agno_system()

    print(f"✅ Agent initialized: {agent.get_agent_info()}")
    print("\nEnter your queries (type 'quit' to exit):")

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

                # Since aprint_response already handles the output, we get response separately for storage
                response_result = await agent.agent.arun(query)
                response_content = (
                    response_result.content
                    if hasattr(response_result, "content")
                    else str(response_result)
                )

                # Store interaction
                await store_int(query, response_content)

            except Exception as e:
                print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        try:
            await agent.cleanup()
            # Also cleanup weaviate connection properly if it exists
            if hasattr(agent, "weaviate_client") and agent.weaviate_client:
                agent.weaviate_client.close()
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
