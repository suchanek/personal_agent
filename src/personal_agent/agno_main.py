"""
Agno-compatible main entry point for the Personal AI Agent with SQLite + LanceDB.

This module orchestrates all components using the native agno framework with
built-in memory capabilities and local file-based storage, eliminating external
database dependencies entirely.
"""

# pylint: disable=C0415, C0301, W0718, W0603, C0413, C0411

import asyncio
import logging
import os
from pathlib import Path
from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.embedder.ollama import OllamaEmbedder
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.knowledge.url import UrlKnowledge
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.storage.sqlite import SqliteStorage
from agno.team.team import Team
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agno.tools.dalle import DalleTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.github import GithubTools
from agno.tools.mcp import MCPTools
from agno.tools.python import PythonTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.youtube import YouTubeTools

from .agents import (
    coding_agent,
    fal_agent,
    gif_agent,
    image_agent,
    ml_gif_agent,
    ml_music_agent,
    ml_video_agent,
    web_agent,
)
from .agents.ollama_agents import finance_agent, youtube_agent

# Import configuration
from .config.settings import CODING_AGENT_MODEL, DATA_DIR, LLM_MODEL

# Import utilities
from .utils import setup_logging

# Load environment variables from .env file
load_dotenv()
cwd = Path(__file__).parent
tmp_dir = cwd.joinpath("tmp")
tmp_dir.mkdir(parents=True, exist_ok=True)

# Global variables for cleanup
agno_agent: Optional[Agent] = None
logger: Optional[logging.Logger] = None

# Local file paths
DATA_DIR = Path(DATA_DIR)
DATA_DIR.mkdir(exist_ok=True)

_description = dedent(
    """\
    You are PersonalAgent, an advanced AI Agent capable of advanced reasoning and problem-solving.
    Your goal is to help users search the internet, analyze data, create code, and provide
    explanations, working code examples, and optional audio explanations for complex concepts."""
)


_instructions = dedent(
    """\
    Your mission is to provide comprehensive answers to your users. Follow these steps to ensure the best possible response:

    1. **Analyze the request**
        - Analyze the request to determine if it requires a knowledge search, creating code, summarizing
        new information, analyzing data.
        - If you need to search the knowledge base, identify 1-3 key search terms related to the request.
        - If you need to create code, search the knowledge base for relevant concepts and use the example code as a guide.
        - When the user asks for an Agent, they mean an Agno Agent.
        - When the user asks for the latest news, use your web search capabilities to find the latest information.
        - When the user asks for an image, use your image generation capabilities to create a vivid image of the concept.
        - when the user asks for financial data, use your finance tools to retrieve stock prices, analyst recommendations, and company news.
        - When the user asks for YouTube videos, use your YouTube tools to find relevant videos and channels.
        - Always take user preferences into account, such as preferred programming languages, frameworks, or specific topics of interest.
        - ensure to provide clear, concise explanations and code examples that are easy to understand and run.
        - Ensure you know the user's preferences, such as preferred programming languages, frameworks, or specific topics of interest.
        - Ensure you know the user's NAME, so you can address them properly in your responses.


    After Analysis, always start the iterative search process. No need to wait for approval from the user.

    2. **Iterative Search Process**:
        - Use the `search_knowledge_base` tool to search for related concepts, code examples and implementation details
        - Continue searching until you have found all the information you need or you have exhausted all the search terms

    After the iterative search process, determine if you need to create code, summarize new information, analyze data, or create an Agent.
    or do analysis of the data.
    If you do, ask the user if they want you to create the Agent and run it.

    3. **Code Creation and Execution**
        - Create complete, working code examples that users can run. For example:
        ```python
        from agno.agent import Agent
        from agno.tools.duckduckgo import DuckDuckGoTools

        agent = Agent(tools=[DuckDuckGoTools()])

        # Perform a web search and capture the response
        response = agent.run("What's happening in France?")
        ```
        - You must remember to use agent.run() and NOT agent.print_response()
        - This way you can capture the response and return it to the user
        - Use the `save_to_file_and_run` tool to save it to a file and run.
        - Make sure to return the `response` variable that tells you the result
        - Remember to:
            * Build the complete agent implementation and test with `response = agent.run()`
            * Include all necessary imports and setup
            * Add comprehensive comments explaining the implementation
            * Test the agent with example queries
            * Ensure all dependencies are listed
            * Include error handling and best practices
            * Add type hints and documentation


    4. **Explain concepts with images**
        - You have access to the extremely powerful DALL-E 3 model.
        - Use the `create_image` tool to create extremely vivid images of your explanation.

    Be concise and clear in your explanations, using images to enhance understanding.
    """
)

# Initialize knowledge base
agent_knowledge = UrlKnowledge(
    urls=["https://docs.agno.com/llms-full.txt"],
    vector_db=LanceDb(
        uri=str(DATA_DIR / "lancedb"),  # Local directory storage
        table_name="agno_assist_knowledge",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

# Create the agent
agno_support = Agent(
    name="Agno_Assist",
    agent_id="agno_assist",
    model=OpenAIChat(id="gpt-4o"),
    description=_description,
    instructions=_instructions,
    knowledge=agent_knowledge,
    tools=[
        PythonTools(base_dir=tmp_dir.joinpath("agents"), read_files=True),
        DalleTools(model="dall-e-3", size="1792x1024", quality="hd", style="vivid"),
    ],
    storage=SqliteStorage(
        table_name="agno_assist_sessions",
        db_file="tmp/agents.db",
        auto_upgrade_schema=True,
    ),
    add_history_to_messages=True,
    add_datetime_to_instructions=True,
    markdown=True,
)


async def create_filesystem_mcp_tools(root_path: str = None) -> Optional[MCPTools]:
    """
    Create filesystem MCP tools with proper session management.

    This function demonstrates how to properly initialize MCPTools with a session.
    Based on the pattern from file_agent.py with persistent session management.

    Args:
        root_path: Root directory for filesystem operations (defaults to current working directory)

    Returns:
        Initialized MCPTools instance or None if initialization fails
    """
    from contextlib import AsyncExitStack

    if root_path is None:
        root_path = str(Path.cwd())

    try:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", root_path],
        )

        # Use AsyncExitStack to keep the session alive
        exit_stack = AsyncExitStack()

        # Create client session and keep it alive
        read, write = await exit_stack.enter_async_context(stdio_client(server_params))
        session = await exit_stack.enter_async_context(ClientSession(read, write))

        # Initialize MCP toolkit
        mcp_tools = MCPTools(session=session)
        await mcp_tools.initialize()

        # Store the exit_stack on the mcp_tools object so it can be cleaned up later
        mcp_tools._exit_stack = exit_stack

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


async def initialize_agno_system():
    """
    Initialize all system components using native agno framework with SQLite + LanceDB.

    Returns:
        Native agno Agent with built-in memory and knowledge (no external dependencies)
    """
    global logger, agno_agent  # noqa: PLW0603
    logger = setup_logging(level=logging.WARNING, name="personal_agent")
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

    agno_tools = []

    # Add GitHub tools only if token is available
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", None)
    if github_token:
        agno_tools.append(GithubTools(access_token=github_token))
        logger.info("GitHub tools enabled with access token")
    else:
        logger.warning("GitHub tools disabled - GITHUB_PERSONAL_ACCESS_TOKEN not found")
        logger.info(
            "To enable GitHub tools, set GITHUB_PERSONAL_ACCESS_TOKEN environment variable"
        )

    # Add filesystem tools using create_filesystem_mcp_tools function
    try:
        filesystem_tools = await create_filesystem_mcp_tools()
        if filesystem_tools:
            agno_tools.append(filesystem_tools)
            logger.info("Filesystem MCP tools enabled")
        else:
            logger.warning("Failed to initialize filesystem MCP tools")
    except Exception as e:
        logger.warning("Failed to load filesystem MCP tools: %s", e)

    # Use agno_tools directly (MCP tools created on-demand with sessions)
    all_tools = agno_tools

    # 4. Create the Native Agno Agent
    agno_agent = Agent(
        name="Personal AI Assistant",
        model=model,
        description="A sophisticated personal assistant with persistent memory and knowledge capabilities",
        instructions=[
            "You are a helpful personal assistant with persistent memory and knowledge.",
            "Your primary role is to coordinate various agents and tools to assist users.",
            ""
            "Use your memory system to remember important information about users and conversations.",
            "Search your knowledge base to provide informed responses based on stored facts.",
            "When users ask about their past interactions, search your memory to provide accurate information.",
            "Store important facts, preferences, and context for future reference.",
            "All your data is stored locally using SQLite and LanceDB for maximum privacy and reliability.",
            "When asked about coding, use your coding agent to assist with programming tasks.",
            "When asked about finance, use your finance agent to provide stock and market information.",
            "When asked about YouTube, use your YouTube agent to find videos and channels.",
            "When asked about the web, use your web agent to search for information online.",
            "When asked about GitHub, use your GitHub tool to search for repositories and code.",
            "When asked about file operations, use your file tool to manage files and directories.",
            "When asked about images, use your image agent to generate and retrieve images.",
            "When asked about gifs, use your gif agent to generate and retrieve gifs.",
            "When asked about audio, use your audio agent to generate and retrieve audio.",
            "When asked about videos, use your video agent to generate and retrieve videos.",
            "When asked about music, use your music agent to generate and retrieve music.",
        ],
        # Memory capabilities
        role="Personal AI Assistant",
        memory=memory,
        enable_agentic_memory=True,  # Disabled for simplicity,
        enable_user_memories=True,  # Disabled for simplicity
        enable_session_summaries=False,  # Disabled to prevent hanging
        add_memory_references=True,
        add_session_summary_references=False,  # Disabled to prevent hanging
        # Knowledge capabilities
        knowledge=knowledge,
        search_knowledge=False if knowledge else False,
        add_references=False if knowledge else False,
        # Session management
        storage=storage,
        # Tool integration
        tools=all_tools,
        show_tool_calls=True,
        # Enhanced features
        add_datetime_to_instructions=True,
        read_chat_history=True,
        markdown=True,
        debug_mode=False,
        add_history_to_messages=True,
        num_history_runs=3,
        add_name_to_instructions=True,
        team=[
            finance_agent,
            youtube_agent,
            coding_agent,
            ml_gif_agent,
            ml_music_agent,
            ml_video_agent,
            fal_agent,
            gif_agent,
            image_agent,
            web_agent,
        ],  # Example agents
    )

    logger.info(
        "✅ SQLite + LanceDB agent created: memory=%s, knowledge=%s, storage=%s, tools=%d",
        agno_agent.memory is not None,
        agno_agent.knowledge is not None,
        agno_agent.storage is not None,
        len(all_tools),
    )
    logger.info("Personal AI Agent initialized successfully")
    logger.info(
        "You can now interact with the agent using its run method or through the CLI"
    )
    return agno_agent


async def Orun_agno_cli():
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
            await agent.print_response()

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

    if len(sys.argv) > 1 and sys.argv[1] == "info":
        # Show storage info
        show_storage_info()
    else:
        # Run CLI mode (web interface moved to Streamlit)
        asyncio.run(run_agno_cli())
