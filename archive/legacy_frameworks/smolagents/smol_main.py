"""
Smolagents-compatible main entry point for the Personal AI Agent.

This module orchestrates all components using smolagents framework instead of LangChain,
while maintaining the same functionality and web interface.
"""

from typing import Optional

# Import configuration
from .config import USE_MCP, USE_WEAVIATE, get_mcp_servers

# Import core components
from .core import SimpleMCPClient, setup_weaviate
from .core.multi_agent_system import create_multi_agent_system
from .core.smol_agent import create_smolagents_executor

# Import smolagents tools and memory functions
from .tools.smol_tools import (
    ALL_TOOLS,
    clear_knowledge_base,
    query_knowledge_base,
    set_mcp_client,
    set_memory_components,
    store_interaction,
)

# Import utilities
from .utils import inject_dependencies, register_cleanup_handlers, setup_logging

# Import smolagents web interface
from .web.smol_interface import create_app, register_routes

# Global variables for cleanup
smolagents_agent: Optional[object] = None
multi_agent_system: Optional[object] = None
logger: Optional[object] = None


def initialize_smolagents_system():
    """
    Initialize all system components for smolagents.

    :return: Initialized smolagents agent and memory functions
    """
    # Setup logging first
    logger = setup_logging()
    logger.info("Starting Personal AI Agent with smolagents...")

    # Initialize MCP client if enabled
    if USE_MCP:
        logger.info("Initializing MCP servers...")
        mcp_servers = get_mcp_servers()
        mcp_client = SimpleMCPClient(mcp_servers)

        if not mcp_client.start_servers():
            logger.error("Failed to start MCP servers")
            raise RuntimeError("MCP server initialization failed")

        logger.info("MCP servers started successfully")

        # Set MCP client in smol_tools
        set_mcp_client(mcp_client)
    else:
        logger.warning("MCP is disabled, tools may not function properly")
        mcp_client = None

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

    # Set memory components in smol_tools
    set_memory_components(weaviate_client, vector_store, USE_WEAVIATE)

    # Create smolagents executor (single agent - legacy mode)
    logger.info("Creating smolagents executor...")
    global smolagents_agent
    smolagents_agent = create_smolagents_executor()
    logger.info("Smolagents executor created with %d tools", len(ALL_TOOLS))

    # Create multi-agent system (new coordinated mode)
    logger.info("Creating multi-agent system...")
    global multi_agent_system
    multi_agent_system = create_multi_agent_system(
        mcp_client=mcp_client,
        weaviate_client=weaviate_client,
        vector_store=vector_store,
    )
    logger.info("Multi-agent system created with specialized agents")

    # Inject dependencies for cleanup
    inject_dependencies(weaviate_client, vector_store, mcp_client, logger)

    return (
        multi_agent_system,  # Return multi-agent system as primary
        smolagents_agent,  # Keep single agent for compatibility
        query_knowledge_base,
        store_interaction,
        clear_knowledge_base,
    )


def create_smolagents_web_app():
    """
    Create and configure the Flask web application with smolagents.

    :return: Configured Flask application
    """
    # Get logger instance first
    logger_instance = setup_logging()

    # Initialize smolagents system
    multi_agent, single_agent, query_kb_func, store_int_func, clear_kb_func = (
        initialize_smolagents_system()
    )

    # Create Flask app
    app = create_app()

    # Register routes with multi-agent system (primary) and single agent (fallback)
    register_routes(
        app,
        multi_agent,
        logger_instance,
        query_kb_func,
        store_int_func,
        clear_kb_func,
        fallback_agent=single_agent,
    )

    # Register cleanup handlers
    register_cleanup_handlers()

    logger_instance.info("Smolagents web application ready!")
    return app


def run_smolagents_web():
    """
    Run the smolagents web application.

    :return: None
    """
    app = create_smolagents_web_app()

    # Run the app
    print("\n🚀 Starting Personal AI Agent with Smolagents...")
    print("🌐 Web interface will be available at: http://127.0.0.1:5001")
    print("📚 Features: MCP integration, Web search, GitHub, Memory, File operations")
    print("⚡ Framework: Smolagents with LiteLLM + Ollama")
    print("\nPress Ctrl+C to stop the server.\n")

    app.run(host="127.0.0.1", port=5001, debug=False)


if __name__ == "__main__":
    run_smolagents_web()
