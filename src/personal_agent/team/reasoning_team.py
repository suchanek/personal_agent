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

Specialized Agents: (not all may be used at once)
    - **Memory Agent**: Manages personal information and factual knowledge storage/retrieval
    - **Web Agent**: Performs web searches using DuckDuckGo search
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
Version: 0.8.72
Last Revision: 2025-10-14 20:06:15
Author: Eric G. Suchanek, PhD

"""

# pylint: disable=C0415,W0212,C0301,W0718

import argparse
import asyncio
import logging
import os
import sys
from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.team.team import Team
from agno.tools.calculator import CalculatorTools
from agno.tools.dalle import DalleTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.pubmed import PubmedTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.toolkit import Toolkit
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from personal_agent.core.agent_instruction_manager import InstructionLevel
from personal_agent.team.team_instructions import TeamAgentInstructions

# Import your personal agent components
try:
    # Try relative imports first (when used as a module)
    from ..cli.command_parser import CommandParser
    from ..config.settings import (
        HOME_DIR,
        LLM_MODEL,
        LMSTUDIO_URL,
        OLLAMA_URL,
        OPENAI_URL,
        PROVIDER,
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

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    from personal_agent.cli.command_parser import CommandParser
    from personal_agent.config.settings import (
        HOME_DIR,
        LLM_MODEL,
        LMSTUDIO_URL,
        OLLAMA_URL,
        OPENAI_URL,
        PROVIDER,
        REMOTE_LMSTUDIO_URL,
        REMOTE_OLLAMA_URL,
    )
    from personal_agent.config.user_id_mgr import get_userid
    from personal_agent.core.agent_model_manager import AgentModelManager
    from personal_agent.core.agno_agent import AgnoPersonalAgent
    from personal_agent.tools.personal_agent_tools import (
        PersonalAgentFilesystemTools,
        PersonalAgentSystemTools,
    )
    from personal_agent.utils import setup_logging

# DEPRECATED: These global model variables are being phased out in favor of PersonalAgentConfig
# They are kept for backward compatibility but should not be used directly
# Instead, use get_config().model or pass model_name parameter explicitly
WRITER_MODEL = LLM_MODEL
SYSTEM_MODEL = LLM_MODEL
CODING_MODEL = SYSTEM_MODEL
MEMORY_AGENT_MODEL = LLM_MODEL

# Load environment variables
load_dotenv()

# Configure logging

logger = setup_logging(__name__)


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
    "- You are a memory and knowledge agent. Return tool responses immediately.",
    "- Optimize token use: prefer list_all_memories over get_all_memories to save tokens!",
    "TOOL SELECTION:",
    "- Personal info → memory tools (store_user_memory, get_all_memories, etc.)",
    "- Documents/articles → knowledge tools (ingest_knowledge_text, query_knowledge_base)",
    "FUNCTION SELECTION:",
    "- list_all_memories: summaries, overviews, quick lists, counts, general requests",
    "- get_all_memories: detailed content, full information, when explicitly requested",
    "- Default to list_all_memories unless details specifically requested",
    "COMMON PATTERNS:",
    "- 'Remember I...' → store_user_memory",
    "- 'What do you remember about me?' → list_all_memories (no params) → return immediately",
    "- 'list/show memories', 'how many', 'summary' → list_all_memories (no params)",
    "- 'detailed/full/complete memory info' → get_all_memories (no params)",
    "- 'Store this poem/article' → ingest_knowledge_text",
    "PATTERN MATCHING:",
    "- list_all_memories keywords: 'list', 'show', 'what memories', 'how many', 'summary', 'stored'",
    "- get_all_memories keywords: 'detailed', 'full', 'complete', 'everything about', 'all details'",
    "- When in doubt, choose list_all_memories (more efficient and user-friendly)",
    "Execute tools directly and return results directly.",
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
                "🚨 DIAGNOSTIC: write_original_content called - topic: '%s', style: '%s', type: '%s', length: %d",
                topic,
                style,
                content_type,
                length,
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
                        lines.append("Beauty and wonder combined")
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
                "🔍 DIAGNOSTIC: Generated %s about %s (%d characters)",
                content_type,
                topic,
                len(content),
            )
            return content

        except Exception as e:
            error_msg = f"Error generating content: {str(e)}"
            logger.error("🔍 DIAGNOSTIC: %s", error_msg)
            return error_msg


def create_writer_agent(
    debug: bool = False, instruction_level: InstructionLevel = InstructionLevel.CONCISE
) -> Agent:
    """Create a specialized writing agent.

    :param debug: Enable debug mode
    :param instruction_level: Instruction sophistication level
    :return: Configured writing agent
    """
    writing_tools = WritingTools()
    agent = Agent(
        name="Writer Agent",
        role="Create written content in the requested tone and style",
        model=AgentModelManager.create_model_from_config(),
        debug_mode=debug,
        tools=[writing_tools],  # Use the instance, not the class
        instructions=TeamAgentInstructions.get_writer_agent_instructions(
            instruction_level
        ),
        markdown=True,
        show_tool_calls=False,  # CRITICAL: Always show tool calls to ensure execution
        add_name_to_instructions=True,
    )
    logger.debug("Created Writer Agent with custom writing tools")
    return agent


def create_image_agent(
    debug: bool = False, instruction_level: InstructionLevel = InstructionLevel.CONCISE
) -> Agent:
    """Create a specialized image creation agent using DALL-E with enhanced error handling.

    :param debug: Enable debug mode
    :param instruction_level: Instruction sophistication level
    :return: Configured image creation agent
    """
    agent = Agent(
        name="Image Agent",
        role="Create images using DALL-E based on text descriptions with comprehensive error handling",
        model=AgentModelManager.create_model_from_config(),
        debug_mode=debug,  # Always enable debug mode for better error tracking
        tools=[
            DalleTools(model="dall-e-3", size="1792x1024", quality="hd", style="vivid"),
        ],
        instructions=TeamAgentInstructions.get_image_agent_instructions(
            instruction_level
        ),
        markdown=True,
        show_tool_calls=False,  # Enable tool call display for better debugging
        add_name_to_instructions=True,
    )

    logger.debug(
        "🚨 DIAGNOSTIC: Created Enhanced Image Agent with comprehensive error handling and diagnostic logging"
    )
    return agent


def create_agents(
    debug: bool = False, instruction_level: InstructionLevel = InstructionLevel.CONCISE
):
    """Create all agents with the correct remote/local configuration.

    :param debug: Enable debug mode
    :param instruction_level: Instruction sophistication level for all agents
    """
    model = AgentModelManager.create_model_from_config()

    # Web search agent using Ollama
    web_agent = Agent(
        name="Web Agent",
        role="Search the web for information",
        model=model,
        tools=[DuckDuckGoTools()],
        instructions=TeamAgentInstructions.get_web_agent_instructions(
            instruction_level
        ),
        show_tool_calls=False,
        debug_mode=debug,
    )

    # System agent using PersonalAgentSystemTools
    system_agent = Agent(
        name="SystemAgent",
        role="Execute system commands and shell operations",
        model=model,
        tools=[PersonalAgentSystemTools(shell_command=True)],
        instructions=TeamAgentInstructions.get_system_agent_instructions(
            instruction_level
        ),
        show_tool_calls=False,
        debug_mode=debug,
    )

    # Finance agent using Ollama
    finance_agent = Agent(
        name="Finance Agent",
        role="Get financial data",
        model=model,
        tools=[
            YFinanceTools(
                stock_price=True,
                analyst_recommendations=True,
                company_info=True,
                company_news=True,
            ),
        ],
        instructions=TeamAgentInstructions.get_finance_agent_instructions(
            instruction_level
        ),
        show_tool_calls=False,
        debug_mode=debug,
    )

    # Medical agent that can search PubMed
    medical_agent = Agent(
        name="Medical Agent",
        role="Search pubmed for medical information",
        model=model,
        description="You are an AI agent that search PubMed for medical information.",
        tools=[PubmedTools()],
        instructions=TeamAgentInstructions.get_medical_agent_instructions(
            instruction_level
        ),
        show_tool_calls=False,
        debug_mode=debug,
    )

    # Writer agent using Ollama
    writer_agent = create_writer_agent(debug=debug, instruction_level=instruction_level)

    # Image agent using DALL-E
    image_agent = create_image_agent(debug=debug, instruction_level=instruction_level)

    # Calculator agent using Ollama
    calculator_agent = Agent(
        name="Calculator Agent",
        model=model,
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
        instructions=TeamAgentInstructions.get_calculator_agent_instructions(
            instruction_level
        ),
        show_tool_calls=False,
        debug_mode=debug,
    )

    python_agent = Agent(
        name="Python Agent",
        model=model,
        role="Create and Execute Python code",
        tools=[
            PythonTools(
                base_dir=HOME_DIR,  # Use user home directory as base with string
                save_and_run=True,
                run_files=True,
                read_files=True,
                list_files=True,
                run_code=True,
            ),
        ],
        instructions=TeamAgentInstructions.get_python_agent_instructions(
            instruction_level
        ),
        show_tool_calls=False,
        debug_mode=debug,
    )

    file_agent = Agent(
        name="File System Agent",
        model=model,
        role="Read and write files in the system",
        tools=[
            FileTools(
                base_dir=HOME_DIR,  # Use user home directory as base with string
                save_files=True,
                list_files=True,
                search_files=True,
            )
        ],
        instructions=TeamAgentInstructions.get_file_agent_instructions(
            instruction_level
        ),
        show_tool_calls=False,
        debug_mode=debug,
    )

    return (
        web_agent,
        system_agent,
        finance_agent,
        medical_agent,
        image_agent,
        python_agent,
        file_agent,
    )


def create_personalized_instructions(agent, base_instructions: list) -> list:
    """Create personalized instructions using the agent's user_id."""
    user_id = getattr(agent, "user_id", None)

    # Get the actual current user_id if not available from agent
    if not user_id:
        user_id = get_userid()

    # Always personalize instructions, even for default_user
    if user_id:
        # Replace "the user" and "user" with the actual user_id in instructions
        personalized_instructions = []
        for instruction in base_instructions:
            # Replace various forms of "user" references with the actual user_id
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
            # Also replace generic "user" at word boundaries to avoid partial replacements
            import re

            personalized_instruction = re.sub(
                r"\buser\b", user_id, personalized_instruction
            )
            personalized_instructions.append(personalized_instruction)

        logger.info("✅ Personalized instructions created for user: %s", user_id)
        return personalized_instructions
    else:
        logger.warning("⚠️ No user_id available, keeping generic instructions")
        return base_instructions


async def create_memory_agent(
    user_id: str = None,
    debug: bool = False,
    use_remote: bool = False,
    recreate: bool = False,
    single: bool = False,  # Simplified: just use single flag directly
) -> Agent:
    """Create a memory agent that uses the shared memory system.

    Args:
        user_id: User identifier for memory operations
        debug: Enable debug mode
        use_remote: Whether to use remote server endpoints
        recreate: Whether to recreate knowledge bases
        single: Whether to enable all tools (single-agent mode)
    """
    # Get user_id dynamically if not provided
    if user_id is None:
        from ..config.runtime_config import get_config

        config = get_config()
        user_id = config.user_id

    logger.info(
        "🔧 Memory agent mode: %s",
        "single-agent (all tools)" if single else "team mode (memory tools only)",
    )

    # Create AgnoPersonalAgent with the new simplified constructor.
    # The agent will pull its provider, model, etc., from the central config.
    # We only need to pass overrides or operational flags.
    from ..core.agent_instruction_manager import InstructionLevel

    memory_agent = AgnoPersonalAgent(
        enable_memory=True,
        enable_mcp=False,
        debug=debug,
        user_id=user_id,
        recreate=recreate,
        alltools=single,  # Use single flag directly to control alltools
        instruction_level=InstructionLevel.CONCISE,
        use_remote=use_remote,  # Still useful as an override
    )

    # After initialization, we need to set the shared memory and add the tools
    # Wait for initialization to complete
    await memory_agent._ensure_initialized()

    # Create personalized instructions using the user's name if available
    personalized_instructions = create_personalized_instructions(
        memory_agent, _memory_specific_instructions
    )
    # memory_agent.instructions = personalized_instructions

    logger.info("✅ Memory agent created with STANDARD instructions")
    return memory_agent


async def create_memory_writer_agent(
    user_id: str = None,
    debug: bool = False,
    use_remote: bool = False,
    recreate: bool = False,
) -> Agent:
    """Create a memory agent that uses the shared memory system and can write content."""
    if user_id is None:
        user_id = get_userid()

    memory_writer_agent = AgnoPersonalAgent(
        enable_memory=True,
        enable_mcp=False,
        debug=debug,
        user_id=user_id,
        recreate=recreate,
        alltools=False,
        initialize_agent=True,
        use_remote=use_remote,
    )

    await memory_writer_agent._ensure_initialized()
    memory_writer_agent.instructions = _memory_specific_instructions
    logger.debug("✅ Memory/Writer agent created")
    return memory_writer_agent


# Create the team
async def create_team(
    use_remote: bool = False, single: bool = False, recreate: bool = False
):
    """Create the team with shared memory context and your existing managers.

    Args:
        use_remote: Whether to use remote Ollama server
        single: Whether to run in single-agent mode with all tools enabled
    """
    from ..config.runtime_config import get_config

    try:
        from ..core.docker_integration import ensure_docker_user_consistency
    except ImportError:
        from personal_agent.core.docker_integration import (
            ensure_docker_user_consistency,
        )

    config = get_config()
    current_user_id = config.user_id

    print("🐳 Ensuring Docker and user synchronization...")
    docker_ready, docker_message = ensure_docker_user_consistency(
        user_id=current_user_id, auto_fix=True, force_restart=False
    )

    if docker_ready:
        print(f"✅ Docker synchronization successful: {docker_message}")
    else:
        print(f"⚠️ Docker synchronization failed: {docker_message}")
        print("Proceeding with team creation, but Docker services may be inconsistent")

    logger.info(
        "🔄 Creating team with provider: %s, model: %s (use_remote=%s)",
        config.provider,
        config.model,
        use_remote,
    )

    memory_agent = await create_memory_agent(
        user_id=current_user_id,
        debug=True,
        use_remote=use_remote,
        single=single,
        recreate=recreate,
    )

    agents = create_agents(debug=True)
    (
        web_agent,
        system_agent,
        finance_agent,
        medical_agent,
        image_agent,
        python_agent,
        file_agent,
    ) = agents

    agent_team = Team(
        name="Personal Agent Team",
        mode="coordinate",
        model=AgentModelManager.create_model_from_config(),
        memory=None,
        tools=[
            # ReasoningTools(add_instructions=True, add_few_shot=True),
        ],
        members=[
            memory_agent,  # Memory agent with your managers
            web_agent,
            system_agent,  # SystemAgent for shell commands
            finance_agent,
            image_agent,  # Image creation agent
            medical_agent,
            python_agent,
            file_agent,
        ],
        instructions=[
            "You are a team coordinator that delegates tasks to specialized agents.",
            f"The user you are interacting with is {current_user_id}",
            f"Be friendly and greet users by name, {current_user_id} when possible.",
            f"Your primary role is to elicit memories and stories from your potentially neuro-degenerative impaired user {current_user_id}",
            f"Help {current_user_id} feel good about themselves!",
            "",
            "CRITICAL SUCCESS RECOGNITION:",
            "- If you see 'Added memory for user' or 'ACCEPTED:' in the output, the memory storage was SUCCESSFUL",
            "- If you see 'Memory stored successfully' or similar confirmation, the task is COMPLETE",
            "- DO NOT make duplicate tool calls for the same task once you see success confirmation",
            "- Trust your team member responses. Don't overthink",
            "",
            "CRITICAL RESPONSE DISPLAY RULES:",
            "- When a team member provides results, DISPLAY THEIR ACTUAL RESULTS directly to the user",
            "- DO NOT interpret, summarize, or rewrite team member responses",
            "- DO NOT add your own <think> tags or commentary when displaying results",
            "- If a memory agent lists memories, show the actual list they provided",
            "- If a web agent finds information, show their actual findings",
            "- Your role is to PASS THROUGH the specialist results, not interpret them",
            "",
            "SIMPLE DELEGATION RULES:",
            "- Memory/personal info → Personal AI Agent (ONE call only per task)",
            "- Web searches → Web Agent",
            "- Financial data → Finance Agent",
            "- Math/calculations → Calculator Agent",
            "- Images → Image Agent",
            "- Code/Python → Python Agent",
            "- Files → File System Agent",
            "- System commands → SystemAgent",
            "- Medical info → Medical Agent",
            "",
            "- Do NOT make duplicate tool calls for the same task",
            "- Only make multiple calls if the first one fails or for different subtasks",
            "",
            "RESPONSE HANDLING:",
            "- Show complete responses from agents WITHOUT modification",
            "- For errors, show the error message to help the user",
            "- DO NOT add interpretation or commentary to specialist results",
            f"You can answer simple questions directly without delegation. Remember you are helping {current_user_id}.",
        ],
        markdown=True,
        show_members_responses=True,
        show_tool_calls=False,
        enable_agentic_context=False,
        share_member_interactions=True,  # Disable shared interactions - memory agent handles this
        enable_user_memories=False,  # Disable team-level memory - memory agent handles this
    )

    logger.info(
        "✅ Team created with %d members - memory handled by Personal AI Agent",
        len(agent_team.members),
    )
    return agent_team


async def cleanup_team(team):
    """Comprehensive cleanup of team resources to prevent ResourceWarnings."""
    logger.debug("🧹 Cleaning up team resources...")

    try:
        # 1. Close team-level resources
        if hasattr(team, "model") and team.model:
            try:
                await _cleanup_model(team.model, "Team")
            except Exception as e:
                logger.debug("⚠️ Error cleaning up team model: %s", e)

        if hasattr(team, "memory") and hasattr(team.memory, "db"):
            try:
                if hasattr(team.memory.db, "close"):
                    await team.memory.db.close()
                logger.debug("✅ Team memory database closed")
            except Exception as e:
                logger.debug("⚠️ Error closing team memory database: %s", e)

        # 2. Close member-level resources
        if hasattr(team, "members") and team.members:
            for i, member in enumerate(team.members):
                member_name = getattr(member, "name", f"Member-{i}")
                logger.debug("🔧 Cleaning up %s...", member_name)

                # Close member's model
                if hasattr(member, "model") and member.model:
                    try:
                        await _cleanup_model(member.model, member_name)
                    except Exception as e:
                        logger.debug("⚠️ Error cleaning up %s model: %s", member_name, e)

                # Close member's memory
                if hasattr(member, "memory") and hasattr(member.memory, "db"):
                    try:
                        if hasattr(member.memory.db, "close"):
                            await member.memory.db.close()
                        logger.debug("✅ %s memory database closed", member_name)
                    except Exception as e:
                        logging.error(
                            "⚠️ Error closing %s memory database: %s", member_name, e
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
                                    "⚠️ Error cleaning up %s-%s: %s",
                                    member_name,
                                    tool_name,
                                    e,
                                )

        # 3. Force garbage collection to help with cleanup
        import gc

        gc.collect()

        # 4. Give asyncio time to close remaining connections
        await asyncio.sleep(0.5)

        logger.debug("✅ Team cleanup completed")

    except Exception as e:
        logging.error("❌ Error during team cleanup: %s", e)


async def _cleanup_model(model, model_name: str):
    """Clean up a specific model's resources."""
    try:
        # Close HTTP sessions in the model
        if hasattr(model, "_session") and model._session:
            if not model._session.closed:
                await model._session.close()
            logger.debug("✅ %s model HTTP session closed", model_name)

        if hasattr(model, "session") and model.session:
            if not model.session.closed:
                await model.session.close()
            logger.debug("✅ %s model session closed", model_name)

        # Close any client connections
        if hasattr(model, "client"):
            if hasattr(model.client, "close"):
                await model.client.close()
            elif hasattr(model.client, "_session") and model.client._session:
                if not model.client._session.closed:
                    await model.client._session.close()
            logger.debug("✅ %s model client closed", model_name)

        # Handle OllamaTools specific cleanup
        if hasattr(model, "_client") and model._client:
            if hasattr(model._client, "close"):
                await model._client.close()
            logger.debug("✅ %s Ollama client closed", model_name)

    except Exception as e:
        logging.error("⚠️ Error cleaning up %s model: %s", model_name, e)


async def _cleanup_tool(tool, tool_name: str):
    """Clean up a specific tool's resources."""
    try:
        # Close HTTP sessions in tools
        if hasattr(tool, "_session") and tool._session:
            if not tool._session.closed:
                await tool._session.close()
            logger.debug("✅ %s tool HTTP session closed", tool_name)

        if hasattr(tool, "session") and tool.session:
            if not tool.session.closed:
                await tool.session.close()
            logger.debug("✅ %s tool session closed", tool_name)

        # Handle DuckDuckGo tools specifically
        if hasattr(tool, "ddgs"):
            if hasattr(tool.ddgs, "_session") and tool.ddgs._session:
                if not tool.ddgs._session.closed:
                    await tool.ddgs._session.close()
                logger.debug("✅ %s DuckDuckGo session closed", tool_name)

            if hasattr(tool.ddgs, "close"):
                await tool.ddgs.close()
                logger.debug("✅ %s DuckDuckGo client closed", tool_name)

        # Handle YFinance tools
        if hasattr(tool, "_session") and "yfinance" in str(type(tool)).lower():
            if tool._session and not tool._session.closed:
                await tool._session.close()
                logger.debug("✅ %s YFinance session closed", tool_name)

        # Close any other client connections
        if hasattr(tool, "client"):
            if hasattr(tool.client, "close"):
                await tool.client.close()
            elif hasattr(tool.client, "_session") and tool.client._session:
                if not tool.client._session.closed:
                    await tool.client._session.close()
            logger.debug("✅ %s tool client closed", tool_name)

    except Exception as e:
        logging.error("⚠️ Error cleaning up %s tool: %s", tool_name, e)


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
async def main(
    use_remote: bool = False,
    query: Optional[str] = None,
    recreate: bool = False,
    instruction_level: InstructionLevel = InstructionLevel.STANDARD,
    single: bool = False,
):
    """Main function to run the team with an enhanced CLI interface."""

    # Initialize Rich console for better formatting
    console = Console(force_terminal=True)

    console.print("🤖 [bold blue]Ollama Multi-Purpose Reasoning Team[/bold blue]")
    console.print("=" * 50)
    console.print("Initializing team with memory and knowledge capabilities...")
    console.print("This may take a moment on first run...")

    # Get configuration
    from personal_agent.config import settings
    from personal_agent.config.runtime_config import get_config

    config = get_config()

    # DEBUG: Log the remote flag and URLs from config
    console.print(f"🔍 DEBUG: use_remote={use_remote}")
    console.print(f"🔍 DEBUG: PROVIDER={config.provider}")
    console.print(f"🔍 DEBUG: OLLAMA_URL={settings.OLLAMA_URL}")
    console.print(f"🔍 DEBUG: REMOTE_OLLAMA_URL={settings.REMOTE_OLLAMA_URL}")

    try:
        # Create the team
        team = await create_team(
            use_remote=use_remote, single=single, recreate=recreate
        )

        # Get the memory agent for CLI commands
        memory_agent = None
        if hasattr(team, "members") and team.members:
            logger.debug(
                "🔍 Searching for memory agent among %d team members", len(team.members)
            )
            for member in team.members:
                member_name = getattr(member, "name", "Unknown")
                logger.debug("🔍 Checking member: %s", member_name)
                if hasattr(member, "name") and "Personal-Agent" in member.name:
                    memory_agent = member
                    logger.info("✅ Found memory agent: %s", member.name)
                    break

            if not memory_agent:
                logger.warning("⚠️ Memory agent not found! Available members:")
                for member in team.members:
                    member_name = getattr(member, "name", "Unknown")
                    logger.warning("   - %s", member_name)

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

                # If it's a memory command, execute it directly with the memory agent
                if command_handler and memory_agent:
                    try:
                        console.print("🧠 [bold green]Memory Agent:[/bold green]")
                        if remaining_text is not None:
                            await command_handler(memory_agent, remaining_text, console)
                        else:
                            await command_handler(memory_agent, console)
                    except Exception as e:
                        console.print(f"💥 Error executing memory command: {e}")
                else:
                    # Otherwise, treat as regular team query - use same method as interactive CLI
                    console.print("🤖 [bold green]Team:[/bold green]")
                    await team.aprint_response(
                        query, stream=True, show_full_reasoning=True
                    )

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

        # Get provider from config (already imported above)
        # config is already available from earlier in the function

        # Determine the correct URL based on provider and use_remote flag
        match config.provider:
            case "ollama":
                actual_url = (
                    settings.REMOTE_OLLAMA_URL if use_remote else settings.OLLAMA_URL
                )
            case "openai":
                actual_url = settings.OPENAI_URL
            case "lm-studio":
                actual_url = (
                    settings.REMOTE_LMSTUDIO_URL
                    if use_remote
                    else settings.LMSTUDIO_URL
                )
            case _:
                actual_url = "unknown"
                logger.warning("Unknown provider: %s", config.provider)

        console.print(
            f"🖥️  Using {config.provider} model {config.model} at: {actual_url}"
        )

        # Enhanced interactive chat loop with command parsing
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Handle team-specific commands FIRST (before memory commands)
                if user_input.lower() == "help":
                    console.print("\n")
                    display_welcome_panel(console, command_parser)
                    continue

                elif user_input.lower() == "clear":

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
                    console.print("    - 'memories' - Show all stored memories")
                    console.print("    - 'analysis' - Show memory analysis")
                    console.print("    - 'stats' - Show memory statistics")
                    console.print(
                        "    - 'wipe' - Clear all memories (requires confirmation)"
                    )
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

                # Parse memory commands using CommandParser
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

                # If it's a recognized memory command, execute it directly with the memory agent
                if command_handler and memory_agent:
                    try:
                        console.print("🧠 [bold green]Memory Agent:[/bold green]")
                        logger.debug(
                            "🔍 Executing command handler: %s", command_handler.__name__
                        )
                        # The command handlers expect an AgnoPersonalAgent, so we pass the memory_agent
                        # which is an AgnoPersonalAgent instance
                        if remaining_text is not None:
                            await command_handler(memory_agent, remaining_text, console)
                        else:
                            await command_handler(memory_agent, console)
                        continue
                    except Exception as e:
                        console.print(f"💥 Error executing command: {e}")
                        logger.error("Command execution failed: %s", e, exc_info=True)
                        continue
                elif command_handler and not memory_agent:
                    console.print(
                        "❌ Memory agent not available - cannot execute memory commands"
                    )
                    logger.error("Command handler found but memory agent is None")
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
        except Exception as e:
            console.print(f"Warning during cleanup: {e}")


def cli_main():
    """Entry point for the paga_team_cli command."""
    # Get configuration instance
    from personal_agent.config.runtime_config import get_config

    config = get_config()

    parser = argparse.ArgumentParser(
        description="Run the Ollama Multi-Purpose Reasoning Team"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=config.provider,  # Use the provider from config
        choices=["ollama", "openai", "lm-studio"],
        help=f"The LLM provider to use. Defaults to '{config.provider}' from configuration.",
    )
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama server"
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Run in single-agent mode with all tools enabled",
    )
    parser.add_argument(
        "--recreate", action="store_true", help="Recreate the knowledge base"
    )
    parser.add_argument(
        "--instruction-level",
        type=str,
        default="STANDARD",
        help="Set the instruction level for the agent (MINIMAL, CONCISE, STANDARD, EXPLICIT, EXPERIMENTAL)",
    )
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Run a one-off query against the initialized team and exit",
    )
    args = parser.parse_args()

    # Convert string instruction level to enum
    try:
        instruction_level_enum = InstructionLevel[args.instruction_level.upper()]
    except KeyError:
        valid_levels = [e.name for e in InstructionLevel]
        print(f"Error: Invalid instruction level '{args.instruction_level}'.")
        print(f"Valid options: {', '.join(valid_levels)}")
        return

    # Update configuration based on command-line arguments
    if args.provider != config.provider:
        config.set_provider(args.provider, auto_set_model=True)
        print(f"🔧 Provider set to: {args.provider}")

    if args.remote:
        config.set_use_remote(True)
        print("🔧 Remote endpoints enabled")

    print(f"Starting Personal Agent Reasoning Team with provider: {config.provider}...")
    asyncio.run(
        main(
            use_remote=args.remote,
            query=args.query,
            recreate=args.recreate,
            instruction_level=instruction_level_enum,
            single=args.single,
        )
    )


if __name__ == "__main__":
    # Run the main function
    cli_main()
    sys.exit(0)

# end of file
