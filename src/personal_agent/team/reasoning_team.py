"""
Ollama Multi-Purpose Reasoning Team Module

This module implements a comprehensive multi-agent team system using Ollama models for various
specialized tasks. The team coordinates between different agents with shared memory and knowledge
management capabilities, providing a unified interface for complex reasoning and task execution.

Key Components:
    - **Multi-Agent Team**: Coordinates specialized agents for different domains
    - **Shared Memory System**: Enables agents to share context and maintain conversation history
    - **Knowledge Management**: Integrates with LightRAG for factual knowledge storage and retrieval
    - **Memory Management**: Stores and retrieves personal user information and preferences
    - **CLI Interface**: Interactive command-line interface with enhanced memory commands

Specialized Agents:
    - **Memory Agent**: Manages personal information and factual knowledge storage/retrieval
    - **Web Agent**: Performs web searches using Google Search
    - **Finance Agent**: Retrieves and analyzes financial data using YFinance
    - **Writer Agent**: Creates content, articles, and creative writing
    - **Calculator Agent**: Performs mathematical calculations and operations
    - **Python Agent**: Executes Python code and scripts
    - **File Agent**: Handles file system operations and management

Features:
    - Ollama model integration with configurable local/remote endpoints
    - Docker service synchronization and management
    - Comprehensive resource cleanup to prevent memory leaks
    - Enhanced CLI with memory commands (!, ?, @, etc.)
    - Shared context between team members for coherent conversations
    - Automatic role mapping fixes for OpenAI API compatibility
    - Timeout handling for knowledge base operations
    - Rich console formatting for better user experience

Usage:
    The module can be run directly as a CLI application or imported for programmatic use:

    ```bash
    # Run as CLI
    python -m personal_agent.team.reasoning_team

    # Or use the installed command
    paga_team_cli
    ```

    Programmatic usage:
    ```python
    import asyncio
    from personal_agent.team.reasoning_team import create_team

    async def main():
        team = await create_team()
        response = await team.arun("What's the weather like today?")
        print(response)

    asyncio.run(main())
    ```

Memory Commands:
    - `! <text>` - Store personal information immediately
    - `? <query>` - Query stored memories
    - `@ <topics>` - Get memories by topic
    - `list` - List all stored memories
    - `recent` - Show recent memories
    - `clear` - Clear conversation (not memories)
    - `help` - Show available commands

Dependencies:
    - agno: Core agent framework
    - ollama: Local LLM inference
    - rich: Enhanced console output
    - asyncio: Asynchronous operations
    - sqlite: Memory persistence
    - docker: Service management (optional)

Configuration:
    The module uses settings from personal_agent.config.settings for:
    - Model selection and endpoints
    - Storage directories
    - User identification
    - Docker service URLs

Note:
    This module requires proper setup of Ollama services and optionally Docker containers
    for LightRAG knowledge and memory services. See the project documentation for
    complete setup instructions.

Author: Personal Agent Team
Version: 1.0.0
"""

# pylint: disable=C0415,W0212,C0301,W0718

import argparse
import asyncio
import logging
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama.tools import OllamaTools
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.calculator import CalculatorTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.file import FileTools
from agno.tools.pubmed import PubmedTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Import your personal agent components
try:
    # Try relative imports first (when used as a module)
    from ..cli.command_parser import CommandParser
    from ..config.settings import (
        AGNO_KNOWLEDGE_DIR,
        AGNO_STORAGE_DIR,
        HOME_DIR,
        LLM_MODEL,
        LMSTUDIO_URL,
        OLLAMA_URL,
        REMOTE_LMSTUDIO_URL,
        REMOTE_OLLAMA_URL,
    )
    from ..config.user_id_mgr import get_userid
    from ..core.agent_model_manager import AgentModelManager
    from ..core.agno_agent import AgnoPersonalAgent
except ImportError:
    # Fall back to absolute imports (when run directly)
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    from personal_agent.cli.command_parser import CommandParser
    from personal_agent.config.settings import (
        AGNO_KNOWLEDGE_DIR,
        AGNO_STORAGE_DIR,
        HOME_DIR,
        LLM_MODEL,
        LMSTUDIO_URL,
        OLLAMA_URL,
        REMOTE_LMSTUDIO_URL,
        REMOTE_OLLAMA_URL,
    )
    from personal_agent.config.user_id_mgr import get_userid
    from personal_agent.core.agent_model_manager import AgentModelManager
    from personal_agent.core.agno_agent import AgnoPersonalAgent

# Load environment variables
load_dotenv()

cwd = Path(__file__).parent.resolve()

PROVIDER = "ollama"


_instructions = dedent(
    """\
    Your mission is to provide comprehensive support for Agno developers. Follow these steps to ensure the best possible response:

    1. **Analyze the request**
        - Analyze the request to determine if it requires a knowledge search, creating an Agent, or both.
        - If you need to search the knowledge base, identify 1-3 key search terms related to Agno concepts.
        - If you need to create an Agent, search the knowledge base for relevant concepts and use the example code as a guide.
        - When the user asks for an Agent, they mean an Agno Agent.
        - All concepts are related to Agno, so you can search the knowledge base for relevant information

    After Analysis, always start the iterative search process. No need to wait for approval from the user.

    2. **Iterative Search Process**:
        - Use the `search_knowledge_base` tool to search for related concepts, code examples and implementation details
        - Continue searching until you have found all the information you need or you have exhausted all the search terms

    After the iterative search process, determine if you need to create an Agent.
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

    4. **Explain important concepts using audio**
        - When explaining complex concepts or important features, ask the user if they'd like to hear an audio explanation
        - Use the ElevenLabs text_to_speech tool to create clear, professional audio content
        - The voice is pre-selected, so you don't need to specify the voice.
        - Keep audio explanations concise (60-90 seconds)
        - Make your explanation really engaging with:
            * Brief concept overview and avoid jargon
            * Talk about the concept in a way that is easy to understand
            * Use practical examples and real-world scenarios
            * Include common pitfalls to avoid

    5. **Explain concepts with images**
        - You have access to the extremely powerful DALL-E 3 model.
        - Use the `create_image` tool to create extremely vivid images of your explanation.

    Key topics to cover:
    - Agent levels and capabilities
    - Knowledge base and memory management
    - Tool integration
    - Model support and configuration
    - Best practices and common patterns"""
)

_code_instructions = dedent(
    """\
    Your mission is to provide comprehensive code support. Follow these steps to ensure the best possible response:

    1. **Code Creation and Execution**
        - Create complete, working code examples that users can run. For example:
        ```python
        from agno.agent import Agent
        from agno.tools.duckduckgo import DuckDuckGoTools

        agent = Agent(tools=[DuckDuckGoTools()])

        # Perform a web search and capture the response
        response = agent.run("What's happening in France?")
        ```
        - When building agents you must remember to use agent.run() and NOT agent.print_response()
        - This way you can capture the agent response and return it to the user
        - Make sure to return the `response` variable that tells you the result
        - Use the `save_to_file_and_run` tool to save code to a file and run.
        - Remember to:
            * Build the complete agent implementation and test 
            * Include all necessary imports and setup
            * Add comprehensive comments explaining the implementation
            * Test a requested agent with example queries via with `response = agent.run()`
            * Test requested code by executing it.
            * Ensure all dependencies are listed
            * Include error handling and best practices
            * Add type hints and documentation

    4. **Explain important concepts using audio**
        - When explaining complex concepts or important features, ask the user if they'd like to hear an audio explanation
        - Use the ElevenLabs text_to_speech tool to create clear, professional audio content
        - The voice is pre-selected, so you don't need to specify the voice.
        - Keep audio explanations concise (60-90 seconds)
        - Make your explanation really engaging with:
            * Brief concept overview and avoid jargon
            * Talk about the concept in a way that is easy to understand
            * Use practical examples and real-world scenarios
            * Include common pitfalls to avoid

    5. **Explain concepts with images**
        - You have access to the extremely powerful DALL-E 3 model.
        - Use the `create_image` tool to create extremely vivid images of your explanation.

    Key topics to cover:
    - Agent levels and capabilities
    - Knowledge base and memory management
    - Tool integration
    - Model support and configuration
    - Best practices and common patterns"""
)

_file_instructions = dedent(
    """\
    Your mission is to provide comprehensive file system management and operations support. Follow these guidelines to ensure safe and effective file handling:

    1. **File Operations Safety**
        - Always validate file paths before performing operations
        - Check if files exist before attempting to read them
        - Confirm overwrite operations when modifying existing files
        - Use relative paths when possible to maintain portability
        - Respect file permissions and system limitations

    2. **File Reading Operations**
        - When reading files, provide clear summaries of content structure
        - For large files, offer to read specific sections or provide previews
        - Identify file types and suggest appropriate handling methods
        - Handle encoding issues gracefully (UTF-8, ASCII, etc.)
        - Report file sizes and modification dates when relevant

    3. **File Writing and Creation**
        - Always confirm the target location before writing files
        - Create necessary directory structures when needed
        - Use appropriate file extensions based on content type
        - Implement backup strategies for important file modifications
        - Provide clear success/failure feedback with specific details

    4. **File Search and Discovery**
        - Use efficient search patterns and filters
        - Provide organized results with file paths, sizes, and dates
        - Support both filename and content-based searches
        - Respect system performance by limiting search scope when appropriate
        - Offer to refine searches if results are too broad or narrow

    5. **File Organization and Management**
        - Suggest logical directory structures for file organization
        - Help identify duplicate files and cleanup opportunities
        - Provide file type analysis and categorization
        - Support batch operations for multiple files
        - Maintain file metadata and preserve important attributes

    6. **Content Analysis and Processing**
        - Analyze file content to determine structure and format
        - Extract key information from documents, logs, and data files
        - Identify patterns, errors, or anomalies in file content
        - Suggest improvements for file organization and naming
        - Support conversion between different file formats when possible

    7. **Error Handling and Recovery**
        - Provide clear error messages with actionable solutions
        - Suggest alternative approaches when operations fail
        - Implement graceful fallbacks for permission or access issues
        - Log important operations for troubleshooting
        - Offer recovery options for failed or interrupted operations

    8. **Best Practices and Security**
        - Never modify system files without explicit confirmation
        - Warn about potentially dangerous operations
        - Respect privacy and confidentiality of file contents
        - Use secure temporary files for intermediate operations
        - Follow platform-specific file system conventions

    Key capabilities to leverage:
    - File reading with content analysis and summarization
    - File writing with validation and backup options
    - Directory listing with filtering and organization
    - File search with pattern matching and content scanning
    - Batch operations for efficiency and consistency
    - Integration with other team agents for comprehensive solutions

    Remember: Always prioritize data safety and user intent. When in doubt, ask for clarification before performing potentially destructive operations."""
)


def create_ollama_model(
    model_name: str = LLM_MODEL, use_remote: bool = False
) -> OllamaTools:
    """Create an Ollama model using your AgentModelManager."""
    # Use LMStudio URL when provider is 'openai', otherwise use Ollama URL
    if PROVIDER == "openai":
        url = REMOTE_LMSTUDIO_URL if use_remote else LMSTUDIO_URL
    else:
        url = REMOTE_OLLAMA_URL if use_remote else OLLAMA_URL

    model_manager = AgentModelManager(
        model_provider=PROVIDER,
        model_name=model_name,
        ollama_base_url=url,
        seed=None,
    )
    return model_manager.create_model()


def create_model(
    provider: str = "ollama", model_name: str = LLM_MODEL, use_remote: bool = False
) -> Agent:
    """Create an Agent using AgentModelManager."""
    if provider == "ollama":
        url = REMOTE_OLLAMA_URL if use_remote else OLLAMA_URL
    else:
        url = REMOTE_LMSTUDIO_URL if use_remote else LMSTUDIO_URL

    model_manager = AgentModelManager(
        model_provider=provider,
        model_name=model_name,
        ollama_base_url=url,
        seed=None,
    )
    model = model_manager.create_model()

    # WORKAROUND: Fix incorrect role mapping in Agno framework
    # The default_role_map incorrectly maps "system" -> "developer"
    # but OpenAI API only accepts: user, assistant, system, tool
    if hasattr(model, "role_map"):
        # Always override the role mapping to fix the bug
        model.role_map = {
            "system": "system",  # Fix: should be "system", not "developer"
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant",
        }
        print(f"🔧 Applied role mapping fix to model: {model_name}")

    return model


def create_openai_model(
    model_name: str = LLM_MODEL, use_remote: bool = False
) -> OpenAIChat:
    """Create an OpenAI model using AgentModelManager."""
    openai_url = REMOTE_LMSTUDIO_URL if use_remote else LMSTUDIO_URL
    model_manager = AgentModelManager(
        model_provider=PROVIDER,
        model_name=model_name,
        ollama_base_url=openai_url,
        seed=None,
    )
    model = model_manager.create_model()

    # WORKAROUND: Fix incorrect role mapping in Agno framework
    # The default_role_map incorrectly maps "system" -> "developer"
    # but OpenAI API only accepts: user, assistant, system, tool
    if hasattr(model, "role_map"):
        # Always override the role mapping to fix the bug
        model.role_map = {
            "system": "system",  # Fix: should be "system", not "developer"
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant",
        }
        print(f"🔧 Applied role mapping fix to model: {model_name}")

    return model


# Web search agent using Ollama
web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=create_model(provider=PROVIDER),
    tools=[GoogleSearchTools()],
    instructions=["Always include sources"],
    show_tool_calls=True,
)

# Finance agent using Ollama
finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=create_model(provider=PROVIDER),
    tools=[
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
        ),
        FileTools(
            base_dir=Path(HOME_DIR),  # Use user home directory as base with Path object
            save_files=True,
            list_files=True,
            search_files=True,
        ),
    ],
    instructions=["Use tables to display data. You can save files and list files."],
    show_tool_calls=True,
)

# Writer agent that can write content
medical_agent = Agent(
    name="Medical Agent",
    role="Write content",
    model=create_model(provider=PROVIDER),
    description="You are an AI agent that can write content.",
    tools=[PubmedTools()],
    instructions=[
        "You are a medical agent that can answer questions about medical topics.",
    ],
)

# Writer agent using Ollama
writer_agent = Agent(
    name="Writer Agent",
    role="Write content",
    model=create_model(provider=PROVIDER),
    description="You are an AI agent that can write content.",
    instructions=[
        "You are a versatile writer who can create content on any topic.",
        "When given a topic, write engaging and informative content in the requested format and style.",
        "If you receive mathematical expressions or calculations from the calculator agent, convert them into clear written text.",
        "Ensure your writing is clear, accurate and tailored to the specific request.",
        "Maintain a natural, engaging tone while being factually precise.",
        "Write something that would be good enough to be published in a newspaper like the New York Times.",
        "You can use markdown to format your content.",
        "You can use your file tools to save files when requested",
    ],
    tools=[
        FileTools(
            base_dir=Path(HOME_DIR),  # Use user home directory as base with Path object
            save_files=True,
            list_files=True,
            search_files=True,
        ),
    ],
    show_tool_calls=True,
)

# Calculator agent using Ollama
calculator_agent = Agent(
    name="Calculator Agent",
    model=create_model(provider=PROVIDER),
    role="Calculate mathematical expressions",
    tools=[
        CalculatorTools(
            add=True,
            subtract=True,
            multiply=True,
            divide=True,
            exponentiate=True,
            factorial=True,
            is_prime=True,
            square_root=True,
        ),
    ],
    show_tool_calls=True,
)

python_agent = Agent(
    name="Python Agent",
    model=create_model(provider=PROVIDER),
    role="Execute Python code",
    tools=[
        PythonTools(
            base_dir=Path(HOME_DIR),  # Use user home directory as base with Path object
            save_and_run=True,
            run_files=True,
            read_files=True,
        ),
    ],
    instructions=dedent(_code_instructions),
    show_tool_calls=True,
)

file_agent = Agent(
    name="File System Agent",
    model=create_model(provider=PROVIDER),
    role="Read and write files in the system",
    tools=[
        FileTools(
            base_dir=Path(HOME_DIR),  # Use user home directory as base with Path object
            save_files=True,
            list_files=True,
            search_files=True,
        )
    ],
    instructions=dedent(_file_instructions),
    show_tool_calls=True,
)


async def create_memory_agent(
    user_id: str = None,
    debug: bool = False,
    use_remote: bool = False,
) -> Agent:
    """Create a memory agent that uses the shared memory system."""
    # Get user_id dynamically if not provided
    if user_id is None:
        user_id = get_userid()

    try:
        from ..tools.knowledge_tools import KnowledgeTools
        from ..tools.refactored_memory_tools import AgnoMemoryTools
    except ImportError:
        from personal_agent.tools.knowledge_tools import KnowledgeTools
        from personal_agent.tools.refactored_memory_tools import AgnoMemoryTools

    # Create AgnoPersonalAgent with proper parameters (it creates its own model internally)
    memory_agent = AgnoPersonalAgent(
        model_provider=PROVIDER,  # Use the correct provider
        model_name=LLM_MODEL,  # Use the configured model
        enable_memory=True,
        enable_mcp=True,
        debug=debug,
        user_id=user_id,
        recreate=False,  # Don't recreate memory database every time
        alltools=False,
        # AgnoPersonalAgent will create its own model using AgentModelManager
        # Note: use_remote parameter removed as it's not supported by AgnoPersonalAgent
    )

    # After initialization, we need to set the shared memory and add the tools
    # Wait for initialization to complete
    await memory_agent._ensure_initialized()

    # Update instructions to include memory-specific guidance
    memory_specific_instructions = [
        "You are a memory and knowledge agent with access to both personal memory and factual knowledge.",
        "CRITICAL TOOL SELECTION RULES:",
        "- Use MEMORY TOOLS for personal information ABOUT THE USER",
        "- Use KNOWLEDGE TOOLS for factual content, documents, poems, stories, articles",
        "- When user says 'store this poem' or 'save this content' -> use ingest_knowledge_text",
        "- When user says 'remember that I...' -> use store_user_memory",
        "- When user asks 'what do you remember about me?' -> use get_all_memories",
        "- When user asks about stored content/documents -> use query_knowledge_base",
        "",
        "MEMORY TOOLS - CORRECT USAGE:",
        "- store_user_memory(content='fact about user', topics=['optional']) - Store new user info",
        "- get_all_memories() - For 'what do you know about me' (NO PARAMETERS)",
        "- query_memory(query='keywords', limit=10) - Search specific user information",
        "- get_recent_memories(limit=10) - Recent interactions",
        "- list_memories() - Simple overview (NO PARAMETERS)",
        "- get_memories_by_topic(topics=['topic1'], limit=10) - Filter by topics",
        "- update_memory(memory_id='id', content='new content', topics=['topics']) - Update existing",
        "- delete_memory(memory_id='id') - Delete specific memory",
        "- store_graph_memory(content='info', topics=['topics'], memory_id='optional') - Store with relationships",
        "- query_graph_memory(query='terms', mode='hybrid', top_k=5) - Explore relationships",
        "",
        "KNOWLEDGE TOOLS - CORRECT USAGE:",
        "- ingest_knowledge_text(content='text', title='title', file_type='txt') - Store factual content",
        "- ingest_knowledge_file(file_path='path', title='optional') - Ingest file",
        "- ingest_knowledge_from_url(url='url', title='optional') - Ingest from web",
        "- query_knowledge_base(query='search terms', mode='hybrid', limit=20) - Search knowledge",
        "",
        "EXAMPLES:",
        "- 'Store this poem: [poem text]' -> ingest_knowledge_text(content=poem, title='User Poem')",
        "- 'Remember I like skiing' -> store_user_memory(content='User likes skiing')",
        "- 'What do you know about me?' -> get_all_memories()",
        "- 'Save this article about AI' -> ingest_knowledge_text(content=article, title='AI Article')",
        "Always execute the tools - do not show JSON or function calls to the user.",
        "Provide natural responses based on the tool results.",
    ]

    print("✅ Memory agent created")
    return memory_agent


# Create the team
async def create_team(use_remote: bool = False):
    """Create the team with shared memory context and your existing managers."""

    # CRITICAL: Ensure Docker and user synchronization BEFORE creating any agents
    try:
        from ..config.user_id_mgr import get_userid
        from ..core.docker_integration import ensure_docker_user_consistency
    except ImportError:
        from personal_agent.config.user_id_mgr import get_userid
        from personal_agent.core.docker_integration import (
            ensure_docker_user_consistency,
        )

    # Get the current user ID dynamically
    current_user_id = get_userid()
    print("🐳 Ensuring Docker and user synchronization...")
    docker_ready, docker_message = ensure_docker_user_consistency(
        user_id=current_user_id, auto_fix=True, force_restart=False
    )

    if docker_ready:
        print(f"✅ Docker synchronization successful: {docker_message}")
    else:
        print(f"⚠️ Docker synchronization failed: {docker_message}")
        print("Proceeding with team creation, but Docker services may be inconsistent")

    # Create memory agent directly using the create_memory_agent function
    memory_agent = await create_memory_agent(
        user_id=current_user_id,
        debug=True,
        use_remote=use_remote,
    )

    # Update other agents to use shared memory (declare as global to modify)
    global web_agent, finance_agent, writer_agent, calculator_agent
    # Create the team without shared memory - only the memory agent handles memory
    agent_team = Team(
        name="Personal Agent Team",
        mode="coordinate",
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        memory=None,  # No team-level memory - only memory agent handles memory
        tools=[
            # ReasoningTools(add_instructions=True, add_few_shot=True),
        ],
        members=[
            memory_agent,  # Memory agent with your managers
            web_agent,
            finance_agent,
            writer_agent,
            calculator_agent,
        ],
        instructions=[
            "You are a team of agents using local Ollama models that can answer a variety of questions.",
            "Your primary goal is to collect user memories and factual knowledge.",
            "DELEGATION RULES:",
            "- For storing poems, articles, documents, or factual content -> delegate to Personal AI Agent",
            "- For storing personal info about the user -> delegate to Personal AI Agent",
            "- For web searches -> delegate to Web Agent",
            "- For financial data -> delegate to Finance Agent",
            "- For writing content -> delegate to Writer Agent",
            "- For calculations -> delegate to Calculator Agent",
            "KNOWLEDGE STORAGE EXAMPLES:",
            "- 'Store this poem' -> delegate to Personal AI Agent (will use knowledge tools)",
            "- 'Save this article' -> delegate to Personal AI Agent (will use knowledge tools)",
            "- 'Remember I like skiing' -> delegate to Personal AI Agent (will use memory tools)",
            "You can also answer directly, you don't HAVE to forward the question to a member agent.",
            "Reason about more complex questions before delegating to a member agent.",
            "If the user is only being conversational, encourage them to talk about themselves, life events, and feelings.",
        ],
        markdown=True,
        show_tool_calls=True,
        show_members_responses=True,
        enable_agentic_context=True,  # Disable shared context - memory agent handles this
        share_member_interactions=True,  # Disable shared interactions - memory agent handles this
        enable_user_memories=False,  # Disable team-level memory - memory agent handles this
    )

    print("✅ Team created - memory handled by Personal AI Agent")
    return agent_team


async def cleanup_team(team):
    """Comprehensive cleanup of team resources to prevent ResourceWarnings."""
    logging.info("🧹 Cleaning up team resources...")

    try:
        # 1. Close team-level resources
        if hasattr(team, "model") and team.model:
            try:
                await _cleanup_model(team.model, "Team")
            except Exception as e:
                logging.info(f"⚠️ Error cleaning up team model: {e}")

        if hasattr(team, "memory") and hasattr(team.memory, "db"):
            try:
                if hasattr(team.memory.db, "close"):
                    await team.memory.db.close()
                logging.info("✅ Team memory database closed")
            except Exception as e:
                logging.info(f"⚠️ Error closing team memory database: {e}")

        # 2. Close member-level resources
        if hasattr(team, "members") and team.members:
            for i, member in enumerate(team.members):
                member_name = getattr(member, "name", f"Member-{i}")
                logging.info(f"🔧 Cleaning up {member_name}...")

                # Close member's model
                if hasattr(member, "model") and member.model:
                    try:
                        await _cleanup_model(member.model, member_name)
                    except Exception as e:
                        logging.info(f"⚠️ Error cleaning up {member_name} model: {e}")

                # Close member's memory
                if hasattr(member, "memory") and hasattr(member.memory, "db"):
                    try:
                        if hasattr(member.memory.db, "close"):
                            await member.memory.db.close()
                        logging.info(f"✅ {member_name} memory database closed")
                    except Exception as e:
                        logging.info(
                            f"⚠️ Error closing {member_name} memory database: {e}"
                        )

                # Close member's tools
                if hasattr(member, "tools") and member.tools:
                    for j, tool in enumerate(member.tools):
                        if tool:  # Check if tool is not None
                            tool_name = getattr(tool.__class__, "__name__", f"Tool-{j}")
                            try:
                                await _cleanup_tool(tool, f"{member_name}-{tool_name}")
                            except Exception as e:
                                logging.info(
                                    f"⚠️ Error cleaning up {member_name}-{tool_name}: {e}"
                                )

        # 3. Force garbage collection to help with cleanup
        import gc

        gc.collect()

        # 4. Give asyncio time to close remaining connections
        await asyncio.sleep(0.5)

        logging.info("✅ Team cleanup completed")

    except Exception as e:
        logging.info(f"❌ Error during team cleanup: {e}")


async def _cleanup_model(model, model_name: str):
    """Clean up a specific model's resources."""
    try:
        # Close HTTP sessions in the model
        if hasattr(model, "_session") and model._session:
            if not model._session.closed:
                await model._session.close()
            logging.info(f"✅ {model_name} model HTTP session closed")

        if hasattr(model, "session") and model.session:
            if not model.session.closed:
                await model.session.close()
            logging.info(f"✅ {model_name} model session closed")

        # Close any client connections
        if hasattr(model, "client"):
            if hasattr(model.client, "close"):
                await model.client.close()
            elif hasattr(model.client, "_session") and model.client._session:
                if not model.client._session.closed:
                    await model.client._session.close()
            logging.info(f"✅ {model_name} model client closed")

        # Handle OllamaTools specific cleanup
        if hasattr(model, "_client") and model._client:
            if hasattr(model._client, "close"):
                await model._client.close()
            logging.info(f"✅ {model_name} Ollama client closed")

    except Exception as e:
        logging.info(f"⚠️ Error cleaning up {model_name} model: {e}")


async def _cleanup_tool(tool, tool_name: str):
    """Clean up a specific tool's resources."""
    try:
        # Close HTTP sessions in tools
        if hasattr(tool, "_session") and tool._session:
            if not tool._session.closed:
                await tool._session.close()
            logging.info(f"✅ {tool_name} tool HTTP session closed")

        if hasattr(tool, "session") and tool.session:
            if not tool.session.closed:
                await tool.session.close()
            logging.info(f"✅ {tool_name} tool session closed")

        # Handle DuckDuckGo tools specifically
        if hasattr(tool, "ddgs"):
            if hasattr(tool.ddgs, "_session") and tool.ddgs._session:
                if not tool.ddgs._session.closed:
                    await tool.ddgs._session.close()
                logging.info(f"✅ {tool_name} DuckDuckGo session closed")

            if hasattr(tool.ddgs, "close"):
                await tool.ddgs.close()
                logging.info(f"✅ {tool_name} DuckDuckGo client closed")

        # Handle YFinance tools
        if hasattr(tool, "_session") and "yfinance" in str(type(tool)).lower():
            if tool._session and not tool._session.closed:
                await tool._session.close()
                logging.info(f"✅ {tool_name} YFinance session closed")

        # Close any other client connections
        if hasattr(tool, "client"):
            if hasattr(tool.client, "close"):
                await tool.client.close()
            elif hasattr(tool.client, "_session") and tool.client._session:
                if not tool.client._session.closed:
                    await tool.client._session.close()
            logging.info(f"✅ {tool_name} tool client closed")

    except Exception as e:
        logging.info(f"⚠️ Error cleaning up {tool_name} tool: {e}")


# Main execution
async def main(use_remote: bool = False):
    """Main function to run the team with an enhanced CLI interface."""

    # Initialize Rich console for better formatting
    console = Console(force_terminal=True)

    console.print("🤖 [bold blue]Ollama Multi-Purpose Reasoning Team[/bold blue]")
    console.print("=" * 50)
    console.print("Initializing team with memory and knowledge capabilities...")
    console.print("This may take a moment on first run...")

    try:
        # Create the team
        team = await create_team(use_remote=use_remote)

        # Get the memory agent for CLI commands
        memory_agent = None
        if hasattr(team, "members") and team.members:
            for member in team.members:
                if hasattr(member, "name") and "Personal AI Agent" in member.name:
                    memory_agent = member
                    break

        console.print("\n✅ [bold green]Team initialized successfully![/bold green]")
        console.print("\n[bold cyan]Team Members:[/bold cyan]")
        console.print(
            "- 🧠 Memory Agent: Store and retrieve personal information and knowledge"
        )
        console.print("- 🌐 Web Agent: Search the web for information")
        console.print("- 💰 Finance Agent: Get financial data and analysis")
        console.print("- ✍️  Writer Agent: Create content and written materials")
        console.print("- 🧮 Calculator Agent: Perform calculations and math")

        # Initialize command parser
        command_parser = CommandParser()

        # Display the enhanced welcome panel
        console.print("\n")
        console.print(
            Panel.fit(
                "🚀 Enhanced Personal AI Agent Team with Memory Commands\n\n"
                "This CLI provides team coordination with direct memory management.\n\n"
                f"{command_parser.get_help_text()}\n\n"
                "[bold yellow]Team Commands:[/bold yellow]\n"
                "• 'help' - Show team capabilities\n"
                "• 'clear' - Clear the screen\n"
                "• 'examples' - Show example queries\n"
                "• 'quit' - Exit the team",
                style="bold blue",
            )
        )

        console.print(f"🖥️  Using Ollama at: {OLLAMA_URL}")

        # Enhanced interactive chat loop with command parsing
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Parse the command using the same system as agno_cli.py
                command_handler, remaining_text, kwargs = command_parser.parse_command(
                    user_input
                )

                # Handle quit command specially
                if (
                    command_handler
                    and hasattr(command_handler, "__name__")
                    and command_handler.__name__ == "_handle_quit"
                ):
                    console.print(
                        "👋 Goodbye! Thanks for using the Personal Agent Team!"
                    )
                    await cleanup_team(team)
                    break

                # If it's a memory command, execute it with the memory agent
                if command_handler and memory_agent:
                    try:
                        if remaining_text is not None:
                            await command_handler(memory_agent, remaining_text, console)
                        else:
                            await command_handler(memory_agent, console)
                        continue
                    except Exception as e:
                        console.print(f"💥 Error executing memory command: {e}")
                        continue

                # Handle team-specific commands
                elif user_input.lower() == "help":
                    console.print("\n📋 [bold cyan]Team Capabilities:[/bold cyan]")
                    console.print("  - Remember personal information and preferences")
                    console.print("  - Search the web for current information")
                    console.print("  - Analyze financial data and stocks")
                    console.print("  - Write content, articles, and creative text")
                    console.print("  - Perform mathematical calculations")
                    console.print(f"\n{command_parser.get_help_text()}")
                    continue

                elif user_input.lower() == "clear":
                    import os

                    os.system("clear" if os.name == "posix" else "cls")
                    console.print("🤖 Personal Agent Team")
                    console.print("💬 Chat cleared. How can I help you?")
                    continue

                elif user_input.lower() == "examples":
                    console.print("\n💡 [bold cyan]Example Queries:[/bold cyan]")
                    console.print("  [yellow]Memory & Personal:[/yellow]")
                    console.print(
                        "    - 'Remember that I love skiing and live in Colorado'"
                    )
                    console.print("    - 'What do you remember about me?'")
                    console.print(
                        "    - '! I work as a software engineer' (immediate storage)"
                    )
                    console.print("    - '? work' (query memories about work)")
                    console.print("\n  [yellow]Web Search:[/yellow]")
                    console.print("    - 'What's the latest news about AI?'")
                    console.print("    - 'Search for information about climate change'")
                    console.print("\n  [yellow]Finance:[/yellow]")
                    console.print("    - 'Give me a financial analysis of NVDA'")
                    console.print("    - 'What's the current stock price of Apple?'")
                    console.print("\n  [yellow]Writing:[/yellow]")
                    console.print("    - 'Write a short poem about AI agents'")
                    console.print("    - 'Create a summary of machine learning'")
                    console.print("\n  [yellow]Math & Calculations:[/yellow]")
                    console.print("    - 'Calculate the square root of 144'")
                    console.print("    - 'What's 15% of 250?'")
                    continue

                # If not a command, treat as regular team chat
                try:
                    console.print("🤖 [bold green]Team:[/bold green]")
                    await team.aprint_response(user_input, stream=True)

                except Exception as e:
                    console.print(f"💥 Error: {e}")

            except KeyboardInterrupt:
                console.print(
                    "\n\n⚠️  Interrupted by user. Type 'quit' to exit gracefully."
                )
                continue
            except EOFError:
                console.print("\n\n👋 Session ended. Goodbye!")
                await cleanup_team(team)
                break
            except Exception as e:
                console.print(f"\n❌ Error processing your request: {str(e)}")
                console.print("Please try again or type 'help' for assistance.")
                continue

    except KeyboardInterrupt:
        console.print("\n\n⚠️  Initialization interrupted by user.")
    except Exception as e:
        console.print(f"\n❌ Error initializing team: {str(e)}")
        console.print("Please check your configuration and try again.")
    finally:
        try:
            if "team" in locals():
                await cleanup_team(team)
                pass
        except Exception as e:
            console.print(f"Warning during cleanup: {e}")


def cli_main():
    """Entry point for the paga_team_cli command."""
    parser = argparse.ArgumentParser(
        description="Run the Ollama Multi-Purpose Reasoning Team"
    )
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama server"
    )
    args = parser.parse_args()

    print("Starting Ollama Multi-Purpose Reasoning Team...")
    asyncio.run(main(use_remote=args.remote))


if __name__ == "__main__":
    # Run the main function
    cli_main()
