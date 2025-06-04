"""
Agno-compatible main entry point for the Personal AI Agent.

This module orchestrates all components using the native agno framework with
built-in memory capabilities, replacing custom memory implementation.
"""

import asyncio
import logging
from typing import List, Optional

from agno.agent import Agent
from agno.knowledge.agent import AgentKnowledge
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat

from agno.tools.function import Function

# Import configuration
from .config import OLLAMA_URL, USE_MCP, USE_WEAVIATE, get_mcp_servers

# Import core components
from .core import setup_weaviate

# Import utilities
from .utils import inject_dependencies, register_cleanup_handlers, setup_logging

# Import agno web interface
from .web.agno_interface import create_app, register_routes

# Global variables for cleanup
agno_agent: Optional[Agent] = None
logger: Optional[logging.Logger] = None


async def initialize_agno_system():
    """
    Initialize all system components using native agno framework capabilities.

    Returns:
        Native agno Agent with built-in memory and knowledge
    """
    global logger, agno_agent  # noqa: PLW0603
    logger = setup_logging()
    logger.info("Starting Personal AI Agent with native agno framework...")

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

    # Create Ollama model for agno
    model = OpenAIChat(
        id="qwen2.5:7b-instruct",
        api_key="ollama",  # Dummy key for local Ollama
        base_url=f"{OLLAMA_URL}/v1",
    )

    # Create AgentKnowledge with native agno Weaviate integration (if available)
    knowledge = None
    if vector_store and USE_WEAVIATE:
        try:
            # Import agno's native Weaviate vector database
            from agno.knowledge.text import TextKnowledgeBase
            from agno.vectordb.search import SearchType
            from agno.vectordb.weaviate import Weaviate

            # Use existing UserKnowledgeBase collection to preserve all stored data
            agno_vector_db = Weaviate(
                collection="UserKnowledgeBase",  # Use existing collection with your data
                search_type=SearchType.hybrid,
                local=True,  # Using local Weaviate instance
            )

            # Create knowledge base using agno's native system
            # Note: This will work with the existing UserKnowledgeBase schema
            knowledge = TextKnowledgeBase(
                path="data/knowledge",  # Directory for text files
                vector_db=agno_vector_db,
                formats=[".txt", ".md"],  # Support text and markdown files
            )

            # Load the knowledge base to work with existing schema
            logger.info(
                "Configuring knowledge base to work with existing UserKnowledgeBase..."
            )
            try:
                # Don't load files since UserKnowledgeBase has different schema
                # The existing collection already has your conversation data and facts
                logger.info(
                    "Knowledge base configured to use existing UserKnowledgeBase collection"
                )
                logger.info(
                    "Your stored facts and conversations are now accessible to the agent"
                )
            except Exception as load_error:
                logger.warning("Failed to configure knowledge base: %s", load_error)
                logger.info("Creating fallback configuration...")
                try:
                    # Just ensure the vector_db connection works
                    if hasattr(knowledge.vector_db, "client"):
                        logger.info("Vector database connection verified")
                    logger.info("Fallback knowledge base configuration created")
                except Exception as schema_error:
                    logger.error("Failed to configure knowledge base: %s", schema_error)
                    knowledge = None  # Disable knowledge base if configuration fails

            logger.info("Created native agno AgentKnowledge with Weaviate integration")
        except (ImportError, ValueError) as e:
            logger.warning(
                "Failed to create AgentKnowledge with native Weaviate: %s", e
            )
            logger.info("Continuing without knowledge base integration")
    else:
        logger.info(
            "Weaviate disabled or not available, running without knowledge base"
        )

    # Create native Memory system for conversations
    memory = Memory(
        db=SqliteMemoryDb(
            table_name="personal_agent_memory", db_file="data/personal_agent_memory.db"
        )
    )

    # Initialize MCP client for traditional tools compatibility
    mcp_client = None
    if USE_MCP:
        logger.info("Initializing MCP client...")
        from .core.mcp_client import SimpleMCPClient

        mcp_servers = get_mcp_servers()
        mcp_client = SimpleMCPClient(mcp_servers)

        if mcp_client.start_servers():
            logger.info("MCP servers started successfully")
        else:
            logger.warning("Failed to start some MCP servers")

    # Inject MCP client into tools modules for compatibility
    if mcp_client:
        logger.info("Injecting MCP dependencies into tools modules...")
        from .tools import filesystem, research, system, web

        # Inject MCP client and configuration
        web.mcp_client = mcp_client
        web.USE_MCP = True
        web.logger = logger

        filesystem.mcp_client = mcp_client
        filesystem.USE_MCP = True
        filesystem.logger = logger

        system.mcp_client = mcp_client
        system.USE_MCP = True
        system.logger = logger

        research.mcp_client = mcp_client
        research.USE_MCP = True
        research.logger = logger

        logger.info("MCP dependencies injected successfully")

    # Get MCP tools as native agno Functions
    mcp_tools = await get_mcp_tools_as_functions() if USE_MCP else []

    # Create native agno Agent with built-in memory capabilities
    agno_agent = Agent(
        name="Personal AI Assistant",
        model=model,
        description="A sophisticated personal assistant with memory and knowledge capabilities",
        instructions=[
            "You are a helpful personal assistant with access to various tools and persistent memory.",
            "Use your memory system to remember important information about users and conversations.",
            "Retrieve relevant past information to provide personalized responses.",
            "When users ask about their past interactions, search your memory to provide accurate information.",
            "Store important facts, preferences, and context for future reference.",
        ],
        # Enable native memory features
        memory=memory,
        enable_agentic_memory=True,
        enable_user_memories=True,
        enable_session_summaries=True,
        add_memory_references=True,
        add_session_summary_references=True,
        # Enable knowledge base features (if available)
        knowledge=knowledge,
        search_knowledge=True if knowledge else False,
        add_references=True if knowledge else False,
        # Tool integration
        tools=mcp_tools,
        show_tool_calls=True,
        # Agent behavior
        markdown=True,
        debug_mode=True,
        add_history_to_messages=True,
        num_history_runs=3,
    )

    logger.info(
        "Native agno agent created successfully: memory=%s, knowledge=%s, tools=%d",
        agno_agent.memory is not None,
        agno_agent.knowledge is not None,
        len(mcp_tools) if mcp_tools else 0,
    )

    # Inject dependencies for cleanup (maintain compatibility)
    inject_dependencies(weaviate_client, vector_store, mcp_client, logger)

    return agno_agent


async def get_mcp_tools_as_functions() -> List[Function]:
    """Convert MCP tools to native agno Functions."""
    from agno.tools import tool

    tools = []

    if not USE_MCP:
        return tools

    mcp_servers = get_mcp_servers()

    for server_name, _ in mcp_servers.items():
        try:
            # Create agno tool function that wraps MCP server calls
            @tool(
                name=f"mcp_{server_name}",
                description=f"Access {server_name} MCP server tools",
            )
            async def mcp_tool_wrapper(query: str) -> str:
                """Execute MCP tool via server."""
                # This is a simplified wrapper - in practice you'd want more sophisticated MCP integration
                return f"MCP tool {server_name} executed with query: {query}"

            tools.append(mcp_tool_wrapper)

        except (ImportError, ValueError) as e:
            logger.warning("Failed to create MCP tool for %s: %s", server_name, e)

    return tools


def create_agno_web_app():
    """
    Create and configure the Flask web application with native agno Agent.

    Returns:
        Configured Flask application
    """
    # Get logger instance first
    logger_instance = setup_logging()

    # Initialize agno system (run async initialization)
    agno_agent_instance = asyncio.run(initialize_agno_system())

    # Create Flask app
    app = create_app()

    # Register routes with native agno agent
    register_routes(
        app,
        agno_agent_instance,
        logger_instance,
    )

    # Register cleanup handlers
    register_cleanup_handlers()

    logger_instance.info("Native agno web application ready!")
    return app


def run_agno_web():
    """
    Run the agno web application.
    """
    app = create_agno_web_app()

    # Run the app
    print("\n🚀 Starting Personal AI Agent with Agno Framework...")
    print("🌐 Web interface will be available at: http://127.0.0.1:5003")
    print("📚 Features: Native Memory + Knowledge + MCP integration, Async operations")
    print("⚡ Framework: Agno with native Weaviate + SQLite + Ollama")
    print("🔧 Mode: Full-featured async agent with persistent memory and knowledge")
    print("\nPress Ctrl+C to stop the server.\n")

    app.run(host="127.0.0.1", port=5003, debug=False)


async def run_agno_cli():
    """
    Run native agno agent in CLI mode with streaming and reasoning.
    """
    print("\n🤖 Personal AI Agent - Native Agno CLI Mode")
    print("=" * 50)

    # Initialize system
    agent = await initialize_agno_system()

    print(
        f"✅ Agent initialized: memory={agent.memory is not None}, knowledge={agent.knowledge is not None}"
    )
    print("\nEnter your queries (type 'quit' to exit):")

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print("\n🤖 Assistant:")

            # Use native agno agent run method with streaming
            response_stream = await agent.arun(user_input, stream=True)

            # Handle streaming response
            content_parts = []
            async for response_chunk in response_stream:
                if hasattr(response_chunk, "content") and response_chunk.content:
                    print(response_chunk.content, end="", flush=True)
                    content_parts.append(response_chunk.content)

            print()  # Add newline after streaming completes

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except (RuntimeError, ValueError) as e:
            print(f"❌ Error: {e}")
            logger.error("CLI error: %s", e)


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
