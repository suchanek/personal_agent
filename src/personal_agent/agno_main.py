"""
Agno-compatible main entry point for the Personal AI Agent with SQLite + LanceDB.

This module orchestrates all components using the native agno framework with
built-in memory capabilities and local file-based storage, eliminating external
database dependencies entirely.
"""

# pylint: disable=C0415, C0301, W0718, W0603
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from agno.agent import Agent
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.github import GithubTools
from agno.tools.mcp import MCPTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.youtube import YouTubeTools

from .agents.ollama_agents import finance_agent, web_agent, youtube_agent

# Import configuration
from .config.settings import LLM_MODEL
from .core.agno_agent import create_agno_agent

# Import utilities
from .utils import register_cleanup_handlers, setup_logging

# Import agno web interface
from .web.agno_interface import create_app, register_routes


async def create_filesystem_mcp_tools(root_path: str = None) -> Optional[MCPTools]:
    """
    Create filesystem MCP tools with proper session management.

    This function demonstrates how to properly initialize MCPTools with a session.
    Based on the pattern from file_agent.py.

    Args:
        root_path: Root directory for filesystem operations (defaults to current working directory)

    Returns:
        Initialized MCPTools instance or None if initialization fails
    """
    if root_path is None:
        root_path = str(Path.cwd())

    try:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", root_path],
        )

        # Create client session
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize MCP toolkit
                mcp_tools = MCPTools(session=session)
                await mcp_tools.initialize()
                return mcp_tools

    except Exception as e:
        if logger:
            logger.error("Failed to create filesystem MCP tools: %s", e)
        return None


async def create_github_mcp_tools() -> Optional[MCPTools]:
    """
    Create GitHub MCP tools with proper session management.

    This function demonstrates how to properly initialize GitHub MCPTools with a session.
    Based on the pattern from github_agents.py.

    Returns:
        Initialized MCPTools instance or None if initialization fails
    """
    if not os.getenv("GITHUB_TOKEN"):
        if logger:
            logger.warning("GITHUB_TOKEN not set, cannot create GitHub MCP tools")
        return None

    try:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
        )

        # Create client session
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize MCP toolkit
                mcp_tools = MCPTools(session=session)
                await mcp_tools.initialize()
                return mcp_tools

    except Exception as e:
        if logger:
            logger.error("Failed to create GitHub MCP tools: %s", e)
        return None


# Global variables for cleanup
agno_agent: Optional[Agent] = None
logger: Optional[logging.Logger] = None

# Local file paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


async def initialize_agno_system():
    """
    Initialize all system components using native agno framework with SQLite + LanceDB.

    Returns:
        Native agno Agent with built-in memory and knowledge (no external dependencies)
    """
    global logger, agno_agent  # noqa: PLW0603
    logger = setup_logging()
    logger.info(
        "Starting Personal AI Agent with SQLite + LanceDB (zero external dependencies)..."
    )

    # Create Ollama model for agno
    model = Ollama(id=LLM_MODEL)

    # 1. SQLite Memory System (for conversations)
    memory = Memory(
        db=SqliteMemoryDb(
            table_name="personal_agent_memory", db_file=str(DATA_DIR / "memory.db")
        ),
        model=model,
    )
    logger.info("Initialized SQLite memory system")

    # 2. LanceDB Knowledge Base (for facts and documents)
    knowledge = None
    try:
        # Ensure knowledge directory exists and has essential files
        knowledge_path = DATA_DIR / "knowledge"

        # Auto-create essential knowledge files if they don't exist
        from .utils.knowledge_init import auto_create_knowledge_files

        try:
            files_created = auto_create_knowledge_files(knowledge_path, logger)
            if files_created:
                logger.info("Created essential knowledge files for new installation")
        except Exception as creation_error:
            logger.warning("Failed to auto-create knowledge files: %s", creation_error)

        knowledge = TextKnowledgeBase(
            path=str(knowledge_path),
            vector_db=LanceDb(
                table_name="personal_agent_knowledge",
                uri=str(DATA_DIR / "lancedb"),  # Local directory storage
                search_type=SearchType.hybrid,
                embedder=OllamaEmbedder(id="nomic-embed-text", dimensions=768),
            ),
            formats=[".txt", ".md", ".json"],  # Support multiple formats
        )
        logger.info("Initialized LanceDB knowledge base")

        # Load knowledge files into the vector database
        if knowledge_path.exists() and any(knowledge_path.iterdir()):
            try:
                knowledge.load(recreate=False)  # Don't recreate, preserve existing data
                logger.info("Loaded knowledge files into LanceDB")

                # Count and report loaded files
                files_count = len(list(knowledge_path.glob("*.*")))
                logger.info("Knowledge base contains %d files", files_count)
            except Exception as load_error:
                logger.warning("Could not load existing knowledge: %s", load_error)
                logger.info("Knowledge base will work with new files only")
        else:
            logger.info(
                "No knowledge files found, knowledge base ready for new content"
            )
    except Exception as e:
        logger.warning("Failed to initialize LanceDB knowledge base: %s", e)
        logger.info("Continuing without knowledge base")
        knowledge = None

    # 3. SQLite Agent Storage (for session management)
    storage = SqliteAgentStorage(
        table_name="personal_agent_sessions", db_file=str(DATA_DIR / "agents.db")
    )
    logger.info("Initialized SQLite agent storage")

    # 4. MCP Tools are created on-demand with proper sessions
    # See file_agent.py and github_agents.py for examples of session-based MCP tools
    logger.info(
        "MCP tools will be initialized on-demand with proper sessions when needed"
    )

    agno_tools = [
        DuckDuckGoTools(),
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
        ),
        YouTubeTools(),
        GithubTools(access_token=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", None)),
    ]

    # Use agno_tools directly (MCP tools created on-demand with sessions)
    all_tools = agno_tools

    # 4. Create the Native Agno Agent
    agno_agent = await create_agno_agent()

    logger.info(
        "✅ SQLite + LanceDB agent created: memory=%s, knowledge=%s, storage=%s, tools=%d",
        agno_agent.memory is not None,
        agno_agent.knowledge is not None,
        agno_agent.storage is not None,
        len(all_tools),
    )

    # No longer need to inject custom MCP dependencies since we're using native Agno MCP tools
    # inject_dependencies(mcp_client, logger)

    return agno_agent


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

    logger_instance.info("SQLite + LanceDB web application ready!")
    return app


def run_agno_web():
    """
    Run the agno web application.
    """
    app = create_agno_web_app()

    # Run the app
    print("\n🚀 Starting Personal AI Agent with SQLite + LanceDB...")
    print("🌐 Web interface will be available at: http://127.0.0.1:5003")
    print("📚 Features: SQLite Memory + LanceDB Knowledge + MCP Tools")
    print("⚡ Storage: Local files only (no external databases)")
    print("🔧 Files: data/memory.db, data/lancedb/, data/knowledge/")
    print("🔒 Privacy: All data stored locally")
    print("\nPress Ctrl+C to stop the server.\n")

    app.run(host="127.0.0.1", port=5003, debug=False)


async def run_agno_cli():
    """
    Run native agno agent in CLI mode with streaming and reasoning.
    """
    print("\n🤖 Personal AI Agent - SQLite + LanceDB CLI Mode")
    print("=" * 60)

    # Initialize system
    agent = await initialize_agno_system()

    print(
        f"✅ Agent initialized: memory={agent.memory is not None}, knowledge={agent.knowledge is not None}, storage={agent.storage is not None}"
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


def show_storage_info():
    """Show information about the local storage setup."""
    print("\n📁 SQLite + LanceDB Storage Structure:")
    print("=" * 45)
    print("data/")
    print("├── memory.db           # SQLite conversation memory")
    print("├── agents.db           # SQLite session storage")
    print("├── lancedb/            # LanceDB vector storage")
    print("│   └── personal_agent_knowledge/")
    print("└── knowledge/          # Your knowledge files")
    print("    ├── facts.txt")
    print("    ├── preferences.md")
    print("    └── documents.json")
    print("\n🎯 Benefits:")
    print("✅ No external databases (no Docker, no servers)")
    print("✅ File-based storage (easy backup/restore)")
    print("✅ Fast local performance")
    print("✅ Works offline")
    print("✅ Cross-platform compatibility")
    print("✅ Zero network dependencies")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        # Run in CLI mode
        asyncio.run(run_agno_cli())
    elif len(sys.argv) > 1 and sys.argv[1] == "info":
        # Show storage info
        show_storage_info()
    else:
        # Run web interface
        run_agno_web()
