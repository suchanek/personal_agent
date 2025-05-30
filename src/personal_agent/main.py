"""
Main entry point for the Personal AI Agent.

This module orchestrates all components of the agent system including
configuration, core services, tools, and web interface.
"""

from typing import Optional

# Import configuration
from personal_agent.config import USE_MCP, USE_WEAVIATE, get_mcp_servers

# Import core components
from personal_agent.core import SimpleMCPClient, create_agent_executor, setup_weaviate

# Import tools
from personal_agent.tools import get_all_tools

# Import utilities
from personal_agent.utils import (
    inject_dependencies,
    register_cleanup_handlers,
    setup_logging,
)

# Import web interface
from personal_agent.web import create_app, register_routes

# Global variables for cleanup
agent_executor: Optional[object] = None
logger: Optional[object] = None


def initialize_system():
    """Initialize all system components."""
    # Setup logging first
    logger = setup_logging()
    logger.info("Starting Personal AI Agent...")

    # Initialize MCP client if enabled
    if USE_MCP:
        logger.info("Initializing MCP servers...")
        mcp_servers = get_mcp_servers()
        mcp_client = SimpleMCPClient(mcp_servers)
        mcp_client.start_servers()
        logger.info("MCP servers started successfully")
    else:
        logger.warning("MCP is disabled, tools may not function properly")
        mcp_client = None

    # Initialize Weaviate if enabled
    if USE_WEAVIATE:
        logger.info("Initializing Weaviate vector store...")
        success = setup_weaviate()
        if success:
            logger.info("Weaviate initialized successfully")
        else:
            logger.warning("Failed to initialize Weaviate")
    else:
        logger.warning("Weaviate is disabled, memory features will not work")

    # Get all tools with injected dependencies
    logger.info("Setting up tools...")
    # Import globals directly from memory module to get updated values
    from personal_agent.core.memory import vector_store, weaviate_client

    tools = get_all_tools(mcp_client, weaviate_client, vector_store, logger)
    logger.info("Loaded %d tools successfully", len(tools))

    # Create agent executor
    logger.info("Creating agent executor...")
    global agent_executor
    agent_executor = create_agent_executor(tools)
    logger.info("Agent executor created successfully")

    # Inject dependencies for cleanup
    inject_dependencies(weaviate_client, vector_store, mcp_client, logger)

    return tools


def create_web_app():
    """Create and configure the Flask web application."""
    # Get logger instance first
    logger_instance = setup_logging()

    # Get tools for web interface
    tools = initialize_system()

    # Extract specific tools needed by web interface
    query_kb_tool = None
    store_interaction_tool = None
    clear_kb_tool = None

    for tool in tools:
        if hasattr(tool, "name"):
            if tool.name == "query_knowledge_base":
                query_kb_tool = tool
            elif tool.name == "store_interaction":
                store_interaction_tool = tool
            elif tool.name == "clear_knowledge_base":
                clear_kb_tool = tool

    # Create Flask app
    app = create_app()

    # Register routes with dependencies
    register_routes(
        app,
        agent_executor,
        logger_instance,
        query_kb_tool,
        store_interaction_tool,
        clear_kb_tool,
    )

    return app


def main():
    """Main entry point for the Personal AI Agent."""
    # Register cleanup handlers
    register_cleanup_handlers()

    logger_instance = setup_logging()
    logger_instance.info("Web interface will be available at: http://127.0.0.1:5001")

    try:
        # Create and run the web application
        app = create_web_app()

        # Disable Flask's reloader in production to avoid resource leaks
        app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)

    except KeyboardInterrupt:
        logger_instance.info("Received keyboard interrupt")
        # cleanup() will be called by atexit, no need to call here
    except Exception as e:
        logger_instance.error("Error running Flask app: %s", e)
        from personal_agent.utils.cleanup import cleanup

        cleanup()
        raise


if __name__ == "__main__":
    main()
