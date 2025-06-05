"""
Agno-compatible main entry point for the Personal AI Agent with SQLite + LanceDB.

This module orchestrates all components using the native agno framework with
built-in memory capabilities and local file-based storage, eliminating external
database dependencies entirely.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from agno.agent import Agent
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType

from agno.tools.function import Function

# Import configuration
from .config import OLLAMA_URL, USE_MCP, get_mcp_servers

# Import utilities
from .utils import inject_dependencies, register_cleanup_handlers, setup_logging

# Import agno web interface
from .web.agno_interface import create_app, register_routes

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
    model = Ollama(id="qwen2.5:7b-instruct")

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

    # Initialize MCP client for tool compatibility (if enabled)
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
    mcp_tools = await get_mcp_tools_as_functions(model) if USE_MCP else []

    # 4. Create the Native Agno Agent
    agno_agent = Agent(
        name="Personal AI Assistant",
        model=model,
        description="A sophisticated personal assistant with persistent memory and knowledge capabilities",
        instructions=[
            "You are a helpful personal assistant with persistent memory and knowledge.",
            "Use your memory system to remember important information about users and conversations.",
            "Search your knowledge base to provide informed responses based on stored facts.",
            "When users ask about their past interactions, search your memory to provide accurate information.",
            "Store important facts, preferences, and context for future reference.",
            "All your data is stored locally using SQLite and LanceDB for maximum privacy and reliability.",
        ],
        # Memory capabilities
        memory=memory,
        enable_agentic_memory=True,
        enable_user_memories=True,
        enable_session_summaries=False,  # Disabled to prevent hanging
        add_memory_references=True,
        add_session_summary_references=False,  # Disabled to prevent hanging
        # Knowledge capabilities
        knowledge=knowledge,
        search_knowledge=True if knowledge else False,
        add_references=True if knowledge else False,
        # Session management
        storage=storage,
        # Tool integration
        tools=mcp_tools,
        show_tool_calls=True,
        # Enhanced features
        add_datetime_to_instructions=True,
        read_chat_history=True,
        markdown=True,
        debug_mode=True,
        add_history_to_messages=True,
        num_history_runs=3,
    )

    logger.info(
        "✅ SQLite + LanceDB agent created: memory=%s, knowledge=%s, storage=%s, tools=%d",
        agno_agent.memory is not None,
        agno_agent.knowledge is not None,
        agno_agent.storage is not None,
        len(mcp_tools) if mcp_tools else 0,
    )

    # Inject dependencies for cleanup (maintain compatibility)
    # Note: No weaviate_client or vector_store since we're using LanceDB
    inject_dependencies(None, None, mcp_client, logger)

    return agno_agent


async def get_mcp_tools_as_functions(model) -> List[Function]:
    """Convert MCP tools to native agno Functions with real MCP server connections."""
    import logging
    from textwrap import dedent

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    from agno.tools import tool
    from agno.tools.mcp import MCPTools

    # Get logger for this function
    logger = logging.getLogger(__name__)

    tools = []

    if not USE_MCP:
        return tools

    mcp_servers = get_mcp_servers()

    for server_name, config in mcp_servers.items():
        try:
            # Extract server configuration
            command = config.get("command", "npx")
            args = config.get("args", [])
            env = config.get("env", {})
            description = config.get(
                "description", f"Access to {server_name} MCP server"
            )

            # Create the actual tool function with proper MCP integration
            def make_mcp_tool(
                name: str, cmd: str, tool_args: list, tool_env: dict, desc: str
            ):
                @tool(
                    name=f"mcp_{name}",
                    description=f"Access {name} MCP server tools: {desc}",
                )
                async def mcp_tool_wrapper(query: str) -> str:
                    """Execute MCP tool via real server connection."""
                    try:
                        # Prepare environment - convert GITHUB_PERSONAL_ACCESS_TOKEN to GITHUB_TOKEN if needed
                        server_env = tool_env.copy() if tool_env else {}
                        if (
                            name == "github"
                            and "GITHUB_PERSONAL_ACCESS_TOKEN" in server_env
                        ):
                            # The GitHub MCP server expects GITHUB_TOKEN
                            server_env["GITHUB_TOKEN"] = server_env[
                                "GITHUB_PERSONAL_ACCESS_TOKEN"
                            ]
                            logger.info(
                                "Converted GITHUB_PERSONAL_ACCESS_TOKEN to GITHUB_TOKEN for GitHub MCP server"
                            )

                        server_params = StdioServerParameters(
                            command=cmd,
                            args=tool_args,
                            env=server_env,
                        )

                        # Create client session using async context manager
                        async with stdio_client(server_params) as (read, write):
                            async with ClientSession(read, write) as session:
                                # Initialize MCP toolkit with session
                                mcp_tools = MCPTools(session=session)
                                await mcp_tools.initialize()

                                # Create specialized instructions based on server type
                                if name == "github":
                                    instructions = dedent(
                                        """\
                                        You are a GitHub assistant. Help users explore repositories and their activity.
                                        
                                        Available tools include:
                                        - search_repositories: Search for repositories by name or keywords
                                        - get_file_contents: Get contents of files in a repository
                                        - search_code: Search for code within repositories
                                        - search_issues: Search for issues in repositories
                                        - list_issues: List issues in a repository
                                        - get_issue: Get details of a specific issue
                                        - list_commits: List commits in a repository
                                        - list_pull_requests: List pull requests in a repository
                                        - get_pull_request: Get details of a specific pull request
                                        
                                        When searching for repository information:
                                        1. Use search_repositories to find repositories by name
                                        2. Use get_file_contents to examine README, setup files, etc.
                                        3. Use search_code to find specific code patterns
                                        4. Use list_issues and list_commits for activity information
                                        
                                        - Provide organized, concise insights about the repository
                                        - Focus on facts and data from the GitHub API
                                        - Use markdown formatting for better readability
                                        - Present numerical data in tables when appropriate
                                        - Include links to relevant GitHub pages when helpful
                                    """
                                    )
                                elif name.startswith("filesystem"):
                                    instructions = f"You are a filesystem assistant for {name}. Help with file and directory operations."
                                elif name == "brave-search":
                                    instructions = "You are a web search assistant. Help users find information on the web."
                                elif name == "puppeteer":
                                    instructions = "You are a browser automation assistant. Help with web scraping and automation tasks."
                                else:
                                    instructions = f"You are an assistant using {name} MCP server. Help with the user's request."

                                # Create a temporary agent for this MCP server
                                temp_agent = Agent(
                                    model=model,  # Use the global model from initialize_agno_system
                                    tools=[mcp_tools],
                                    instructions=instructions,
                                    markdown=True,
                                    show_tool_calls=False,  # Keep clean for production
                                )

                                # Run the query
                                response = await temp_agent.arun(query)
                                return response.content

                    except Exception as e:
                        logger.error("Error running %s MCP server: %s", name, e)
                        return f"Error using {name}: {str(e)}"

                return mcp_tool_wrapper

            # Create the tool and add it to the list
            tool_func = make_mcp_tool(server_name, command, args, env, description)
            tools.append(tool_func)
            logger.info("Created real MCP tool function for: %s", server_name)

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
