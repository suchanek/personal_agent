"""
Personal Agent Reasoning Team

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
    - **SystemAgent**: Executes system commands and shell operations safely
    - **Finance Agent**: Retrieves and analyzes financial data using YFinance
    - **Medical Agent**: Searches PubMed for medical information and research
    - **Writer Agent**: Creates content, articles, and creative writing
    - **Calculator Agent**: Performs mathematical calculations and operations
    - **Python Agent**: Executes Python code and scripts
    - **File Agent**: Handles file system operations and management
    - **Image Agent**: Creates images using DALL-E based on text descriptions

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
import sys
from pathlib import Path
from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama.tools import OllamaTools
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.calculator import CalculatorTools
from agno.tools.dalle import DalleTools
from agno.tools.file import FileTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.pubmed import PubmedTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.toolkit import Toolkit
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
    from ..tools.personal_agent_tools import (
        PersonalAgentFilesystemTools,
        PersonalAgentSystemTools,
    )
    from ..utils import setup_logging

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
    from personal_agent.utils import setup_logging

WRITER_MODEL = "llama3.1:8b"

# Load environment variables
load_dotenv()

# Configure logging

logger = setup_logging(__name__)

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

_memory_specific_instructions = [
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

    return model


class WritingTools(Toolkit):
    """Custom writing tools for the writer agent."""

    def __init__(self):
        tools = [
            self.write_original_content,
        ]
        super().__init__(name="writing_tools", tools=tools)

    def write_original_content(
        self,
        content_type: str,
        topic: str,
        length: int = 3,
        style: str = "informative",
        audience: str = "general",
    ) -> str:
        """Write original content based on the specified parameters.

        Args:
            content_type: Type of content (e.g., 'article', 'poem', 'story', 'essay', 'limerick')
            topic: The main topic or subject to write about
            length: Length specification (paragraphs for articles, lines for poems, etc.)
            style: Writing style (e.g., 'formal', 'casual', 'humorous', 'limerick', 'informative')
            audience: Target audience (e.g., 'general', 'children', 'professionals')

        Returns:
            The written content as a string
        """
        try:
            # CRITICAL DIAGNOSTIC: Log every call to this method
            logger.warning(
                f"🚨 DIAGNOSTIC: write_original_content called - topic: '{topic}', style: '{style}', type: '{content_type}', length: {length}"
            )
            # Generate content based on parameters - KEEP IT CONCISE
            if content_type.lower() == "limerick":
                content = f"""Here's a limerick about {topic}:

There once was a topic called {topic},
So fine and so wonderfully epic,
With rhythm and rhyme,
It passes the time,
And makes every reader quite tropic!"""

            elif content_type.lower() == "poem":
                # Generate a simple poem with specified number of lines
                lines = []
                for i in range(min(length, 8)):  # Cap at 8 lines max
                    if i == 0:
                        lines.append(f"In the world of {topic}, we find")
                    elif i == 1:
                        lines.append(f"Beauty and wonder combined")
                    else:
                        lines.append(f"Line {i+1} about {topic} so fine")
                content = "\n".join(lines)

            elif content_type.lower() in ["summary", "article", "essay"]:
                # For summaries and articles, respect word/character limits
                if length > 1000:  # If length seems like word count
                    # Generate approximately the requested word count
                    words_per_sentence = 15
                    sentences_needed = min(
                        length // words_per_sentence, 50
                    )  # Cap at 50 sentences

                    sentences = []
                    sentences.append(f"# {topic.title()}")
                    sentences.append(
                        f"This {style} {content_type} covers {topic} for {audience} readers."
                    )

                    for i in range(
                        min(sentences_needed - 2, 10)
                    ):  # Cap at 10 additional sentences
                        sentences.append(
                            f"Key point {i+1} about {topic} written in {style} style."
                        )

                    content = "\n\n".join(sentences)
                else:
                    # Generate specified number of paragraphs (capped)
                    paragraphs = []
                    paragraphs.append(f"# {topic.title()}")
                    paragraphs.append(
                        f"This {style} {content_type} covers {topic} for {audience} readers."
                    )

                    for i in range(min(length, 5)):  # Cap at 5 paragraphs
                        paragraphs.append(
                            f"Section {i+1}: Key insights about {topic} in {style} tone."
                        )

                    content = "\n\n".join(paragraphs)

            else:  # Default short content
                content = f"""# {topic.title()}

This {style} {content_type} about {topic} is written for {audience}.

Key points about {topic} presented in {style} style.

Conclusion about {topic}."""

            logger.info(
                f"🔍 DIAGNOSTIC: Generated {content_type} about {topic} ({len(content)} characters)"
            )
            return content

        except Exception as e:
            error_msg = f"Error generating content: {str(e)}"
            logger.error(f"🔍 DIAGNOSTIC: {error_msg}")
            return error_msg


def create_writer_agent(
    model_provider: str = "ollama",
    model_name: str = WRITER_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
    use_remote: bool = False,
) -> Agent:
    """Create a specialized writing agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :param use_remote: Use remote Ollama
    :return: Configured writing agent
    """

    # Create writing tools instance
    writing_tools = WritingTools()

    agent = Agent(
        name="Writer Agent",
        role="Create written content in the requested tone and style",
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        debug_mode=debug,
        tools=[
            FileTools(
                base_dir=Path(HOME_DIR),
                save_files=True,
                read_files=True,
                list_files=True,
            ),
        ],  # File tools for reading/writing documents
        instructions=[
            "You are a versatile writer who can create content on any topic.",
            "When given a topic, write engaging and informative content in the requested format and style.",
            "If you receive mathematical expressions or calculations from the calculator agent, convert them into clear written text.",
            "Ensure your writing is clear, accurate and tailored to the specific request.",
            "Maintain a natural, engaging tone while being factually precise.",
            "Write something that would be good enough to be published in a newspaper like the New York Times.",
        ],
        markdown=True,
        show_tool_calls=True,  # CRITICAL: Always show tool calls to ensure execution
        add_name_to_instructions=True,
    )

    logger.info("Created Writer Agent with custom writing tools")
    return agent


def create_image_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    debug: bool = False,
    use_remote: bool = False,
) -> Agent:
    """Create a specialized image creation agent using DALL-E.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param debug: Enable debug mode
    :param use_remote: Use remote Ollama
    :return: Configured image creation agent
    """

    agent = Agent(
        name="Image Agent",
        role="Create images using DALL-E based on text descriptions",
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        debug_mode=debug,
        tools=[
            DalleTools(model="dall-e-3", size="1792x1024", quality="hd", style="vivid"),
        ],
        instructions=[
            "You are an AI image creation specialist using DALL-E.",
            "When asked to create an image, use the create_image tool with the user's description.",
            "After the tool creates the image, return the image URL in markdown format: ![description](URL)",
            "You may include brief context or description along with the image.",
            "Focus on providing the image markdown format clearly and prominently in your response.",
        ],
        markdown=True,
        show_tool_calls=True,  # Enable tool call display for better debugging
        add_name_to_instructions=True,
    )

    logger.info(
        "🚨 DIAGNOSTIC: Created Image Agent with simplified instructions and disabled tool call display"
    )
    return agent


def create_agents(use_remote: bool = False, debug: bool = False):
    """Create all agents with the correct remote/local configuration."""

    # Web search agent using Ollama
    web_agent = Agent(
        name="Web Agent",
        role="Search the web for information",
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        tools=[GoogleSearchTools()],
        instructions=[
            "Search the web for information based on the input. Always include sources"
        ],
        show_tool_calls=True,
    )

    # System agent using PersonalAgentSystemTools
    system_agent = Agent(
        name="SystemAgent",
        role="Execute system commands and shell operations",
        # model=create_model(provider=PROVIDER, use_remote=use_remote),
        tools=[PersonalAgentSystemTools(shell_command=True)],
        instructions=[
            "You are a system agent that can execute shell commands safely.",
            "Provide clear output and error messages from command execution.",
        ],
        show_tool_calls=True,
    )

    # Finance agent using Ollama
    finance_agent = Agent(
        name="Finance Agent",
        role="Get financial data",
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        tools=[
            YFinanceTools(
                stock_price=True,
                analyst_recommendations=True,
                company_info=True,
                company_news=True,
            ),
        ],
        instructions=["Use tables to display data. "],
        show_tool_calls=True,
    )

    # Medical agent that can search PubMed
    medical_agent = Agent(
        name="Medical Agent",
        role="Search pubmed for medical information",
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        description="You are an AI agent that search PubMed for medical information.",
        tools=[PubmedTools()],
        instructions=[
            "You are a medical agent that can answer questions about medical topics.",
            "Search PubMed for medical information and write about it.",
            "Use tables to display data.",
        ],
        show_tool_calls=True,
    )

    # Writer agent using Ollama
    writer_agent = create_writer_agent()

    # Image agent using DALL-E
    image_agent = create_image_agent(use_remote=use_remote)

    # Calculator agent using Ollama
    calculator_agent = Agent(
        name="Calculator Agent",
        # model=create_model(provider=PROVIDER, use_remote=use_remote),
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
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        role="Create and Execute Python code",
        tools=[
            PythonTools(
                base_dir=Path(
                    HOME_DIR
                ),  # Use user home directory as base with Path object
                save_and_run=True,
                run_files=True,
                read_files=True,
                list_files=True,
                run_code=True,
            ),
        ],
        instructions=dedent(_code_instructions),
        show_tool_calls=True,
    )

    file_agent = Agent(
        name="File System Agent",
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        role="Read and write files in the system",
        tools=[
            FileTools(
                base_dir=Path(
                    HOME_DIR
                ),  # Use user home directory as base with Path object
                save_files=True,
                list_files=True,
                search_files=True,
            )
        ],
        instructions=dedent(_file_instructions),
        show_tool_calls=True,
    )

    return (
        web_agent,
        system_agent,
        finance_agent,
        medical_agent,
        writer_agent,
        image_agent,
        calculator_agent,
        python_agent,
        file_agent,
    )


def create_personalized_instructions(agent, base_instructions: list) -> list:
    """Create personalized instructions using the agent's user_id."""
    user_id = getattr(agent, "user_id", "user")

    # Use the user_id directly instead of generic "user" references
    if user_id and user_id != "default_user":
        # Replace "the user" and "user" with the actual user_id in instructions
        personalized_instructions = []
        for instruction in base_instructions:
            # Replace various forms of "user" references
            personalized_instruction = instruction.replace("the user", user_id)
            personalized_instruction = personalized_instruction.replace(
                "ABOUT THE USER", f"ABOUT {user_id.upper()}"
            )
            personalized_instruction = personalized_instruction.replace(
                "about the user", f"about {user_id}"
            )
            personalized_instruction = personalized_instruction.replace(
                "User ", f"{user_id} "
            )
            personalized_instruction = personalized_instruction.replace(
                "user ", f"{user_id} "
            )
            personalized_instructions.append(personalized_instruction)

        logger.info(f"✅ Personalized instructions created for user: {user_id}")
        return personalized_instructions
    else:
        logger.info("⚠️ Using default user_id, keeping generic instructions")
        return base_instructions


async def create_memory_agent(
    user_id: str = None,
    debug: bool = False,
    use_remote: bool = False,
    recreate: bool = False,
) -> Agent:
    """Create a memory agent that uses the shared memory system."""
    # Get user_id dynamically if not provided
    if user_id is None:
        user_id = get_userid()

    # Determine the correct URL based on use_remote flag
    if PROVIDER == "ollama":
        ollama_url = REMOTE_OLLAMA_URL if use_remote else OLLAMA_URL
    else:
        ollama_url = REMOTE_LMSTUDIO_URL if use_remote else LMSTUDIO_URL

    # Create AgnoPersonalAgent with proper parameters (it creates its own model internally)
    memory_agent = AgnoPersonalAgent(
        model_provider=PROVIDER,  # Use the correct provider
        model_name=LLM_MODEL,  # Use the configured model
        enable_memory=True,
        enable_mcp=False,
        debug=debug,
        user_id=user_id,
        recreate=recreate,
        alltools=False,
        ollama_base_url=ollama_url,  # Pass the correct URL based on use_remote flag
    )

    # After initialization, we need to set the shared memory and add the tools
    # Wait for initialization to complete
    await memory_agent._ensure_initialized()

    # Create personalized instructions using the user's name if available
    personalized_instructions = create_personalized_instructions(
        memory_agent, _memory_specific_instructions
    )
    memory_agent.instructions = personalized_instructions

    logger.info("✅ Memory agent created with personalized instructions")
    return memory_agent


async def create_memory_writer_agent(
    user_id: str = None,
    debug: bool = False,
    use_remote: bool = False,
    recreate: bool = False,
) -> Agent:
    """Create a memory agent that uses the shared memory system and can write content."""
    # Get user_id dynamically if not provided
    if user_id is None:
        user_id = get_userid()

    # Determine the correct URL based on use_remote flag
    if PROVIDER == "ollama":
        ollama_url = REMOTE_OLLAMA_URL if use_remote else OLLAMA_URL
    else:
        ollama_url = REMOTE_LMSTUDIO_URL if use_remote else LMSTUDIO_URL

    # DEBUG: Log the URL selection for memory agent
    logger.info(
        f"🔍 create_memory_writer_agent: provider={PROVIDER}, use_remote={use_remote}, selected_url={ollama_url}"
    )

    # Create AgnoPersonalAgent with proper parameters (it creates its own model internally)
    memory_writer_agent = AgnoPersonalAgent(
        model_provider=PROVIDER,  # Use the correct provider
        model_name=LLM_MODEL,  # Use the configured model
        enable_memory=True,
        enable_mcp=False,
        debug=debug,
        user_id=user_id,
        recreate=recreate,
        alltools=False,
        initialize_agent=True,
        ollama_base_url=ollama_url,  # Pass the correct URL based on use_remote flag
    )

    # After initialization, we need to set the shared memory and add the tools
    # Wait for initialization to complete
    # await memory_writer_agent._ensure_initialized()

    # Update instructions to include memory-specific guidance

    memory_writer_agent.instructions = _memory_specific_instructions
    logger.info("✅ Memory/Writer agent created")
    return memory_writer_agent


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

    # Create all other agents with the correct remote/local configuration
    agents = create_agents(use_remote=use_remote)
    (
        web_agent,
        system_agent,
        finance_agent,
        medical_agent,
        writer_agent,
        image_agent,
        calculator_agent,
        python_agent,
        file_agent,
    ) = agents

    # Create the team without shared memory - only the memory agent handles memory
    agent_team = Team(
        name="Personal Agent Team",
        mode="coordinate",
        model=create_model(provider=PROVIDER, use_remote=use_remote),
        memory=None,  # No team-level memory - only memory agent handles memory
        tools=[
            ReasoningTools(add_instructions=True, add_few_shot=True),
        ],
        members=[
            memory_agent,  # Memory agent with your managers
            web_agent,
            system_agent,  # SystemAgent for shell commands
            finance_agent,
            writer_agent,
            image_agent,  # Image creation agent
            calculator_agent,
            medical_agent,
            python_agent,
            file_agent,
        ],
        instructions=[
            "You are a team of agents using local Ollama models that can answer a variety of questions.",
            "Your primary goal is to collect user memories and factual knowledge.",
            "DELEGATION RULES:",
            "- For storing poems, articles, documents, or factual content -> delegate to Personal AI Agent",
            "- For storing personal info about the user -> delegate to Personal AI Agent",
            "- For web searches -> delegate to Web Agent",
            "- For financial data -> delegate to Finance Agent",
            "- For writing content -> delegate to Writer Agent ONCE ONLY",
            "- For calculations -> delegate to Calculator Agent",
            "- For image creation -> delegate to Image Agent",
            "",
            "CRITICAL IMAGE DELEGATION RULES:",
            "- For image creation requests, delegate to Image Agent",
            "- ALWAYS extract and display the actual image URL from the Image Agent's response",
            "- Look for ![description](URL) format in the Image Agent's response",
            "- Copy the exact ![description](URL) markdown from Image Agent to your response",
            "- Do NOT summarize, describe, or replace the image URL with text",
            "- Do NOT use emojis instead of the actual image URL",
            "- The user needs to see the clickable image link, not a description",
            "- Example: If Image Agent returns ![robot](https://example.com/image.png), show exactly that",
            "",
            "CRITICAL WRITING DELEGATION RULES:",
            "- Delegate to Writer Agent ONLY ONCE per user request",
            "- Do NOT call Writer Agent multiple times to edit or improve content",
            "- Accept the Writer Agent's first response as final",
            "- Include ALL requirements (tone, style, length) in the initial delegation",
            "",
            "KNOWLEDGE STORAGE EXAMPLES:",
            "- 'Store this poem' -> delegate to Personal AI Agent (will use knowledge tools)",
            "- 'Save this article' -> delegate to Personal AI Agent (will use knowledge tools)",
            "- 'Remember I like skiing' -> delegate to Personal AI Agent (will use memory tools)",
            "You can also answer directly, you don't HAVE to forward the question to a member agent.",
            "Reason about more complex questions before delegating to a member agent.",
            "If the user is only being conversational, encourage them to talk about themselves, life events, and feelings.",
        ],
        markdown=True,
        show_members_responses=True,
        show_tool_calls=True,
        enable_agentic_context=True,
        share_member_interactions=True,  # Disable shared interactions - memory agent handles this
        enable_user_memories=False,  # Disable team-level memory - memory agent handles this
    )

    logger.info(
        f"✅ Team created with {len(agent_team.members)} members - memory handled by Personal AI Agent"
    )
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
                        logging.error(
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
                                logging.error(
                                    f"⚠️ Error cleaning up {member_name}-{tool_name}: {e}"
                                )

        # 3. Force garbage collection to help with cleanup
        import gc

        gc.collect()

        # 4. Give asyncio time to close remaining connections
        await asyncio.sleep(0.5)

        logging.info("✅ Team cleanup completed")

    except Exception as e:
        logging.error(f"❌ Error during team cleanup: {e}")


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
        logging.error(f"⚠️ Error cleaning up {model_name} model: {e}")


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
        logging.error(f"⚠️ Error cleaning up {tool_name} tool: {e}")


def display_welcome_panel(console: Console, command_parser: CommandParser):
    """Display the welcome panel with team capabilities and commands."""
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


# Main execution
async def main(use_remote: bool = False, query: Optional[str] = None):
    """Main function to run the team with an enhanced CLI interface."""

    # Initialize Rich console for better formatting
    console = Console(force_terminal=True)

    console.print("🤖 [bold blue]Ollama Multi-Purpose Reasoning Team[/bold blue]")
    console.print("=" * 50)
    console.print("Initializing team with memory and knowledge capabilities...")
    console.print("This may take a moment on first run...")

    # DEBUG: Log the remote flag and URLs
    console.print(f"🔍 DEBUG: use_remote={use_remote}")
    console.print(f"🔍 DEBUG: PROVIDER={PROVIDER}")
    console.print(f"🔍 DEBUG: OLLAMA_URL={OLLAMA_URL}")
    console.print(f"🔍 DEBUG: REMOTE_OLLAMA_URL={REMOTE_OLLAMA_URL}")

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
        console.print("- ⚙️  SystemAgent: Execute system commands and shell operations")
        console.print("- 💰 Finance Agent: Get financial data and analysis")
        console.print("- 🏥 Medical Agent: Search PubMed for medical information")
        console.print("- ✍️  Writer Agent: Create content and written materials")
        console.print(
            "- 🎨 Image Agent: Create images using DALL-E based on descriptions"
        )
        console.print("- 🧮 Calculator Agent: Perform calculations and math")
        console.print("- 🐍 Python Agent: Create and execute Python code")
        console.print("- 📁 File System Agent: Read and write files in the system")

        # If a one-off query was provided, process it and exit
        if query:
            try:
                # Parse the command using the same system as the interactive CLI
                command_parser = CommandParser()
                command_handler, remaining_text, kwargs = command_parser.parse_command(
                    query
                )

                # If it's a memory command, execute it with the memory agent
                if command_handler and memory_agent:
                    try:
                        if remaining_text is not None:
                            await command_handler(memory_agent, remaining_text, console)
                        else:
                            await command_handler(memory_agent, console)
                    except Exception as e:
                        console.print(f"💥 Error executing memory command: {e}")
                else:
                    # Otherwise, treat as regular team query - use same method as interactive CLI
                    console.print("🤖 [bold green]Team:[/bold green]")
                    await team.aprint_response(query, stream=True, show_full_reasoning=True)

            except Exception as e:
                console.print(f"💥 Error: {e}")
            finally:
                await cleanup_team(team)
            return

        # Initialize command parser
        command_parser = CommandParser()

        # Display the enhanced welcome panel
        console.print("\n")
        display_welcome_panel(console, command_parser)

        # Fix: Show the correct URL based on use_remote flag
        if PROVIDER == "ollama":
            actual_url = REMOTE_OLLAMA_URL if use_remote else OLLAMA_URL
        else:
            actual_url = REMOTE_LMSTUDIO_URL if use_remote else LMSTUDIO_URL

        console.print(f"🖥️  Using {PROVIDER} model {LLM_MODEL} at: {actual_url}")

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
                    console.print("\n")
                    display_welcome_panel(console, command_parser)
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
                    console.print("\n  [yellow]Image Creation:[/yellow]")
                    console.print("    - 'Create an image of a futuristic AI robot'")
                    console.print(
                        "    - 'Generate a picture of a sunset over mountains'"
                    )
                    console.print(
                        "    - 'Make an abstract art piece with vibrant colors'"
                    )
                    console.print("\n  [yellow]Math & Calculations:[/yellow]")
                    console.print("    - 'Calculate the square root of 144'")
                    console.print("    - 'What's 15% of 250?'")
                    continue

                # If not a command, treat as regular team chat
                try:
                    console.print("🤖 [bold green]Team:[/bold green]")

                    # Use non-streaming response for better response parsing
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
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Run a one-off query against the initialized team and exit",
    )
    args = parser.parse_args()

    print("Starting Personal Agent Reasoning Team...")
    asyncio.run(main(use_remote=args.remote, query=args.query))


if __name__ == "__main__":
    # Run the main function
    cli_main()
    sys.exit(0)

# end of file
